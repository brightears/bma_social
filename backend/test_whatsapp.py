#!/usr/bin/env python3
"""
Test WhatsApp integration
"""
import asyncio
import httpx
import json
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000/api/v1"
WEBHOOK_URL = "http://localhost:8000/api/v1/webhooks/whatsapp"

# Test data
TEST_PHONE = "66812345678"  # Thai phone number format
TEST_CUSTOMER_NAME = "Test Customer"
TEST_MESSAGE = "Hello, I need help with my music zone!"

# Login credentials (from init_db.py)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "changeme123"

async def test_whatsapp_integration():
    async with httpx.AsyncClient() as client:
        print("🧪 Testing WhatsApp Integration\n")
        
        # 1. Login as admin
        print("1️⃣ Logging in as admin...")
        login_response = await client.post(
            f"{API_URL}/auth/login",
            data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return
        
        tokens = login_response.json()
        access_token = tokens["access_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}
        print("✅ Logged in successfully")
        
        # 2. Simulate incoming WhatsApp message
        print("\n2️⃣ Simulating incoming WhatsApp message...")
        
        webhook_payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "123456789",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "15550555555",
                            "phone_number_id": "123456"
                        },
                        "contacts": [{
                            "profile": {
                                "name": TEST_CUSTOMER_NAME
                            },
                            "wa_id": TEST_PHONE
                        }],
                        "messages": [{
                            "from": TEST_PHONE,
                            "id": f"test_message_{datetime.now().timestamp()}",
                            "timestamp": str(int(datetime.now().timestamp())),
                            "text": {
                                "body": TEST_MESSAGE
                            },
                            "type": "text"
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        webhook_response = await client.post(
            WEBHOOK_URL,
            json=webhook_payload
        )
        
        if webhook_response.status_code == 200:
            print("✅ Webhook processed successfully")
        else:
            print(f"❌ Webhook failed: {webhook_response.text}")
            return
        
        # 3. Get conversations
        print("\n3️⃣ Fetching conversations...")
        conv_response = await client.get(
            f"{API_URL}/conversations/",
            headers=auth_headers
        )
        
        if conv_response.status_code == 200:
            conversations = conv_response.json()
            if conversations:
                print(f"✅ Found {len(conversations)} conversation(s)")
                
                # Get the first conversation
                conv = conversations[0]
                print(f"   Customer: {conv['customer_name']}")
                print(f"   Channel: {conv['channel']}")
                print(f"   Last message: {conv['last_message_preview']}")
                conversation_id = conv['id']
            else:
                print("❌ No conversations found")
                return
        else:
            print(f"❌ Failed to get conversations: {conv_response.text}")
            return
        
        # 4. Get messages in conversation
        print("\n4️⃣ Fetching messages...")
        msg_response = await client.get(
            f"{API_URL}/messages/conversation/{conversation_id}",
            headers=auth_headers
        )
        
        if msg_response.status_code == 200:
            messages = msg_response.json()
            print(f"✅ Found {len(messages)} message(s)")
            for msg in messages:
                direction = "←" if msg['direction'] == "inbound" else "→"
                print(f"   {direction} {msg['content'][:50]}...")
        else:
            print(f"❌ Failed to get messages: {msg_response.text}")
        
        # 5. Send a reply (Note: This will fail without valid WhatsApp credentials)
        print("\n5️⃣ Attempting to send a reply...")
        reply_data = {
            "conversation_id": conversation_id,
            "content": "Thank you for contacting BMA Support! We'll help you with your music zone.",
            "type": "text"
        }
        
        send_response = await client.post(
            f"{API_URL}/messages/send",
            json=reply_data,
            headers=auth_headers
        )
        
        if send_response.status_code == 200:
            print("✅ Message sent successfully!")
        elif send_response.status_code == 500:
            print("⚠️  Message sending failed (expected without WhatsApp credentials)")
            error = send_response.json()
            print(f"   Error: {error.get('detail', 'Unknown error')}")
        else:
            print(f"❌ Unexpected error: {send_response.text}")
        
        print("\n✅ WhatsApp integration test completed!")
        print("\n📝 Next steps:")
        print("1. Configure your WhatsApp Business API credentials in .env")
        print("2. Set up webhook URL in Meta Business platform")
        print("3. Start receiving real messages!")

if __name__ == "__main__":
    asyncio.run(test_whatsapp_integration())