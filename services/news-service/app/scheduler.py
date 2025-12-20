import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .config import settings
from .services.storage import StorageService
from .services.news_service import NewsService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def refresh_all_users_news(storage: StorageService):
    """
    Background job to refresh news for all users.
    """
    logger.info("Starting scheduled news refresh...")
    if not storage.prefs_container:
        logger.warning("Storage not initialized, skipping refresh.")
        return

    # In a real app, query all users. Here we might just scan the prefs container.
    try:
        # Simplified: Query all user preferences
        query = "SELECT * FROM c"
        preferences = [item async for item in storage.prefs_container.query_items(
            query=query, enable_cross_partition_query=True
        )]
        
        service = NewsService(storage)
        
        tasks = []
        for pref in preferences:
            user_id = pref.get("id")
            if user_id:
                tasks.append(service.refresh_news(user_id))
        
        results = await asyncio.gather(*tasks)
        logger.info(f"Refreshed news for {len(results)} users.")
        
    except Exception as e:
        logger.error(f"Scheduled refresh failed: {e}")

def start_scheduler(storage: StorageService):
    if not settings.azure_cosmos_connection_string:
        logger.warning("Scheduler disabled due to missing storage config.")
        return

    # Schedule job every 4 hours
    scheduler.add_job(
        refresh_all_users_news,
        args=[storage],
        trigger=IntervalTrigger(hours=4),
        id="refresh_news_job",
        replace_existing=True
    )
    scheduler.start()
    logger.info("News scheduler started.")

def shutdown_scheduler():
    scheduler.shutdown()
    logger.info("News scheduler stopped.")
