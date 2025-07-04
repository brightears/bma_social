# BMA Social API Documentation

## Overview

BMA Social API is a RESTful API built with FastAPI that provides comprehensive endpoints for multi-channel customer communication management. The API supports WhatsApp integration, contact management, campaign creation, quotation generation, and more.

**Base URL**: `https://bma-social-api.onrender.com/api/v1`

**Documentation**: 
- Swagger UI: `https://bma-social-api.onrender.com/docs`
- ReDoc: `https://bma-social-api.onrender.com/redoc`

## Authentication

The API uses JWT (JSON Web Token) authentication. All endpoints except login and webhook verification require authentication.

### Login

```http
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "your-password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "is_active": true
  }
}
```

### Using the Token

Include the JWT token in the Authorization header for all authenticated requests:

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

## Core Endpoints

### Users

#### List Users
```http
GET /users
Authorization: Bearer {token}
```

Query Parameters:
- `skip`: Offset for pagination (default: 0)
- `limit`: Number of results (default: 100)
- `role`: Filter by role (admin, manager, agent)
- `is_active`: Filter by active status

#### Create User
```http
POST /users
Authorization: Bearer {token}
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "New User",
  "role": "agent",
  "is_active": true
}
```

#### Get User
```http
GET /users/{user_id}
Authorization: Bearer {token}
```

#### Update User
```http
PUT /users/{user_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "full_name": "Updated Name",
  "role": "manager",
  "is_active": true
}
```

### Conversations

#### List Conversations
```http
GET /conversations
Authorization: Bearer {token}
```

Query Parameters:
- `skip`: Offset for pagination
- `limit`: Number of results
- `channel`: Filter by channel (whatsapp)
- `status`: Filter by status (active, archived)
- `customer_id`: Filter by customer
- `assigned_to`: Filter by assigned user

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "customer_id": "uuid",
      "channel": "whatsapp",
      "channel_conversation_id": "wa_123",
      "status": "active",
      "last_message_at": "2025-01-04T10:00:00Z",
      "assigned_to": "uuid",
      "metadata": {},
      "created_at": "2025-01-04T09:00:00Z",
      "customer": {
        "id": "uuid",
        "name": "John Doe",
        "phone": "+66812345678"
      }
    }
  ],
  "total": 50,
  "skip": 0,
  "limit": 20
}
```

#### Get Conversation Messages
```http
GET /conversations/{conversation_id}/messages
Authorization: Bearer {token}
```

Query Parameters:
- `skip`: Offset for pagination
- `limit`: Number of results
- `order`: Sort order (asc, desc)

#### Send Message
```http
POST /conversations/{conversation_id}/messages
Authorization: Bearer {token}
Content-Type: application/json

{
  "content": "Hello, how can I help you?",
  "type": "text"
}
```

For media messages:
```json
{
  "content": "Please see the attached document",
  "type": "document",
  "media_url": "https://example.com/document.pdf",
  "media_mime_type": "application/pdf",
  "media_filename": "quotation.pdf"
}
```

### Messages

#### Update Message Status
```http
PUT /messages/{message_id}/status
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "read",
  "updated_at": "2025-01-04T10:00:00Z"
}
```

### Contacts

#### List Contacts
```http
GET /contacts
Authorization: Bearer {token}
```

Query Parameters:
- `skip`: Offset for pagination
- `limit`: Number of results
- `search`: Search by name, email, or phone
- `tags`: Filter by tags (comma-separated)

#### Create Contact
```http
POST /contacts
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+66812345678",
  "company": "Example Corp",
  "tags": ["customer", "vip"],
  "metadata": {
    "source": "website",
    "notes": "Interested in premium plan"
  }
}
```

#### Import Contacts
```http
POST /contacts/import
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: contacts.csv
```

CSV Format:
```csv
name,email,phone,company,tags
John Doe,john@example.com,+66812345678,Example Corp,"customer,vip"
```

#### Export Contacts
```http
GET /contacts/export
Authorization: Bearer {token}
```

Query Parameters:
- `format`: Export format (csv, json)
- `tags`: Filter by tags

### Campaigns

#### List Campaigns
```http
GET /campaigns
Authorization: Bearer {token}
```

Query Parameters:
- `skip`: Offset for pagination
- `limit`: Number of results
- `status`: Filter by status (draft, scheduled, sent, completed)
- `channel`: Filter by channel

#### Create Campaign
```http
POST /campaigns
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "New Year Promotion",
  "channel": "whatsapp",
  "template_id": "uuid",
  "contact_ids": ["uuid1", "uuid2"],
  "scheduled_at": "2025-01-15T10:00:00Z",
  "metadata": {
    "promotion_type": "seasonal",
    "discount": "20%"
  }
}
```

#### Send Campaign
```http
POST /campaigns/{campaign_id}/send
Authorization: Bearer {token}
```

#### Get Campaign Analytics
```http
GET /campaigns/{campaign_id}/analytics
Authorization: Bearer {token}
```

**Response:**
```json
{
  "campaign_id": "uuid",
  "total_recipients": 100,
  "sent": 98,
  "delivered": 95,
  "read": 80,
  "failed": 2,
  "click_through_rate": 0.15,
  "conversion_rate": 0.08
}
```

### Templates

#### List Templates
```http
GET /templates
Authorization: Bearer {token}
```

Query Parameters:
- `channel`: Filter by channel
- `category`: Filter by category

#### Create Template
```http
POST /templates
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Welcome Message",
  "channel": "whatsapp",
  "category": "greeting",
  "content": "Hello {{name}}, welcome to Bright Ears Music Asia!",
  "variables": ["name"],
  "metadata": {
    "language": "en",
    "approved": true
  }
}
```

### Quotations

#### List Quotations
```http
GET /quotations
Authorization: Bearer {token}
```

Query Parameters:
- `skip`: Offset for pagination
- `limit`: Number of results
- `status`: Filter by status (draft, sent, viewed, accepted, rejected)
- `customer_id`: Filter by customer
- `currency`: Filter by currency (THB, USD)

#### Create Quotation
```http
POST /quotations
Authorization: Bearer {token}
Content-Type: application/json

{
  "customer_id": "uuid",
  "title": "Website Development Quote",
  "company_name": "Example Corp",
  "company_address": "123 Business St, Bangkok",
  "company_tax_id": "1234567890123",
  "currency": "THB",
  "items": [
    {
      "description": "Website Design",
      "quantity": 1,
      "unit_price": 50000,
      "total": 50000
    },
    {
      "description": "Development (10 pages)",
      "quantity": 10,
      "unit_price": 5000,
      "total": 50000
    }
  ],
  "discount_percent": 10,
  "tax_percent": 7,
  "payment_terms": "50% deposit, 50% on completion",
  "validity_days": 30,
  "notes": "Price includes 1 year of hosting"
}
```

#### Generate PDF
```http
GET /quotations/{quotation_id}/pdf
Authorization: Bearer {token}
```

Returns the quotation as a PDF file.

#### Send via WhatsApp
```http
POST /quotations/{quotation_id}/send
Authorization: Bearer {token}
Content-Type: application/json

{
  "phone_number": "+66812345678",
  "message": "Please find attached your quotation"
}
```

### Quotation Templates

#### List Quotation Templates
```http
GET /quotations/templates
Authorization: Bearer {token}
```

#### Create Quotation Template
```http
POST /quotations/templates
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Standard Web Development",
  "description": "Template for web development projects",
  "title": "Web Development Quotation",
  "items": [
    {
      "description": "Website Design",
      "quantity": 1,
      "unit_price": 50000,
      "total": 50000
    }
  ],
  "payment_terms": "50% deposit, 50% on completion",
  "validity_days": 30,
  "notes": "Standard terms apply"
}
```

### Admin

#### Get System Statistics
```http
GET /admin/stats
Authorization: Bearer {token}
```

**Response:**
```json
{
  "users": {
    "total": 10,
    "active": 8,
    "by_role": {
      "admin": 2,
      "manager": 3,
      "agent": 5
    }
  },
  "conversations": {
    "total": 1500,
    "active": 120,
    "today": 45
  },
  "messages": {
    "total": 25000,
    "today": 890,
    "sent": 12000,
    "received": 13000
  },
  "campaigns": {
    "total": 50,
    "active": 5,
    "completed": 40
  },
  "quotations": {
    "total": 200,
    "accepted": 150,
    "pending": 30
  }
}
```

### Webhooks

#### WhatsApp Webhook Verification
```http
GET /webhooks/whatsapp?hub.mode=subscribe&hub.challenge=test&hub.verify_token=your-token
```

#### WhatsApp Webhook Handler
```http
POST /webhooks/whatsapp
Content-Type: application/json

{
  "entry": [
    {
      "id": "ENTRY_ID",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "1234567890",
              "phone_number_id": "PHONE_NUMBER_ID"
            },
            "messages": [
              {
                "from": "1234567890",
                "id": "MESSAGE_ID",
                "timestamp": "1234567890",
                "text": {
                  "body": "Hello"
                },
                "type": "text"
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}
```

## Error Responses

All error responses follow a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Codes

- `400 Bad Request`: Invalid request data or parameters
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: Insufficient permissions for the requested action
- `404 Not Found`: Requested resource not found
- `409 Conflict`: Resource already exists or conflict with current state
- `422 Unprocessable Entity`: Request validation failed
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Validation Errors

For validation errors (422), the response includes field-specific errors:

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "invalid email address",
      "type": "value_error.email"
    }
  ]
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Default rate limit**: 100 requests per minute per IP
- **Authenticated users**: 1000 requests per minute per user
- **Bulk operations**: 10 requests per minute

Rate limit information is included in response headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704355200
```

## Pagination

List endpoints support pagination using `skip` and `limit` parameters:

```http
GET /contacts?skip=20&limit=10
```

Paginated responses include metadata:
```json
{
  "items": [...],
  "total": 150,
  "skip": 20,
  "limit": 10
}
```

## Filtering and Searching

Most list endpoints support filtering via query parameters:

```http
GET /conversations?channel=whatsapp&status=active
GET /contacts?search=john&tags=customer,vip
GET /quotations?status=sent&currency=USD
```

## Webhook Security

Webhooks include signature verification:

1. **WhatsApp**: Validates using the `X-Hub-Signature-256` header
2. **Custom webhooks**: Use HMAC-SHA256 signatures

## Best Practices

1. **Authentication**: Store tokens securely and refresh before expiration
2. **Error Handling**: Always check response status and handle errors gracefully
3. **Rate Limiting**: Implement exponential backoff for rate limit errors
4. **Pagination**: Use pagination for large datasets to improve performance
5. **Webhooks**: Verify webhook signatures and respond quickly (< 5 seconds)

## SDKs and Code Examples

### Python Example
```python
import httpx
from typing import Dict, Any

class BMASocialClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )
    
    def send_message(self, conversation_id: str, content: str) -> Dict[str, Any]:
        response = self.client.post(
            f"/conversations/{conversation_id}/messages",
            json={"content": content, "type": "text"}
        )
        response.raise_for_status()
        return response.json()

# Usage
client = BMASocialClient("https://bma-social-api.onrender.com/api/v1", "your-token")
message = client.send_message("conversation-uuid", "Hello!")
```

### JavaScript/TypeScript Example
```typescript
import axios, { AxiosInstance } from 'axios';

class BMASocialClient {
  private api: AxiosInstance;

  constructor(baseURL: string, token: string) {
    this.api = axios.create({
      baseURL,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
  }

  async sendMessage(conversationId: string, content: string) {
    const response = await this.api.post(`/conversations/${conversationId}/messages`, {
      content,
      type: 'text'
    });
    return response.data;
  }
}

// Usage
const client = new BMASocialClient('https://bma-social-api.onrender.com/api/v1', 'your-token');
const message = await client.sendMessage('conversation-uuid', 'Hello!');
```

## Changelog

### Version 1.0.0 (January 2025)
- Initial release with WhatsApp integration
- Contact management system
- Campaign creation and management
- Quotation system with multi-currency support
- Admin tools and user management