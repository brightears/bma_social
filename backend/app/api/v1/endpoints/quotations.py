from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, validator
from datetime import datetime, timedelta
from decimal import Decimal
import logging
import uuid

from app.models import Quotation, QuotationStatus, QuotationTemplate, Customer, User, Message, Conversation
from app.models.conversation import ConversationChannel
from app.models.message import MessageType, MessageDirection, MessageStatus
from app.api.v1.dependencies import get_db, get_current_user
from app.services.pdf_service import pdf_service
from app.services.whatsapp_service import whatsapp_service

router = APIRouter()
logger = logging.getLogger(__name__)


class QuotationItem(BaseModel):
    description: str
    quantity: int = 1
    unit_price: float
    total: float = None
    
    @validator('total', pre=True, always=True)
    def calculate_total(cls, v, values):
        if v is None and 'quantity' in values and 'unit_price' in values:
            return values['quantity'] * values['unit_price']
        return v


class QuotationCreate(BaseModel):
    customer_id: str
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    company_tax_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    items: List[QuotationItem]
    discount_percent: float = 0
    tax_percent: float = 7
    payment_terms: str = "50% deposit, 50% on completion"
    validity_days: int = 30
    notes: Optional[str] = None
    
    @validator('discount_percent', 'tax_percent')
    def validate_percentages(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Percentage must be between 0 and 100')
        return v


class QuotationUpdate(BaseModel):
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    company_tax_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    items: Optional[List[QuotationItem]] = None
    discount_percent: Optional[float] = None
    tax_percent: Optional[float] = None
    payment_terms: Optional[str] = None
    validity_days: Optional[int] = None
    notes: Optional[str] = None


class QuotationResponse(BaseModel):
    id: str
    quote_number: str
    customer_id: str
    customer_name: str
    customer_phone: str
    customer_email: Optional[str]
    company_name: Optional[str]
    company_address: Optional[str]
    company_tax_id: Optional[str]
    title: str
    description: Optional[str]
    items: List[Dict[str, Any]]
    subtotal: float
    discount_percent: float
    discount_amount: float
    tax_percent: float
    tax_amount: float
    total_amount: float
    payment_terms: str
    validity_days: int
    notes: Optional[str]
    status: QuotationStatus
    sent_at: Optional[datetime]
    viewed_at: Optional[datetime]
    responded_at: Optional[datetime]
    pdf_url: Optional[str]
    created_at: datetime
    created_by_name: str
    
    class Config:
        from_attributes = True


class SendQuotationRequest(BaseModel):
    channel: str = "whatsapp"  # whatsapp, line, email
    message: Optional[str] = None  # Optional custom message


@router.get("/", response_model=List[QuotationResponse])
async def get_quotations(
    skip: int = 0,
    limit: int = 100,
    status: Optional[QuotationStatus] = None,
    customer_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all quotations with optional filtering"""
    
    query = select(Quotation)
    
    if status:
        query = query.where(Quotation.status == status)
    
    if customer_id:
        query = query.where(Quotation.customer_id == customer_id)
    
    query = query.order_by(Quotation.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    quotations = result.scalars().all()
    
    # Get customer and creator info
    customer_ids = list(set(q.customer_id for q in quotations))
    creator_ids = list(set(q.created_by_id for q in quotations))
    
    customers = {}
    if customer_ids:
        customer_result = await db.execute(
            select(Customer).where(Customer.id.in_(customer_ids))
        )
        customers = {c.id: c for c in customer_result.scalars().all()}
    
    creators = {}
    if creator_ids:
        creator_result = await db.execute(
            select(User).where(User.id.in_(creator_ids))
        )
        creators = {u.id: u for u in creator_result.scalars().all()}
    
    # Build response
    response = []
    for quotation in quotations:
        customer = customers.get(quotation.customer_id)
        creator = creators.get(quotation.created_by_id)
        
        response.append(QuotationResponse(
            id=str(quotation.id),
            quote_number=quotation.quote_number,
            customer_id=str(quotation.customer_id),
            customer_name=customer.name if customer else "Unknown",
            customer_phone=customer.phone if customer else "",
            customer_email=customer.email if customer else None,
            company_name=quotation.company_name,
            company_address=quotation.company_address,
            company_tax_id=quotation.company_tax_id,
            title=quotation.title,
            description=quotation.description,
            items=quotation.items or [],
            subtotal=float(quotation.subtotal),
            discount_percent=float(quotation.discount_percent),
            discount_amount=float(quotation.discount_amount),
            tax_percent=float(quotation.tax_percent),
            tax_amount=float(quotation.tax_amount),
            total_amount=float(quotation.total_amount),
            payment_terms=quotation.payment_terms,
            validity_days=quotation.validity_days,
            notes=quotation.notes,
            status=quotation.status,
            sent_at=quotation.sent_at,
            viewed_at=quotation.viewed_at,
            responded_at=quotation.responded_at,
            pdf_url=quotation.pdf_url,
            created_at=quotation.created_at,
            created_by_name=creator.full_name or creator.username if creator else "Unknown"
        ))
    
    return response


@router.post("/", response_model=QuotationResponse, status_code=status.HTTP_201_CREATED)
async def create_quotation(
    quotation: QuotationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new quotation"""
    
    try:
        # Generate quote number
        today = datetime.now()
        count_result = await db.execute(
            select(func.count(Quotation.id)).where(
                func.date(Quotation.created_at) == today.date()
            )
        )
        count = count_result.scalar() or 0
        quote_number = f"QT{today.strftime('%Y%m%d')}{count + 1:03d}"
        
        # Calculate totals
        subtotal = sum(item.total for item in quotation.items)
        discount_amount = subtotal * (quotation.discount_percent / 100)
        amount_after_discount = subtotal - discount_amount
        tax_amount = amount_after_discount * (quotation.tax_percent / 100)
        total_amount = amount_after_discount + tax_amount
        
        # Create quotation
        db_quotation = Quotation(
            quote_number=quote_number,
            customer_id=quotation.customer_id,
            company_name=quotation.company_name,
            company_address=quotation.company_address,
            company_tax_id=quotation.company_tax_id,
            title=quotation.title,
            description=quotation.description,
            items=[item.dict() for item in quotation.items],
            subtotal=Decimal(str(subtotal)),
            discount_percent=Decimal(str(quotation.discount_percent)),
            discount_amount=Decimal(str(discount_amount)),
            tax_percent=Decimal(str(quotation.tax_percent)),
            tax_amount=Decimal(str(tax_amount)),
            total_amount=Decimal(str(total_amount)),
            payment_terms=quotation.payment_terms,
            validity_days=quotation.validity_days,
            notes=quotation.notes,
            created_by_id=current_user.id
        )
        
        db.add(db_quotation)
        await db.commit()
        await db.refresh(db_quotation)
        
        # Get customer info
        customer_result = await db.execute(
            select(Customer).where(Customer.id == quotation.customer_id)
        )
        customer = customer_result.scalar_one_or_none()
        
        return QuotationResponse(
            id=str(db_quotation.id),
            quote_number=db_quotation.quote_number,
            customer_id=str(db_quotation.customer_id),
            customer_name=customer.name if customer else "Unknown",
            customer_phone=customer.phone if customer else "",
            customer_email=customer.email if customer else None,
            company_name=db_quotation.company_name,
            company_address=db_quotation.company_address,
            company_tax_id=db_quotation.company_tax_id,
            title=db_quotation.title,
            description=db_quotation.description,
            items=db_quotation.items,
            subtotal=float(db_quotation.subtotal),
            discount_percent=float(db_quotation.discount_percent),
            discount_amount=float(db_quotation.discount_amount),
            tax_percent=float(db_quotation.tax_percent),
            tax_amount=float(db_quotation.tax_amount),
            total_amount=float(db_quotation.total_amount),
            payment_terms=db_quotation.payment_terms,
            validity_days=db_quotation.validity_days,
            notes=db_quotation.notes,
            status=db_quotation.status,
            sent_at=db_quotation.sent_at,
            viewed_at=db_quotation.viewed_at,
            responded_at=db_quotation.responded_at,
            pdf_url=db_quotation.pdf_url,
            created_at=db_quotation.created_at,
            created_by_name=current_user.full_name or current_user.username
        )
        
    except Exception as e:
        logger.error(f"Error creating quotation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create quotation: {str(e)}"
        )


@router.get("/{quotation_id}", response_model=QuotationResponse)
async def get_quotation(
    quotation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific quotation"""
    
    result = await db.execute(
        select(Quotation).where(Quotation.id == quotation_id)
    )
    quotation = result.scalar_one_or_none()
    
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    # Get customer and creator info
    customer_result = await db.execute(
        select(Customer).where(Customer.id == quotation.customer_id)
    )
    customer = customer_result.scalar_one_or_none()
    
    creator_result = await db.execute(
        select(User).where(User.id == quotation.created_by_id)
    )
    creator = creator_result.scalar_one_or_none()
    
    return QuotationResponse(
        id=str(quotation.id),
        quote_number=quotation.quote_number,
        customer_id=str(quotation.customer_id),
        customer_name=customer.name if customer else "Unknown",
        customer_phone=customer.phone if customer else "",
        customer_email=customer.email if customer else None,
        company_name=quotation.company_name,
        company_address=quotation.company_address,
        company_tax_id=quotation.company_tax_id,
        title=quotation.title,
        description=quotation.description,
        items=quotation.items or [],
        subtotal=float(quotation.subtotal),
        discount_percent=float(quotation.discount_percent),
        discount_amount=float(quotation.discount_amount),
        tax_percent=float(quotation.tax_percent),
        tax_amount=float(quotation.tax_amount),
        total_amount=float(quotation.total_amount),
        payment_terms=quotation.payment_terms,
        validity_days=quotation.validity_days,
        notes=quotation.notes,
        status=quotation.status,
        sent_at=quotation.sent_at,
        viewed_at=quotation.viewed_at,
        responded_at=quotation.responded_at,
        pdf_url=quotation.pdf_url,
        created_at=quotation.created_at,
        created_by_name=creator.full_name or creator.username if creator else "Unknown"
    )


@router.get("/{quotation_id}/pdf")
async def get_quotation_pdf(
    quotation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate and download quotation PDF"""
    
    # Get quotation
    result = await db.execute(
        select(Quotation).where(Quotation.id == quotation_id)
    )
    quotation = result.scalar_one_or_none()
    
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    # Get customer info
    customer_result = await db.execute(
        select(Customer).where(Customer.id == quotation.customer_id)
    )
    customer = customer_result.scalar_one_or_none()
    
    # Prepare data for PDF
    pdf_data = {
        'quote_number': quotation.quote_number,
        'created_at': quotation.created_at.isoformat(),
        'valid_until': (quotation.created_at + timedelta(days=quotation.validity_days)).isoformat(),
        'customer_name': customer.name if customer else "Unknown",
        'company_name': quotation.company_name,
        'company_address': quotation.company_address,
        'company_tax_id': quotation.company_tax_id,
        'items': quotation.items,
        'subtotal': float(quotation.subtotal),
        'discount_percent': float(quotation.discount_percent),
        'discount_amount': float(quotation.discount_amount),
        'tax_percent': float(quotation.tax_percent),
        'tax_amount': float(quotation.tax_amount),
        'total_amount': float(quotation.total_amount),
        'payment_terms': quotation.payment_terms,
        'notes': quotation.notes
    }
    
    # Generate PDF
    pdf_bytes = pdf_service.generate_quotation_pdf(pdf_data)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=quotation_{quotation.quote_number}.pdf"
        }
    )


@router.post("/{quotation_id}/send")
async def send_quotation(
    quotation_id: str,
    send_request: SendQuotationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send quotation to customer via specified channel"""
    
    # Get quotation
    result = await db.execute(
        select(Quotation).where(Quotation.id == quotation_id)
    )
    quotation = result.scalar_one_or_none()
    
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    # Get customer
    customer_result = await db.execute(
        select(Customer).where(Customer.id == quotation.customer_id)
    )
    customer = customer_result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Generate PDF
    pdf_data = {
        'quote_number': quotation.quote_number,
        'created_at': quotation.created_at.isoformat(),
        'valid_until': (quotation.created_at + timedelta(days=quotation.validity_days)).isoformat(),
        'customer_name': customer.name,
        'company_name': quotation.company_name,
        'company_address': quotation.company_address,
        'company_tax_id': quotation.company_tax_id,
        'items': quotation.items,
        'subtotal': float(quotation.subtotal),
        'discount_percent': float(quotation.discount_percent),
        'discount_amount': float(quotation.discount_amount),
        'tax_percent': float(quotation.tax_percent),
        'tax_amount': float(quotation.tax_amount),
        'total_amount': float(quotation.total_amount),
        'payment_terms': quotation.payment_terms,
        'notes': quotation.notes
    }
    
    pdf_bytes = pdf_service.generate_quotation_pdf(pdf_data)
    
    # Send based on channel
    if send_request.channel == "whatsapp":
        if not customer.whatsapp_id and not customer.phone:
            raise HTTPException(status_code=400, detail="Customer has no WhatsApp ID or phone number")
        
        # Upload PDF to WhatsApp
        media_id = await whatsapp_service.upload_media(pdf_bytes)
        
        # Prepare message
        default_message = f"Hello {customer.name},\n\nPlease find attached your quotation {quotation.quote_number} for {quotation.title}.\n\nTotal Amount: ฿{quotation.total_amount:,.2f}\n\nThis quotation is valid for {quotation.validity_days} days."
        message = send_request.message or default_message
        
        # Send document - format phone number if needed
        phone_number = customer.whatsapp_id or customer.phone
        formatted_phone = whatsapp_service.format_phone_number(phone_number)
        
        await whatsapp_service.send_document_message(
            to_phone=formatted_phone,
            document_id=media_id,
            filename=f"Quotation_{quotation.quote_number}.pdf",
            caption=message
        )
        
        # Create conversation and message record
        conv_result = await db.execute(
            select(Conversation).where(
                Conversation.customer_id == customer.id,
                Conversation.channel == ConversationChannel.WHATSAPP
            )
        )
        conversation = conv_result.scalar_one_or_none()
        
        if not conversation:
            conversation = Conversation(
                customer_id=customer.id,
                channel=ConversationChannel.WHATSAPP
            )
            db.add(conversation)
            await db.flush()
        
        # Record message
        message_record = Message(
            conversation_id=conversation.id,
            type=MessageType.DOCUMENT,
            content=f"Quotation {quotation.quote_number}",
            direction=MessageDirection.OUTBOUND,
            status=MessageStatus.SENT,
            extra_data={"quotation_id": str(quotation.id)}
        )
        db.add(message_record)
        
    elif send_request.channel == "line":
        # TODO: Implement LINE sending when LINE integration is ready
        raise HTTPException(status_code=501, detail="LINE integration not yet implemented")
        
    elif send_request.channel == "email":
        # TODO: Implement email sending when email integration is ready
        raise HTTPException(status_code=501, detail="Email integration not yet implemented")
        
    else:
        raise HTTPException(status_code=400, detail="Invalid channel")
    
    # Update quotation status
    quotation.status = QuotationStatus.SENT
    quotation.sent_at = datetime.utcnow()
    
    await db.commit()
    
    return {"status": "sent", "channel": send_request.channel}


@router.put("/{quotation_id}", response_model=QuotationResponse)
async def update_quotation(
    quotation_id: str,
    quotation_update: QuotationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a quotation (only if in draft status)"""
    
    result = await db.execute(
        select(Quotation).where(Quotation.id == quotation_id)
    )
    quotation = result.scalar_one_or_none()
    
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    if quotation.status != QuotationStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail="Can only update quotations in draft status"
        )
    
    # Update fields
    if quotation_update.company_name is not None:
        quotation.company_name = quotation_update.company_name
    if quotation_update.company_address is not None:
        quotation.company_address = quotation_update.company_address
    if quotation_update.company_tax_id is not None:
        quotation.company_tax_id = quotation_update.company_tax_id
    if quotation_update.title is not None:
        quotation.title = quotation_update.title
    if quotation_update.description is not None:
        quotation.description = quotation_update.description
    if quotation_update.payment_terms is not None:
        quotation.payment_terms = quotation_update.payment_terms
    if quotation_update.validity_days is not None:
        quotation.validity_days = quotation_update.validity_days
    if quotation_update.notes is not None:
        quotation.notes = quotation_update.notes
    
    # Recalculate if items or percentages changed
    if quotation_update.items is not None or quotation_update.discount_percent is not None or quotation_update.tax_percent is not None:
        items = quotation_update.items if quotation_update.items is not None else quotation.items
        discount_percent = quotation_update.discount_percent if quotation_update.discount_percent is not None else float(quotation.discount_percent)
        tax_percent = quotation_update.tax_percent if quotation_update.tax_percent is not None else float(quotation.tax_percent)
        
        subtotal = sum(item['total'] for item in items)
        discount_amount = subtotal * (discount_percent / 100)
        amount_after_discount = subtotal - discount_amount
        tax_amount = amount_after_discount * (tax_percent / 100)
        total_amount = amount_after_discount + tax_amount
        
        quotation.items = [item.dict() if hasattr(item, 'dict') else item for item in items]
        quotation.subtotal = Decimal(str(subtotal))
        quotation.discount_percent = Decimal(str(discount_percent))
        quotation.discount_amount = Decimal(str(discount_amount))
        quotation.tax_percent = Decimal(str(tax_percent))
        quotation.tax_amount = Decimal(str(tax_amount))
        quotation.total_amount = Decimal(str(total_amount))
    
    quotation.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(quotation)
    
    # Get customer and creator info
    customer_result = await db.execute(
        select(Customer).where(Customer.id == quotation.customer_id)
    )
    customer = customer_result.scalar_one_or_none()
    
    creator_result = await db.execute(
        select(User).where(User.id == quotation.created_by_id)
    )
    creator = creator_result.scalar_one_or_none()
    
    return QuotationResponse(
        id=str(quotation.id),
        quote_number=quotation.quote_number,
        customer_id=str(quotation.customer_id),
        customer_name=customer.name if customer else "Unknown",
        customer_phone=customer.phone if customer else "",
        customer_email=customer.email if customer else None,
        company_name=quotation.company_name,
        company_address=quotation.company_address,
        company_tax_id=quotation.company_tax_id,
        title=quotation.title,
        description=quotation.description,
        items=quotation.items or [],
        subtotal=float(quotation.subtotal),
        discount_percent=float(quotation.discount_percent),
        discount_amount=float(quotation.discount_amount),
        tax_percent=float(quotation.tax_percent),
        tax_amount=float(quotation.tax_amount),
        total_amount=float(quotation.total_amount),
        payment_terms=quotation.payment_terms,
        validity_days=quotation.validity_days,
        notes=quotation.notes,
        status=quotation.status,
        sent_at=quotation.sent_at,
        viewed_at=quotation.viewed_at,
        responded_at=quotation.responded_at,
        pdf_url=quotation.pdf_url,
        created_at=quotation.created_at,
        created_by_name=creator.full_name or creator.username if creator else "Unknown"
    )


@router.delete("/{quotation_id}")
async def delete_quotation(
    quotation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a quotation (only if in draft status)"""
    
    result = await db.execute(
        select(Quotation).where(Quotation.id == quotation_id)
    )
    quotation = result.scalar_one_or_none()
    
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    if quotation.status != QuotationStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail="Can only delete quotations in draft status"
        )
    
    await db.delete(quotation)
    await db.commit()
    
    return {"status": "deleted"}