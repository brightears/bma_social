from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

from app.models import User
from app.models.base import Base
from app.api.v1.dependencies import get_db, get_current_superuser
from app.api.v1.dependencies.database import get_engine

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/sync-database")
async def sync_database(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    Sync database schema - creates any missing tables
    Only accessible by superusers
    """
    try:
        # Create all tables that don't exist
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Get list of tables
        result = await db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """))
        tables = [row[0] for row in result.fetchall()]
        
        return {
            "status": "success",
            "message": "Database schema synchronized",
            "tables": tables
        }
    except Exception as e:
        logger.error(f"Error syncing database: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync database: {str(e)}"
        )


@router.get("/database-info")
async def get_database_info(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    Get database information
    Only accessible by superusers
    """
    try:
        # Get list of tables with row counts
        result = await db.execute(text("""
            SELECT 
                t.table_schema,
                t.table_name,
                pg_size_pretty(pg_total_relation_size(t.table_schema||'.'||t.table_name)) AS size,
                COALESCE(s.n_live_tup, 0) AS row_count
            FROM information_schema.tables t
            LEFT JOIN pg_stat_user_tables s 
                ON t.table_schema = s.schemaname 
                AND t.table_name = s.relname
            WHERE t.table_schema = 'public' 
                AND t.table_type = 'BASE TABLE'
            ORDER BY t.table_name;
        """))
        
        tables = []
        for row in result.fetchall():
            tables.append({
                "schema": row[0],
                "table": row[1],
                "size": row[2],
                "row_count": row[3]
            })
        
        return {
            "tables": tables,
            "total_tables": len(tables)
        }
    except Exception as e:
        logger.error(f"Error getting database info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get database info: {str(e)}"
        )