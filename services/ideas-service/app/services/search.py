import logging
from typing import List, Optional, Any

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizedQuery

from ..config import settings
from ..models import Idea

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self, service_name: str, index_name: str, api_key: Optional[str] = None):
        endpoint = f"https://{service_name}.search.windows.net"
        credential = AzureKeyCredential(api_key) if api_key else None
        # Note: Managed Identity support would need DefaultAzureCredential if api_key is None
        
        self.client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)

    async def index_idea(self, idea: Idea):
        """Uploads an idea to the search index."""
        document = {
            "id": idea.id,
            "title": idea.title,
            "description": idea.description,
            "tags": idea.tags,
            "status": idea.status,
            "created_at": idea.created_at.isoformat(),
            "updated_at": idea.updated_at.isoformat(),
            "author_id": idea.author_id,
            "vote_count": idea.vote_count
            # Embeddings would be added here if we had vector search implemented
        }
        try:
            await self.client.upload_documents(documents=[document])
        except Exception as e:
            logger.error(f"Failed to index idea {idea.id}: {e}")
            raise

    async def delete_idea(self, idea_id: str):
        """Removes an idea from the search index."""
        try:
            await self.client.delete_documents(documents=[{"id": idea_id}])
        except Exception as e:
            logger.error(f"Failed to delete idea {idea_id} from index: {e}")
            # Don't raise, as mapped to DB delete which might have succeeded

    async def search_ideas(self, search_text: str, top: int = 20, filter_str: Optional[str] = None) -> List[dict]:
        """Searches for ideas."""
        try:
            results = await self.client.search(
                search_text=search_text,
                top=top,
                filter=filter_str,
                include_total_count=True
            )
            
            output = []
            async for result in results:
                output.append(result)
            return output
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
