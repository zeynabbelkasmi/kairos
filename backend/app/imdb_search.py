"""Suggest a well-rated film from IMDb when the user asks for one (no API key).

The request is the one imdb.com itself sends to its GraphQL endpoint. Titles and plots come
back in French thanks to the x-imdb-user-language header. Like the Google Maps search, this
is an unofficial endpoint meant for prototyping: IMDb forbids public or commercial use of this
data, and it can change at any time. Nothing is persisted.
"""
import os
import random
import re
import unicodedata

import httpx

GRAPHQL_URL = "https://caching.graphql.imdb.com/"
HEADERS = {
    "content-type": "application/json",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36",
    "x-imdb-client-name": "imdb-web-next",
    "x-imdb-user-language": "fr-FR",
    "x-imdb-user-country": "FR",
}
QUERY = """
query Films($genres: [String!]!, $minRating: Float!, $minVotes: Int!) {
  advancedTitleSearch(
    first: 50,
    constraints: {
      titleTypeConstraint: { anyTitleTypeIds: ["movie"] }
      genreConstraint: { anyGenreIds: $genres }
      userRatingsConstraint: { aggregateRatingRange: { min: $minRating }, ratingsCountRange: { min: $minVotes } }
    },
    sort: { sortBy: POPULARITY, sortOrder: ASC }
  ) {
    edges { node { title {
      id titleText { text } releaseYear { year }
      ratingsSummary { aggregateRating voteCount }
      runtime { seconds } genres { genres { id } }
      primaryImage { url } plot { plotText { plainText } }
    } } }
  }
}
"""

# Words that mean "I want a film".
FILM_WORDS = ["film", "films", "cine", "cinema", "movie", "movies"]

# Words in the request -> IMDb genre ids.
GENRE_WORDS = {
    "Comedy": ["comedie", "drole", "rire", "marrant"],
    "Horror": ["horreur", "peur", "flippant", "epouvante"],
    "Action": ["action"],
    "Adventure": ["aventure"],
    "Romance": ["romance", "romantique", "amour"],
    "Animation": ["animation", "anime", "dessin anime"],
    "Sci-Fi": ["science fiction", "science-fiction", "sf", "futur", "espace"],
    "Thriller": ["thriller", "suspense"],
    "Crime": ["policier", "crime", "enquete", "mafia"],
    "Mystery": ["mystere", "enigme"],
    "Documentary": ["documentaire", "docu"],
    "Drama": ["drame", "emouvant", "pleurer"],
    "Family": ["famille", "enfant", "enfants"],
    "Fantasy": ["fantastique", "fantasy", "magie"],
    "War": ["guerre"],
    "History": ["historique", "histoire"],
    "Music": ["musique", "musical"],
    "Sport": ["sport"],
    "Western": ["western"],
}

# Mood chosen in the form -> genres that suit it.
MOOD_GENRES = {
    "fatigue": ["Comedy", "Animation", "Family"],
    "creatif": ["Animation", "Fantasy", "Sci-Fi"],
    "calme": ["Drama", "Romance", "Documentary"],
    "energie": ["Action", "Adventure", "Thriller"],
}
DEFAULT_GENRES = ["Comedy", "Drama", "Adventure"]

GENRE_FR = {
    "Action": "Action", "Adventure": "Aventure", "Animation": "Animation", "Biography": "Biopic",
    "Comedy": "Comédie", "Crime": "Policier", "Documentary": "Documentaire", "Drama": "Drame",
    "Family": "Famille", "Fantasy": "Fantastique", "History": "Histoire", "Horror": "Horreur",
    "Music": "Musique", "Musical": "Comédie musicale", "Mystery": "Mystère", "Romance": "Romance",
    "Sci-Fi": "Science-fiction", "Sport": "Sport", "Thriller": "Thriller", "War": "Guerre",
    "Western": "Western",
}


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def _has(text: str, word: str) -> bool:
    return re.search(rf"\b{re.escape(word)}\b", text) is not None


def wants_film(user_input: str) -> bool:
    text = _norm(user_input)
    return any(_has(text, w) for w in FILM_WORDS)


def pick_genres(user_input: str, mood: str | None) -> list[str]:
    text = _norm(user_input)
    asked = [g for g, words in GENRE_WORDS.items() if any(_has(text, w) for w in words)]
    if asked:
        return asked
    m = _norm(mood or "")
    for key, genres in MOOD_GENRES.items():
        if key in m:
            return genres
    return MOOD_GENRES["calme"] if "quete" in m else DEFAULT_GENRES


def _poster(url: str) -> str:
    # "..._V1_.jpg" is the original; "_V1_QL75_UX600_" asks IMDb's CDN for a 600 px wide copy.
    return re.sub(r"\._V1_.*\.jpg$", "._V1_QL75_UX600_.jpg", url) if url else ""


async def search_film(user_input: str, mood: str | None, exclude_titles: set[str]) -> dict | None:
    """Return one popular, well-rated film matching the request, or None."""
    genres = pick_genres(user_input, mood)
    variables = {
        "genres": genres,
        "minRating": float(os.getenv("IMDB_MIN_RATING", "7.0")),
        "minVotes": int(os.getenv("IMDB_MIN_VOTES", "25000")),
    }
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(GRAPHQL_URL, headers=HEADERS, json={"query": QUERY, "variables": variables})
        response.raise_for_status()
    edges = (((response.json().get("data") or {}).get("advancedTitleSearch") or {}).get("edges")) or []

    films = []
    for edge in edges:
        t = (edge.get("node") or {}).get("title") or {}
        title = (t.get("titleText") or {}).get("text")
        ratings = t.get("ratingsSummary") or {}
        poster = _poster((t.get("primaryImage") or {}).get("url", ""))
        if not title or not ratings.get("aggregateRating") or not poster or _norm(title) in exclude_titles:
            continue
        seconds = (t.get("runtime") or {}).get("seconds") or 0
        films.append({
            "id": f"film_{t['id']}", "imdb_id": t["id"], "title": title,
            "year": (t.get("releaseYear") or {}).get("year"),
            "rating": float(ratings["aggregateRating"]), "votes": int(ratings.get("voteCount") or 0),
            "runtime_min": round(seconds / 60) if seconds else None,
            "genres": [GENRE_FR.get(g["id"], g["id"]) for g in (t.get("genres") or {}).get("genres", [])][:3],
            "plot": ((t.get("plot") or {}).get("plotText") or {}).get("plainText", ""),
            "image_url": poster, "imdb_url": f"https://www.imdb.com/title/{t['id']}/",
        })
    return random.SystemRandom().choice(films) if films else None
