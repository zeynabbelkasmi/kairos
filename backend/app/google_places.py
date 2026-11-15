"""Search current businesses with Google Places. No Places content is persisted."""
import asyncio
import math
import os
from urllib.parse import quote

import httpx


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_m = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi, d_lambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * earth_radius_m * math.asin(math.sqrt(a))

PLACES_URL = "https://places.googleapis.com/v1/places:searchNearby"
FIELDS = ",".join([
    "places.id", "places.displayName", "places.formattedAddress", "places.location",
    "places.types", "places.primaryTypeDisplayName", "places.googleMapsUri",
    "places.businessStatus", "places.rating", "places.userRatingCount",
    "places.photos.name", "places.photos.authorAttributions", "places.photos.googleMapsUri",
])

TYPE_MAP = {
    "cafe": ["coffee_shop", "cafe"],
    "restaurant": ["restaurant"],
    "park": ["park", "city_park", "botanical_garden"],
    "museum": ["museum", "art_museum", "art_gallery"],
    "library": ["library", "book_store"],
    "viewpoint": ["tourist_attraction"],
    "art": ["art_studio", "art_gallery", "cultural_center"],
}
TYPE_CATEGORY = {
    "coffee_shop": "outdoor", "cafe": "outdoor", "restaurant": "outdoor",
    "park": "outdoor", "city_park": "outdoor", "botanical_garden": "outdoor",
    "tourist_attraction": "outdoor", "museum": "intellectual", "art_museum": "intellectual",
    "art_gallery": "creative", "library": "intellectual", "book_store": "intellectual",
    "art_studio": "creative", "cultural_center": "creative",
}


async def _photo_uri(client: httpx.AsyncClient, key: str, photo: dict) -> str:
    resource = photo.get("name", "")
    if not resource:
        return ""
    url = f"https://places.googleapis.com/v1/{quote(resource, safe='/')}/media"
    try:
        response = await client.get(url, params={"maxWidthPx": 1000, "skipHttpRedirect": "true", "key": key})
        response.raise_for_status()
        return str(response.json().get("photoUri", ""))
    except (httpx.HTTPError, ValueError):
        return ""


async def search_places(lat: float, lon: float, radius: int, wanted: set[str]) -> list[dict]:
    """Return only currently operational, named Google places with a photo and a usable Maps link."""
    key = os.getenv("GOOGLE_PLACES_API_KEY", "").strip()
    if not key:
        return []
    types = list(dict.fromkeys(t for category in wanted for t in TYPE_MAP.get(category, [])))
    if not types:
        types = ["coffee_shop", "cafe", "park", "city_park", "museum", "library", "art_gallery"]
    min_rating = float(os.getenv("GOOGLE_PLACES_MIN_RATING", "4.2"))
    min_reviews = int(os.getenv("GOOGLE_PLACES_MIN_REVIEWS", "10"))
    body = {
        "includedTypes": types,
        "maxResultCount": 20,
        "rankPreference": "POPULARITY",
        "languageCode": "fr",
        "regionCode": "MA",
        "locationRestriction": {"circle": {"center": {"latitude": lat, "longitude": lon}, "radius": float(radius)}},
    }
    async with httpx.AsyncClient(timeout=18) as client:
        response = await client.post(PLACES_URL, json=body, headers={
            "Content-Type": "application/json", "X-Goog-Api-Key": key, "X-Goog-FieldMask": FIELDS,
        })
        response.raise_for_status()
        raw = response.json().get("places", [])
        candidates = []
        for place in raw:
            location = place.get("location") or {}
            name = (place.get("displayName") or {}).get("text", "").strip()
            address = place.get("formattedAddress", "").strip()
            place_id = place.get("id", "")
            place_types = place.get("types", [])
            category = next((TYPE_CATEGORY[t] for t in place_types if t in TYPE_CATEGORY), None)
            rating = place.get("rating")
            review_count = place.get("userRatingCount", 0)
            if (place.get("businessStatus") != "OPERATIONAL" or not name or not address or not place_id
                    or not category or not place.get("googleMapsUri") or not location
                    or rating is None or float(rating) < min_rating or int(review_count) < min_reviews):
                continue
            photo = next(iter(place.get("photos", [])), None)
            if not photo:
                continue
            plat, plon = float(location["latitude"]), float(location["longitude"])
            candidates.append({
                "id": f"google_{place_id}", "place_id": place_id, "title": name,
                "address": address, "category": category,
                "category_tag": (place.get("primaryTypeDisplayName") or {}).get("text", "Lieu Ã  proximitÃ©"),
                "maps_url": place["googleMapsUri"], "lat": plat, "lon": plon,
                "distance_m": int(round(haversine_m(lat, lon, plat, plon), -1)),
                "rating": float(rating), "user_rating_count": int(review_count),
                "photo": photo, "image_url": "",
            })
        candidates.sort(key=lambda p: (-p["rating"], -p["user_rating_count"], p["distance_m"]))
        # Fetch fresh media URIs for only the cards that can be shown. Google photo references are not cached.
        selected = candidates[:8]
        photo_uris = await asyncio.gather(*[_photo_uri(client, key, item["photo"]) for item in selected])
        results = []
        for item, uri in zip(selected, photo_uris):
            if not uri:
                continue
            item["image_url"] = uri
            author = next(iter(item["photo"].get("authorAttributions", [])), {})
            item["photo_author"] = author.get("displayName", "")
            item["photo_author_url"] = author.get("uri", "")
            item["photo_google_maps_uri"] = item["photo"].get("googleMapsUri", item["maps_url"])
            item.pop("photo", None)
            results.append(item)
        return results

