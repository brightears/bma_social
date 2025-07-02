from sqlalchemy import Column, String, Boolean, ForeignKey, Text, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class MessageType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    LOCATION = "location"
    TEMPLATE = "template"
    QUICK_REPLY = "quick_reply"


class MessageDirection(str, enum.Enum):
    INBOUND = "inbound"   # From customer to us
    OUTBOUND = "outbound" # From us to customer


class MessageStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class Message(BaseModel):
    __tablename__ = "messages"
    
    # Relationships
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    sender_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # Null for customer messages
    
    # Message content
    type = Column(Enum(MessageType), default=MessageType.TEXT, nullable=False)
    content = Column(Text, nullable=False)
    media_url = Column(String, nullable=True)
    
    # Message metadata
    direction = Column(Enum(MessageDirection), nullable=False, index=True)
    status = Column(Enum(MessageStatus), default=MessageStatus.PENDING, nullable=False)
    
    # External IDs
    external_id = Column(String, nullable=True, unique=True)  # WhatsApp/Line message ID
    template_name = Column(String, nullable=True)  # For template messages
    
    # Additional data
    extra_data = Column(JSON, default=dict)  # Store provider-specific data
    error_message = Column(String, nullable=True)  # For failed messages
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", backref="sent_messages")