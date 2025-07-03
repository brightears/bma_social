from sqlalchemy import Column, String, Text, JSON, Enum, Numeric, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum
from decimal import Decimal


class QuotationStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Quotation(BaseModel):
    __tablename__ = "quotations"
    
    # Reference number
    quote_number = Column(String, unique=True, nullable=False, index=True)
    
    # Customer info
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    company_name = Column(String, nullable=True)
    company_address = Column(Text, nullable=True)
    company_tax_id = Column(String, nullable=True)
    
    # Quotation details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Items (stored as JSON array)
    items = Column(JSON, default=list)
    # Format: [{"description": "Service", "quantity": 1, "unit_price": 1000, "total": 1000}]
    
    # Totals
    subtotal = Column(Numeric(12, 2), default=0)
    discount_percent = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(12, 2), default=0)
    tax_percent = Column(Numeric(5, 2), default=7)  # Default 7% VAT
    tax_amount = Column(Numeric(12, 2), default=0)
    total_amount = Column(Numeric(12, 2), default=0)
    
    # Terms and conditions
    payment_terms = Column(String, default="50% deposit, 50% on completion")
    validity_days = Column(Integer, default=30)
    notes = Column(Text, nullable=True)
    
    # Status tracking
    status = Column(Enum(QuotationStatus), default=QuotationStatus.DRAFT, nullable=False, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    viewed_at = Column(DateTime(timezone=True), nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Document storage
    pdf_url = Column(String, nullable=True)  # Stored PDF URL
    
    # Created by
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    customer = relationship("Customer", backref="quotations")
    created_by = relationship("User", backref="created_quotations")


class QuotationTemplate(BaseModel):
    __tablename__ = "quotation_templates"
    
    # Template info
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Default values
    title = Column(String, nullable=True)
    items = Column(JSON, default=list)
    payment_terms = Column(String, nullable=True)
    validity_days = Column(Integer, default=30)
    notes = Column(Text, nullable=True)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    
    # Created by
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    created_by = relationship("User", backref="quotation_templates")