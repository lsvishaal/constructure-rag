"""
Authentication models.

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from src.core.config import PROJECT_CONTEXT_ID, BUILD_WATERMARK


class Token(BaseModel):
    """JWT Token response model."""
    access_token: str
    token_type: str = "bearer"
    watermark: str = BUILD_WATERMARK


class TokenData(BaseModel):
    """Data extracted from JWT token."""
    username: Optional[str] = None
    email: Optional[str] = None
    exp: Optional[datetime] = None


class UserBase(BaseModel):
    """Base user model."""
    email: EmailStr
    full_name: Optional[str] = None
    disabled: bool = False


class UserCreate(UserBase):
    """User creation model."""
    password: str = Field(..., min_length=8)


class User(UserBase):
    """User response model (no password)."""
    id: str
    created_at: datetime
    project_context: str = PROJECT_CONTEXT_ID
    
    model_config = {"from_attributes": True}


class UserInDB(UserBase):
    """User model with hashed password (internal use)."""
    id: str
    hashed_password: str
    created_at: datetime
    watermark: str = BUILD_WATERMARK
