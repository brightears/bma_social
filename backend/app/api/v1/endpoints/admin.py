from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, inspect
import logging
from typing import Dict, List, Any

from app.models import User
from app.models.base import Base
from app.api.v1.dependencies import get_db, get_current_superuser
from app.api.v1.dependencies.database import get_engine

router = APIRouter()
logger = logging.getLogger(__name__)


def get_column_type_sql(column) -> str:
    """Convert SQLAlchemy column type to PostgreSQL SQL type"""
    from sqlalchemy import String, Integer, Numeric, Text, Boolean, DateTime, Date, Time, JSON, Enum
    from sqlalchemy.dialects.postgresql import UUID
    
    col_type = column.type
    
    if isinstance(col_type, String):
        length = getattr(col_type, 'length', None)
        return f"VARCHAR({length})" if length else "VARCHAR"
    elif isinstance(col_type, Integer):
        return "INTEGER"
    elif isinstance(col_type, Numeric):
        precision = getattr(col_type, 'precision', None)
        scale = getattr(col_type, 'scale', None)
        if precision and scale:
            return f"NUMERIC({precision}, {scale})"
        return "NUMERIC"
    elif isinstance(col_type, Text):
        return "TEXT"
    elif isinstance(col_type, Boolean):
        return "BOOLEAN"
    elif isinstance(col_type, DateTime):
        return "TIMESTAMP WITH TIME ZONE"
    elif isinstance(col_type, Date):
        return "DATE"
    elif isinstance(col_type, Time):
        return "TIME"
    elif isinstance(col_type, JSON):
        return "JSON"
    elif isinstance(col_type, UUID):
        return "UUID"
    elif isinstance(col_type, Enum):
        # For Enum types, we'll use VARCHAR to avoid complexity with PostgreSQL enums
        return "VARCHAR"
    else:
        # Default fallback
        return str(col_type)


async def check_and_add_missing_columns(db: AsyncSession, table_name: str, model_class) -> List[str]:
    """Check and add missing columns for a specific table"""
    missing_columns_added = []
    
    # Get existing columns from database
    result = await db.execute(text(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = '{table_name}'
    """))
    existing_columns = {row[0] for row in result.fetchall()}
    
    # Get columns from SQLAlchemy model
    mapper = inspect(model_class)
    
    for column in mapper.columns:
        column_name = column.name
        
        if column_name not in existing_columns:
            # Determine SQL type
            sql_type = get_column_type_sql(column)
            
            # Build ALTER TABLE statement
            alter_stmt = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {sql_type}"
            
            # Add default value if specified
            if column.default is not None:
                if hasattr(column.default, 'arg'):
                    default_value = column.default.arg
                    if isinstance(default_value, str):
                        alter_stmt += f" DEFAULT '{default_value}'"
                    else:
                        alter_stmt += f" DEFAULT {default_value}"
            
            # For NOT NULL columns, we need to handle existing rows
            if not column.nullable and column.default is None:
                # Add column as nullable first
                try:
                    await db.execute(text(alter_stmt))
                    await db.commit()
                    
                    # Set a default value for existing rows
                    default_val = "''" if "VARCHAR" in sql_type or "TEXT" in sql_type else "0"
                    await db.execute(text(f"UPDATE {table_name} SET {column_name} = {default_val} WHERE {column_name} IS NULL"))
                    await db.commit()
                    
                    # Then add NOT NULL constraint
                    await db.execute(text(f"ALTER TABLE {table_name} ALTER COLUMN {column_name} SET NOT NULL"))
                    await db.commit()
                    
                    missing_columns_added.append(f"{table_name}.{column_name}")
                    logger.info(f"Added missing column {column_name} to {table_name} table")
                except Exception as e:
                    logger.error(f"Failed to add column {column_name} to {table_name}: {e}")
                    await db.rollback()
            else:
                # Add NOT NULL constraint if specified
                if not column.nullable:
                    alter_stmt += " NOT NULL"
                
                try:
                    await db.execute(text(alter_stmt))
                    missing_columns_added.append(f"{table_name}.{column_name}")
                    logger.info(f"Added missing column {column_name} to {table_name} table")
                except Exception as e:
                    logger.error(f"Failed to add column {column_name} to {table_name}: {e}")
    
    return missing_columns_added


@router.post("/sync-database")
async def sync_database(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    Sync database schema - creates any missing tables and adds missing columns
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
        
        # Check and add missing columns
        missing_columns_added = []
        
        # Import models to check for missing columns
        try:
            from app.models import Quotation, QuotationTemplate, Customer
            
            # Check quotations table
            if 'quotations' in tables:
                columns_added = await check_and_add_missing_columns(db, 'quotations', Quotation)
                missing_columns_added.extend(columns_added)
            
            # Check quotation_templates table  
            if 'quotation_templates' in tables:
                columns_added = await check_and_add_missing_columns(db, 'quotation_templates', QuotationTemplate)
                missing_columns_added.extend(columns_added)
                
            # Check customers table
            if 'customers' in tables:
                columns_added = await check_and_add_missing_columns(db, 'customers', Customer)
                missing_columns_added.extend(columns_added)
                
        except ImportError as e:
            logger.warning(f"Could not import models for column checking: {e}")
        
        # Commit the schema changes
        await db.commit()
        
        # Apply any necessary data migrations
        # Set default currency for existing quotations (in case any have NULL)
        try:
            await db.execute(text("""
                UPDATE quotations 
                SET currency = 'THB' 
                WHERE currency IS NULL
            """))
            await db.commit()
        except Exception as e:
            # This might fail if the column was just added with NOT NULL constraint
            # and default value, which is fine
            logger.debug(f"Currency update skipped: {e}")
        
        logger.info(f"Database sync completed. Tables: {tables}, Missing columns added: {missing_columns_added}")
        
        return {
            "status": "success",
            "message": "Database schema synchronized",
            "tables": tables,
            "tables_count": len(tables),
            "missing_columns_added": missing_columns_added
        }
    except Exception as e:
        logger.error(f"Error syncing database: {e}")
        await db.rollback()
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


@router.get("/check-table-columns/{table_name}")
async def check_table_columns(
    table_name: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    Check columns for a specific table comparing database vs model
    Only accessible by superusers
    """
    try:
        # Get columns from database
        result = await db.execute(text("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' 
            AND table_name = :table_name
            ORDER BY ordinal_position;
        """), {"table_name": table_name})
        
        db_columns = {}
        for row in result.fetchall():
            db_columns[row[0]] = {
                "type": row[1],
                "nullable": row[2] == 'YES',
                "default": row[3]
            }
        
        # Try to get model columns
        model_columns = {}
        model_found = False
        
        try:
            if table_name == "quotations":
                from app.models import Quotation
                model_class = Quotation
                model_found = True
            elif table_name == "quotation_templates":
                from app.models import QuotationTemplate
                model_class = QuotationTemplate
                model_found = True
            elif table_name == "customers":
                from app.models import Customer
                model_class = Customer
                model_found = True
            elif table_name == "users":
                from app.models import User as UserModel
                model_class = UserModel
                model_found = True
                
            if model_found:
                mapper = inspect(model_class)
                for column in mapper.columns:
                    model_columns[column.name] = {
                        "type": str(column.type),
                        "nullable": column.nullable,
                        "default": str(column.default.arg) if column.default else None
                    }
        except Exception as e:
            logger.warning(f"Could not inspect model for {table_name}: {e}")
        
        # Find differences
        missing_in_db = set(model_columns.keys()) - set(db_columns.keys())
        missing_in_model = set(db_columns.keys()) - set(model_columns.keys())
        
        return {
            "table_name": table_name,
            "database_columns": db_columns,
            "model_columns": model_columns,
            "model_found": model_found,
            "missing_in_database": list(missing_in_db),
            "missing_in_model": list(missing_in_model),
            "total_db_columns": len(db_columns),
            "total_model_columns": len(model_columns)
        }
    except Exception as e:
        logger.error(f"Error checking table columns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check table columns: {str(e)}"
        )