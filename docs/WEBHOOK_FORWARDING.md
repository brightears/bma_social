# Webhook Forwarding Setup Guide

This guide shows how to forward WhatsApp webhooks from your zone monitor to BMA Social.

## Step 1: Locate Your Current Webhook

In your `syb-zone-monitor` project, find the file with your WhatsApp webhook endpoint.
It should look something like:

```python
@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    # Your existing code
```

## Step 2: Add httpx Import

At the top of the file, add:

```python
import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)
```

## Step 3: Modify Your Webhook Function

Replace your existing webhook function with this enhanced version:

```python
@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """Handle WhatsApp webhook and forward to BMA Social"""
    
    # Get the raw body
    body = await request.json()
    
    # --- YOUR EXISTING ZONE MONITOR CODE STARTS HERE ---
    # Process the webhook for zone monitor
    # (Keep all your existing code that handles zone notifications)
    
    
    
    # --- YOUR EXISTING ZONE MONITOR CODE ENDS HERE ---
    
    # Forward to BMA Social
    async def forward_to_bma_social():
        """Forward webhook to BMA Social in background"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://bma-social-api.onrender.com/api/v1/webhooks/whatsapp",
                    json=body,
                    timeout=httpx.Timeout(5.0),
                    headers={
                        "Content-Type": "application/json",
                        "X-Forwarded-From": "zone-monitor"
                    }
                )
                if response.status_code == 200:
                    logger.info("Successfully forwarded webhook to BMA Social")
                else:
                    logger.warning(f"BMA Social returned {response.status_code}")
        except Exception as e:
            # Don't let BMA Social errors affect zone monitor
            logger.error(f"Failed to forward to BMA Social: {e}")
    
    # Run forwarding in background so it doesn't slow down the response
    asyncio.create_task(forward_to_bma_social())
    
    # Return success to WhatsApp
    return {"status": "ok"}
```

## Step 4: Handle Webhook Verification

Make sure your verification endpoint also exists:

```python
@app.get("/webhook/whatsapp")
async def verify_webhook(
    request: Request,
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    """WhatsApp webhook verification"""
    if hub_mode == "subscribe" and hub_verify_token == "your-verify-token":
        return Response(content=hub_challenge)
    return {"status": "error"}
```

## Step 5: Add httpx to Requirements

In your zone monitor's `requirements.txt`, make sure you have:

```
httpx>=0.25.0
```

## Step 6: Test the Setup

1. Deploy your updated zone monitor
2. Send a test WhatsApp message
3. Check both applications:
   - Zone monitor should process as normal
   - BMA Social should receive the message too

## Troubleshooting

### Check Zone Monitor Logs
Look for:
- "Successfully forwarded webhook to BMA Social"
- Any error messages about forwarding

### Check BMA Social Logs
In Render dashboard for BMA Social:
- Look for "Received WhatsApp webhook"
- Check for new conversations/messages

### Common Issues

1. **Timeout errors**: BMA Social might be slow to start
   - Solution: Increase timeout or retry

2. **Connection refused**: BMA Social URL might be wrong
   - Solution: Verify the URL is exactly: `https://bma-social-api.onrender.com/api/v1/webhooks/whatsapp`

3. **Both systems process the same message**: This is normal!
   - Zone monitor: Handles zone-related messages
   - BMA Social: Handles all messages for customer support

## Important Notes

- The forwarding happens in the background (asyncio.create_task)
- Errors in BMA Social won't affect zone monitor
- Both systems will receive ALL messages
- Each system should filter what it needs

## Security Consideration

You might want to add a shared secret between the services:

```python
# In zone monitor
headers={
    "Content-Type": "application/json",
    "X-Forwarded-From": "zone-monitor",
    "X-Shared-Secret": "your-secret-key"
}

# In BMA Social webhook
if request.headers.get("X-Shared-Secret") == "your-secret-key":
    # Trust this webhook came from zone monitor
    pass
```