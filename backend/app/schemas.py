from typing import Optional

from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    user_input: str = ""
    mood: Optional[str] = None
    is_alone: bool = True
    max_options: int = Field(3, ge=3, le=3)
    lat: Optional[float] = None  # position de l'utilisateur (gÃ©olocalisation navigateur)
    lon: Optional[float] = None
    radius: int = Field(2000, ge=300, le=10000)  # mÃ¨tres


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
    is_place: bool = False
    rating: Optional[float] = None
    user_rating_count: Optional[int] = None
    photo_author: str = ""
    photo_author_url: str = ""
    photo_google_maps_uri: str = ""
    opening_hours: str = ""


class RecommendResponse(BaseModel):
    recommendations: list[Recommendation] = Field(min_length=3, max_length=3)
    source: str = "llm"  # "llm" ou "fallback"
    places_source: str = "google"  # google | maps | google_no_match | google_not_configured | google_error | maps_error | no_location

class CompleteRequest(BaseModel):
    activity_id: str
    title: str
    category_tag: str


class HistoryItem(BaseModel):
    id: int
    activity_id: str
    title: str
    category_tag: str
    completed_at: str
