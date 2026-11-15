"""Generate screen-free activities and combine them with verified Google Places results."""
import json
import logging
import os
import random
import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from uuid import uuid4

import httpx

from .database import list_completed
from .imdb_search import search_film, wants_film
from .schemas import Recommendation, RecommendRequest

log = logging.getLogger("kairos")


def _load_dotenv() -> None:
    """Charge backend/.env (KEY=VALUE) sans dÃ©pendance externe."""
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
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")  # Ollama local par dÃ©faut
    LLM_MODEL = os.getenv("LLM_MODEL", "qwen3:8b")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "120"))

CATEGORY_ORDER = ["outdoor", "creative", "intellectual"]
COLOR = {"outdoor": "sauge", "creative": "peche", "intellectual": "lilas"}
CATEGORY_TAG = {"outdoor": "SORTIE LOCALE", "creative": "IDÉE CRÉATIVE", "intellectual": "IDÉE À DÉCOUVRIR"}

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


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def parse_llm_json(text: str) -> dict:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        raise ValueError("Le modèle n'a pas renvoyé de JSON.")
    result = json.loads(match.group(0))
    if not isinstance(result, dict):
        raise ValueError("La réponse du modèle doit être un objet JSON.")
    return result


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
    """TolÃ¨re les fautes de frappe (Â« coffeshops Â», Â« bibliotheqe Â») sur les mots assez longs."""
    if token == syn:
        return True
    return len(token) >= 5 and len(syn) >= 5 and SequenceMatcher(None, token, syn).ratio() >= 0.85


def intent(text: str) -> tuple[set[str], list[str]]:
    """Ce que l'utilisateur demande : types de lieux (cafÃ©, parcâ€¦) et mots Ã  chercher dans les noms."""
    t = norm(text)
    tokens = re.findall(r"[a-z0-9]+", t)
    wanted: set[str] = set()
    matched: set[str] = set()  # mots dÃ©jÃ  reconnus comme type de lieu
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
    mood_words = [k for ks in KEYWORDS.values() for k in ks]  # Â« fatiguÃ©e Â», Â« Ã©crans Â»â€¦ = humeur, pas un nom de lieu
    words = [w for w in tokens if len(w) >= 4 and w not in STOP and w not in matched
             and not any(k in w for k in mood_words)]
    return wanted, list(dict.fromkeys(words))[:3]


@dataclass
class Cand:
    id: str
    category: str
    category_tag: str
    title: str
    location: str
    description: str
    type: str = "indoor"
    image_url: str = ""
    maps_url: str | None = None
    instructions: list[str] = field(default_factory=list)
    lat: float | None = None
    lon: float | None = None
    distance_m: int | None = None
    is_place: bool = False
    rating: float | None = None
    user_rating_count: int | None = None
    photo_author: str = ""
    photo_author_url: str = ""
    photo_google_maps_uri: str = ""
    opening_hours: str = ""
    is_film: bool = False
    imdb_url: str | None = None
    year: int | None = None
    runtime_min: int | None = None
    genres: list[str] = field(default_factory=list)


def _idea_fallback(req: RecommendRequest) -> list[Cand]:
    """Compose varied suggestions from reusable parts when the LLM is offline."""
    rng = random.SystemRandom()
    recent = {norm(row.title) for row in list_completed()[:100]}
    ideas: list[Cand] = []
    for category in CATEGORY_ORDER:
        for _ in range(20):
            if category == "outdoor":
                action = rng.choice(["Micro-balade", "Exploration à pied", "Pause d'observation", "Boucle tranquille"])
                theme = rng.choice(["les sons du quartier", "les façades et les couleurs", "les arbres et les ombres", "les détails insolites", "les odeurs du marché"])
                title = f"{action} : {theme}"
                description = f"Une sortie courte pour explorer {theme}, téléphone rangé."
                instructions = ["Choisis un itinéraire public et sûr près de toi.", "Marche 15 minutes sans regarder ton téléphone.", f"Repère trois détails liés à {theme}.", "Au retour, garde ton détail préféré en mémoire."]
                location, rec_type, tag = "Près de toi · sans lieu imposé", "outdoor", "IDÉE DE SORTIE"
            elif category == "creative":
                medium = rng.choice(["croquis", "collage", "petit texte", "composition de couleurs", "pliage papier"])
                subject = rng.choice(["un objet du quotidien", "un souvenir", "une émotion", "un lieu imaginaire", "les formes autour de toi"])
                title = f"{medium.capitalize()} : {subject}"
                description = f"Crée quelque chose de simple avec {medium}, en prenant {subject} comme point de départ."
                instructions = ["Rassemble une feuille et le matériel déjà disponible.", f"Crée un {medium} inspiré par {subject} pendant 15 minutes.", "Ne cherche pas la perfection; termine par un titre."]
                location, rec_type, tag = "À LA MAISON", "indoor", CATEGORY_TAG[category]
            else:
                exercise = rng.choice(["Défi mémoire", "Question à explorer", "Lecture attentive", "Récit de souvenir", "Jeu de logique papier"])
                subject = rng.choice(["un souvenir marquant", "une question qui t'intrigue", "un objet familier", "une idée lue récemment", "un lieu que tu connais"])
                title = f"{exercise} : {subject}"
                description = f"Une courte pause de réflexion autour de {subject}, sans recherche en ligne."
                instructions = [f"Prends {subject} comme point de départ.", "Écris ou réfléchis pendant 10 minutes sans consulter ton téléphone.", "Garde une seule idée ou question pour la suite."]
                location, rec_type, tag = "À LA MAISON", "indoor", CATEGORY_TAG[category]
            if norm(title) not in recent:
                break
        ideas.append(Cand(
            id=f"idea_{uuid4().hex}", category=category, category_tag=tag, title=title,
            location=location, description=description, type=rec_type, instructions=instructions,
        ))
    rng.shuffle(ideas)
    return ideas

async def generate_activities(req: RecommendRequest) -> list[Cand]:
    """Generate one distinct, screen-free activity for each of the three idea categories."""
    previous = [row.title for row in list_completed()[:80]]
    previous_normalized = {norm(title) for title in previous}
    payload = {
        "model": LLM_MODEL, "temperature": 1.0,
        "messages": [
            {"role": "system", "content": (
                "Tu es un coach d'activités sans écran. Propose exactement trois idées distinctes, "
                "réalistes, réalisables aujourd'hui, adaptées à la demande. Une par catégorie: outdoor, creative, intellectual. "
                "N'invente aucun établissement, adresse ou lieu. Pour outdoor, propose une action sans nommer de spot. "
                "Retourne exactement trois objets dans le tableau, un pour chaque catégorie, comme ceci: "
                "{\"activities\":[{\"category\":\"outdoor\",\"title\":\"...\",\"description\":\"...\",\"instructions\":[\"...\"]},"
                "{\"category\":\"creative\",\"title\":\"...\",\"description\":\"...\",\"instructions\":[\"...\"]},"
                "{\"category\":\"intellectual\",\"title\":\"...\",\"description\":\"...\",\"instructions\":[\"...\"]}]} "
                "Pas de Markdown ni de texte hors JSON."
            )},
            {"role": "user", "content": (
                f"Demande: {req.user_input or 'une pause'}. Humeur: {req.mood or 'non précisée'}. "
                f"Évite ces activités déjà faites: {previous}. "
                + ("/no_think" if LLM_PROVIDER == "local" else "")
            )},
        ],
    }
    headers = {"Authorization": f"Bearer {LLM_API_KEY}"} if LLM_API_KEY else {}
    payload["response_format"] = {"type": "json_object"}
    async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
        response = await client.post(f"{LLM_BASE_URL}/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
    raw_items = parse_llm_json(response.json()["choices"][0]["message"]["content"]).get("activities", [])
    result: list[Cand] = []
    seen: set[str] = set()
    for item in raw_items:
        category = item.get("category")
        title = str(item.get("title", "")).strip()
        if category not in CATEGORY_ORDER or not title or category in seen or norm(title) in previous_normalized:
            continue
        seen.add(category)
        is_outdoor = category == "outdoor"
        instructions = item.get("instructions", [])
        if not isinstance(instructions, list):
            instructions = []
        result.append(Cand(
            id=f"idea_{uuid4().hex}", category=category,
            category_tag="IDÉE DE SORTIE" if is_outdoor else CATEGORY_TAG[category],
            title=title, location="Près de toi · sans lieu imposé" if is_outdoor else "À LA MAISON",
            description=str(item.get("description", "Une activité à essayer maintenant.")),
            type="outdoor" if is_outdoor else "indoor", instructions=[str(s) for s in instructions[:6]],
        ))
    if len(result) != 3:
        raise ValueError("Le LLM n'a pas produit les trois idées attendues")
    return result


def _place_candidate(place: dict) -> Cand:
    return Cand(
        id=place["id"], category=place["category"], category_tag=place["category_tag"],
        title=place["title"], location=place["address"],
        description=" · ".join(filter(None, [
            f"{place['rating']:.1f}/5", f"{place['user_rating_count']} avis",
            f"à {place['distance_m']} m", place.get("opening_hours", ""),
        ])),
        type="outdoor", image_url=place["image_url"], maps_url=place["maps_url"],
        lat=place["lat"], lon=place["lon"], distance_m=place["distance_m"],
        is_place=True, rating=place["rating"], user_rating_count=place["user_rating_count"],
        photo_author=place["photo_author"], photo_author_url=place["photo_author_url"],
        photo_google_maps_uri=place["photo_google_maps_uri"],
        opening_hours=place.get("opening_hours", ""),
    )


def to_rec(candidate: Cand) -> Recommendation:
    return Recommendation(
        id=candidate.id, type=candidate.type, category_tag=candidate.category_tag,
        tag_color=COLOR[candidate.category], title=candidate.title,
        location_name=candidate.location, image_url=candidate.image_url,
        description=candidate.description, maps_url=candidate.maps_url,
        instructions=candidate.instructions, lat=candidate.lat, lon=candidate.lon,
        distance_m=candidate.distance_m, is_place=candidate.is_place,
        rating=candidate.rating, user_rating_count=candidate.user_rating_count,
        photo_author=candidate.photo_author, photo_author_url=candidate.photo_author_url,
        photo_google_maps_uri=candidate.photo_google_maps_uri,
        opening_hours=candidate.opening_hours,
        is_film=candidate.is_film, imdb_url=candidate.imdb_url, year=candidate.year,
        runtime_min=candidate.runtime_min, genres=candidate.genres,
    )


def _film_candidate(film: dict) -> Cand:
    return Cand(
        id=film["id"], category="intellectual", category_tag="Film", title=film["title"],
        location="À la maison ou au cinéma", description=film["plot"] or "Un film bien noté sur IMDb.",
        image_url=film["image_url"], rating=film["rating"], user_rating_count=film["votes"],
        is_film=True, imdb_url=film["imdb_url"], year=film["year"],
        runtime_min=film["runtime_min"], genres=film["genres"],
    )


async def recommend(req: RecommendRequest) -> tuple[list[Recommendation], str, str, str]:
    lat, lon = req.lat, req.lon
    wanted, _ = intent(req.user_input)
    places: list[dict] = []
    places_source = "no_location"
    if lat is not None and lon is not None:
        # PLACES_PROVIDER: "auto" (official API if a key is set, else Maps web search),
        # "google_places" (official API only) or "maps" (Maps web search only).
        provider = os.getenv("PLACES_PROVIDER", "auto").lower()
        has_key = bool(os.getenv("GOOGLE_PLACES_API_KEY", "").strip())
        use_official = provider == "google_places" or (provider == "auto" and has_key)
        try:
            if use_official:
                from .google_places import search_places
                places = await search_places(lat, lon, req.radius, wanted)
                places_source = "google" if places else ("google_no_match" if has_key else "google_not_configured")
            else:
                from .maps_search import search_maps
                places = await search_maps(lat, lon, req.radius, wanted)
                places_source = "maps" if places else "google_no_match"
        except Exception as e:
            log.warning("Places search unavailable (%s): %s", "google_places" if use_official else "maps", e)
            places_source = "google_error" if use_official else "maps_error"

    # A film card only when the request talks about films ("un film drôle ce soir").
    film: Cand | None = None
    film_source = "none"
    if wants_film(req.user_input):
        try:
            seen = {norm(row.title) for row in list_completed()[:200]}
            found = await search_film(req.user_input, req.mood, seen)
            film = _film_candidate(found) if found else None
            film_source = "imdb" if film else "imdb_no_match"
        except Exception as e:
            log.warning("IMDb search unavailable: %s", e)
            film_source = "imdb_error"

    try:
        ideas = await generate_activities(req)
        source = "llm"
    except Exception as e:
        log.warning("LLM unavailable; using varied local activity ideas: %s", e)
        ideas = _idea_fallback(req)
        source = "fallback"

    if wanted:
        selected = [_place_candidate(p) for p in places[:3]]
        selected.extend(ideas[: 3 - len(selected)])
    else:
        selected = [_place_candidate(places[0])] if places else []
        needed_categories = {idea.category for idea in selected}
        selected.extend(idea for idea in ideas if idea.category not in needed_categories)
        selected = selected[:3]
    # Always return exactly three distinct options, even if Places has no results.
    seen_ids = {item.id for item in selected}
    if len(selected) < 3:
        for idea in ideas:
            if idea.id not in seen_ids:
                selected.append(idea)
                seen_ids.add(idea.id)
            if len(selected) == 3:
                break
    selected = selected[:3]
    if film:
        # The film takes the place of the home "à découvrir" idea, else of the last card.
        drop = next((i for i, c in enumerate(selected) if c.category == "intellectual" and not c.is_place),
                    len(selected) - 1)
        selected = [film] + [c for i, c in enumerate(selected) if i != drop]
    return [to_rec(item) for item in selected[:3]], source, places_source, film_source
