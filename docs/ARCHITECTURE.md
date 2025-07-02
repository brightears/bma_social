# Architecture & Integration Strategy

## Overview

BMA Social follows a microservices architecture pattern, designed to integrate seamlessly with the existing BMA CRM while maintaining independence for scaling and deployment.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         External Services                        │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │  WhatsApp   │  │     Line     │  │    Email (SMTP)        │ │
│  │Business API │  │ Business API │  │    Providers           │ │
│  └──────┬──────┘  └──────┬───────┘  └───────────┬────────────┘ │
└─────────┼────────────────┼──────────────────────┼──────────────┘
          │                │                      │
┌─────────▼────────────────▼──────────────────────▼──────────────┐
│                        BMA Social Platform                       │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    API Gateway (FastAPI)                 │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│   │
│  │  │   Auth   │  │ Rate     │  │  CORS    │  │ Logging ││   │
│  │  │Middleware│  │ Limiter  │  │ Handler  │  │         ││   │
│  │  └──────────┘  └──────────┘  └──────────┘  └─────────┘│   │
│  └─────────────────────────┬───────────────────────────────┘   │
│                            │                                     │
│  ┌─────────────────────────▼───────────────────────────────┐   │
│  │                    Business Logic Layer                  │   │
│  │  ┌────────────┐  ┌────────────┐  ┌─────────────────┐   │   │
│  │  │Conversation│  │  Campaign  │  │    Analytics    │   │   │
│  │  │  Service   │  │  Service   │  │    Service      │   │   │
│  │  └────────────┘  └────────────┘  └─────────────────┘   │   │
│  │  ┌────────────┐  ┌────────────┐  ┌─────────────────┐   │   │
│  │  │  Message   │  │  Template  │  │  Integration    │   │   │
│  │  │  Service   │  │  Service   │  │    Service      │   │   │
│  │  └────────────┘  └────────────┘  └─────────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Data Access Layer                      │   │
│  │  ┌────────────┐  ┌────────────┐  ┌─────────────────┐   │   │
│  │  │PostgreSQL  │  │   Redis    │  │   File Storage  │   │   │
│  │  │   (Main)   │  │  (Cache)   │  │   (S3/Local)   │   │   │
│  │  └────────────┘  └────────────┘  └─────────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                 Background Jobs (Celery)                  │   │
│  │  ┌────────────┐  ┌────────────┐  ┌─────────────────┐   │   │
│  │  │  Campaign  │  │  Message   │  │    Data Sync    │   │   │
│  │  │ Scheduler  │  │   Queue    │  │     Worker      │   │   │
│  │  └────────────┘  └────────────┘  └─────────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │     BMA CRM         │
                    │  (Django System)     │
                    └─────────────────────┘
```

## Key Design Decisions

### 1. Microservices Architecture

**Decision**: Keep BMA Social separate from BMA CRM

**Rationale**:
- Different technology stacks (FastAPI vs Django)
- Independent scaling requirements
- Separate deployment cycles
- Clear separation of concerns

**Trade-offs**:
- (+) Independent development and deployment
- (+) Technology flexibility
- (+) Better fault isolation
- (-) Additional integration complexity
- (-) Potential data duplication

### 2. Asynchronous Architecture

**Decision**: Use async/await throughout with FastAPI

**Rationale**:
- High concurrent connection requirements
- Real-time messaging needs
- Efficient handling of I/O-bound operations
- Better resource utilization

### 3. Event-Driven Communication

**Decision**: Use message queues for inter-service communication

**Rationale**:
- Decoupled services
- Better reliability with retry mechanisms
- Scalable message processing
- Audit trail for all events

## Integration Strategy with BMA CRM

### 1. API-Based Integration

```python
# Example integration service
class CRMIntegrationService:
    async def get_customer(self, customer_id: str) -> Customer:
        """Fetch customer data from CRM with caching"""
        
        # Check cache first
        cached = await redis.get(f"customer:{customer_id}")
        if cached:
            return Customer.parse_raw(cached)
        
        # Fetch from CRM API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.CRM_API_URL}/customers/{customer_id}",
                headers={"Authorization": f"Bearer {settings.CRM_API_KEY}"}
            )
            
        customer = Customer(**response.json())
        
        # Cache for 5 minutes
        await redis.setex(
            f"customer:{customer_id}", 
            300, 
            customer.json()
        )
        
        return customer
```

### 2. Shared Authentication

**JWT Token Flow**:
1. User logs into CRM
2. CRM issues JWT token
3. BMA Social validates token with shared secret
4. Same user session across both platforms

```python
# Shared JWT validation
async def validate_crm_token(token: str) -> User:
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("sub")
        return await get_user_from_crm(user_id)
    except JWTError:
        raise credentials_exception
```

### 3. Event Synchronization

**Webhook Events from CRM**:
- Customer created/updated
- Contract status changes
- Zone online/offline events
- Payment status updates

**Events to CRM**:
- Message sent/received
- Campaign engagement
- Customer interaction logs

### 4. Data Synchronization Strategy

```yaml
Sync Patterns:
  
  Real-time:
    - Customer profile updates
    - Zone status changes
    - Critical notifications
    
  Near Real-time (1-5 min):
    - Contract renewals
    - Payment reminders
    - Campaign triggers
    
  Batch (Daily):
    - Analytics aggregation
    - Historical data sync
    - Cleanup operations
```

## Security Architecture

### 1. Authentication & Authorization

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  API Gateway│────▶│   Service   │
└─────────────┘     └─────────────┘     └─────────────┘
      │                    │                    │
      │ JWT Token         │ Validate          │ Check
      │                   │ Token             │ Permissions
      ▼                   ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│Auth Headers │     │  Auth       │     │    RBAC     │
│Bearer Token │     │  Service    │     │   Rules     │
└─────────────┘     └─────────────┘     └─────────────┘
```

### 2. Data Security

- **Encryption at Rest**: PostgreSQL with encrypted volumes
- **Encryption in Transit**: TLS 1.3 for all connections
- **Message Encryption**: End-to-end for sensitive data
- **PII Protection**: Automatic masking in logs

### 3. API Security

- Rate limiting per user/IP
- Request validation with Pydantic
- SQL injection prevention via ORM
- XSS protection in responses

## Scalability Considerations

### 1. Horizontal Scaling

```yaml
Load Balancer (Render)
    │
    ├── Web Service Instance 1
    ├── Web Service Instance 2
    └── Web Service Instance N
         │
         ├── Shared PostgreSQL (Connection Pooling)
         ├── Shared Redis (Cluster Mode)
         └── Shared Message Queue
```

### 2. Database Optimization

- **Read Replicas**: For analytics queries
- **Partitioning**: Messages table by date
- **Indexing**: On frequently queried fields
- **Connection Pooling**: Via asyncpg

### 3. Caching Strategy

```python
Cache Layers:
  1. Application Cache (In-memory)
     - User sessions
     - Permissions
     
  2. Redis Cache
     - Customer data (5 min TTL)
     - Template renders (1 hour TTL)
     - API responses (varied TTL)
     
  3. CDN Cache
     - Static assets
     - Public API responses
```

## Monitoring & Observability

### 1. Metrics Collection

- **Application Metrics**: Prometheus + Grafana
- **Business Metrics**: Custom dashboard
- **Infrastructure**: Render monitoring

### 2. Logging Strategy

```python
Structured Logging:
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "message_service",
  "trace_id": "abc123",
  "user_id": "user_456",
  "action": "message_sent",
  "channel": "whatsapp",
  "duration_ms": 150
}
```

### 3. Distributed Tracing

- Request flow tracking across services
- Performance bottleneck identification
- Error tracking with Sentry

## Development Workflow

### 1. Environment Management

```
Development:
  - Local PostgreSQL/Redis
  - Mock external services
  - Debug logging enabled
  
Staging:
  - Render preview environments
  - Shared test database
  - Integration testing
  
Production:
  - Full Render deployment
  - Production databases
  - Monitoring enabled
```

### 2. CI/CD Pipeline

```yaml
GitHub Actions:
  1. Run tests
  2. Type checking (mypy)
  3. Linting (flake8, black)
  4. Security scanning
  5. Deploy to Render
```

## Future Considerations

### 1. Multi-Region Deployment
- Deploy closer to Thai users
- Database replication across regions
- CDN for static assets

### 2. AI/ML Integration
- Message sentiment analysis
- Smart reply suggestions
- Optimal send time prediction
- Customer churn prediction

### 3. Additional Channels
- SMS integration
- Facebook Messenger
- Instagram Direct
- Twitter DMs

### 4. Advanced Analytics
- Real-time dashboards
- Custom report builder
- Export capabilities
- Predictive analytics