"""
Storage service for Ideas Hub.

Provides Cosmos DB operations for idea persistence including
CRUD operations and querying.
"""

import logging
from typing import Any

from azure.cosmos.aio import ContainerProxy, CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from ..config import settings
from ..models import Idea

logger = logging.getLogger(__name__)


class StorageService:
    """
    Handles Cosmos DB storage operations for ideas.

    Provides methods for creating, reading, updating, and deleting ideas
    in the Cosmos DB container.
    """

    def __init__(
        self, connection_string: str, database_name: str, container_name: str
    ) -> None:
        """
        Initialize the storage service.

        Args:
            connection_string: Cosmos DB connection string.
            database_name: Name of the database.
            container_name: Name of the container.
        """
        self.client = CosmosClient.from_connection_string(connection_string)
        self.database_name = database_name
        self.container_name = container_name
        self.container: ContainerProxy | None = None

    async def initialize(self) -> None:
        """
        Initialize the Cosmos DB container connection.

        Raises:
            Exception: If initialization fails.
        """
        try:
            database = self.client.get_database_client(self.database_name)
            self.container = database.get_container_client(self.container_name)
            logger.info("Initialized Cosmos DB container: %s", self.container_name)
        except Exception as e:
            logger.error("Failed to initialize Cosmos DB: %s", e)
            raise

    async def get_idea(self, idea_id: str) -> Idea | None:
        """
        Get an idea by ID.

        Args:
            idea_id: ID of the idea to retrieve.

        Returns:
            The idea if found, None otherwise.

        Raises:
            RuntimeError: If storage service is not initialized.
        """
        if not self.container:
            raise RuntimeError("Storage service not initialized")

        try:
            item = await self.container.read_item(item=idea_id, partition_key=idea_id)
            return Idea.from_cosmos_item(item)
        except CosmosResourceNotFoundError:
            return None

    async def create_idea(self, idea: Idea) -> Idea:
        """
        Create a new idea.

        Args:
            idea: The idea to create.

        Returns:
            The created idea.

        Raises:
            RuntimeError: If storage service is not initialized.
        """
        if not self.container:
            raise RuntimeError("Storage service not initialized")

        item = idea.to_cosmos_item()
        await self.container.create_item(body=item)
        logger.info("Created idea: %s", idea.id)
        return idea

    async def update_idea(self, idea: Idea) -> Idea:
        """
        Update an existing idea.

        Args:
            idea: The idea to update.

        Returns:
            The updated idea.

        Raises:
            RuntimeError: If storage service is not initialized.
        """
        if not self.container:
            raise RuntimeError("Storage service not initialized")

        item = idea.to_cosmos_item()
        await self.container.upsert_item(body=item)
        logger.info("Updated idea: %s", idea.id)
        return idea

    async def delete_idea(self, idea_id: str) -> None:
        """
        Delete an idea.

        Args:
            idea_id: ID of the idea to delete.

        Raises:
            RuntimeError: If storage service is not initialized.
        """
        if not self.container:
            raise RuntimeError("Storage service not initialized")

        try:
            await self.container.delete_item(item=idea_id, partition_key=idea_id)
            logger.info("Deleted idea: %s", idea_id)
        except CosmosResourceNotFoundError:
            pass

    async def list_ideas(
        self, limit: int = 20, skip: int = 0, status: str | None = None
    ) -> list[Idea]:
        """
        List ideas with pagination.

        Args:
            limit: Maximum number of ideas to return.
            skip: Number of ideas to skip.
            status: Optional status filter.

        Returns:
            List of ideas.

        Raises:
            RuntimeError: If storage service is not initialized.
        """
        if not self.container:
            raise RuntimeError("Storage service not initialized")

        if status:
            query = """
                SELECT * FROM c
                WHERE c.type = 'idea' AND c.status = @status
                ORDER BY c.createdAt DESC
                OFFSET @skip LIMIT @limit
            """
            parameters = [
                {"name": "@status", "value": status},
                {"name": "@skip", "value": skip},
                {"name": "@limit", "value": limit},
            ]
        else:
            query = """
                SELECT * FROM c
                WHERE c.type = 'idea'
                ORDER BY c.createdAt DESC
                OFFSET @skip LIMIT @limit
            """
            parameters = [
                {"name": "@skip", "value": skip},
                {"name": "@limit", "value": limit},
            ]

        items = [
            item
            async for item in self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True,
            )
        ]

        return [Idea.from_cosmos_item(item) for item in items]

    async def count_ideas(self, status: str | None = None) -> int:
        """
        Count total number of ideas.

        Args:
            status: Optional status filter.

        Returns:
            Total count of ideas.

        Raises:
            RuntimeError: If storage service is not initialized.
        """
        if not self.container:
            raise RuntimeError("Storage service not initialized")

        if status:
            query = """
                SELECT VALUE COUNT(1) FROM c
                WHERE c.type = 'idea' AND c.status = @status
            """
            parameters = [{"name": "@status", "value": status}]
        else:
            query = "SELECT VALUE COUNT(1) FROM c WHERE c.type = 'idea'"
            parameters = []

        result = [
            item
            async for item in self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True,
            )
        ]

        return result[0] if result else 0

    # ==========================================================================
    # Like Operations
    # ==========================================================================

    async def get_like(self, idea_id: str, user_id: str) -> dict | None:
        """Get a like for a specific idea and user."""
        if not self.container:
            raise RuntimeError("Storage service not initialized")

        like_id = f"{idea_id}_{user_id}"
        try:
            item = await self.container.read_item(item=like_id, partition_key=idea_id)
            return item
        except CosmosResourceNotFoundError:
            return None

    async def create_like(self, like_data: dict) -> dict:
        """Create a new like."""
        if not self.container:
            raise RuntimeError("Storage service not initialized")

        like_data["type"] = "idea_like"
        await self.container.create_item(body=like_data)
        logger.info("Created like: %s", like_data.get("likeId"))
        return like_data

    async def delete_like(self, idea_id: str, user_id: str) -> None:
        """Delete a like."""
        if not self.container:
            raise RuntimeError("Storage service not initialized")

        like_id = f"{idea_id}_{user_id}"
        try:
            await self.container.delete_item(item=like_id, partition_key=idea_id)
            logger.info("Deleted like: %s", like_id)
        except CosmosResourceNotFoundError:
            pass

    # ==========================================================================
    # Comment Operations
    # ==========================================================================

    async def create_comment(self, comment_data: dict) -> dict:
        """Create a new comment."""
        if not self.container:
            raise RuntimeError("Storage service not initialized")

        comment_data["type"] = "idea_comment"
        await self.container.create_item(body=comment_data)
        logger.info("Created comment: %s", comment_data.get("commentId"))
        return comment_data

    async def list_comments(
        self, idea_id: str, limit: int = 20, skip: int = 0
    ) -> list[dict]:
        """List comments for an idea with pagination."""
        if not self.container:
            raise RuntimeError("Storage service not initialized")

        query = """
            SELECT * FROM c
            WHERE c.type = 'idea_comment' AND c.ideaId = @idea_id
            ORDER BY c.createdAt DESC
            OFFSET @skip LIMIT @limit
        """
        parameters = [
            {"name": "@idea_id", "value": idea_id},
            {"name": "@skip", "value": skip},
            {"name": "@limit", "value": limit},
        ]

        items = [
            item
            async for item in self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True,
            )
        ]
        return items

    async def delete_comment(self, comment_id: str) -> None:
        """Delete a comment."""
        if not self.container:
            raise RuntimeError("Storage service not initialized")

        try:
            # Need to find the comment first to get partition key
            query = "SELECT * FROM c WHERE c.commentId = @comment_id"
            parameters = [{"name": "@comment_id", "value": comment_id}]
            
            items = [
                item
                async for item in self.container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True,
                )
            ]
            
            if items:
                idea_id = items[0].get("ideaId", comment_id)
                await self.container.delete_item(item=comment_id, partition_key=idea_id)
                logger.info("Deleted comment: %s", comment_id)
        except CosmosResourceNotFoundError:
            pass
