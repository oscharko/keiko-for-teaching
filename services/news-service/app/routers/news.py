from typing import List
from fastapi import APIRouter, Request, HTTPException, status

from ..models import NewsPreferences, NewsPreferencesUpdate, NewsArticle
from ..services.news_service import NewsService

router = APIRouter(tags=["news"])

@router.get("/user/news-preferences", response_model=NewsPreferences)
async def get_preferences(request: Request, user_id: str = "default_user"):
    # Note: user_id should be extracted from auth/headers in real app
    # Adding simplified header-based extraction or query param for now
    storage = request.app.state.storage
    if not storage:
        return NewsPreferences(id=user_id, topics=[])
        
    prefs = await storage.get_user_preferences(user_id)
    return NewsPreferences(**prefs)

@router.post("/user/news-preferences", response_model=NewsPreferences)
async def update_preferences(
    request: Request, 
    prefs_update: NewsPreferencesUpdate,
    user_id: str = "default_user"
):
    storage = request.app.state.storage
    if not storage:
        raise HTTPException(status_code=503, detail="Storage unavailable")
        
    await storage.update_user_preferences(user_id, prefs_update.topics)
    return NewsPreferences(id=user_id, topics=prefs_update.topics)

@router.get("/user/news", response_model=List[NewsArticle])
async def get_news(request: Request, user_id: str = "default_user"):
    storage = request.app.state.storage
    if not storage:
        return []
        
    service = NewsService(storage)
    return await service.get_user_news(user_id)

@router.post("/user/refresh-news", response_model=List[NewsArticle])
async def refresh_news(request: Request, user_id: str = "default_user"):
    storage = request.app.state.storage
    if not storage:
        raise HTTPException(status_code=503, detail="Storage unavailable")
        
    service = NewsService(storage)
    return await service.refresh_news(user_id)


@router.delete("/user/news-preferences/{term}")
async def delete_news_preference(request: Request, term: str, user_id: str = "default_user"):
    """Delete a specific topic from user's news preferences."""
    storage = request.app.state.storage
    if not storage:
        raise HTTPException(status_code=503, detail="Storage unavailable")

    # Get current preferences
    prefs = await storage.get_user_preferences(user_id)
    current_topics = prefs.get("topics", [])

    # URL decode the term (in case it contains special characters)
    from urllib.parse import unquote
    decoded_term = unquote(term)

    # Remove the topic if it exists
    if decoded_term in current_topics:
        current_topics.remove(decoded_term)
        await storage.update_user_preferences(user_id, current_topics)
        return NewsPreferences(id=user_id, topics=current_topics)
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Topic '{decoded_term}' not found in preferences"
        )


@router.get("/news/status")
async def news_status(request: Request):
    """Get news service status and configuration."""
    storage = request.app.state.storage
    return {
        "enabled": storage is not None,
        "storage_connected": storage is not None,
    }

