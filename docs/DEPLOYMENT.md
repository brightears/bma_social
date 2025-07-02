# Deployment Guide

This guide covers deploying BMA Social to Render with PostgreSQL and Redis.

## Prerequisites

- GitHub repository connected to Render
- Render account with payment method (for databases)
- Domain name (optional)

## Services Required

1. **Web Service** - FastAPI backend
2. **PostgreSQL** - Primary database  
3. **Redis** - Cache and message queue
4. **Background Worker** - Celery tasks (optional)

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

1. Create `render.yaml` in project root:

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
BACKEND_CORS_ORIGINS=["https://bma-social.onrender.com"]
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
2. Set up health check endpoint: `/health`
3. Configure alerts for downtime

## Post-Deployment

### 1. Webhook Configuration

Update WhatsApp webhook URL:
1. Go to Meta for Developers
2. Update webhook URL to: `https://your-domain/api/v1/webhooks/whatsapp`
3. Verify with token from environment

### 2. Database Backups

Enable automatic backups in Render:
- Database > Settings > Backups
- Set retention period (7 days recommended)

### 3. Scaling

When ready to scale:
- Upgrade web service plan for more resources
- Enable auto-scaling in Settings
- Add more background workers as needed

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
render logs bma-social-api

# SSH into service
render ssh bma-social-api

# Run database migrations
render job create --service bma-social-api --command "cd backend && alembic upgrade head"
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

1. **Enable Caching**
   - Use Redis for frequently accessed data
   - Cache CRM customer data (5 min TTL)
   - Cache message templates

2. **Database Optimization**
   - Add indexes for common queries
   - Use connection pooling
   - Regular VACUUM operations

3. **CDN for Static Assets**
   - Use Cloudflare for frontend assets
   - Cache API responses where appropriate