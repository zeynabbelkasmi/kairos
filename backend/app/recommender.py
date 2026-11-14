"""Vrais lieux (OpenStreetMap) + catalogue local, sélection aléatoire pondérée, justification par le LLM avec repli."""
import json
import logging
import os
import random
import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path

import httpx

from .database import Activity, all_activities
from .osm import CATEGORY_TAG, nearby
from .schemas import Recommendation, RecommendRequest

log = logging.getLogger("kairos")


def _load_dotenv() -> None:
    """Charge backend/.env (KEY=VALUE) sans dépendance externe."""
    env = Path(__file__).resolve().parent.parent / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()

try:  # certificats Windows (antivirus type Kaspersky qui intercepte le HTTPS)
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass


def _default_provider() -> str:
    if os.getenv("OLLAMA_API_KEY"):
        return "ollama_cloud"
    if os.getenv("GEMINI_API_KEY"):
        return "gemini"
    return "local"


# Fournisseur : "ollama_cloud" (ollama.com), "gemini" (API Google) ou "local" (Ollama / LM Studio sur ta machine)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", _default_provider()).lower()
if LLM_PROVIDER == "ollama_cloud":
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://ollama.com/v1")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-oss:20b")
    LLM_API_KEY = os.getenv("OLLAMA_API_KEY", "")
elif LLM_PROVIDER == "gemini":
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai")
    LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    LLM_API_KEY = os.getenv("GEMINI_API_KEY", "")
else:
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")  # Ollama local par défaut
    LLM_MODEL = os.getenv("LLM_MODEL", "qwen3:8b")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "120"))

RABAT = (34.0209, -6.8416)  # position par défaut si l'utilisateur ne partage pas la sienne
CATEGORY_ORDER = ["outdoor", "creative", "intellectual"]
COLOR = {"outdoor": "sauge", "creative": "peche", "intellectual": "lilas"}
PER_CATEGORY = 4

MOOD_TAGS = {
    "fatigue": ["fatigue", "calme"],
    "creatif": ["creatif"],
    "calme": ["calme", "nature"],
    "energie": ["energie", "mouvement"],
    "sature": ["ecran_detox", "calme", "nature"],
}
KEYWORDS = {
    "nature": ["air", "dehors", "nature", "marcher", "promen", "mer", "ocean", "parc", "jardin", "soleil"],
    "lecture": ["lire", "lecture", "livre", "philo", "penser", "reflechir"],
    "ecriture": ["ecrire", "journal", "introspect", "vider la tete"],
    "creatif": ["creer", "dessin", "manuel", "creati", "bricol", "diy", "peindre"],
    "mouvement": ["bouger", "courir", "sport", "energie", "marche"],
    "calme": ["calme", "repos", "stress", "anxi", "fatigu", "sature", "epuise", "decompress"],
    "ecran_detox": ["ecran", "telephone", "scroll", "reseaux", "instagram", "tiktok"],
    "social": ["ami", "amie", "copain", "famille", "ensemble", "deux"],
}

OSM_TEMPLATES = [
    "{label} à {d} m de toi : un endroit tout proche pour changer d'air.",
    "À {d} m seulement, {label_low} : parfait pour décrocher sans effort.",
    "Un {label_low} à {d} m, idéal pour une pause loin des écrans.",
]


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def mood_key(mood: str | None) -> str | None:
    m = norm(mood or "")
    for key in MOOD_TAGS:
        if key in m:
            return key
    if "quete" in m:
        return "calme"
    return None


WANT = {
    "cafe": ["cafe", "cafes", "coffee", "coffees", "coffeeshop", "coffeeshops", "coffe", "salon de the"],
    "restaurant": ["restaurant", "restaurants", "resto", "restos", "manger", "diner", "dejeuner"],
    "park": ["parc", "parcs", "jardin", "jardins", "park", "parks", "nature", "foret", "promenade"],
    "museum": ["musee", "musees", "museum", "galerie", "galeries", "expo", "exposition"],
    "library": ["bibliotheque", "bibliotheques", "librairie", "librairies", "livre", "livres"],
    "viewpoint": ["vue", "vues", "panorama", "point de vue", "coucher"],
    "art": ["atelier", "ateliers", "peinture", "poterie", "craft", "crafts", "dessin"],
}
STOP = set("je suis avec besoin pour des les une dans envie faire prendre sortir mais trop tres pas qui que "
           "sur plus aime aimerais voudrais bien ce cette ses leur nous vous elle juste sans chez entre tout "
           "moment endroit endroits lieu lieux autour pres proche veux veut voulais cherche chercher trouver "
           "aller allons quelque chose idee idees propose proposer propositions montre conseille recommande "
           "shop shops place places spot spots sympa calme petit petite bonne bon want find near some".split())


def _fuzzy(token: str, syn: str) -> bool:
    """Tolère les fautes de frappe (« coffeshops », « bibliotheqe ») sur les mots assez longs."""
    if token == syn:
        return True
    return len(token) >= 5 and len(syn) >= 5 and SequenceMatcher(None, token, syn).ratio() >= 0.85


def intent(text: str) -> tuple[set[str], list[str]]:
    """Ce que l'utilisateur demande : types de lieux (café, parc…) et mots à chercher dans les noms."""
    t = norm(text)
    tokens = re.findall(r"[a-z0-9]+", t)
    wanted: set[str] = set()
    matched: set[str] = set()  # mots déjà reconnus comme type de lieu
    for ptype, syns in WANT.items():
        for syn in syns:
            if " " in syn:
                if syn in t:
                    wanted.add(ptype)
                    matched.update(syn.split())
                continue
            for tok in tokens:
                if _fuzzy(tok, syn):
                    wanted.add(ptype)
                    matched.add(tok)
    mood_words = [k for ks in KEYWORDS.values() for k in ks]  # « fatiguée », « écrans »… = humeur, pas un nom de lieu
    words = [w for w in tokens if len(w) >= 4 and w not in STOP and w not in matched
             and not any(k in w for k in mood_words)]
    return wanted, list(dict.fromkeys(words))[:3]


def score(a: Activity, req: RecommendRequest) -> float:
    tags = set(a.vibe_tags)
    s = 0.0
    if not req.is_alone and not a.is_social:
        s -= 5
    if req.is_alone and not a.solo_ok:
        return -100
    if not req.is_alone and "social" in tags:
        s += 1.5
    mk = mood_key(req.mood)
    if mk:
        s += 2 * len(tags & set(MOOD_TAGS[mk]))
    text = norm(req.user_input)
    for tag, words in KEYWORDS.items():
        if tag in tags and any(w in text for w in words):
            s += 1.5
    return s


@dataclass
class Cand:
    """Un choix possible : lieu réel OSM ou activité du catalogue local."""
    id: str
    category: str
    category_tag: str
    title: str
    location: str
    description: str
    kind: str  # "osm" ou "db"
    type: str = "outdoor"
    image_url: str = ""
    maps_url: str | None = None
    instructions: list[str] = field(default_factory=list)
    lat: float | None = None
    lon: float | None = None
    distance_m: int | None = None
    vibe_tags: list[str] = field(default_factory=list)


def from_db(a: Activity) -> Cand:
    return Cand(
        id=a.id, category=a.category, category_tag=a.category_tag, title=a.title,
        location=a.location_tag, description=a.description, kind="db",
        type=a.type, image_url="", maps_url=a.maps_url,  # pas de photo catalogue : les liens Unsplash étaient approximatifs
        instructions=a.instructions, vibe_tags=a.vibe_tags,
    )


def from_osm(p: dict, rng: random.Random) -> Cand:
    d = p["distance_m"]
    template = rng.choice(OSM_TEMPLATES)
    desc = template.format(label=p["label"], label_low=p["label"][0].lower() + p["label"][1:], d=d)
    return Cand(
        id=p["id"], category=p["category"], category_tag=CATEGORY_TAG[p["category"]],
        title=p["name"], location=f"{p['label']} · à {d} m", description=desc, kind="osm",
        type="indoor" if p["category"] != "outdoor" else "outdoor",
        image_url=p["image"],
        maps_url=f"https://www.google.com/maps/search/?api=1&query={p['lat']},{p['lon']}",
        lat=p["lat"], lon=p["lon"], distance_m=d,
    )


async def candidates(req: RecommendRequest) -> tuple[dict[str, list[Cand]], str]:
    """Pour chaque catégorie : quelques lieux OSM tirés au hasard + activités du catalogue les mieux notées.
    Le hasard (et le bruit sur le score) fait que deux demandes identiques ne donnent pas les mêmes options."""
    rng = random.Random()
    lat, lon = (req.lat, req.lon) if req.lat is not None and req.lon is not None else RABAT
    wanted, words = intent(req.user_input)
    places = await nearby(lat, lon, req.radius, wanted, words)
    osm_down = places is None
    places = places or []
    requested = bool(wanted or words) and not osm_down  # OSM injoignable : on ne filtre pas le catalogue à vide
    if requested:
        places = [p for p in places if p["type"] in wanted or p["name_match"]]

    db_scored: dict[str, list[tuple[float, Activity]]] = {c: [] for c in CATEGORY_ORDER}
    for a in all_activities():
        s = score(a, req)
        if s > -100:
            db_scored[a.category].append((s + rng.uniform(0, 2), a))

    out: dict[str, list[Cand]] = {}
    for cat in CATEGORY_ORDER:
        osm_pool = [from_osm(p, rng) for p in places if p["category"] == cat]
        rng.shuffle(osm_pool)
        chosen = osm_pool[:PER_CATEGORY]
        db_ranked = [from_db(a) for _, a in sorted(db_scored[cat], key=lambda t: t[0], reverse=True)]
        if requested and cat == "outdoor":  # demande précise : seul le catalogue qui correspond au nom est gardé
            db_ranked = [c for c in db_ranked if any(norm(w) in norm(c.title + " " + c.location) for w in words)]
        chosen += db_ranked[: PER_CATEGORY - len(chosen)]
        out[cat] = chosen
    if osm_down:
        return out, "osm_down"  # cartes en ligne injoignables : seulement le catalogue local
    if requested and not places and not out["outdoor"]:
        return out, "no_match"  # rien de proche pour ta demande : la carte sortie reste vide
    return out, ("osm_match" if requested else ("osm" if places else "catalogue"))


SYSTEM_PROMPT = """Tu es Kairos, un assistant anti-doomscrolling bienveillant.
On te donne l'état de l'utilisateur et des lieux ou activités candidats (avec leur id), groupés par catégorie. Les lieux avec une distance sont de vrais endroits proches de l'utilisateur.
Ta tâche : choisir EXACTEMENT une option par catégorie demandée, la plus adaptée, et écrire pour chacune une phrase courte (max 25 mots), chaleureuse, en français, tutoyant l'utilisateur, qui explique POURQUOI elle correspond à son besoin.
Règles strictes :
- Utilise UNIQUEMENT des id présents dans la liste fournie. N'invente jamais de lieu.
- Réponds UNIQUEMENT avec un JSON valide, sans texte autour, sans markdown, au format :
{"picks": [{"id": "<id>", "description": "<phrase personnalisée>"}]}"""


def build_user_prompt(req: RecommendRequest, cands: dict[str, list[Cand]], cats: list[str]) -> str:
    lines = [
        f"Message de l'utilisateur : \"{req.user_input}\"",
        f"Humeur : {req.mood or 'non précisée'}",
        f"Contexte social : {'seul(e)' if req.is_alone else 'accompagné(e)'}",
        f"Nombre d'options à retourner : {len(cats)} (catégories : {', '.join(cats)})",
        "",
        "Candidats :",
    ]
    for c in cats:
        lines.append(f"[{c}]")
        for a in cands[c]:
            dist = f" | à {a.distance_m} m" if a.distance_m is not None else ""
            tags = f" | tags={','.join(a.vibe_tags)}" if a.vibe_tags else ""
            lines.append(f"- id={a.id} | {a.title} | {a.location}{dist} | {a.description}{tags}")
    if LLM_PROVIDER == "local":
        lines.append("\n/no_think")  # désactive le mode réflexion de Qwen 3
    return "\n".join(lines)


def parse_llm_json(text: str) -> dict:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        raise ValueError("pas de JSON dans la réponse du LLM")
    return json.loads(m.group(0))


async def ask_llm(req: RecommendRequest, cands: dict[str, list[Cand]], cats: list[str]) -> dict[str, tuple[str, str]]:
    """Retourne {category: (id, description)} choisi par le LLM."""
    payload = {
        "model": LLM_MODEL,
        "temperature": 0.9,  # plus de variété d'une demande à l'autre
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(req, cands, cats)},
        ],
    }
    headers = {}
    if LLM_API_KEY:
        headers["Authorization"] = f"Bearer {LLM_API_KEY}"
    if LLM_PROVIDER in ("gemini", "ollama_cloud"):
        payload["response_format"] = {"type": "json_object"}
    async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
        r = await client.post(f"{LLM_BASE_URL}/chat/completions", json=payload, headers=headers)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
    data = parse_llm_json(content)
    by_id = {a.id: a for c in cats for a in cands[c]}
    picks: dict[str, tuple[str, str]] = {}
    for p in data.get("picks", []):
        a = by_id.get(str(p.get("id")))
        desc = str(p.get("description") or "").strip()
        if a and a.category not in picks:
            picks[a.category] = (a.id, desc or a.description)
    return picks


def to_rec(c: Cand, description: str) -> Recommendation:
    return Recommendation(
        id=c.id, type=c.type, category_tag=c.category_tag, tag_color=COLOR[c.category],
        title=c.title, location_name=c.location, image_url=c.image_url,
        description=description, maps_url=c.maps_url, instructions=c.instructions,
        lat=c.lat, lon=c.lon, distance_m=c.distance_m,
    )


async def recommend(req: RecommendRequest) -> tuple[list[Recommendation], str, str]:
    cats = CATEGORY_ORDER[: max(2, min(3, req.max_options))]
    cands, places_source = await candidates(req)
    cats = [c for c in cats if cands[c]]
    picks: dict[str, tuple[str, str]] = {}
    source = "llm"
    try:
        picks = await ask_llm(req, cands, cats)
    except Exception as e:  # LLM absent, timeout, JSON invalide…
        log.warning("LLM indisponible, repli sans IA : %s", e)
        source = "fallback"
    by_id = {a.id: a for c in cats for a in cands[c]}
    recs = []
    for c in cats:
        if c in picks:
            aid, desc = picks[c]
            recs.append(to_rec(by_id[aid], desc))
        else:
            pick = random.choice(cands[c][:3])  # variété même sans IA
            recs.append(to_rec(pick, pick.description))
    random.shuffle(recs)
    return recs, source, places_source
