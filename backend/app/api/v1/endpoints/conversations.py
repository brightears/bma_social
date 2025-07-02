from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.models import (
    Conversation, Customer, User, Message,
    ConversationStatus, ConversationChannel
)
from app.api.v1.dependencies import get_db, get_current_user

router = APIRouter()


class ConversationResponse(BaseModel):
    id: str
    customer_id: str
    customer_name: str
    customer_phone: Optional[str]
    channel: ConversationChannel
    status: ConversationStatus
    unread_count: int
    last_message_at: datetime
    last_message_preview: Optional[str]
    assigned_to_id: Optional[str]
    assigned_to_name: Optional[str]
    created_at: datetime
    tags: List[str]
    
    class Config:
        from_attributes = True


class CreateConversationRequest(BaseModel):
    customer_id: str
    channel: ConversationChannel
    subject: Optional[str] = None
    initial_message: Optional[str] = None


class UpdateConversationRequest(BaseModel):
    status: Optional[ConversationStatus] = None
    assigned_to_id: Optional[str] = None
    tags: Optional[List[str]] = None
    subject: Optional[str] = None


@router.get("/", response_model=List[ConversationResponse])
async def get_conversations(
    channel: Optional[ConversationChannel] = None,
    status: Optional[ConversationStatus] = None,
    assigned_to_id: Optional[str] = Query(None, description="Filter by assigned user ID"),
    unassigned: bool = False,
    search: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all conversations with filters"""
    
    # Build query
    query = select(Conversation)
    
    # Apply filters
    filters = []
    
    if channel:
        filters.append(Conversation.channel == channel)
    
    if status:
        filters.append(Conversation.status == status)
    elif status is None:
        # By default, exclude archived conversations
        filters.append(Conversation.status != ConversationStatus.ARCHIVED)
    
    if assigned_to_id:
        filters.append(Conversation.assigned_to_id == assigned_to_id)
    
    if unassigned:
        filters.append(Conversation.assigned_to_id.is_(None))
    
    if filters:
        query = query.where(and_(*filters))
    
    # Order by last message
    query = query.order_by(Conversation.last_message_at.desc())
    query = query.limit(limit).offset(offset)
    
    # Execute query
    result = await db.execute(query)
    conversations = result.scalars().all()
    
    # Get related data
    customer_ids = [c.customer_id for c in conversations]
    user_ids = [c.assigned_to_id for c in conversations if c.assigned_to_id]
    
    # Get customers
    customers = {}
    if customer_ids:
        customer_result = await db.execute(
            select(Customer).where(Customer.id.in_(customer_ids))
        )
        customers = {c.id: c for c in customer_result.scalars().all()}
    
    # Get assigned users
    users = {}
    if user_ids:
        user_result = await db.execute(
            select(User).where(User.id.in_(user_ids))
        )
        users = {u.id: u for u in user_result.scalars().all()}
    
    # Get last messages
    last_messages = {}
    if conversations:
        # Subquery to get last message per conversation
        message_result = await db.execute(
            select(Message)
            .where(Message.conversation_id.in_([c.id for c in conversations]))
            .distinct(Message.conversation_id)
            .order_by(Message.conversation_id, Message.created_at.desc())
        )
        for msg in message_result.scalars().all():
            if msg.conversation_id not in last_messages:
                last_messages[msg.conversation_id] = msg
    
    # Build response
    response = []
    for conv in conversations:
        customer = customers.get(conv.customer_id)
        if not customer:
            continue
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            if not any([
                search_lower in customer.name.lower(),
                search_lower in (customer.phone or "").lower(),
                search_lower in (customer.email or "").lower()
            ]):
                continue
        
        conv_response = ConversationResponse(
            id=str(conv.id),
            customer_id=str(customer.id),
            customer_name=customer.name,
            customer_phone=customer.phone,
            channel=conv.channel,
            status=conv.status,
            unread_count=conv.unread_count,
            last_message_at=conv.last_message_at,
            last_message_preview=None,
            assigned_to_id=str(conv.assigned_to_id) if conv.assigned_to_id else None,
            assigned_to_name=None,
            created_at=conv.created_at,
            tags=conv.tags or []
        )
        
        # Add assigned user name
        if conv.assigned_to_id and conv.assigned_to_id in users:
            user = users[conv.assigned_to_id]
            conv_response.assigned_to_name = user.full_name or user.username
        
        # Add last message preview
        last_msg = last_messages.get(conv.id)
        if last_msg:
            conv_response.last_message_preview = last_msg.content[:100]
            if len(last_msg.content) > 100:
                conv_response.last_message_preview += "..."
        
        response.append(conv_response)
    
    return response


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a single conversation by ID"""
    
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get customer
    customer_result = await db.execute(
        select(Customer).where(Customer.id == conversation.customer_id)
    )
    customer = customer_result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get assigned user
    assigned_to_name = None
    if conversation.assigned_to_id:
        user_result = await db.execute(
            select(User).where(User.id == conversation.assigned_to_id)
        )
        user = user_result.scalar_one_or_none()
        if user:
            assigned_to_name = user.full_name or user.username
    
    # Get last message
    message_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(1)
    )
    last_message = message_result.scalar_one_or_none()
    
    return ConversationResponse(
        id=str(conversation.id),
        customer_id=str(customer.id),
        customer_name=customer.name,
        customer_phone=customer.phone,
        channel=conversation.channel,
        status=conversation.status,
        unread_count=conversation.unread_count,
        last_message_at=conversation.last_message_at,
        last_message_preview=last_message.content[:100] if last_message else None,
        assigned_to_id=str(conversation.assigned_to_id) if conversation.assigned_to_id else None,
        assigned_to_name=assigned_to_name,
        created_at=conversation.created_at,
        tags=conversation.tags or []
    )


@router.post("/", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    data: CreateConversationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new conversation"""
    
    # Verify customer exists
    customer_result = await db.execute(
        select(Customer).where(Customer.id == data.customer_id)
    )
    customer = customer_result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Check for existing open conversation
    existing_result = await db.execute(
        select(Conversation).where(
            and_(
                Conversation.customer_id == data.customer_id,
                Conversation.channel == data.channel,
                Conversation.status != ConversationStatus.CLOSED
            )
        )
    )
    existing = existing_result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="An open conversation already exists for this customer and channel"
        )
    
    # Create conversation
    conversation = Conversation(
        customer_id=customer.id,
        channel=data.channel,
        status=ConversationStatus.OPEN,
        subject=data.subject,
        assigned_to_id=current_user.id,
        last_message_at=datetime.utcnow()
    )
    db.add(conversation)
    await db.flush()
    
    # Create initial message if provided
    if data.initial_message:
        from app.models import MessageDirection, MessageStatus, MessageType
        
        message = Message(
            conversation_id=conversation.id,
            sender_user_id=current_user.id,
            type=MessageType.TEXT,
            content=data.initial_message,
            direction=MessageDirection.OUTBOUND,
            status=MessageStatus.PENDING
        )
        db.add(message)
    
    await db.commit()
    
    return ConversationResponse(
        id=str(conversation.id),
        customer_id=str(customer.id),
        customer_name=customer.name,
        customer_phone=customer.phone,
        channel=conversation.channel,
        status=conversation.status,
        unread_count=0,
        last_message_at=conversation.last_message_at,
        last_message_preview=data.initial_message[:100] if data.initial_message else None,
        assigned_to_id=str(current_user.id),
        assigned_to_name=current_user.full_name or current_user.username,
        created_at=conversation.created_at,
        tags=[]
    )


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    data: UpdateConversationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a conversation"""
    
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Update fields
    if data.status is not None:
        conversation.status = data.status
        if data.status == ConversationStatus.CLOSED:
            conversation.closed_at = datetime.utcnow()
    
    if data.assigned_to_id is not None:
        # Verify user exists
        user_result = await db.execute(
            select(User).where(User.id == data.assigned_to_id)
        )
        if not user_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Invalid user ID")
        conversation.assigned_to_id = data.assigned_to_id
    
    if data.tags is not None:
        conversation.tags = data.tags
    
    if data.subject is not None:
        conversation.subject = data.subject
    
    await db.commit()
    
    # Return updated conversation
    return await get_conversation(conversation_id, current_user, db)


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a conversation (requires admin)"""
    
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Delete conversation (cascades to messages)
    await db.delete(conversation)
    await db.commit()
    
    return {"status": "deleted"}