from typing import List, Optional
from pydantic import BaseModel

class Location(BaseModel):
    id: str
    name: str
    description: str
    latitude: float
    longitude: float
    category: str  # e.g., 'attraction', 'restaurant', 'hotel'

class RouteRequest(BaseModel):
    start_id: str
    end_id: str
    waypoints: Optional[List[str]] = []

class DiaryEntry(BaseModel):
    id: str
    user_id: str
    title: str
    content: str
    likes: int = 0
    tags: List[str] = []

class RecommendationRequest(BaseModel):
    user_id: str
    categories: List[str]
    limit: int = 5
