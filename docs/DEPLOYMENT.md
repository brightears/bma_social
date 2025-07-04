# Deployment Guide

This guide covers deploying BMA Social to Render with PostgreSQL and Redis. Last updated: January 4, 2025.

## Prerequisites

- GitHub repository connected to Render
- Render account with payment method (for databases)
- Domain name (optional)

## Services Required

1. **Backend Web Service** - FastAPI backend API
2. **Frontend Web Service** - React TypeScript application
3. **PostgreSQL** - Primary database  
4. **Redis** - Cache and message queue (optional, for future features)
5. **Webhook Router** - Separate service for WhatsApp webhook forwarding
6. **Background Worker** - Celery tasks (optional, for scheduled campaigns)

## Step-by-Step Deployment

### 1. Database Setup

#### PostgreSQL on Render

1. Create a new PostgreSQL database:
   - Go to Render Dashboard > New > PostgreSQL
   - Name: `bma-social-db`
   - Region: Singapore (closest to Thailand)
   - Plan: Starter ($7/month) or higher

2. Note the connection details:
   - Internal Database URL (for app connection)
   - External Database URL (for migrations)

#### Redis on Render

1. Create a new Redis instance:
   - Go to Render Dashboard > New > Redis
   - Name: `bma-social-redis`
   - Region: Same as PostgreSQL
   - Plan: Starter ($10/month)

2. Note the connection URL

### 2. Web Service Configuration

#### Backend Service

1. Create a new Web Service on Render:
   - Name: `bma-social-api`
   - Environment: Python 3
   - Build Command: `cd backend && pip install -r requirements.txt`
   - Start Command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

#### Frontend Service

2. Create another Web Service for frontend:
   - Name: `bma-social-frontend`
   - Environment: Node
   - Build Command: `cd frontend && npm install && npm run build`
   - Start Command: `cd frontend && npm run start`
   - Publish Directory: `frontend/build`

3. Create `render.yaml` in project root:

```yaml
services:
  # Web Service
  - type: web
    name: bma-social-api
    env: python
    region: singapore
    plan: starter
    buildCommand: "pip install -r backend/requirements.txt"
    startCommand: "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: DATABASE_URL
        fromDatabase:
          name: bma-social-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          name: bma-social-redis
          type: redis
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: ENVIRONMENT
        value: production

  # Background Worker (Optional)
  - type: worker
    name: bma-social-worker
    env: python
    region: singapore
    plan: starter
    buildCommand: "pip install -r backend/requirements.txt"
    startCommand: "cd backend && celery -A app.worker worker --loglevel=info"
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: bma-social-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          name: bma-social-redis
          type: redis
          property: connectionString

databases:
  - name: bma-social-db
    plan: starter
    region: singapore

  - name: bma-social-redis
    type: redis
    plan: starter
    region: singapore
```

2. Push to GitHub:
```bash
git add render.yaml
git commit -m "Add Render configuration"
git push origin main
```

### 3. Environment Variables

Set these in Render Dashboard > Environment:

```env
# WhatsApp Configuration
WHATSAPP_ACCESS_TOKEN=your-token
WHATSAPP_PHONE_NUMBER_ID=your-number-id
WHATSAPP_VERIFY_TOKEN=your-verify-token
WHATSAPP_WEBHOOK_URL=https://bma-social-api.onrender.com/api/v1/webhooks/whatsapp

# Line Configuration  
LINE_CHANNEL_ACCESS_TOKEN=your-token
LINE_CHANNEL_SECRET=your-secret

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email
SMTP_PASSWORD=your-app-password

# CRM Integration
CRM_API_URL=https://bmasia-crm.onrender.com/api
CRM_API_KEY=your-api-key

# CORS Origins
BACKEND_CORS_ORIGINS=["https://bma-social-frontend.onrender.com", "http://localhost:3000"]

# Frontend URL (for email links, etc)
FRONTEND_URL=https://bma-social-frontend.onrender.com

# JWT Settings
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 4. Database Migrations

1. SSH into your web service or run locally:
```bash
export DATABASE_URL=your-external-database-url
cd backend
alembic upgrade head
```

2. Or create a one-time job in Render:
   - Command: `cd backend && alembic upgrade head`

### 5. Domain Configuration (Optional)

1. Add custom domain in Render:
   - Settings > Custom Domains
   - Add `social.brightearsmusicasia.com`

2. Update DNS records:
   - CNAME: `social` -> `bma-social-api.onrender.com`

### 6. Monitoring Setup

1. Enable Render's built-in monitoring
2. Health check endpoints:
   - Backend: `https://bma-social-api.onrender.com/health`
   - Frontend: `https://bma-social-frontend.onrender.com`
3. Configure alerts for downtime
4. Monitor key metrics:
   - Response time
   - Error rate
   - Database connections
   - Memory usage

## Post-Deployment

### 1. Initial Setup

1. **Create Admin User**:
   ```bash
   # SSH into backend service
   render ssh bma-social-api
   
   # Run Python shell
   cd backend
   python
   
   # Create admin user
   from app.core.security import get_password_hash
   from app.models.user import User
   from app.core.database import SessionLocal
   
   db = SessionLocal()
   admin = User(
       username="admin",
       email="admin@bma.com",
       hashed_password=get_password_hash("your-secure-password"),
       full_name="System Admin",
       role="admin",
       is_active=True
   )
   db.add(admin)
   db.commit()
   ```

2. **Configure Frontend Environment**:
   - Update `frontend/.env.production` with correct API URL
   - Ensure REACT_APP_API_URL points to backend

### 2. Webhook Configuration

#### WhatsApp Setup
1. Deploy webhook router service separately
2. Configure router to forward to BMA Social API
3. Update Meta for Developers:
   - Webhook URL: `https://your-webhook-router/webhooks/whatsapp`
   - Verify Token: Match with environment variable
   - Subscribe to: messages, message_status

#### Webhook Router Configuration
```javascript
// webhook-router configuration
const endpoints = [
  'https://bma-social-api.onrender.com/api/v1/webhooks/whatsapp',
  'https://other-service/webhook'  // If needed
];
```

### 2. Database Backups

Enable automatic backups in Render:
- Database > Settings > Backups
- Set retention period (7 days recommended)

### 3. Database Management

1. **Regular Backups**:
   - Enable automatic daily backups
   - Set retention to 7-30 days
   - Test restore procedure monthly

2. **Maintenance**:
   ```sql
   -- Run periodically
   VACUUM ANALYZE;
   REINDEX DATABASE "bma-social-db";
   ```

3. **Monitoring**:
   - Track slow queries
   - Monitor connection pool usage
   - Watch for table bloat

### 4. Scaling

When ready to scale:

1. **Vertical Scaling**:
   - Upgrade Render plan (Starter → Standard → Pro)
   - Increase database resources
   - Add more RAM/CPU

2. **Horizontal Scaling**:
   - Enable auto-scaling (2-10 instances)
   - Add Redis for session management
   - Implement load balancing

3. **Performance Optimization**:
   - Enable CDN for static assets
   - Implement database read replicas
   - Add caching layer with Redis
   - Use background jobs for heavy tasks

## Production Checklist

- [ ] SSL certificates active and auto-renewing
- [ ] Environment variables properly set
- [ ] Database migrations completed
- [ ] Admin user created
- [ ] Webhooks verified and working
- [ ] CORS configured correctly
- [ ] Health checks passing
- [ ] Monitoring alerts configured
- [ ] Backup strategy implemented
- [ ] Error tracking enabled
- [ ] Rate limiting configured
- [ ] Security headers enabled

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check DATABASE_URL format
   - Ensure database is in same region
   - Verify firewall rules

2. **WhatsApp Webhook Verification Failed**
   - Check WHATSAPP_VERIFY_TOKEN matches
   - Ensure webhook endpoint is accessible
   - Check logs for verification attempts

3. **Slow Performance**
   - Enable Redis caching
   - Add database indexes
   - Upgrade to larger instance

### Useful Commands

```bash
# View logs
render logs bma-social-api --tail
render logs bma-social-frontend --tail

# SSH into service
render ssh bma-social-api
render ssh bma-social-frontend

# Run database migrations
render job create --service bma-social-api --command "cd backend && alembic upgrade head"

# Create database backup
render postgres backup create bma-social-db

# Run production shell
render run bma-social-api --command "cd backend && python"
```

## Rollback Procedure

1. Identify the issue in logs
2. Revert to previous commit:
   ```bash
   git revert HEAD
   git push origin main
   ```
3. Render will automatically redeploy

## Performance Optimization

1. **Frontend Optimization**
   - Enable code splitting
   - Lazy load components
   - Optimize images (WebP format)
   - Enable gzip compression
   - Use React.memo for expensive components
   - Implement virtual scrolling for long lists

2. **Backend Optimization**
   - Enable response caching with Redis
   - Use database connection pooling
   - Implement query result caching
   - Add indexes for common queries:
     ```sql
     CREATE INDEX idx_conversations_customer_id ON conversations(customer_id);
     CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
     CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
     ```
   - Use eager loading for relationships
   - Implement pagination for all list endpoints

3. **Infrastructure Optimization**
   - Use CDN for static assets (Cloudflare)
   - Enable HTTP/2
   - Configure proper cache headers
   - Use Redis for session storage
   - Implement request queuing for webhooks

## Security Hardening

1. **Application Security**
   - Enable security headers (HSTS, CSP, etc.)
   - Implement request rate limiting
   - Use prepared statements (via SQLAlchemy)
   - Validate all input data
   - Sanitize file uploads
   - Implement CSRF protection

2. **Infrastructure Security**
   - Use environment variables for secrets
   - Enable firewall rules
   - Restrict database access
   - Use HTTPS everywhere
   - Regular security updates
   - Monitor for vulnerabilities

3. **Access Control**
   - Implement IP whitelisting for admin
   - Use strong password policies
   - Enable 2FA for admin accounts
   - Regular access audits
   - Session timeout policies