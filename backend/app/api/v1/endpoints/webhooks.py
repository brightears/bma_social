from fastapi import APIRouter, Request, Response, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import json
from typing import Optional
from datetime import datetime

from app.core.config import settings
from app.services.whatsapp_service import whatsapp_service
from app.models import (
    Customer, Conversation, Message,
    ConversationChannel, ConversationStatus,
    MessageType, MessageDirection, MessageStatus
)
from app.api.v1.dependencies import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/whatsapp")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    """
    WhatsApp webhook verification endpoint
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified successfully")
        return Response(content=hub_challenge)
    
    logger.warning(f"Invalid webhook verification attempt: {hub_verify_token}")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle incoming WhatsApp webhooks (messages and status updates)
    """
    try:
        # Get raw body for logging
        body = await request.json()
        logger.info(f"Received WhatsApp webhook: {json.dumps(body)}")
        
        # Parse message
        message_data = whatsapp_service.parse_webhook_message(body)
        if message_data:
            await handle_incoming_message(db, message_data)
            return {"status": "ok"}
        
        # Parse status update
        status_data = whatsapp_service.parse_webhook_status(body)
        if status_data:
            await handle_status_update(db, status_data)
            return {"status": "ok"}
        
        logger.info("Webhook received but no message or status to process")
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {e}", exc_info=True)
        # Return 200 to prevent WhatsApp from retrying
        return {"status": "error", "message": str(e)}


async def handle_incoming_message(db: AsyncSession, message_data: dict):
    """Process incoming WhatsApp message"""
    
    # 1. Find or create customer
    phone = message_data["from_phone"]
    customer_result = await db.execute(
        select(Customer).where(Customer.whatsapp_id == phone)
    )
    customer = customer_result.scalar_one_or_none()
    
    if not customer:
        # Create new customer
        customer = Customer(
            name=message_data["from_name"],
            phone=phone,
            whatsapp_id=phone,
            preferred_channel="whatsapp",
            is_active=True
        )
        db.add(customer)
        await db.flush()
        logger.info(f"Created new customer: {customer.name} ({phone})")
    
    # 2. Find or create conversation
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.customer_id == customer.id,
            Conversation.channel == ConversationChannel.WHATSAPP,
            Conversation.status != ConversationStatus.CLOSED
        ).order_by(Conversation.created_at.desc())
    )
    conversation = conv_result.scalar_one_or_none()
    
    if not conversation:
        # Create new conversation
        conversation = Conversation(
            customer_id=customer.id,
            channel=ConversationChannel.WHATSAPP,
            status=ConversationStatus.OPEN,
            last_message_at=datetime.utcnow()
        )
        db.add(conversation)
        await db.flush()
        logger.info(f"Created new conversation for customer {customer.name}")
    
    # 3. Create message record
    message_type = MessageType.TEXT
    if message_data["type"] == "image":
        message_type = MessageType.IMAGE
    elif message_data["type"] == "video":
        message_type = MessageType.VIDEO
    elif message_data["type"] == "audio":
        message_type = MessageType.AUDIO
    elif message_data["type"] == "document":
        message_type = MessageType.DOCUMENT
    elif message_data["type"] == "location":
        message_type = MessageType.LOCATION
    
    message = Message(
        conversation_id=conversation.id,
        type=message_type,
        content=message_data["content"],
        media_url=message_data.get("media_url"),
        direction=MessageDirection.INBOUND,
        status=MessageStatus.DELIVERED,
        external_id=message_data["message_id"],
        extra_data={
            "whatsapp_timestamp": message_data["timestamp"],
            "context": message_data.get("context")
        }
    )
    db.add(message)
    
    # Update conversation
    conversation.last_message_at = datetime.utcnow()
    conversation.unread_count += 1
    
    await db.commit()
    logger.info(f"Saved incoming message {message.id} from {customer.name}")
    
    # TODO: Send real-time notification to connected agents


async def handle_status_update(db: AsyncSession, status_data: dict):
    """Process message status updates"""
    
    # Find message by external ID
    result = await db.execute(
        select(Message).where(Message.external_id == status_data["message_id"])
    )
    message = result.scalar_one_or_none()
    
    if not message:
        logger.warning(f"Received status for unknown message: {status_data['message_id']}")
        return
    
    # Update status
    status_map = {
        "sent": MessageStatus.SENT,
        "delivered": MessageStatus.DELIVERED,
        "read": MessageStatus.READ,
        "failed": MessageStatus.FAILED
    }
    
    new_status = status_map.get(status_data["status"])
    if new_status:
        message.status = new_status
        if new_status == MessageStatus.FAILED and status_data.get("errors"):
            message.error_message = json.dumps(status_data["errors"])
        
        await db.commit()
        logger.info(f"Updated message {message.id} status to {new_status}")
    
    # TODO: Send real-time status update to connected agents


@router.post("/line")
async def line_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle incoming LINE webhooks
    """
    # TODO: Implement LINE webhook handling
    body = await request.json()
    logger.info(f"Received LINE webhook: {json.dumps(body)}")
    return {"status": "ok"}


@router.post("/generic")
async def generic_webhook(
    provider: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Generic webhook endpoint for other providers
    """
    body = await request.json()
    logger.info(f"Received {provider} webhook: {json.dumps(body)}")
    return {"status": "ok", "provider": provider}