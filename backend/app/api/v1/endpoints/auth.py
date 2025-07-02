from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.sql import func

from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_token
)
from app.core.config import settings
from app.models import User
from app.api.v1.dependencies import get_db, get_current_user

router = APIRouter()


class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str]
    role: str
    is_active: bool
    
    class Config:
        from_attributes = True


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    User login endpoint - authenticate with username/email and password
    """
    # Try to find user by username or email
    result = await db.execute(
        select(User).where(
            (User.username == form_data.username) | 
            (User.email == form_data.username)
        )
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Update last login
    user.last_login = func.now()
    await db.commit()
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user (admin only in production, open in dev)
    """
    # Check if user already exists
    result = await db.execute(
        select(User).where(
            (User.username == user_data.username) | 
            (User.email == user_data.email)
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create new user
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        is_active=True,
        is_superuser=False  # First user could be made superuser
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return UserResponse.from_orm(db_user)


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    User logout endpoint
    """
    # In a real implementation, you might want to:
    # - Add the token to a blacklist
    # - Clear any server-side sessions
    # - Log the logout event
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(refresh_token, credentials_exception)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except:
        raise credentials_exception
    
    # Verify user still exists and is active
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise credentials_exception
    
    # Create new tokens
    new_access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information
    """
    return UserResponse.from_orm(current_user)