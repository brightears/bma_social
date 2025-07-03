from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, validator
from datetime import datetime
import logging

from app.models import Campaign, Customer, User, Message, Conversation
from app.models.campaign import CampaignStatus, CampaignChannel
from app.models.message import MessageDirection, MessageStatus, MessageType
from app.models.conversation import ConversationChannel
from app.api.v1.dependencies import get_db, get_current_user
from app.services.whatsapp_service import whatsapp_service
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)


class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    channel: CampaignChannel = CampaignChannel.WHATSAPP
    message_content: str
    template_id: Optional[str] = None
    segment_filters: Dict[str, Any] = {}
    scheduled_at: Optional[datetime] = None
    
    @validator('name')
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Campaign name cannot be empty')
        return v.strip()


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    message_content: Optional[str] = None
    segment_filters: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None


class CampaignResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    channel: CampaignChannel
    template_id: Optional[str]
    message_content: Optional[str]
    status: CampaignStatus
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    segment_filters: Dict[str, Any]
    recipient_count: int
    sent_count: int
    delivered_count: int
    read_count: int
    clicked_count: int
    failed_count: int
    created_at: datetime
    created_by_id: str
    created_by_name: str
    
    class Config:
        from_attributes = True


class CampaignRecipient(BaseModel):
    id: str
    name: str
    phone: str
    whatsapp_id: Optional[str]
    tags: List[str]


@router.get("/", response_model=List[CampaignResponse])
async def get_campaigns(
    skip: int = 0,
    limit: int = 100,
    status: Optional[CampaignStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all campaigns with optional filtering"""
    
    query = select(Campaign)
    
    if status:
        query = query.where(Campaign.status == status)
    
    query = query.order_by(Campaign.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    campaigns = result.scalars().all()
    
    # Get creator names
    user_ids = list(set(c.created_by_id for c in campaigns))
    if user_ids:
        user_result = await db.execute(
            select(User).where(User.id.in_(user_ids))
        )
        users = {u.id: u for u in user_result.scalars().all()}
    else:
        users = {}
    
    # Build response
    response = []
    for campaign in campaigns:
        campaign_data = CampaignResponse(
            id=str(campaign.id),
            name=campaign.name,
            description=campaign.description,
            channel=campaign.channel,
            template_id=str(campaign.template_id) if campaign.template_id else None,
            message_content=campaign.message_content,
            status=campaign.status,
            scheduled_at=campaign.scheduled_at,
            started_at=campaign.started_at,
            completed_at=campaign.completed_at,
            segment_filters=campaign.segment_filters or {},
            recipient_count=campaign.recipient_count,
            sent_count=campaign.sent_count,
            delivered_count=campaign.delivered_count,
            read_count=campaign.read_count,
            clicked_count=campaign.clicked_count,
            failed_count=campaign.failed_count,
            created_at=campaign.created_at,
            created_by_id=str(campaign.created_by_id),
            created_by_name=users.get(campaign.created_by_id, {}).full_name or users.get(campaign.created_by_id, {}).username or "Unknown"
        )
        response.append(campaign_data)
    
    return response


@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new campaign"""
    
    try:
        # Create campaign
        db_campaign = Campaign(
            name=campaign.name,
            description=campaign.description,
            channel=campaign.channel,
            template_id=campaign.template_id,
            message_content=campaign.message_content,
            status=CampaignStatus.SCHEDULED if campaign.scheduled_at else CampaignStatus.DRAFT,
            scheduled_at=campaign.scheduled_at,
            segment_filters=campaign.segment_filters,
            created_by_id=current_user.id
        )
        
        # Calculate recipient count
        recipient_count = await calculate_recipients(db, campaign.segment_filters)
        db_campaign.recipient_count = recipient_count
        
        db.add(db_campaign)
        await db.commit()
        await db.refresh(db_campaign)
        
        return CampaignResponse(
            id=str(db_campaign.id),
            name=db_campaign.name,
            description=db_campaign.description,
            channel=db_campaign.channel,
            template_id=str(db_campaign.template_id) if db_campaign.template_id else None,
            message_content=db_campaign.message_content,
            status=db_campaign.status,
            scheduled_at=db_campaign.scheduled_at,
            started_at=db_campaign.started_at,
            completed_at=db_campaign.completed_at,
            segment_filters=db_campaign.segment_filters or {},
            recipient_count=db_campaign.recipient_count,
            sent_count=db_campaign.sent_count,
            delivered_count=db_campaign.delivered_count,
            read_count=db_campaign.read_count,
            clicked_count=db_campaign.clicked_count,
            failed_count=db_campaign.failed_count,
            created_at=db_campaign.created_at,
            created_by_id=str(db_campaign.created_by_id),
            created_by_name=current_user.full_name or current_user.username
        )
        
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create campaign: {str(e)}"
        )


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific campaign"""
    
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Get creator info
    user_result = await db.execute(
        select(User).where(User.id == campaign.created_by_id)
    )
    creator = user_result.scalar_one_or_none()
    
    return CampaignResponse(
        id=str(campaign.id),
        name=campaign.name,
        description=campaign.description,
        channel=campaign.channel,
        template_id=str(campaign.template_id) if campaign.template_id else None,
        message_content=campaign.message_content,
        status=campaign.status,
        scheduled_at=campaign.scheduled_at,
        started_at=campaign.started_at,
        completed_at=campaign.completed_at,
        segment_filters=campaign.segment_filters or {},
        recipient_count=campaign.recipient_count,
        sent_count=campaign.sent_count,
        delivered_count=campaign.delivered_count,
        read_count=campaign.read_count,
        clicked_count=campaign.clicked_count,
        failed_count=campaign.failed_count,
        created_at=campaign.created_at,
        created_by_id=str(campaign.created_by_id),
        created_by_name=creator.full_name or creator.username if creator else "Unknown"
    )


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    campaign_update: CampaignUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a campaign (only if in draft status)"""
    
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.SCHEDULED]:
        raise HTTPException(
            status_code=400,
            detail="Can only update campaigns in draft or scheduled status"
        )
    
    # Update fields
    if campaign_update.name is not None:
        campaign.name = campaign_update.name
    if campaign_update.description is not None:
        campaign.description = campaign_update.description
    if campaign_update.message_content is not None:
        campaign.message_content = campaign_update.message_content
    if campaign_update.segment_filters is not None:
        campaign.segment_filters = campaign_update.segment_filters
        # Recalculate recipients
        campaign.recipient_count = await calculate_recipients(db, campaign_update.segment_filters)
    if campaign_update.scheduled_at is not None:
        campaign.scheduled_at = campaign_update.scheduled_at
        campaign.status = CampaignStatus.SCHEDULED if campaign_update.scheduled_at else CampaignStatus.DRAFT
    
    campaign.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(campaign)
    
    # Get creator info
    user_result = await db.execute(
        select(User).where(User.id == campaign.created_by_id)
    )
    creator = user_result.scalar_one_or_none()
    
    return CampaignResponse(
        id=str(campaign.id),
        name=campaign.name,
        description=campaign.description,
        channel=campaign.channel,
        template_id=str(campaign.template_id) if campaign.template_id else None,
        message_content=campaign.message_content,
        status=campaign.status,
        scheduled_at=campaign.scheduled_at,
        started_at=campaign.started_at,
        completed_at=campaign.completed_at,
        segment_filters=campaign.segment_filters or {},
        recipient_count=campaign.recipient_count,
        sent_count=campaign.sent_count,
        delivered_count=campaign.delivered_count,
        read_count=campaign.read_count,
        clicked_count=campaign.clicked_count,
        failed_count=campaign.failed_count,
        created_at=campaign.created_at,
        created_by_id=str(campaign.created_by_id),
        created_by_name=creator.full_name or creator.username if creator else "Unknown"
    )


@router.get("/{campaign_id}/recipients", response_model=List[CampaignRecipient])
async def get_campaign_recipients(
    campaign_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get recipients for a campaign based on its filters"""
    
    # Get campaign
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Get filtered customers
    customers = await get_filtered_customers(db, campaign.segment_filters, skip, limit)
    
    # Convert to response
    recipients = []
    for customer in customers:
        recipients.append(CampaignRecipient(
            id=str(customer.id),
            name=customer.name,
            phone=customer.phone,
            whatsapp_id=customer.whatsapp_id,
            tags=customer.tags or []
        ))
    
    return recipients


@router.post("/{campaign_id}/send", status_code=status.HTTP_202_ACCEPTED)
async def send_campaign(
    campaign_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a campaign immediately"""
    
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.SCHEDULED]:
        raise HTTPException(
            status_code=400,
            detail="Campaign must be in draft or scheduled status to send"
        )
    
    # Update campaign status
    campaign.status = CampaignStatus.RUNNING
    campaign.started_at = datetime.utcnow()
    await db.commit()
    
    # Run campaign in background
    background_tasks.add_task(execute_campaign, campaign_id)
    
    return {"status": "Campaign started", "campaign_id": campaign_id}


@router.post("/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Pause a running campaign"""
    
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status != CampaignStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail="Can only pause running campaigns"
        )
    
    campaign.status = CampaignStatus.PAUSED
    await db.commit()
    
    return {"status": "Campaign paused"}


@router.post("/{campaign_id}/resume")
async def resume_campaign(
    campaign_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Resume a paused campaign"""
    
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status != CampaignStatus.PAUSED:
        raise HTTPException(
            status_code=400,
            detail="Can only resume paused campaigns"
        )
    
    campaign.status = CampaignStatus.RUNNING
    await db.commit()
    
    # Resume campaign in background
    background_tasks.add_task(execute_campaign, campaign_id)
    
    return {"status": "Campaign resumed"}


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a campaign (only if in draft status)"""
    
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status != CampaignStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail="Can only delete campaigns in draft status"
        )
    
    await db.delete(campaign)
    await db.commit()
    
    return {"status": "Campaign deleted"}


# Helper functions
async def calculate_recipients(db: AsyncSession, filters: Dict[str, Any]) -> int:
    """Calculate number of recipients based on filters"""
    
    query = select(func.count(Customer.id)).where(Customer.is_active == True)
    
    # Apply tag filters
    if filters.get("tags"):
        for tag in filters["tags"]:
            query = query.where(Customer.tags.contains([tag]))
    
    # Apply other filters as needed
    if filters.get("has_whatsapp"):
        query = query.where(Customer.whatsapp_id.isnot(None))
    
    result = await db.execute(query)
    return result.scalar() or 0


async def get_filtered_customers(
    db: AsyncSession,
    filters: Dict[str, Any],
    skip: int = 0,
    limit: int = None
) -> List[Customer]:
    """Get customers based on filters"""
    
    query = select(Customer).where(Customer.is_active == True)
    
    # Apply tag filters
    if filters.get("tags"):
        for tag in filters["tags"]:
            query = query.where(Customer.tags.contains([tag]))
    
    # Apply other filters
    if filters.get("has_whatsapp"):
        query = query.where(Customer.whatsapp_id.isnot(None))
    
    query = query.offset(skip)
    if limit:
        query = query.limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


async def execute_campaign(campaign_id: str):
    """Execute a campaign - send messages to recipients"""
    
    from app.api.v1.dependencies.database import get_async_session_context
    
    async with get_async_session_context() as db:
        try:
            # Get campaign
            result = await db.execute(
                select(Campaign).where(Campaign.id == campaign_id)
            )
            campaign = result.scalar_one_or_none()
            
            if not campaign or campaign.status != CampaignStatus.RUNNING:
                return
            
            # Get recipients
            customers = await get_filtered_customers(db, campaign.segment_filters or {})
            
            # Send messages
            for customer in customers:
                if campaign.status != CampaignStatus.RUNNING:
                    break  # Campaign was paused
                
                try:
                    # Create or get conversation
                    conv_result = await db.execute(
                        select(Conversation).where(
                            and_(
                                Conversation.customer_id == customer.id,
                                Conversation.channel == ConversationChannel.WHATSAPP
                            )
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
                    
                    # Create message record
                    message = Message(
                        conversation_id=conversation.id,
                        type=MessageType.TEXT,
                        content=campaign.message_content,
                        direction=MessageDirection.OUTBOUND,
                        status=MessageStatus.PENDING,
                        extra_data={"campaign_id": str(campaign.id)}
                    )
                    db.add(message)
                    await db.flush()
                    
                    # Send via WhatsApp
                    if customer.whatsapp_id:
                        response = await whatsapp_service.send_text_message(
                            to_phone=customer.whatsapp_id,
                            text=campaign.message_content
                        )
                        
                        if response and "messages" in response:
                            message.external_id = response["messages"][0]["id"]
                            message.status = MessageStatus.SENT
                            campaign.sent_count += 1
                        else:
                            message.status = MessageStatus.FAILED
                            campaign.failed_count += 1
                    else:
                        message.status = MessageStatus.FAILED
                        message.error_message = "No WhatsApp ID"
                        campaign.failed_count += 1
                    
                    await db.commit()
                    
                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error sending to customer {customer.id}: {e}")
                    campaign.failed_count += 1
                    await db.commit()
                    continue
            
            # Mark campaign as completed
            campaign.status = CampaignStatus.COMPLETED
            campaign.completed_at = datetime.utcnow()
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error executing campaign {campaign_id}: {e}")
            # Mark campaign as failed
            try:
                result = await db.execute(
                    select(Campaign).where(Campaign.id == campaign_id)
                )
                campaign = result.scalar_one_or_none()
                if campaign:
                    campaign.status = CampaignStatus.FAILED
                    await db.commit()
            except:
                pass