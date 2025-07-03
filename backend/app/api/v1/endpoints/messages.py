from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime
import logging

from app.models import (
    Message, Conversation, Customer, User,
    MessageType, MessageDirection, MessageStatus,
    ConversationChannel
)
from app.services.whatsapp_service import whatsapp_service
from app.api.v1.dependencies import get_db, get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


class SendMessageRequest(BaseModel):
    conversation_id: UUID
    content: str
    type: MessageType = MessageType.TEXT
    media_url: Optional[str] = None
    template_name: Optional[str] = None
    template_params: Optional[dict] = None


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    type: MessageType
    content: str
    media_url: Optional[str]
    direction: MessageDirection
    status: MessageStatus
    created_at: datetime
    sender_name: Optional[str]
    
    class Config:
        from_attributes = True


@router.post("/send", response_model=MessageResponse)
async def send_message(
    message_data: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a message in a conversation"""
    
    # Get conversation with customer
    result = await db.execute(
        select(Conversation).where(Conversation.id == message_data.conversation_id)
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
    
    # Create message record
    message = Message(
        conversation_id=conversation.id,
        sender_user_id=current_user.id,
        type=message_data.type,
        content=message_data.content,
        media_url=message_data.media_url,
        direction=MessageDirection.OUTBOUND,
        status=MessageStatus.PENDING,
        template_name=message_data.template_name
    )
    db.add(message)
    await db.flush()
    
    # Send via appropriate channel
    try:
        if conversation.channel == ConversationChannel.WHATSAPP:
            await send_whatsapp_message(customer, message, message_data)
        elif conversation.channel == ConversationChannel.LINE:
            # TODO: Implement LINE sending
            raise HTTPException(status_code=501, detail="LINE messaging not implemented yet")
        elif conversation.channel == ConversationChannel.EMAIL:
            # TODO: Implement email sending
            raise HTTPException(status_code=501, detail="Email messaging not implemented yet")
        
        # Update message status
        message.status = MessageStatus.SENT
        
        # Update conversation
        conversation.last_message_at = datetime.utcnow()
        if conversation.assigned_to_id is None:
            conversation.assigned_to_id = current_user.id
        
        await db.commit()
        
        # Prepare response
        response = MessageResponse.model_validate(message)
        response.sender_name = current_user.full_name or current_user.username
        
        return response
        
    except Exception as e:
        message.status = MessageStatus.FAILED
        message.error_message = str(e)
        await db.commit()
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


async def send_whatsapp_message(customer: Customer, message: Message, request_data: SendMessageRequest):
    """Send message via WhatsApp"""
    
    if not customer.whatsapp_id:
        raise HTTPException(status_code=400, detail="Customer has no WhatsApp ID")
    
    # Format phone number
    to_phone = whatsapp_service.format_phone_number(customer.whatsapp_id)
    
    # Send based on message type
    if request_data.template_name:
        # Send template message
        response = await whatsapp_service.send_template_message(
            to_phone=to_phone,
            template_name=request_data.template_name,
            components=request_data.template_params.get("components") if request_data.template_params else None
        )
    elif message.type == MessageType.TEXT:
        # Send text message
        response = await whatsapp_service.send_text_message(
            to_phone=to_phone,
            text=message.content
        )
    elif message.type in [MessageType.IMAGE, MessageType.VIDEO, MessageType.DOCUMENT, MessageType.AUDIO]:
        # Send media message
        if not message.media_url:
            raise ValueError("Media URL is required for media messages")
        
        media_type_map = {
            MessageType.IMAGE: "image",
            MessageType.VIDEO: "video",
            MessageType.DOCUMENT: "document",
            MessageType.AUDIO: "audio"
        }
        
        response = await whatsapp_service.send_media_message(
            to_phone=to_phone,
            media_type=media_type_map[message.type],
            media_url=message.media_url,
            caption=message.content if message.type != MessageType.AUDIO else None
        )
    else:
        raise ValueError(f"Unsupported message type: {message.type}")
    
    # Store WhatsApp message ID
    if response and "messages" in response:
        message.external_id = response["messages"][0]["id"]


@router.get("/conversation/{conversation_id}", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: UUID,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get messages in a conversation"""
    
    # Verify conversation exists
    conv_result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    if not conv_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get messages with sender info
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    messages = result.scalars().all()
    
    # Get sender names
    user_ids = [m.sender_user_id for m in messages if m.sender_user_id]
    users = {}
    if user_ids:
        user_result = await db.execute(
            select(User).where(User.id.in_(user_ids))
        )
        users = {u.id: u for u in user_result.scalars().all()}
    
    # Build response
    response = []
    for message in messages:
        msg_response = MessageResponse.model_validate(message)
        if message.sender_user_id and message.sender_user_id in users:
            user = users[message.sender_user_id]
            msg_response.sender_name = user.full_name or user.username
        response.append(msg_response)
    
    # Mark messages as read
    unread_messages = [m for m in messages if m.direction == MessageDirection.INBOUND and m.status != MessageStatus.READ]
    if unread_messages:
        for msg in unread_messages:
            msg.status = MessageStatus.READ
        
        # Update conversation unread count
        conv_result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = conv_result.scalar_one()
        conversation.unread_count = 0
        
        await db.commit()
    
    return response


@router.post("/{message_id}/read")
async def mark_message_read(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark a message as read"""
    
    result = await db.execute(
        select(Message).where(Message.id == message_id)
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if message.direction == MessageDirection.INBOUND and message.status != MessageStatus.READ:
        message.status = MessageStatus.READ
        
        # Send read receipt to WhatsApp if applicable
        if message.external_id:
            try:
                await whatsapp_service.mark_as_read(message.external_id)
            except Exception as e:
                logger.error(f"Failed to send read receipt: {e}")
        
        await db.commit()
    
    return {"status": "ok"}


@router.delete("/{message_id}")
async def delete_message(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a message (soft delete)"""
    
    result = await db.execute(
        select(Message).where(Message.id == message_id)
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Only allow deleting own messages or if admin
    if message.sender_user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to delete this message")
    
    # Soft delete by marking as deleted in extra_data
    if not message.extra_data:
        message.extra_data = {}
    message.extra_data["deleted"] = True
    message.extra_data["deleted_by"] = str(current_user.id)
    message.extra_data["deleted_at"] = datetime.utcnow().isoformat()
    
    await db.commit()
    
    return {"status": "deleted"}