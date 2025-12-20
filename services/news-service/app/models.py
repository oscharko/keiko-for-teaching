from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class NewsPreferences(BaseModel):
    id: str
    topics: List[str]

class NewsPreferencesUpdate(BaseModel):
    topics: List[str]

class NewsArticle(BaseModel):
    id: str
    title: str
    summary: str
    url: str
    source: str
    published_at: str
    image_url: Optional[str] = None
    topics: List[str] = []
