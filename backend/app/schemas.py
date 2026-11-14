from typing import Optional

from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    user_input: str = ""
    mood: Optional[str] = None
    is_alone: bool = True
    max_options: int = Field(3, ge=2, le=3)
    lat: Optional[float] = None  # position de l'utilisateur (géolocalisation navigateur)
    lon: Optional[float] = None
    radius: int = Field(2000, ge=300, le=10000)  # mètres


class Recommendation(BaseModel):
    id: str
    type: str
    category_tag: str
    tag_color: str
    title: str
    location_name: str
    image_url: str = ""
    description: str
    maps_url: Optional[str] = None
    instructions: list[str] = []
    lat: Optional[float] = None
    lon: Optional[float] = None
    distance_m: Optional[int] = None


class RecommendResponse(BaseModel):
    recommendations: list[Recommendation]
    source: str = "llm"  # "llm" ou "fallback"
    places_source: str = "none"  # "osm" si de vrais lieux ont été trouvés, sinon "catalogue" ou "none"
