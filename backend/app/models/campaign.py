from sqlalchemy import Column, String, Boolean, ForeignKey, Text, JSON, Enum, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class CampaignChannel(str, enum.Enum):
    WHATSAPP = "whatsapp"
    LINE = "line"
    EMAIL = "email"
    ALL = "all"


class Campaign(BaseModel):
    __tablename__ = "campaigns"
    
    # Basic info
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Campaign configuration
    channel = Column(Enum(CampaignChannel), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("templates.id"), nullable=True)
    message_content = Column(Text, nullable=True)  # For non-template messages
    
    # Scheduling
    status = Column(Enum(CampaignStatus), default=CampaignStatus.DRAFT, nullable=False, index=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Targeting
    segment_filters = Column(JSON, default=dict)  # Customer filtering criteria
    recipient_count = Column(Integer, default=0)
    
    # Performance metrics
    sent_count = Column(Integer, default=0)
    delivered_count = Column(Integer, default=0)
    read_count = Column(Integer, default=0)
    clicked_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    
    # Created by
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    template = relationship("Template", backref="campaigns")
    created_by = relationship("User", backref="created_campaigns")