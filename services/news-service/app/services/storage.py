import logging
from typing import List, Optional, Any

from azure.cosmos.aio import CosmosClient, ContainerProxy
from azure.cosmos.exceptions import CosmosResourceNotFoundError

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self, connection_string: str, database_name: str, news_container_name: str, prefs_container_name: str):
        self.client = CosmosClient.from_connection_string(connection_string)
        self.database_name = database_name
        self.news_container_name = news_container_name
        self.prefs_container_name = prefs_container_name
        
        self.news_container: Optional[ContainerProxy] = None
        self.prefs_container: Optional[ContainerProxy] = None

    async def initialize(self):
        try:
            database = self.client.get_database_client(self.database_name)
            self.news_container = database.get_container_client(self.news_container_name)
            self.prefs_container = database.get_container_client(self.prefs_container_name)
            logger.info(f"Initialized Cosmos DB containers: {self.news_container_name}, {self.prefs_container_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB: {e}")
            raise

    # --- Preferences ---
    async def get_user_preferences(self, user_id: str) -> dict:
        if not self.prefs_container:
            return {}
        try:
            item = await self.prefs_container.read_item(item=user_id, partition_key=user_id)
            return item
        except CosmosResourceNotFoundError:
            return {"id": user_id, "topics": []}

    async def update_user_preferences(self, user_id: str, topics: List[str]):
        if not self.prefs_container:
            return
        item = {"id": user_id, "topics": topics}
        await self.prefs_container.upsert_item(body=item)

    # --- News Cache ---
    async def get_cached_news(self, user_id: str) -> List[dict]:
        if not self.news_container:
            return []
        
        # Simple query: Get news where partition key matches user_id (assuming simple partitioning for now)
        # Note: In a real scenario, news might be shared, but looking at source it seemed personalized.
        query = "SELECT * FROM c WHERE c.userId = @userId"
        parameters = [{"name": "@userId", "value": user_id}]
        
        items = [item async for item in self.news_container.query_items(
            query=query, parameters=parameters
        )]
        return items

    async def save_news_batch(self, news_items: List[dict]):
        if not self.news_container:
            return
        
        # This implementation assumes items valid and contain 'id' and partition key
        for item in news_items:
            await self.news_container.upsert_item(body=item)
            
    async def clear_user_news(self, user_id: str):
        # Implementation depends on stored procedure or bulk delete, simplified here
        pass
