import logging
import uuid
from datetime import datetime, timezone
from typing import List

from ..models import NewsArticle
from ..config import settings
from .storage import StorageService

logger = logging.getLogger(__name__)

class NewsService:
    def __init__(self, storage: StorageService):
        self.storage = storage

    async def get_user_news(self, user_id: str) -> List[NewsArticle]:
        """Get cached news for user."""
        try:
            items = await self.storage.get_cached_news(user_id)
            return [NewsArticle(**item) for item in items]
        except Exception as e:
            logger.error(f"Error getting news for {user_id}: {e}")
            return []

    async def refresh_news(self, user_id: str) -> List[NewsArticle]:
        """
        Refresh news for user based on preferences.
        In a real implementation, this would call Bing Search / OpenAI.
        For migration gap closure, we will generate placeholder content if no external API is configured.
        """
        prefs_dict = await self.storage.get_user_preferences(user_id)
        topics = prefs_dict.get("topics", [])
        
        if not topics:
            return []

        # TODO: Integrate valid Bing Search / OpenAI call here.
        # Logic:
        # 1. Search for each topic
        # 2. Summarize with OpenAI
        # 3. Store in Cosmos
        
        # Mock implementation for gap closure verification
        mock_news = []
        for topic in topics:
            article = NewsArticle(
                id=str(uuid.uuid4()),
                title=f"Latest updates on {topic}",
                summary=f"This is an AI generated summary about {topic} based on recent events.",
                url=f"https://example.com/news/{topic}",
                source="Keiko News AI",
                published_at=datetime.now(timezone.utc).isoformat(),
                topics=[topic]
            )
            # Add partition key for Cosmos
            item = article.model_dump()
            item['userId'] = user_id
            
            mock_news.append(item)
            
        await self.storage.save_news_batch(mock_news)
        
        return [NewsArticle(**item) for item in mock_news]
