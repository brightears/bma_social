from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    conversations,
    messages,
    campaigns,
    templates,
    webhooks,
    analytics,
    contacts,
    quotations,
    admin
)

api_router = APIRouter()

# Authentication
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Users
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Conversations
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])

# Messages
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])

# Campaigns
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])

# Templates
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])

# Webhooks
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])

# Analytics
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

# Contacts
api_router.include_router(contacts.router, prefix="/contacts", tags=["contacts"])

# Quotations
api_router.include_router(quotations.router, prefix="/quotations", tags=["quotations"])

# Admin
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])