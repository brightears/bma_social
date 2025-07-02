"""
Initialize database with tables and create first superuser
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine
from app.models.base import Base
from app.models import User
from app.core.config import settings
from app.core.security import get_password_hash
from app.api.v1.dependencies.database import get_session_maker


async def init_db():
    """Initialize database"""
    print("Creating database tables...")
    
    # Create engine
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("Tables created successfully!")
    
    # Create first superuser
    AsyncSessionLocal = get_session_maker()
    async with AsyncSessionLocal() as session:
        # Check if superuser already exists
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.email == "admin@bma-social.com")
        )
        existing_user = result.scalar_one_or_none()
        
        if not existing_user:
            print("Creating superuser...")
            superuser = User(
                email="admin@bma-social.com",
                username="admin",
                full_name="System Administrator",
                hashed_password=get_password_hash("changeme123"),
                is_active=True,
                is_superuser=True,
                role="admin"
            )
            session.add(superuser)
            await session.commit()
            print("Superuser created!")
            print("Username: admin")
            print("Password: changeme123")
            print("⚠️  Please change this password immediately!")
        else:
            print("Superuser already exists.")
    
    await engine.dispose()
    print("Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(init_db())