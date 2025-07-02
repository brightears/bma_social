from fastapi import APIRouter, HTTPException, status
from typing import Any, List
from pydantic import BaseModel

router = APIRouter()


class UserCreate(BaseModel):
    email: str
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool


@router.get("/", response_model=List[UserResponse], summary="Get all users")
async def get_users(skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve all users.
    """
    # TODO: Implement user retrieval logic
    return []


@router.get("/{user_id}", response_model=UserResponse, summary="Get user by ID")
async def get_user(user_id: int) -> Any:
    """
    Get a specific user by ID.
    """
    # TODO: Implement user retrieval logic
    raise HTTPException(status_code=404, detail="User not found")


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Create new user")
async def create_user(user: UserCreate) -> Any:
    """
    Create new user.
    """
    # TODO: Implement user creation logic
    return UserResponse(
        id=1,
        email=user.email,
        username=user.username,
        is_active=True
    )


@router.put("/{user_id}", response_model=UserResponse, summary="Update user")
async def update_user(user_id: int, user: UserCreate) -> Any:
    """
    Update a user.
    """
    # TODO: Implement user update logic
    raise HTTPException(status_code=404, detail="User not found")


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete user")
async def delete_user(user_id: int) -> None:
    """
    Delete a user.
    """
    # TODO: Implement user deletion logic
    pass