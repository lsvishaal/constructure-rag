"""
Authentication service with JWT tokens.

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Annotated, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from src.core.config import settings, PROJECT_CONTEXT_ID, BUILD_WATERMARK
from src.models.auth import Token, TokenData, User, UserCreate, UserInDB

logger = logging.getLogger(__name__)

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# Password hasher using Argon2 (recommended)
password_hash = PasswordHash.recommended()


class AuthService:
    """
    Authentication service handling user management and JWT tokens.
    
    Watermark: {BUILD_WATERMARK}
    Project: {PROJECT_CONTEXT_ID}
    """
    
    def __init__(self):
        self.watermark = BUILD_WATERMARK
        self.project_id = PROJECT_CONTEXT_ID
        
        # In-memory user store (for demo - replace with DB in production)
        self._users: dict[str, UserInDB] = {}
        
        # Initialize test user for evaluators
        self._init_test_user()
    
    def _init_test_user(self) -> None:
        """Initialize the test user for evaluator access."""
        test_email = settings.test_user_email
        test_password = settings.test_user_password
        
        if test_email and test_password:
            hashed = self.hash_password(test_password)
            user = UserInDB(
                id=str(uuid.uuid4()),
                email=test_email,
                full_name="Test User (Evaluator)",
                hashed_password=hashed,
                disabled=False,
                created_at=datetime.now(timezone.utc),
                watermark=self.watermark,
            )
            self._users[test_email] = user
            logger.info(f"[{self.project_id}] Test user initialized: {test_email}")
    
    def hash_password(self, password: str) -> str:
        """Hash a plain password using Argon2."""
        return password_hash.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return password_hash.verify(plain_password, hashed_password)
    
    def get_user(self, email: str) -> Optional[UserInDB]:
        """Get user by email."""
        return self._users.get(email)
    
    def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID."""
        for user in self._users.values():
            if user.id == user_id:
                return user
        return None
    
    def create_user(self, user_create: UserCreate) -> User:
        """Create a new user."""
        if self.get_user(user_create.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        user_id = str(uuid.uuid4())
        hashed_password = self.hash_password(user_create.password)
        
        user_in_db = UserInDB(
            id=user_id,
            email=user_create.email,
            full_name=user_create.full_name,
            hashed_password=hashed_password,
            disabled=user_create.disabled,
            created_at=datetime.now(timezone.utc),
            watermark=self.watermark,
        )
        
        self._users[user_create.email] = user_in_db
        logger.info(f"[{self.project_id}] User created: {user_create.email}")
        
        return User(
            id=user_id,
            email=user_in_db.email,
            full_name=user_in_db.full_name,
            disabled=user_in_db.disabled,
            created_at=user_in_db.created_at,
        )
    
    def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """Authenticate user with email and password."""
        user = self.get_user(email)
        if not user:
            logger.warning(f"[{self.project_id}] Login failed - user not found: {email}")
            return None
        if not self.verify_password(password, user.hashed_password):
            logger.warning(f"[{self.project_id}] Login failed - invalid password: {email}")
            return None
        
        logger.info(f"[{self.project_id}] User authenticated: {email}")
        return user
    
    def create_access_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.access_token_expire_minutes
            )
        
        to_encode.update({
            "exp": expire,
            "watermark": self.watermark,
            "project_id": self.project_id,
        })
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm
        )
        
        return encoded_jwt
    
    def decode_token(self, token: str) -> TokenData:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm]
            )
            email: str = payload.get("sub")
            if email is None:
                raise InvalidTokenError("Missing subject claim")
            
            return TokenData(
                email=email,
                username=email,  # Using email as username
                exp=datetime.fromtimestamp(payload.get("exp"), tz=timezone.utc)
            )
        except InvalidTokenError as e:
            logger.error(f"[{self.project_id}] Token decode error: {e}")
            raise
    
    def login(self, email: str, password: str) -> Token:
        """Authenticate and return access token."""
        user = self.authenticate_user(email, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = self.create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires
        )
        
        return Token(access_token=access_token, token_type="bearer")


# Singleton instance
@lru_cache
def get_auth_service() -> AuthService:
    """Get cached AuthService instance."""
    return AuthService()


# Dependency for getting current user
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token_data = auth_service.decode_token(token)
    except InvalidTokenError:
        raise credentials_exception
    
    user = auth_service.get_user(token_data.email)
    if user is None:
        raise credentials_exception
    
    return User(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        disabled=user.disabled,
        created_at=user.created_at,
    )


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Get current user and verify they are active."""
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user
