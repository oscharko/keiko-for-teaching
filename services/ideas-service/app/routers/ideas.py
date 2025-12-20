"""
Ideas router for the Ideas Hub API.

Provides REST endpoints for idea management including CRUD operations,
search, status updates, and LLM-based review functionality.
"""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status

from ..models import Idea, IdeaCreate, IdeaStatus, IdeaUpdate
from ..services.audit import AuditAction, AuditLogger
from ..services.permissions import (
    IdeaPermission,
    can_delete_idea,
    can_edit_idea,
    can_view_idea,
    has_permission,
)
from ..services.scoring import IdeaScorer

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ideas"])

# In-memory storage for beta simplicity
# In a real app, this would be a database
IDEAS_DB: dict[str, Idea] = {}

# Initialize scorer with default configuration
scorer = IdeaScorer()

@router.post("/ideas", response_model=Idea, status_code=status.HTTP_201_CREATED)
async def create_idea(request: Request, idea_in: IdeaCreate) -> Idea:
    """
    Create a new idea.

    Args:
        request: FastAPI request object.
        idea_in: Idea creation data.

    Returns:
        The created idea.
    """
    now = datetime.now(timezone.utc)
    idea_id = str(uuid.uuid4())

    idea = Idea(
        id=idea_id,
        created_at=now,
        updated_at=now,
        **idea_in.model_dump(),
        vote_count=0,
    )

    storage = request.app.state.storage
    search = request.app.state.search
    audit: AuditLogger | None = getattr(request.app.state, "audit", None)

    if storage:
        await storage.create_idea(idea)
        if search:
            try:
                await search.index_idea(idea)
            except Exception as e:
                logger.error("Failed to index idea: %s", e)

        # Log audit entry
        if audit:
            await audit.log_create(
                idea_id=idea_id,
                user_id=idea.author_id or "anonymous",
                idea_data=idea.model_dump(),
            )
    else:
        # Fallback for testing/dev (In-memory)
        IDEAS_DB[idea_id] = idea

    logger.info("Created idea: %s", idea_id)
    return idea

@router.get("/ideas", response_model=list[Idea])
async def list_ideas(request: Request, skip: int = 0, limit: int = 20) -> list[Idea]:
    """
    List ideas with pagination.

    Args:
        request: FastAPI request object.
        skip: Number of ideas to skip.
        limit: Maximum number of ideas to return.

    Returns:
        List of ideas.
    """
    storage = request.app.state.storage
    if storage:
        return await storage.list_ideas(limit=limit, skip=skip)

    # Fallback
    ideas = list(IDEAS_DB.values())
    ideas.sort(key=lambda x: x.created_at, reverse=True)
    return ideas[skip : skip + limit]


@router.get("/ideas/{idea_id}", response_model=Idea)
async def get_idea(request: Request, idea_id: str) -> Idea:
    """
    Get a specific idea.

    Args:
        request: FastAPI request object.
        idea_id: ID of the idea to retrieve.

    Returns:
        The requested idea.

    Raises:
        HTTPException: If idea is not found.
    """
    storage = request.app.state.storage
    if storage:
        idea = await storage.get_idea(idea_id)
        if not idea:
            raise HTTPException(status_code=404, detail="Idea not found")
        return idea

    # Fallback
    if idea_id not in IDEAS_DB:
        raise HTTPException(status_code=404, detail="Idea not found")
    return IDEAS_DB[idea_id]

@router.put("/ideas/{idea_id}", response_model=Idea)
async def update_idea(request: Request, idea_id: str, idea_update: IdeaUpdate) -> Idea:
    """
    Update an idea.

    Args:
        request: FastAPI request object.
        idea_id: ID of the idea to update.
        idea_update: Update data.

    Returns:
        The updated idea.

    Raises:
        HTTPException: If idea is not found.
    """
    storage = request.app.state.storage
    audit: AuditLogger | None = getattr(request.app.state, "audit", None)

    if storage:
        current_idea = await storage.get_idea(idea_id)
        if not current_idea:
            raise HTTPException(status_code=404, detail="Idea not found")

        old_values = current_idea.model_dump()
        update_data = idea_update.model_dump(exclude_unset=True)
        updated_idea = current_idea.model_copy(update=update_data)
        updated_idea.updated_at = datetime.now(timezone.utc)

        await storage.update_idea(updated_idea)

        search = request.app.state.search
        if search:
            try:
                await search.index_idea(updated_idea)
            except Exception as e:
                logger.error("Failed to update index for idea: %s", e)

        # Log audit entry
        if audit:
            await audit.log_update(
                idea_id=idea_id,
                user_id=updated_idea.author_id or "anonymous",
                old_values=old_values,
                new_values=updated_idea.model_dump(),
            )

        logger.info("Updated idea: %s", idea_id)
        return updated_idea

    # Fallback
    if idea_id not in IDEAS_DB:
        raise HTTPException(status_code=404, detail="Idea not found")

    current_idea = IDEAS_DB[idea_id]
    update_data = idea_update.model_dump(exclude_unset=True)

    updated_idea = current_idea.model_copy(update=update_data)
    updated_idea.updated_at = datetime.now(timezone.utc)

    IDEAS_DB[idea_id] = updated_idea
    return updated_idea

@router.delete("/ideas/{idea_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_idea(request: Request, idea_id: str) -> None:
    """
    Delete an idea.

    Args:
        request: FastAPI request object.
        idea_id: ID of the idea to delete.
    """
    storage = request.app.state.storage
    search = request.app.state.search
    audit: AuditLogger | None = getattr(request.app.state, "audit", None)

    if storage:
        # Get idea title for audit before deletion
        idea = await storage.get_idea(idea_id)
        idea_title = idea.title if idea else ""

        await storage.delete_idea(idea_id)
        if search:
            try:
                await search.delete_idea(idea_id)
            except Exception as e:
                logger.error("Failed to delete idea from index: %s", e)

        # Log audit entry
        if audit:
            await audit.log_delete(
                idea_id=idea_id,
                user_id="anonymous",  # Would come from auth context
                idea_title=idea_title,
            )

        logger.info("Deleted idea: %s", idea_id)
        return

    # Fallback
    if idea_id in IDEAS_DB:
        del IDEAS_DB[idea_id]


@router.get("/search", response_model=list[Idea])
async def search_ideas(
    request: Request,
    q: str,
    skip: int = 0,
    limit: int = 20,
    idea_status: str | None = None,
) -> list[Idea]:
    """
    Search ideas.

    Args:
        request: FastAPI request object.
        q: Search query string.
        skip: Number of results to skip.
        limit: Maximum number of results to return.
        idea_status: Optional status filter.

    Returns:
        List of matching ideas.
    """
    search = request.app.state.search
    if search:
        # Filter string for OData
        filter_str = None
        if idea_status:
            filter_str = f"status eq '{idea_status}'"

        results = await search.search_ideas(
            search_text=q, top=limit, filter_str=filter_str
        )

        # Convert search results back to Idea models
        ideas = []
        for result in results:
            try:
                # Search Index fields should match model fields
                if "id" in result:
                    clean_data = {
                        k: v for k, v in result.items() if not k.startswith("@")
                    }
                    ideas.append(Idea(**clean_data))
            except Exception as e:
                logger.error("Error mapping search result to Idea: %s", e)
        return ideas

    # Fallback: simple text match on title/desc in memory
    filtered = []
    q_lower = q.lower()
    for idea in IDEAS_DB.values():
        if q_lower in idea.title.lower() or q_lower in idea.description.lower():
            if idea_status and idea.status != idea_status:
                continue
            filtered.append(idea)

    filtered.sort(key=lambda x: x.created_at, reverse=True)
    return filtered[skip : skip + limit]


@router.post("/ideas/{idea_id}/review", response_model=dict)
async def review_idea(request: Request, idea_id: str) -> dict:
    """
    Review idea with LLM and calculate scores.

    Args:
        request: FastAPI request object.
        idea_id: ID of the idea to review.

    Returns:
        Review results including scores and recommendations.

    Raises:
        HTTPException: If idea is not found.
    """
    storage = request.app.state.storage
    if storage:
        idea = await storage.get_idea(idea_id)
    else:
        idea = IDEAS_DB.get(idea_id)

    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    # Calculate scores if KPI estimates are available
    if idea.kpi_estimates:
        impact, feasibility, recommendation = scorer.calculate_scores(idea.kpi_estimates)
    else:
        impact = 0.0
        feasibility = 0.0
        recommendation = "unclassified"

    review_result = {
        "idea_id": idea_id,
        "review": "This idea shows promise. Consider specifying the target audience more clearly.",
        "impact_score": impact,
        "feasibility_score": feasibility,
        "recommendation_class": recommendation,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("Reviewed idea %s: impact=%s, feasibility=%s", idea_id, impact, feasibility)
    return review_result


@router.patch("/ideas/{idea_id}/status", response_model=Idea)
async def update_status(request: Request, idea_id: str, new_status: str) -> Idea:
    """
    Update idea status.

    Args:
        request: FastAPI request object.
        idea_id: ID of the idea to update.
        new_status: New status value.

    Returns:
        The updated idea.

    Raises:
        HTTPException: If idea is not found or status is invalid.
    """
    valid_statuses = [s.value for s in IdeaStatus]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of {valid_statuses}",
        )

    storage = request.app.state.storage
    audit: AuditLogger | None = getattr(request.app.state, "audit", None)

    if storage:
        idea = await storage.get_idea(idea_id)
        if not idea:
            raise HTTPException(status_code=404, detail="Idea not found")

        old_status = idea.status
        idea.status = new_status
        idea.updated_at = datetime.now(timezone.utc)
        await storage.update_idea(idea)

        search = request.app.state.search
        if search:
            try:
                await search.index_idea(idea)
            except Exception as e:
                logger.error("Failed to update search index: %s", e)

        # Log audit entry for status change
        if audit:
            await audit.log_status_change(
                idea_id=idea_id,
                user_id=idea.author_id or "anonymous",
                old_status=old_status,
                new_status=new_status,
            )

        logger.info("Updated status for idea %s: %s -> %s", idea_id, old_status, new_status)
        return idea

    # Fallback
    if idea_id not in IDEAS_DB:
        raise HTTPException(status_code=404, detail="Idea not found")

    idea = IDEAS_DB[idea_id]
    idea.status = new_status
    idea.updated_at = datetime.now(timezone.utc)
    IDEAS_DB[idea_id] = idea
    return idea


@router.post("/ideas/{idea_id}/score", response_model=Idea)
async def calculate_idea_scores(request: Request, idea_id: str) -> Idea:
    """
    Calculate and update scores for an idea based on its KPI estimates.

    Args:
        request: FastAPI request object.
        idea_id: ID of the idea to score.

    Returns:
        The updated idea with calculated scores.

    Raises:
        HTTPException: If idea is not found.
    """
    storage = request.app.state.storage
    audit: AuditLogger | None = getattr(request.app.state, "audit", None)

    if storage:
        idea = await storage.get_idea(idea_id)
    else:
        idea = IDEAS_DB.get(idea_id)

    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    if not idea.kpi_estimates:
        raise HTTPException(
            status_code=400,
            detail="Idea has no KPI estimates. Cannot calculate scores.",
        )

    # Store old scores for audit
    old_scores = {
        "impactScore": idea.impact_score,
        "feasibilityScore": idea.feasibility_score,
        "recommendationClass": idea.recommendation_class,
    }

    # Calculate new scores
    impact, feasibility, recommendation = scorer.calculate_scores(idea.kpi_estimates)

    idea.impact_score = impact
    idea.feasibility_score = feasibility
    idea.recommendation_class = recommendation
    idea.updated_at = datetime.now(timezone.utc)

    if storage:
        await storage.update_idea(idea)

        # Log audit entry for score update
        if audit:
            await audit.log_score_update(
                idea_id=idea_id,
                user_id="system",
                old_scores=old_scores,
                new_scores={
                    "impactScore": impact,
                    "feasibilityScore": feasibility,
                    "recommendationClass": recommendation,
                },
            )
    else:
        IDEAS_DB[idea_id] = idea

    logger.info(
        "Calculated scores for idea %s: impact=%s, feasibility=%s, recommendation=%s",
        idea_id,
        impact,
        feasibility,
        recommendation,
    )
    return idea


@router.get("/ideas/{idea_id}/audit", response_model=list[dict])
async def get_idea_audit_trail(
    request: Request, idea_id: str, limit: int = 50
) -> list[dict]:
    """
    Get audit trail for an idea.

    Args:
        request: FastAPI request object.
        idea_id: ID of the idea.
        limit: Maximum number of entries to return.

    Returns:
        List of audit entries.
    """
    audit: AuditLogger | None = getattr(request.app.state, "audit", None)

    if not audit:
        return []

    entries = await audit.get_audit_trail(idea_id=idea_id, limit=limit)
    return [entry.to_dict() for entry in entries]


# =============================================================================
# Similar Ideas Endpoints
# =============================================================================

@router.get("/similar", response_model=list[dict])
async def find_similar_ideas(
    request: Request,
    text: str,
    threshold: float = 0.7,
    limit: int = 5,
) -> list[dict]:
    """
    Find similar ideas based on text content.

    Args:
        request: FastAPI request object.
        text: Text to search for similar ideas.
        threshold: Similarity threshold 0-1 (default: 0.7).
        limit: Maximum results (default: 5).

    Returns:
        List of similar ideas with similarity scores.
    """
    search = request.app.state.search
    storage = request.app.state.storage

    if not text.strip():
        raise HTTPException(status_code=400, detail="text parameter is required")

    similar_results = []

    if search:
        # Use Azure AI Search for vector similarity
        try:
            results = await search.search_ideas(search_text=text, top=limit * 2)
            for result in results:
                # Skip if no ID
                if "id" not in result:
                    continue
                similar_results.append({
                    "ideaId": result.get("id"),
                    "title": result.get("title", ""),
                    "summary": result.get("summary", ""),
                    "similarityScore": result.get("@search.score", 0),
                    "status": result.get("status", ""),
                })
        except Exception as e:
            logger.error("Search error: %s", e)
    else:
        # Fallback: simple text matching
        text_lower = text.lower()
        for idea in IDEAS_DB.values():
            title_match = text_lower in idea.title.lower()
            desc_match = text_lower in idea.description.lower()
            if title_match or desc_match:
                similar_results.append({
                    "ideaId": idea.id,
                    "title": idea.title,
                    "summary": idea.summary,
                    "similarityScore": 0.8 if title_match else 0.6,
                    "status": idea.status,
                })

    return similar_results[:limit]


# =============================================================================
# Like Endpoints
# =============================================================================

# In-memory storage for likes (fallback)
LIKES_DB: dict[str, dict] = {}


@router.post("/ideas/{idea_id}/likes", response_model=dict)
async def add_like(request: Request, idea_id: str, user_id: str = "anonymous") -> dict:
    """
    Add a like to an idea.

    A user can only like an idea once.
    """
    storage = request.app.state.storage

    if storage:
        idea = await storage.get_idea(idea_id)
        if not idea:
            raise HTTPException(status_code=404, detail="Idea not found")

        # Check if already liked
        existing = await storage.get_like(idea_id, user_id)
        if existing:
            raise HTTPException(status_code=409, detail="Already liked this idea")

        # Create like
        like_id = f"{idea_id}_{user_id}"
        now = datetime.now(timezone.utc)
        like_data = {
            "likeId": like_id,
            "ideaId": idea_id,
            "userId": user_id,
            "createdAt": now.isoformat(),
        }
        await storage.create_like(like_data)

        # Update vote count
        idea.vote_count += 1
        await storage.update_idea(idea)

        return like_data

    # Fallback
    if idea_id not in IDEAS_DB:
        raise HTTPException(status_code=404, detail="Idea not found")

    like_key = f"{idea_id}_{user_id}"
    if like_key in LIKES_DB:
        raise HTTPException(status_code=409, detail="Already liked this idea")

    now = datetime.now(timezone.utc)
    like_data = {
        "likeId": like_key,
        "ideaId": idea_id,
        "userId": user_id,
        "createdAt": now.isoformat(),
    }
    LIKES_DB[like_key] = like_data
    IDEAS_DB[idea_id].vote_count += 1
    return like_data


@router.delete("/ideas/{idea_id}/likes", status_code=status.HTTP_204_NO_CONTENT)
async def remove_like(request: Request, idea_id: str, user_id: str = "anonymous") -> None:
    """Remove a like from an idea."""
    storage = request.app.state.storage

    if storage:
        idea = await storage.get_idea(idea_id)
        if not idea:
            raise HTTPException(status_code=404, detail="Idea not found")

        # Delete like
        await storage.delete_like(idea_id, user_id)

        # Update vote count
        idea.vote_count = max(0, idea.vote_count - 1)
        await storage.update_idea(idea)
        return

    # Fallback
    like_key = f"{idea_id}_{user_id}"
    if like_key in LIKES_DB:
        del LIKES_DB[like_key]
        if idea_id in IDEAS_DB:
            IDEAS_DB[idea_id].vote_count = max(0, IDEAS_DB[idea_id].vote_count - 1)


@router.get("/ideas/{idea_id}/likes/count", response_model=dict)
async def get_like_count(request: Request, idea_id: str, user_id: str = "anonymous") -> dict:
    """Get the like count for an idea and user's like status."""
    storage = request.app.state.storage

    if storage:
        idea = await storage.get_idea(idea_id)
        if not idea:
            raise HTTPException(status_code=404, detail="Idea not found")

        user_has_liked = await storage.get_like(idea_id, user_id) is not None

        return {
            "ideaId": idea_id,
            "likeCount": idea.vote_count,
            "userHasLiked": user_has_liked,
        }

    # Fallback
    if idea_id not in IDEAS_DB:
        raise HTTPException(status_code=404, detail="Idea not found")

    like_key = f"{idea_id}_{user_id}"
    return {
        "ideaId": idea_id,
        "likeCount": IDEAS_DB[idea_id].vote_count,
        "userHasLiked": like_key in LIKES_DB,
    }


@router.get("/ideas/{idea_id}/engagement", response_model=dict)
async def get_engagement(request: Request, idea_id: str, user_id: str = "anonymous") -> dict:
    """Get aggregated engagement metrics for an idea."""
    storage = request.app.state.storage

    if storage:
        idea = await storage.get_idea(idea_id)
        if not idea:
            raise HTTPException(status_code=404, detail="Idea not found")

        user_has_liked = await storage.get_like(idea_id, user_id) is not None

        return {
            "ideaId": idea_id,
            "likeCount": idea.vote_count,
            "commentCount": idea.comment_count,
            "userHasLiked": user_has_liked,
        }

    # Fallback
    if idea_id not in IDEAS_DB:
        raise HTTPException(status_code=404, detail="Idea not found")

    like_key = f"{idea_id}_{user_id}"
    return {
        "ideaId": idea_id,
        "likeCount": IDEAS_DB[idea_id].vote_count,
        "commentCount": IDEAS_DB[idea_id].comment_count,
        "userHasLiked": like_key in LIKES_DB,
    }


@router.post("/ideas/engagement/batch", response_model=dict)
async def get_engagement_batch(request: Request, idea_ids: list[str], user_id: str = "anonymous") -> dict:
    """Get engagement metrics for multiple ideas in one request."""
    storage = request.app.state.storage
    result = {}

    for idea_id in idea_ids:
        try:
            if storage:
                idea = await storage.get_idea(idea_id)
                if idea:
                    user_has_liked = await storage.get_like(idea_id, user_id) is not None
                    result[idea_id] = {
                        "likeCount": idea.vote_count,
                        "commentCount": idea.comment_count,
                        "userHasLiked": user_has_liked,
                    }
            else:
                if idea_id in IDEAS_DB:
                    like_key = f"{idea_id}_{user_id}"
                    result[idea_id] = {
                        "likeCount": IDEAS_DB[idea_id].vote_count,
                        "commentCount": IDEAS_DB[idea_id].comment_count,
                        "userHasLiked": like_key in LIKES_DB,
                    }
        except Exception as e:
            logger.error("Error fetching engagement for %s: %s", idea_id, e)

    return {"engagements": result}


# =============================================================================
# Comment Endpoints
# =============================================================================

# In-memory storage for comments (fallback)
COMMENTS_DB: dict[str, dict] = {}


@router.post("/ideas/{idea_id}/comments", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_comment(
    request: Request, idea_id: str, content: str, user_id: str = "anonymous"
) -> dict:
    """Create a new comment on an idea."""
    if not content.strip():
        raise HTTPException(status_code=400, detail="content is required")

    storage = request.app.state.storage

    now = datetime.now(timezone.utc)
    comment_id = str(uuid.uuid4())

    if storage:
        idea = await storage.get_idea(idea_id)
        if not idea:
            raise HTTPException(status_code=404, detail="Idea not found")

        comment_data = {
            "commentId": comment_id,
            "ideaId": idea_id,
            "userId": user_id,
            "content": content,
            "createdAt": now.isoformat(),
            "updatedAt": now.isoformat(),
        }
        await storage.create_comment(comment_data)

        # Update comment count
        idea.comment_count += 1
        await storage.update_idea(idea)

        return comment_data

    # Fallback
    if idea_id not in IDEAS_DB:
        raise HTTPException(status_code=404, detail="Idea not found")

    comment_data = {
        "commentId": comment_id,
        "ideaId": idea_id,
        "userId": user_id,
        "content": content,
        "createdAt": now.isoformat(),
        "updatedAt": now.isoformat(),
    }
    COMMENTS_DB[comment_id] = comment_data
    IDEAS_DB[idea_id].comment_count += 1
    return comment_data


@router.get("/ideas/{idea_id}/comments", response_model=list[dict])
async def list_comments(
    request: Request, idea_id: str, page: int = 1, page_size: int = 20
) -> list[dict]:
    """List comments for an idea with pagination."""
    storage = request.app.state.storage

    if storage:
        idea = await storage.get_idea(idea_id)
        if not idea:
            raise HTTPException(status_code=404, detail="Idea not found")

        comments = await storage.list_comments(idea_id, limit=page_size, skip=(page - 1) * page_size)
        return comments

    # Fallback
    if idea_id not in IDEAS_DB:
        raise HTTPException(status_code=404, detail="Idea not found")

    comments = [c for c in COMMENTS_DB.values() if c.get("ideaId") == idea_id]
    comments.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
    start = (page - 1) * page_size
    return comments[start : start + page_size]


@router.delete("/ideas/{idea_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(request: Request, idea_id: str, comment_id: str) -> None:
    """Delete a comment."""
    storage = request.app.state.storage

    if storage:
        idea = await storage.get_idea(idea_id)
        if idea:
            await storage.delete_comment(comment_id)
            idea.comment_count = max(0, idea.comment_count - 1)
            await storage.update_idea(idea)
        return

    # Fallback
    if comment_id in COMMENTS_DB:
        del COMMENTS_DB[comment_id]
        if idea_id in IDEAS_DB:
            IDEAS_DB[idea_id].comment_count = max(0, IDEAS_DB[idea_id].comment_count - 1)


# =============================================================================
# Role & Permissions Endpoints
# =============================================================================

@router.get("/role", response_model=dict)
async def get_current_user_role(request: Request, user_id: str = "anonymous") -> dict:
    """Get the current user's role and permissions."""
    # Create auth_claims dict from user_id
    auth_claims = {"oid": user_id, "sub": user_id}
    
    from ..services.permissions import IdeaPermission, IdeaRole
    from ..services.permissions import get_user_role as permissions_get_user_role
    from ..services.permissions import get_user_permissions

    role = permissions_get_user_role(auth_claims)
    permissions = get_user_permissions(auth_claims)

    return {
        "userId": user_id,
        "role": role.value,
        "permissions": permissions,
    }


# =============================================================================
# Export Endpoints
# =============================================================================

@router.get("/export/csv")
async def export_ideas_csv(
    request: Request,
    status_filter: str | None = None,
    recommendation: str | None = None,
) -> Any:
    """Export ideas to CSV format."""
    from fastapi.responses import StreamingResponse
    import csv
    import io

    storage = request.app.state.storage

    # Get ideas
    if storage:
        ideas = await storage.list_ideas(limit=1000)
    else:
        ideas = list(IDEAS_DB.values())

    # Apply filters
    if status_filter:
        ideas = [i for i in ideas if i.status == status_filter]
    if recommendation:
        ideas = [i for i in ideas if i.recommendation_class == recommendation]

    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "ID", "Title", "Description", "Status", "Department",
        "Impact Score", "Feasibility Score", "Recommendation",
        "Created At", "Author"
    ])

    # Data
    for idea in ideas:
        writer.writerow([
            idea.id,
            idea.title,
            idea.description[:200] + "..." if len(idea.description) > 200 else idea.description,
            idea.status,
            idea.department,
            idea.impact_score,
            idea.feasibility_score,
            idea.recommendation_class,
            idea.created_at.isoformat() if idea.created_at else "",
            idea.author_id or "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ideas_export.csv"}
    )


@router.get("/export/report")
async def export_ideas_report(
    request: Request,
    status_filter: str | None = None,
) -> dict:
    """Generate a summary report of ideas."""
    storage = request.app.state.storage

    if storage:
        ideas = await storage.list_ideas(limit=1000)
    else:
        ideas = list(IDEAS_DB.values())

    if status_filter:
        ideas = [i for i in ideas if i.status == status_filter]

    # Generate summary statistics
    status_counts = {}
    recommendation_counts = {}
    total_impact = 0.0
    total_feasibility = 0.0

    for idea in ideas:
        status_counts[idea.status] = status_counts.get(idea.status, 0) + 1
        recommendation_counts[idea.recommendation_class] = (
            recommendation_counts.get(idea.recommendation_class, 0) + 1
        )
        total_impact += idea.impact_score
        total_feasibility += idea.feasibility_score

    count = len(ideas)
    avg_impact = total_impact / count if count > 0 else 0
    avg_feasibility = total_feasibility / count if count > 0 else 0

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "totalIdeas": count,
        "averageImpactScore": round(avg_impact, 2),
        "averageFeasibilityScore": round(avg_feasibility, 2),
        "statusDistribution": status_counts,
        "recommendationDistribution": recommendation_counts,
    }

