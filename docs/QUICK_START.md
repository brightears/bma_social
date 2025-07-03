# Quick Start Guide - BMA Social

## Overview
BMA Social is a unified communication platform that allows your team to manage WhatsApp, Line, and Email conversations in one place.

## Current Deployment URLs
- **Frontend**: https://bma-social-frontend.onrender.com
- **Backend API**: https://bma-social-api.onrender.com
- **API Docs**: https://bma-social-api.onrender.com/docs

## Login Credentials
- **Username**: admin
- **Password**: changeme123

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   WhatsApp      │────▶│  Webhook Router  │────▶│   Zone Monitor  │
│   Business API  │     │   (Render)       │     │   (Existing)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │
                                ▼
                        ┌──────────────────┐
                        │   BMA Social     │
                        │   Backend API    │
                        │   (Render)       │
                        └──────────────────┘
                                │
                        ┌───────┴────────┐
                        ▼                ▼
                ┌──────────────┐  ┌──────────────┐
                │  PostgreSQL  │  │    Redis     │
                │   (Render)   │  │   (Render)   │
                └──────────────┘  └──────────────┘
                        
                ┌──────────────────┐
                │   BMA Social     │
                │   Frontend       │
                │   (React)        │
                └──────────────────┘
```

## Features Working
1. ✅ Receiving WhatsApp messages
2. ✅ Sending WhatsApp messages
3. ✅ Storing conversations and customer data
4. ✅ JWT Authentication
5. ✅ React frontend deployed
6. ✅ Login functionality working
7. ✅ Conversation list display
8. ✅ Click to view individual conversations
9. ✅ Send messages to specific conversations
10. ✅ Auto-refresh for new messages (every 3 seconds)

## Recently Fixed
- ✅ CORS issue resolved (temporarily allowing all origins)
- ✅ Conversation click handling fixed (ListItem → ListItemButton)
- ✅ Message ordering corrected (oldest to newest)
- ✅ Added auto-refresh for real-time updates

## Testing the API

### Get Access Token
```bash
curl -X POST https://bma-social-api.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=changeme123"
```

### Get Conversations
```bash
curl -X GET https://bma-social-api.onrender.com/api/v1/conversations/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Send WhatsApp Message
```bash
curl -X POST https://bma-social-api.onrender.com/api/v1/messages/send \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "CONVERSATION_ID",
    "content": "Hello from BMA Social!",
    "type": "text"
  }'
```

## Next Steps
1. Fix CORS configuration for frontend login
2. Add more team members/users
3. Implement Line messenger integration
4. Add bulk messaging features