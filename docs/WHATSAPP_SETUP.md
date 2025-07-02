# WhatsApp Business API Setup Guide

This guide will help you connect your WhatsApp Business account to BMA Social.

## Prerequisites

1. **WhatsApp Business Account** approved for API access
2. **Meta Business Account** with WhatsApp Business API setup
3. **Access Token** from Meta for Developers
4. **Phone Number ID** from your WhatsApp Business account

## Step 1: Get Your Credentials

### From Meta for Developers:

1. Go to [Meta for Developers](https://developers.facebook.com)
2. Navigate to your app → WhatsApp → API Setup
3. Copy:
   - **Access Token** (temporary or permanent)
   - **Phone Number ID** 
   - **WhatsApp Business Account ID**

## Step 2: Configure BMA Social

### Update Environment Variables:

Add these to your `.env` file or Render environment variables:

```env
# WhatsApp Configuration
WHATSAPP_ACCESS_TOKEN=your-access-token-here
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
WHATSAPP_VERIFY_TOKEN=your-custom-verify-token
WHATSAPP_WEBHOOK_URL=https://bma-social-api.onrender.com/api/v1/webhooks/whatsapp
```

## Step 3: Configure Webhook in Meta

### In Meta for Developers:

1. Go to your app → WhatsApp → Configuration
2. Under "Webhook", click "Edit"
3. Set:
   - **Callback URL**: `https://bma-social-api.onrender.com/api/v1/webhooks/whatsapp`
   - **Verify Token**: Same as `WHATSAPP_VERIFY_TOKEN` in your `.env`
4. Click "Verify and Save"

### Subscribe to Webhook Fields:

After verification, subscribe to:
- ✅ `messages` - To receive incoming messages
- ✅ `message_status` - To track delivery status
- ✅ `message_template_status_update` - For template approvals

## Step 4: Test Your Connection

### 1. Send a Test Message

From your WhatsApp app, send a message to your business number.

### 2. Check Logs

In Render dashboard, check your service logs:
```
Received WhatsApp webhook: {...}
Created new customer: Customer Name (66812345678)
Saved incoming message...
```

### 3. Check API

Visit `https://bma-social-api.onrender.com/docs` and test:
- `GET /api/v1/conversations/` - Should show the new conversation
- `GET /api/v1/messages/conversation/{id}` - Should show the message

## Step 5: Message Templates

### Creating Templates:

1. Go to Meta Business Suite → WhatsApp Manager → Message Templates
2. Create templates for common messages:
   - Welcome messages
   - Zone offline notifications
   - Contract renewal reminders

### Using Templates in BMA Social:

```json
POST /api/v1/messages/send
{
  "conversation_id": "uuid",
  "template_name": "zone_offline_notification",
  "template_params": {
    "components": [
      {
        "type": "body",
        "parameters": [
          {"type": "text", "text": "Zone 123"},
          {"type": "text", "text": "Central World"}
        ]
      }
    ]
  }
}
```

## Common Issues

### 1. Webhook Verification Fails
- Check that `WHATSAPP_VERIFY_TOKEN` matches exactly
- Ensure your API is publicly accessible
- Check Render logs for verification attempts

### 2. Messages Not Received
- Verify webhook subscriptions are active
- Check that customer initiated conversation within 24 hours
- Review Render logs for webhook payloads

### 3. Cannot Send Messages
- Ensure `WHATSAPP_ACCESS_TOKEN` is valid
- Check that phone number is correctly formatted
- Verify customer has messaged you first (24-hour window)

### 4. Access Token Expired
Temporary tokens expire in 24 hours. Get a permanent token:
1. Go to Meta for Developers
2. System Users → Add System User
3. Generate permanent token with `whatsapp_business_messaging` permission

## Phone Number Formatting

BMA Social automatically formats phone numbers:
- Thai numbers: `0812345678` → `66812345678`
- Already formatted: `66812345678` → `66812345678`
- With country code: `+66812345678` → `66812345678`

## Testing Locally

1. Use ngrok for local webhook testing:
```bash
ngrok http 8000
```

2. Update webhook URL in Meta to ngrok URL
3. Run the test script:
```bash
python test_whatsapp.py
```

## Production Checklist

- [ ] Permanent access token configured
- [ ] Webhook verified and subscribed
- [ ] Message templates approved
- [ ] Error notifications set up
- [ ] Rate limiting configured
- [ ] Backup phone number added

## Rate Limits

WhatsApp API has rate limits:
- **Messaging**: Based on your tier (1K, 10K, 100K, unlimited)
- **API Calls**: 200 calls per hour per phone number

BMA Social handles rate limiting automatically and queues messages when limits are reached.

## Support

For WhatsApp API issues:
- [WhatsApp Business API Documentation](https://developers.facebook.com/docs/whatsapp)
- [Meta Business Help Center](https://www.facebook.com/business/help)

For BMA Social issues:
- Check Render logs
- Review error messages in API responses
- Contact the development team