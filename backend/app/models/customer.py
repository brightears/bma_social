from sqlalchemy import Column, String, Boolean, JSON
from app.models.base import BaseModel


class Customer(BaseModel):
    __tablename__ = "customers"
    
    # Basic info
    name = Column(String, nullable=False, index=True)
    email = Column(String, nullable=True, index=True)
    phone = Column(String, nullable=True, index=True)
    
    # Channel identifiers
    whatsapp_id = Column(String, nullable=True, unique=True, index=True)
    line_user_id = Column(String, nullable=True, unique=True, index=True)
    
    # CRM integration
    crm_customer_id = Column(String, nullable=True, unique=True, index=True)
    
    # Preferences
    preferred_channel = Column(String, default="whatsapp")
    language = Column(String, default="en")
    timezone = Column(String, default="Asia/Bangkok")
    
    # Status
    is_active = Column(Boolean, default=True)
    opt_out = Column(Boolean, default=False)
    
    # Additional data
    tags = Column(JSON, default=list)
    metadata = Column(JSON, default=dict)