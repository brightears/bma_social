from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Enum, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import BaseModel
import enum


class ConversationStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    PENDING = "pending"
    ARCHIVED = "archived"


class ConversationChannel(str, enum.Enum):
    WHATSAPP = "whatsapp"
    LINE = "line"
    EMAIL = "email"


class Conversation(BaseModel):
    __tablename__ = "conversations"
    
    # Relationships
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    assigned_to_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    # Channel info
    channel = Column(Enum(ConversationChannel), nullable=False, index=True)
    channel_conversation_id = Column(String, nullable=True)  # External ID from WhatsApp/Line
    
    # Status
    status = Column(Enum(ConversationStatus), default=ConversationStatus.OPEN, nullable=False, index=True)
    unread_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    last_message_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    subject = Column(String, nullable=True)
    tags = Column(JSON, default=list)
    
    # Relationships
    customer = relationship("Customer", backref="conversations")
    assigned_to = relationship("User", backref="assigned_conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")