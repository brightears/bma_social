"""
WhatsApp Business API Service
Handles sending and receiving messages via Meta's Cloud API
"""
import httpx
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from app.core.config import settings
from app.models import Customer, Conversation, Message, MessageType, MessageDirection, MessageStatus

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service for interacting with WhatsApp Business API"""
    
    def __init__(self):
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.api_version = "v18.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        
    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def send_text_message(self, to_phone: str, text: str, preview_url: bool = False) -> Dict[str, Any]:
        """
        Send a text message to a WhatsApp user
        
        Args:
            to_phone: Recipient's phone number (with country code)
            text: Message text
            preview_url: Whether to show URL previews
            
        Returns:
            Response from WhatsApp API
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "text",
            "text": {
                "preview_url": preview_url,
                "body": text
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def send_template_message(
        self, 
        to_phone: str, 
        template_name: str, 
        language_code: str = "en",
        components: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Send a template message
        
        Args:
            to_phone: Recipient's phone number
            template_name: Name of approved template
            language_code: Language code (default: en)
            components: Template components with parameters
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code}
            }
        }
        
        if components:
            payload["template"]["components"] = components
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def send_media_message(
        self, 
        to_phone: str, 
        media_type: str, 
        media_url: str, 
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send media message (image, video, document, audio)
        
        Args:
            to_phone: Recipient's phone number
            media_type: Type of media (image, video, document, audio)
            media_url: URL of the media file
            caption: Optional caption for the media
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        media_object = {"link": media_url}
        if caption and media_type in ["image", "video", "document"]:
            media_object["caption"] = caption
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": media_type,
            media_type: media_object
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def send_reaction(self, to_phone: str, message_id: str, emoji: str) -> Dict[str, Any]:
        """Send a reaction to a message"""
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "reaction",
            "reaction": {
                "message_id": message_id,
                "emoji": emoji
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def mark_as_read(self, message_id: str) -> Dict[str, Any]:
        """Mark a message as read"""
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
    
    def parse_webhook_message(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse incoming webhook data from WhatsApp
        
        Returns parsed message data or None if not a message event
        """
        try:
            # Extract the message from webhook structure
            entry = webhook_data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            
            # Check if this is a message event
            if "messages" not in value:
                return None
            
            message = value["messages"][0]
            contact = value["contacts"][0]
            
            # Parse message type and content
            message_type = message.get("type", "text")
            content = ""
            media_url = None
            
            if message_type == "text":
                content = message["text"]["body"]
            elif message_type in ["image", "video", "audio", "document"]:
                media_data = message[message_type]
                media_url = media_data.get("link")
                content = media_data.get("caption", f"[{message_type}]")
            elif message_type == "location":
                loc = message["location"]
                content = f"Location: {loc.get('latitude')}, {loc.get('longitude')}"
            
            return {
                "message_id": message["id"],
                "from_phone": message["from"],
                "from_name": contact["profile"]["name"],
                "timestamp": int(message["timestamp"]),
                "type": message_type,
                "content": content,
                "media_url": media_url,
                "context": message.get("context"),  # For replies
            }
            
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing webhook message: {e}")
            return None
    
    def parse_webhook_status(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse message status updates from webhook
        
        Returns status update data or None
        """
        try:
            entry = webhook_data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            
            # Check if this is a status update
            if "statuses" not in value:
                return None
            
            status = value["statuses"][0]
            
            return {
                "message_id": status["id"],
                "recipient_phone": status["recipient_id"],
                "status": status["status"],  # sent, delivered, read, failed
                "timestamp": int(status["timestamp"]),
                "errors": status.get("errors", [])
            }
            
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing webhook status: {e}")
            return None
    
    async def get_media_url(self, media_id: str) -> Optional[str]:
        """Get the download URL for a media file"""
        url = f"{self.base_url}/{media_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data.get("url")
    
    async def download_media(self, media_url: str) -> bytes:
        """Download media file from WhatsApp"""
        async with httpx.AsyncClient() as client:
            response = await client.get(media_url, headers=self.headers)
            response.raise_for_status()
            return response.content
    
    async def upload_media(self, file_data: bytes, file_type: str = "application/pdf") -> str:
        """Upload media to WhatsApp and get media ID"""
        url = f"{self.base_url}/media"
        
        files = {
            'file': ('document.pdf', file_data, file_type),
            'messaging_product': (None, 'whatsapp'),
            'type': (None, 'application/pdf')
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                files=files,
                headers={'Authorization': f'Bearer {self.access_token}'}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("id")
    
    async def send_document_message(self, to_phone: str, document_url: str = None, document_id: str = None, 
                                   filename: str = "document.pdf", caption: str = None) -> dict:
        """Send a document message via WhatsApp"""
        url = f"{self.base_url}/messages"
        
        message_data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "document",
            "document": {
                "filename": filename
            }
        }
        
        if document_id:
            message_data["document"]["id"] = document_id
        elif document_url:
            message_data["document"]["link"] = document_url
        else:
            raise ValueError("Either document_url or document_id must be provided")
        
        if caption:
            message_data["document"]["caption"] = caption
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=message_data, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    @staticmethod
    def format_phone_number(phone: str) -> str:
        """
        Format phone number for WhatsApp API
        Remove any non-digit characters and ensure it starts with country code
        """
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, phone))
        
        # Add Thailand country code if not present
        if not digits.startswith('66') and len(digits) == 9:
            digits = '66' + digits
        elif digits.startswith('0') and len(digits) == 10:
            digits = '66' + digits[1:]
        
        return digits


# Singleton instance
whatsapp_service = WhatsAppService()