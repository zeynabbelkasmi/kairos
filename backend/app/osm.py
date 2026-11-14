"""Vrais lieux autour de l'utilisateur via OpenStreetMap (Overpass API : gratuit, sans clé)."""
import asyncio
import logging
import math
import re
import time
from urllib.parse import quote

import httpx

log = logging.getLogger("kairos")

OVERPASS_URLS = [  # interrogés en parallèle : le premier qui répond gagne
    "https://lz4.overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
OVERPASS_TIMEOUT = 50  # secondes : les serveurs publics mettent souvent 20-30 s
CACHE_TTL = 600  # secondes
_cache: dict[tuple, tuple[float, list[dict]]] = {}

# (clé OSM, regex sur la valeur, catégorie Kairos, libellé, type de lieu)
RULES = [
    ("leisure", r"^(park|garden)$", "outdoor", "Parc", "park"),
    ("amenity", r"^cafe$", "outdoor", "Café", "cafe"),
    ("amenity", r"^(restaurant|fast_food)$", "outdoor", "Restaurant", "restaurant"),
    ("tourism", r"^(viewpoint|attraction)$", "outdoor", "Point de vue", "viewpoint"),
    ("amenity", r"^library$", "intellectual", "Bibliothèque", "library"),
    ("shop", r"^books$", "intellectual", "Librairie", "library"),
    ("tourism", r"^(museum|gallery)$", "intellectual", "Musée", "museum"),
    ("amenity", r"^arts_centre$", "creative", "Centre d'art", "art"),
    ("shop", r"^(art|craft)$", "creative", "Atelier créatif", "art"),
]

CATEGORY_TAG = {
    "outdoor": "SORTIE LOCALE",
    "intellectual": "SORTIE CULTURELLE",
    "creative": "ATELIER PROCHE",
}


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _classify(tags: dict, wanted: set[str]) -> tuple[str, str, str] | None:
    for key, pattern, cat, label, ptype in RULES:
        value = tags.get(key)
        if value and re.match(pattern, value) and (not wanted or ptype in wanted):
            return cat, label, ptype
    return None


def _query(lat: float, lon: float, radius: int, wanted: set[str], words: list[str]) -> str:
    parts = [
        f'nwr(around:{radius},{lat},{lon})["{key}"~"{pattern}"];'
        for key, pattern, _, _, ptype in RULES
        if not wanted or ptype in wanted
    ]
    # recherche par nom : « coffee », « tour »… (mots nettoyés, uniquement lettres)
    parts += [f'nwr(around:{radius},{lat},{lon})["name"~"{w}",i];' for w in words]
    return f"[out:json][timeout:25];({''.join(parts)});out center tags 300;"


def _image(tags: dict) -> str:
    """Photo réelle depuis Wikimedia Commons, si OSM la renseigne (sinon vide)."""
    commons = tags.get("wikimedia_commons", "")
    if commons.startswith("File:"):
        return "https://commons.wikimedia.org/wiki/Special:FilePath/" + quote(commons[5:]) + "?width=800"
    image = tags.get("image", "")
    if image.startswith("https://commons.wikimedia.org/"):
        return image
    return ""


async def _fetch(query: str) -> dict | None:
    """Envoie la requête à tous les miroirs en même temps et garde la première réponse valide."""
    async with httpx.AsyncClient(timeout=OVERPASS_TIMEOUT,
                                 headers={"User-Agent": "KairosApp/1.0 (projet personnel)"}) as client:
        async def one(url: str) -> dict:
            r = await client.post(url, data={"data": query})
            r.raise_for_status()
            return r.json()

        tasks = {asyncio.create_task(one(u)): u for u in OVERPASS_URLS}
        try:
            for fut in asyncio.as_completed(tasks):
                try:
                    return await fut
                except Exception as e:  # serveur saturé, timeout…
                    log.warning("Overpass : un miroir a échoué : %s", type(e).__name__)
        finally:
            for t in tasks:
                t.cancel()
    return None


async def nearby(lat: float, lon: float, radius: int = 2000,
                 wanted: set[str] | None = None, words: list[str] | None = None) -> list[dict] | None:
    """Lieux nommés, classés, avec position, distance et photo si disponible.
    wanted : types demandés (ex. {"cafe"}) ; words : mots à chercher dans le nom.
    Renvoie None si OSM est injoignable (à distinguer de [] = rien trouvé)."""
    wanted = wanted or set()
    words = [w for w in (words or []) if re.fullmatch(r"[a-z0-9]{3,20}", w)]
    key = (round(lat, 3), round(lon, 3), radius, tuple(sorted(wanted)), tuple(words))
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < CACHE_TTL:
        return hit[1]

    data = await _fetch(_query(lat, lon, radius, wanted, words))
    if data is None:
        log.warning("Overpass : aucun miroir n'a répondu")
        return None

    places: list[dict] = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name")
        center = el.get("center") or {}
        plat = el.get("lat", center.get("lat"))
        plon = el.get("lon", center.get("lon"))
        if not name or plat is None or plon is None:
            continue
        classified = _classify(tags, wanted)
        name_match = bool(words) and any(re.search(w, name, re.I) for w in words)
        if classified is None:
            if not name_match:
                continue
            classified = ("outdoor", "Lieu", "other")
        cat, label, ptype = classified
        places.append({
            "id": f"osm_{el['type']}_{el['id']}",
            "name": name,
            "category": cat,
            "label": label,
            "type": ptype,
            "name_match": name_match,
            "image": _image(tags),
            "lat": plat,
            "lon": plon,
            "distance_m": int(round(haversine_m(lat, lon, plat, plon), -1)),
        })

    _cache[key] = (time.time(), places)
    return places
