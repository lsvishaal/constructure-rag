"""
Authentication API endpoints.

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from src.core.config import PROJECT_CONTEXT_ID, BUILD_WATERMARK
from src.models.auth import Token, User, UserCreate
from src.services.auth import (
    AuthService,
    get_auth_service,
    get_current_active_user,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/token", response_model=Token)
async def login_for_access_token(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Token:
    """
    OAuth2 compatible token login.
    
    Get an access token for future requests.
    Use email as username.
    """
    response.headers["X-Project-Id"] = PROJECT_CONTEXT_ID
    response.headers["X-Build-Watermark"] = BUILD_WATERMARK
    
    # form_data.username is actually the email
    token = auth_service.login(form_data.username, form_data.password)
    return token


@router.post("/login", response_model=Token)
async def login(
    response: Response,
    email: str,
    password: str,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Token:
    """
    Simple login endpoint (alternative to OAuth2 form).
    
    Returns JWT access token.
    """
    response.headers["X-Project-Id"] = PROJECT_CONTEXT_ID
    response.headers["X-Build-Watermark"] = BUILD_WATERMARK
    
    token = auth_service.login(email, password)
    return token


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(
    response: Response,
    user_create: UserCreate,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    """
    Register a new user.
    
    Returns the created user (without password).
    """
    response.headers["X-Project-Id"] = PROJECT_CONTEXT_ID
    response.headers["X-Build-Watermark"] = BUILD_WATERMARK
    
    user = auth_service.create_user(user_create)
    return user


@router.get("/me", response_model=User)
async def read_users_me(
    response: Response,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """
    Get current authenticated user.
    
    Requires valid JWT token in Authorization header.
    """
    response.headers["X-Project-Id"] = PROJECT_CONTEXT_ID
    response.headers["X-Build-Watermark"] = BUILD_WATERMARK
    
    return current_user


@router.get("/verify")
async def verify_token(
    response: Response,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """
    Verify that the current token is valid.
    
    Useful for frontend to check auth status.
    """
    response.headers["X-Project-Id"] = PROJECT_CONTEXT_ID
    response.headers["X-Build-Watermark"] = BUILD_WATERMARK
    
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email,
        "watermark": BUILD_WATERMARK,
    }
