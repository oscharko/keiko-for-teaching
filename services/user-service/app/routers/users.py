"""User profile and preferences endpoints."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(tags=["users"])


class UserPreferences(BaseModel):
    """User preferences model."""

    theme: str = Field(default="light", description="UI theme (light/dark)")
    language: str = Field(default="en", description="Preferred language")
    notifications_enabled: bool = Field(default=True, description="Enable notifications")
    default_model: str = Field(default="gpt-4o", description="Default AI model")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: int = Field(default=4096, ge=1, le=32000, description="Max tokens")


class UserProfile(BaseModel):
    """User profile model."""

    user_id: str
    email: str | None = None
    name: str | None = None
    preferences: UserPreferences = Field(default_factory=UserPreferences)


class UpdatePreferencesRequest(BaseModel):
    """Update preferences request."""

    preferences: UserPreferences


@router.get("/users/{user_id}", response_model=UserProfile)
async def get_user_profile(user_id: str, request: Request) -> UserProfile:
    """Get user profile and preferences.
    
    Args:
        user_id: User ID
        request: FastAPI request object
        
    Returns:
        UserProfile: User profile with preferences
        
    Raises:
        HTTPException: If user not found
    """
    cache_client = request.app.state.cache_client
    
    # Try to get from cache
    profile_data = await cache_client.get(f"profile:{user_id}")
    
    if profile_data:
        return UserProfile(**profile_data)
    
    # If not in cache, create default profile
    default_profile = UserProfile(
        user_id=user_id,
        preferences=UserPreferences(),
    )
    
    # Store in cache
    await cache_client.set(f"profile:{user_id}", default_profile.model_dump())
    
    return default_profile


@router.put("/users/{user_id}/preferences")
async def update_user_preferences(
    user_id: str,
    update_request: UpdatePreferencesRequest,
    request: Request,
) -> UserProfile:
    """Update user preferences.
    
    Args:
        user_id: User ID
        update_request: Updated preferences
        request: FastAPI request object
        
    Returns:
        UserProfile: Updated user profile
    """
    cache_client = request.app.state.cache_client
    
    # Get existing profile
    profile_data = await cache_client.get(f"profile:{user_id}")
    
    if profile_data:
        profile = UserProfile(**profile_data)
    else:
        profile = UserProfile(user_id=user_id)
    
    # Update preferences
    profile.preferences = update_request.preferences
    
    # Save to cache
    await cache_client.set(f"profile:{user_id}", profile.model_dump())
    
    logger.info(f"Updated preferences for user {user_id}")
    
    return profile


@router.get("/users/{user_id}/preferences", response_model=UserPreferences)
async def get_user_preferences(user_id: str, request: Request) -> UserPreferences:
    """Get user preferences only.
    
    Args:
        user_id: User ID
        request: FastAPI request object
        
    Returns:
        UserPreferences: User preferences
    """
    profile = await get_user_profile(user_id, request)
    return profile.preferences

