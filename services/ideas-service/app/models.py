"""
Data models for the Ideas Hub module.

This module defines the data structures for idea submission, analysis,
and management. Models follow Pydantic v2 patterns with Cosmos DB
serialization support.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class IdeaStatus(str, Enum):
    """Status of an idea in the workflow."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


class RecommendationClass(str, Enum):
    """Recommendation classification based on impact and feasibility scores."""

    QUICK_WIN = "quick_win"  # High feasibility, medium+ impact
    HIGH_LEVERAGE = "high_leverage"  # High impact, high feasibility
    STRATEGIC = "strategic"  # High impact, lower feasibility
    EVALUATE = "evaluate"  # Lower scores, needs review
    UNCLASSIFIED = "unclassified"  # Not yet classified


class IdeaKPIEstimates(BaseModel):
    """
    KPI estimates extracted from an idea by LLM analysis.

    All values are estimates and may be None if not applicable.
    """

    time_savings_hours: float | None = None
    cost_reduction_eur: float | None = None
    quality_improvement_percent: float | None = None
    employee_satisfaction_impact: float | None = None  # -100 to 100
    scalability_potential: float | None = None  # 0 to 100
    implementation_effort_days: float | None = None
    risk_level: str | None = None  # low, medium, high

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timeSavingsHours": self.time_savings_hours,
            "costReductionEur": self.cost_reduction_eur,
            "qualityImprovementPercent": self.quality_improvement_percent,
            "employeeSatisfactionImpact": self.employee_satisfaction_impact,
            "scalabilityPotential": self.scalability_potential,
            "implementationEffortDays": self.implementation_effort_days,
            "riskLevel": self.risk_level,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IdeaKPIEstimates":
        """Create instance from dictionary."""
        return cls(
            time_savings_hours=data.get("timeSavingsHours"),
            cost_reduction_eur=data.get("costReductionEur"),
            quality_improvement_percent=data.get("qualityImprovementPercent"),
            employee_satisfaction_impact=data.get("employeeSatisfactionImpact"),
            scalability_potential=data.get("scalabilityPotential"),
            implementation_effort_days=data.get("implementationEffortDays"),
            risk_level=data.get("riskLevel"),
        )


class IdeaBase(BaseModel):
    """Base model for idea creation and updates."""

    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    problem_description: str = Field(default="")
    expected_benefit: str = Field(default="")
    affected_processes: list[str] = Field(default_factory=list)
    target_users: list[str] = Field(default_factory=list)
    department: str = Field(default="")
    tags: list[str] = Field(default_factory=list)
    status: str = Field(default=IdeaStatus.SUBMITTED.value)


class IdeaCreate(IdeaBase):
    """Model for creating a new idea."""

    pass


class IdeaUpdate(BaseModel):
    """Model for updating an existing idea."""

    title: str | None = None
    description: str | None = None
    problem_description: str | None = None
    expected_benefit: str | None = None
    affected_processes: list[str] | None = None
    target_users: list[str] | None = None
    department: str | None = None
    tags: list[str] | None = None
    status: str | None = None


class Idea(IdeaBase):
    """
    Represents an idea submitted by an employee.

    Contains both user-provided fields and LLM-generated analysis fields.
    """

    # Core identification
    id: str
    author_id: str | None = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # LLM-generated fields (populated after analysis)
    summary: str = ""
    embedding: list[float] = Field(default_factory=list)

    # Scoring fields - Initial deterministic scores
    impact_score: float = 0.0
    feasibility_score: float = 0.0
    recommendation_class: str = RecommendationClass.UNCLASSIFIED.value

    # KPI estimates
    kpi_estimates: dict[str, Any] = Field(default_factory=dict)

    # LLM Review fields (Hybrid Approach)
    review_impact_score: float | None = None
    review_feasibility_score: float | None = None
    review_recommendation_class: str | None = None
    review_reasoning: str = ""
    reviewed_at: datetime | None = None
    reviewed_by: str = ""

    # Clustering
    cluster_label: str = ""

    # Analysis metadata
    analyzed_at: datetime | None = None
    analysis_version: str = ""

    # Similar ideas detected during creation
    similar_ideas: list[dict[str, Any]] = Field(default_factory=list)

    # Engagement
    vote_count: int = 0
    comment_count: int = 0

    model_config = {"from_attributes": True}

    def to_cosmos_item(self) -> dict[str, Any]:
        """
        Convert the idea to a Cosmos DB document format.

        Returns:
            Dictionary representation suitable for Cosmos DB storage.
        """
        return {
            "id": self.id,
            "ideaId": self.id,
            "type": "idea",
            "authorId": self.author_id,
            "title": self.title,
            "description": self.description,
            "problemDescription": self.problem_description,
            "expectedBenefit": self.expected_benefit,
            "affectedProcesses": self.affected_processes,
            "targetUsers": self.target_users,
            "department": self.department,
            "status": self.status,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            "summary": self.summary,
            "tags": self.tags,
            "embedding": self.embedding,
            "impactScore": self.impact_score,
            "feasibilityScore": self.feasibility_score,
            "recommendationClass": self.recommendation_class,
            "kpiEstimates": self.kpi_estimates,
            "reviewImpactScore": self.review_impact_score,
            "reviewFeasibilityScore": self.review_feasibility_score,
            "reviewRecommendationClass": self.review_recommendation_class,
            "reviewReasoning": self.review_reasoning,
            "reviewedAt": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "reviewedBy": self.reviewed_by,
            "clusterLabel": self.cluster_label,
            "analyzedAt": self.analyzed_at.isoformat() if self.analyzed_at else None,
            "analysisVersion": self.analysis_version,
            "similarIdeas": self.similar_ideas,
            "voteCount": self.vote_count,
            "commentCount": self.comment_count,
        }

    @classmethod
    def from_cosmos_item(cls, item: dict[str, Any]) -> "Idea":
        """
        Create an Idea instance from a Cosmos DB document.

        Args:
            item: Dictionary from Cosmos DB query result.

        Returns:
            Idea instance populated with document data.
        """
        # Parse datetime fields
        created_at = item.get("createdAt")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        elif not isinstance(created_at, datetime):
            created_at = datetime.now()

        updated_at = item.get("updatedAt")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        elif not isinstance(updated_at, datetime):
            updated_at = datetime.now()

        reviewed_at = item.get("reviewedAt")
        if isinstance(reviewed_at, str):
            reviewed_at = datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
        elif not isinstance(reviewed_at, datetime):
            reviewed_at = None

        analyzed_at = item.get("analyzedAt")
        if isinstance(analyzed_at, str):
            analyzed_at = datetime.fromisoformat(analyzed_at.replace("Z", "+00:00"))
        elif not isinstance(analyzed_at, datetime):
            analyzed_at = None

        return cls(
            id=item.get("ideaId", item.get("id", "")),
            author_id=item.get("authorId"),
            title=item.get("title", ""),
            description=item.get("description", ""),
            problem_description=item.get("problemDescription", ""),
            expected_benefit=item.get("expectedBenefit", ""),
            affected_processes=item.get("affectedProcesses", []),
            target_users=item.get("targetUsers", []),
            department=item.get("department", ""),
            status=item.get("status", IdeaStatus.SUBMITTED.value),
            created_at=created_at,
            updated_at=updated_at,
            summary=item.get("summary", ""),
            tags=item.get("tags", []),
            embedding=item.get("embedding", []),
            impact_score=item.get("impactScore", 0.0),
            feasibility_score=item.get("feasibilityScore", 0.0),
            recommendation_class=item.get(
                "recommendationClass", RecommendationClass.UNCLASSIFIED.value
            ),
            kpi_estimates=item.get("kpiEstimates", {}),
            review_impact_score=item.get("reviewImpactScore"),
            review_feasibility_score=item.get("reviewFeasibilityScore"),
            review_recommendation_class=item.get("reviewRecommendationClass"),
            review_reasoning=item.get("reviewReasoning", ""),
            reviewed_at=reviewed_at,
            reviewed_by=item.get("reviewedBy", ""),
            cluster_label=item.get("clusterLabel", ""),
            analyzed_at=analyzed_at,
            analysis_version=item.get("analysisVersion", ""),
            similar_ideas=item.get("similarIdeas", []),
            vote_count=item.get("voteCount", 0),
            comment_count=item.get("commentCount", 0),
        )

    def to_search_document(self) -> dict[str, Any]:
        """
        Convert the idea to an Azure AI Search document format.

        Returns:
            Dictionary representation suitable for Azure AI Search indexing.
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "problemDescription": self.problem_description,
            "expectedBenefit": self.expected_benefit,
            "summary": self.summary,
            "tags": self.tags,
            "authorId": self.author_id,
            "department": self.department,
            "status": self.status,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            "impactScore": self.impact_score,
            "feasibilityScore": self.feasibility_score,
            "recommendationClass": self.recommendation_class,
            "reviewImpactScore": self.review_impact_score,
            "reviewFeasibilityScore": self.review_feasibility_score,
            "reviewRecommendationClass": self.review_recommendation_class,
            "clusterLabel": self.cluster_label,
            "embedding": self.embedding if self.embedding else None,
        }

    def get_text_for_embedding(self) -> str:
        """Get combined text for embedding generation."""
        parts = [self.title, self.description]
        if self.problem_description:
            parts.append(self.problem_description)
        if self.expected_benefit:
            parts.append(self.expected_benefit)
        return " ".join(parts)

    def can_be_edited(self) -> bool:
        """Check if the idea can still be edited."""
        return self.status in [IdeaStatus.DRAFT.value, IdeaStatus.SUBMITTED.value]

    def is_owner(self, user_id: str) -> bool:
        """Check if the given user is the owner of this idea."""
        return self.author_id == user_id


class IdeaListResponse(BaseModel):
    """Response model for paginated idea list."""

    ideas: list[Idea]
    total_count: int
    page: int
    page_size: int
    has_more: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            "ideas": [idea.to_cosmos_item() for idea in self.ideas],
            "totalCount": self.total_count,
            "page": self.page,
            "pageSize": self.page_size,
            "hasMore": self.has_more,
        }


class SimilarIdea(BaseModel):
    """Represents a similar idea found during duplicate detection."""

    idea_id: str
    title: str
    summary: str | None = None
    similarity_score: float
    status: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            "ideaId": self.idea_id,
            "title": self.title,
            "summary": self.summary,
            "similarityScore": self.similarity_score,
            "status": self.status,
        }


class SimilarIdeasResponse(BaseModel):
    """Response model for similar ideas search."""

    similar_ideas: list[SimilarIdea]
    threshold: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            "similarIdeas": [si.to_dict() for si in self.similar_ideas],
            "threshold": self.threshold,
        }


class IdeaLike(BaseModel):
    """
    Represents a like on an idea.

    Stores the relationship between a user and an idea they liked.
    """

    like_id: str
    idea_id: str
    user_id: str
    created_at: datetime

    def to_cosmos_item(self) -> dict[str, Any]:
        """Convert to Cosmos DB document format."""
        return {
            "id": self.like_id,
            "likeId": self.like_id,
            "ideaId": self.idea_id,
            "userId": self.user_id,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "type": "idea_like",
        }

    @classmethod
    def from_cosmos_item(cls, item: dict[str, Any]) -> "IdeaLike":
        """Create an IdeaLike instance from a Cosmos DB document."""
        created_at = item.get("createdAt")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        elif not isinstance(created_at, datetime):
            created_at = datetime.now()

        return cls(
            like_id=item.get("likeId", item.get("id", "")),
            idea_id=item.get("ideaId", ""),
            user_id=item.get("userId", ""),
            created_at=created_at,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON API response."""
        return {
            "likeId": self.like_id,
            "ideaId": self.idea_id,
            "userId": self.user_id,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }


class IdeaComment(BaseModel):
    """
    Represents a comment on an idea.

    Allows team members to provide feedback and discuss ideas.
    """

    comment_id: str
    idea_id: str
    user_id: str
    content: str
    created_at: datetime
    updated_at: datetime

    def to_cosmos_item(self) -> dict[str, Any]:
        """Convert to Cosmos DB document format."""
        return {
            "id": self.comment_id,
            "commentId": self.comment_id,
            "ideaId": self.idea_id,
            "userId": self.user_id,
            "content": self.content,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            "type": "idea_comment",
        }

    @classmethod
    def from_cosmos_item(cls, item: dict[str, Any]) -> "IdeaComment":
        """Create an IdeaComment instance from a Cosmos DB document."""
        created_at = item.get("createdAt")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        elif not isinstance(created_at, datetime):
            created_at = datetime.now()

        updated_at = item.get("updatedAt")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        elif not isinstance(updated_at, datetime):
            updated_at = datetime.now()

        return cls(
            comment_id=item.get("commentId", item.get("id", "")),
            idea_id=item.get("ideaId", ""),
            user_id=item.get("userId", ""),
            content=item.get("content", ""),
            created_at=created_at,
            updated_at=updated_at,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON API response."""
        return {
            "commentId": self.comment_id,
            "ideaId": self.idea_id,
            "userId": self.user_id,
            "content": self.content,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_owner(self, user_id: str) -> bool:
        """Check if the given user is the owner of this comment."""
        return self.user_id == user_id


class IdeaCommentsResponse(BaseModel):
    """Response model for paginated comment list."""

    comments: list[IdeaComment]
    total_count: int
    page: int
    page_size: int
    has_more: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            "comments": [comment.to_dict() for comment in self.comments],
            "totalCount": self.total_count,
            "page": self.page,
            "pageSize": self.page_size,
            "hasMore": self.has_more,
        }


class IdeaEngagement(BaseModel):
    """
    Aggregated engagement metrics for an idea.

    Contains like count, comment count, and user-specific status.
    """

    idea_id: str
    like_count: int = 0
    comment_count: int = 0
    user_has_liked: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON API response."""
        return {
            "ideaId": self.idea_id,
            "likeCount": self.like_count,
            "commentCount": self.comment_count,
            "userHasLiked": self.user_has_liked,
        }
