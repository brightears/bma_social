#!/usr/bin/env python3
"""
Create admin user for BMA Social
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Set environment variables if running locally
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://bma_social_user:pCHVsmUr4RJajJyAheZvwWn3XJfGvxMJ@dpg-d1ibdq2dbo4c73erpme0-a/bma_social")

from app.models import User
from app.core.security import get_password_hash


async def create_admin():
    # Get database URL
    db_url = os.environ.get('DATABASE_URL', '')
    
    # Convert to asyncpg format
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql+asyncpg://', 1)
    elif db_url.startswith('postgresql://'):
        db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    
    # Create engine
    engine = create_async_engine(db_url, echo=True)
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Check if admin exists
        result = await session.execute(
            select(User).where(User.username == "admin")
        )
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print("Admin user already exists!")
            return
        
        # Create admin user
        admin = User(
            email="admin@bma-social.com",
            username="admin",
            full_name="System Administrator",
            hashed_password=get_password_hash("changeme123"),
            is_active=True,
            is_superuser=True,
            role="admin"
        )
        
        session.add(admin)
        await session.commit()
        
        print("Admin user created successfully!")
        print("Username: admin")
        print("Password: changeme123")
        print("Please change this password immediately!")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_admin())