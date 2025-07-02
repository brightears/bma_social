from sqlalchemy import Column, String, Boolean, Text, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
import enum


class TemplateChannel(str, enum.Enum):
    WHATSAPP = "whatsapp"
    LINE = "line"
    EMAIL = "email"


class TemplateStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"


class Template(BaseModel):
    __tablename__ = "templates"
    
    # Basic info
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Template content
    channel = Column(Enum(TemplateChannel), nullable=False, index=True)
    content = Column(Text, nullable=False)
    subject = Column(String, nullable=True)  # For email templates
    
    # Variables
    variables = Column(JSON, default=list)  # ["customer_name", "order_number"]
    
    # WhatsApp specific
    whatsapp_template_name = Column(String, nullable=True)  # Name in WhatsApp Business
    whatsapp_template_id = Column(String, nullable=True)    # ID from WhatsApp
    language_code = Column(String, default="en", nullable=False)
    
    # Status
    status = Column(Enum(TemplateStatus), default=TemplateStatus.DRAFT, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Media
    media_type = Column(String, nullable=True)  # image, video, document
    media_url = Column(String, nullable=True)
    
    # Additional settings
    category = Column(String, nullable=True)  # marketing, utility, authentication
    tags = Column(JSON, default=list)