# API Documentation

## Overview

BMA Social API is built with FastAPI and follows RESTful principles. All endpoints are prefixed with `/api/v1/`.

## Authentication

All API requests require authentication using JWT tokens.

### Obtaining a Token

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### Using the Token

Include the token in the Authorization header:
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

## Core Endpoints

### Conversations

#### List Conversations
```http
GET /api/v1/conversations
```

Query Parameters:
- `channel`: Filter by channel (whatsapp, line, email)
- `status`: Filter by status (open, closed, pending)
- `assigned_to`: Filter by assigned user ID
- `customer_id`: Filter by customer ID
- `limit`: Number of results (default: 20)
- `offset`: Pagination offset

#### Get Conversation
```http
GET /api/v1/conversations/{conversation_id}
```

#### Create Conversation
```http
POST /api/v1/conversations
Content-Type: application/json

{
  "customer_id": "uuid",
  "channel": "whatsapp",
  "channel_id": "1234567890"
}
```

### Messages

#### Send Message
```http
POST /api/v1/messages
Content-Type: application/json

{
  "conversation_id": "uuid",
  "content": "Hello, how can I help you?",
  "type": "text",
  "attachments": []
}
```

#### Get Messages
```http
GET /api/v1/conversations/{conversation_id}/messages
```

### Campaigns

#### Create Campaign
```http
POST /api/v1/campaigns
Content-Type: application/json

{
  "name": "January Promotion",
  "channel": "whatsapp",
  "template_id": "uuid",
  "segment_id": "uuid",
  "scheduled_at": "2024-01-15T10:00:00Z"
}
```

#### Get Campaign Analytics
```http
GET /api/v1/campaigns/{campaign_id}/analytics
```

### Templates

#### Create Template
```http
POST /api/v1/templates
Content-Type: application/json

{
  "name": "Welcome Message",
  "channel": "whatsapp",
  "content": "Hello {{customer_name}}, welcome to BMA!",
  "variables": ["customer_name"]
}
```

## Webhooks

### WhatsApp Webhook
```http
POST /api/v1/webhooks/whatsapp
GET /api/v1/webhooks/whatsapp  # For verification
```

### Line Webhook
```http
POST /api/v1/webhooks/line
```

## Error Responses

All errors follow this format:
```json
{
  "detail": "Error message",
  "code": "ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

Common HTTP Status Codes:
- `200 OK`: Successful request
- `201 Created`: Resource created
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limiting

- **Default**: 100 requests per minute per user
- **Bulk Operations**: 10 requests per minute
- **Webhooks**: No rate limiting

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
```

## Pagination

List endpoints support pagination:
```http
GET /api/v1/conversations?limit=20&offset=40
```

Response includes pagination metadata:
```json
{
  "data": [...],
  "pagination": {
    "total": 150,
    "limit": 20,
    "offset": 40,
    "has_next": true,
    "has_prev": true
  }
}
```

## WebSocket Support

Real-time updates via WebSocket:
```javascript
const ws = new WebSocket('wss://api.bma-social.com/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle real-time updates
};
```

## SDK Examples

### Python
```python
import httpx

client = httpx.Client(
    base_url="https://api.bma-social.com/api/v1",
    headers={"Authorization": f"Bearer {token}"}
)

# Send a message
response = client.post("/messages", json={
    "conversation_id": "uuid",
    "content": "Hello!"
})
```

### JavaScript
```javascript
const api = axios.create({
  baseURL: 'https://api.bma-social.com/api/v1',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

// Send a message
const response = await api.post('/messages', {
  conversation_id: 'uuid',
  content: 'Hello!'
});
```