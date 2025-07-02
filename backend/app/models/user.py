from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    AGENT = "agent"
    VIEWER = "viewer"


class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.AGENT, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # CRM integration
    crm_user_id = Column(String, nullable=True, index=True)  # ID in BMA CRM system