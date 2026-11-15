"""Search nearby places through the public Google Maps web search (no API key).

The request is the one the Maps web page itself sends (learned with API Anything,
site "google-maps", operation "searchPlaces"). Kairos adds a viewport centred on the
user so results are local, then keeps only places inside the requested radius.
This is an unofficial endpoint: Google can change it at any time, and it is meant for
prototyping. Nothing is persisted.
"""
import asyncio
import json
import os
from typing import Any
from urllib.parse import quote

import httpx

from .google_places import haversine_m

SEARCH_URL = "https://www.google.com/search"
# Protobuf-style parameter captured from the Maps frontend. {query} is the search text,
# {viewport} centres the search on the user (see _viewport).
PB_TEMPLATE = (
    "!1s{query}{viewport}!7i20!10b1!12m58!1m5!18b1!30b1!31m1!1b1!34e1!2m4!5m1!6e2!20e3!39b1!6m29!32i1!49b1!63m0!66b1!85b1!114b1!149b1!206b1!209b1!212b1!215b1!216b1!222b1!223b1!234b1!235b1!239b1!246b1!253b1!260b1!262b1!266b1!270b1!271b1!273b1!281b1!294b1!302i300!303i100!10b1!12b1!13b1!14b1!16b1!17m1!3e1!20m3!5e2!6b1!14b1!46m1!1b0!96b1!97m1!2b1!99b1!19m4!2m3!1i360!2i120!4i8!20m57!2m2!1i203!2i100!3m2!2i4!5b1!6m6!1m2!1i86!2i86!1m2!1i408!2i240!7m33!1m3!1e1!2b0!3e3!1m3!1e2!2b1!3e2!1m3!1e2!2b0!3e3!1m3!1e8!2b0!3e3!1m3!1e10!2b0!3e3!1m3!1e10!2b1!3e2!1m3!1e10!2b0!3e4!1m3!1e9!2b1!3e2!2b1!9b0!15m8!1m7!1m2!1m1!1e2!2m2!1i195!2i195!3i20!22m5!1sxibfaoTYN-GS8L0P1vzKsA4!7e81!14m1!3sxibfaoTYN-GS8L0P1vzKsA4!15i9937!24m107!1m25!13m9!2b1!3b1!4b1!6i1!8b1!9b1!14b1!20b1!25b1!18m14!3b1!4b1!5b1!6b1!13b1!14b1!17b1!21b1!22b1!32b1!33m1!1b1!34b1!36e2!10m1!8e3!11m1!3e1!17b1!20m2!1e3!1e6!24b1!25b1!26b1!27b1!29b1!30m1!2b1!36b1!37b1!39m3!2m2!2i1!3i1!43b1!52b1!54m1!1b1!55b1!56m1!1b1!61m2!1m1!1e1!65m5!3m4!1m3!1m2!1i224!2i298!72m22!1m8!2b1!5b1!7b1!12m4!1b1!2b1!4m1!1e1!4b1!8m10!1m6!4m1!1e1!4m1!1e3!4m1!1e4!3sother_user_google_review_posts__and__hotel_and_vr_partner_review_posts!6m1!1e1!9b1!89b1!90m2!1m1!1e2!98m3!1b1!2b1!3b1!103b1!113b1!114m3!1b1!2m1!1b1!117b1!122m1!1b1!126b1!127b1!128m1!1b1!26m4!2m3!1i80!2i92!4i8!30m28!1m6!1m2!1i0!2i0!2m2!1i530!2i768!1m6!1m2!1i974!2i0!2m2!1i1024!2i768!1m6!1m2!1i0!2i0!2m2!1i1024!2i20!1m6!1m2!1i0!2i748!2m2!1i1024!2i768!34m19!2b1!3b1!4b1!6b1!8m6!1b1!3b1!4b1!5b1!6b1!7b1!9b1!12b1!14b1!20b1!23b1!25b1!26b1!31b1!37m1!1e81!42b1!49m10!3b1!6m2!1b1!2b1!7m2!1e3!2b1!8b1!9b1!10e2!50m3!2e2!3m1!3b1!61b1!67m5!7b1!10b1!14b1!15m1!1b0!69i800!77b1"
)
HEADERS = {
    "accept": "*/*",
    "origin": "https://www.google.com",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36",
    "sec-ch-ua": "\"Google Chrome\";v=\"155\", \"Chromium\";v=\"155\", \"Not(A:Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
}

# Kairos place type -> (Maps search words, Kairos category)
QUERIES = {
    "cafe": ("café", "outdoor"),
    "restaurant": ("restaurant", "outdoor"),
    "park": ("parc jardin", "outdoor"),
    "museum": ("musée", "intellectual"),
    "library": ("bibliothèque librairie", "intellectual"),
    "viewpoint": ("point de vue", "outdoor"),
    "art": ("galerie d'art atelier", "creative"),
}
DEFAULT_TYPES = ["cafe", "park", "museum"]
PHOTO_SIZE = "=w1000-h600-k-no"


def _get(node: Any, *path: int) -> Any:
    """Safe nested index: returns None instead of raising when the shape differs."""
    for index in path:
        if not isinstance(node, list) or index >= len(node):
            return None
        node = node[index]
    return node


def _viewport(lat: float, lon: float, radius: int) -> str:
    # !1d is the visible span in metres; a bit wider than the circle so edge places are returned.
    return f"!4m8!1m3!1d{radius * 2.5:.0f}!2d{lon}!3d{lat}!3m2!1i1024!2i768!4f13.1"


def maps_place_url(name: str, place_id: str) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={quote(name)}&query_place_id={place_id}"


def _photo(place: list) -> str:
    url = _get(place, 37, 0, 0, 6, 0) or _get(place, 72, 0, 0, 6, 0)
    if not isinstance(url, str) or "googleusercontent.com" not in url:
        return ""
    return url.split("=")[0] + PHOTO_SIZE  # the suffix after "=" sets the image size


async def _search(client: httpx.AsyncClient, query: str, lat: float, lon: float, radius: int) -> list[list]:
    pb = PB_TEMPLATE.replace("{viewport}", _viewport(lat, lon, radius)).replace("{query}", query)
    params = {"tbm": "map", "authuser": "0", "hl": "fr", "gl": "ma", "q": query, "pb": pb}
    headers = {**HEADERS, "referer": f"https://www.google.com/maps/search/{quote(query)}/"}
    response = await client.get(SEARCH_URL, params=params, headers=headers)
    response.raise_for_status()
    data = json.loads(response.text.removeprefix(")]}'"))
    return [row[1] for row in (_get(data, 64) or []) if isinstance(_get(row, 1), list)]


async def search_maps(lat: float, lon: float, radius: int, wanted: set[str]) -> list[dict]:
    """Return named, rated places with a photo, at most `radius` metres from the user."""
    types = [t for t in QUERIES if t in wanted][:3] or DEFAULT_TYPES
    min_rating = float(os.getenv("GOOGLE_PLACES_MIN_RATING", "4.2"))
    min_reviews = int(os.getenv("GOOGLE_PLACES_MIN_REVIEWS", "10"))
    async with httpx.AsyncClient(timeout=18) as client:
        batches = await asyncio.gather(*[_search(client, QUERIES[t][0], lat, lon, radius) for t in types],
                                       return_exceptions=True)
    if all(isinstance(b, BaseException) for b in batches):
        raise batches[0]

    seen: set[str] = set()
    results = []
    for place_type, batch in zip(types, batches):
        if isinstance(batch, BaseException):
            continue
        for place in batch:
            name = _get(place, 11)
            place_id = _get(place, 78)
            plat, plon = _get(place, 9, 2), _get(place, 9, 3)
            rating, reviews = _get(place, 4, 7), _get(place, 4, 8) or 0
            hours = _get(place, 203, 1, 4, 0) or ""
            image_url = _photo(place)
            if (not name or not place_id or place_id in seen or plat is None or plon is None
                    or rating is None or float(rating) < min_rating or int(reviews) < min_reviews
                    or not image_url or "définitivement" in hours.lower() or "temporairement" in hours.lower()):
                continue
            distance = haversine_m(lat, lon, float(plat), float(plon))
            if distance > radius:  # the viewport is a square; keep only the circle
                continue
            seen.add(place_id)
            maps_url = maps_place_url(name, place_id)
            results.append({
                "id": f"maps_{place_id}", "place_id": place_id, "title": name,
                "address": _get(place, 18) or _get(place, 39) or "",
                "category": QUERIES[place_type][1],
                "category_tag": (_get(place, 13, 0) or "Lieu à proximité"),
                "maps_url": maps_url, "lat": float(plat), "lon": float(plon),
                "distance_m": int(round(distance, -1)),
                "rating": float(rating), "user_rating_count": int(reviews),
                "image_url": image_url, "opening_hours": hours,
                "photo_author": "", "photo_author_url": "", "photo_google_maps_uri": maps_url,
            })
    results.sort(key=lambda p: (-p["rating"], -p["user_rating_count"], p["distance_m"]))
    return results[:8]
