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
        
        # Apply any necessary data migrations
        # Set default currency for existing quotations
        await db.execute(text("""
            UPDATE quotations 
            SET currency = 'THB' 
            WHERE currency IS NULL
        """))
        await db.commit()
        
        logger.info(f"Database sync completed. Tables: {tables}")
        
        return {
            "status": "success",
            "message": "Database schema synchronized",
            "tables": tables,
            "tables_count": len(tables)
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


@router.get("/check-quotations-table")
async def check_quotations_table(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    Check if quotations table exists and get its structure
    Only accessible by superusers
    """
    try:
        # Check if quotations table exists
        result = await db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'quotations'
            );
        """))
        table_exists = result.scalar()
        
        columns = []
        if table_exists:
            # Get column information
            result = await db.execute(text("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' 
                AND table_name = 'quotations'
                ORDER BY ordinal_position;
            """))
            
            for row in result.fetchall():
                columns.append({
                    "name": row[0],
                    "type": row[1],
                    "nullable": row[2] == 'YES',
                    "default": row[3]
                })
        
        # Also check if we can import the model
        try:
            from app.models import Quotation
            model_imported = True
            model_error = None
        except Exception as e:
            model_imported = False
            model_error = str(e)
        
        return {
            "table_exists": table_exists,
            "columns": columns,
            "columns_count": len(columns),
            "model_imported": model_imported,
            "model_error": model_error
        }
    except Exception as e:
        logger.error(f"Error checking quotations table: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check quotations table: {str(e)}"
        )


@router.get("/check-api-routes")
async def check_api_routes(
    current_user: User = Depends(get_current_superuser)
):
    """
    Check all registered API routes
    Only accessible by superusers
    """
    from app.main import app
    
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if route.methods else [],
                "name": route.name if hasattr(route, 'name') else None
            })
    
    # Sort routes by path
    routes.sort(key=lambda x: x['path'])
    
    # Filter quotation routes
    quotation_routes = [r for r in routes if 'quotation' in r['path'].lower()]
    
    return {
        "total_routes": len(routes),
        "quotation_routes": quotation_routes,
        "all_routes": routes
    }


@router.post("/fix-quotations-currency")
async def fix_quotations_currency(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    Fix existing quotations that don't have currency set
    Only accessible by superusers
    """
    try:
        # Check how many quotations need fixing
        result = await db.execute(text("""
            SELECT COUNT(*) FROM quotations WHERE currency IS NULL
        """))
        null_count = result.scalar() or 0
        
        # Update quotations with null currency
        await db.execute(text("""
            UPDATE quotations 
            SET currency = 'THB' 
            WHERE currency IS NULL
        """))
        
        await db.commit()
        
        return {
            "status": "success",
            "message": f"Fixed {null_count} quotations with missing currency",
            "quotations_updated": null_count
        }
    except Exception as e:
        logger.error(f"Error fixing quotations currency: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fix quotations currency: {str(e)}"
        )