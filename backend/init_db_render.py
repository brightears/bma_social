#!/usr/bin/env python3
"""
Initialize database on Render
Run this script once to create all tables
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from app.models.base import Base

# Import all models to ensure they're registered
from app.models.user import User
from app.models.customer import Customer
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.campaign import Campaign
from app.models.template import Template


async def init_db():
    # Get DATABASE_URL from environment
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return
    
    print(f"Connecting to database...")
    
    # Create engine
    engine = create_async_engine(database_url, echo=True)
    
    # Create all tables
    async with engine.begin() as conn:
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("✓ Tables created successfully!")
    
    # Close engine
    await engine.dispose()
    print("✓ Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(init_db())