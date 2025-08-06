"""
PostgreSQL database connection and session management
Async SQLAlchemy setup with connection pooling
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator
from config.settings import settings

logger = logging.getLogger(__name__)

# Database engine configuration
DATABASE_URL = f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"

# Create async engine with optimized settings
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.debug,  # Log SQL queries in debug mode
    future=True,
    pool_size=20,  # Connection pool size
    max_overflow=30,  # Additional connections beyond pool_size
    pool_pre_ping=True,  # Validate connections before use
    pool_recycle=3600,  # Recycle connections every hour
    connect_args={
        "server_settings": {
            "jit": "off",  # Disable JIT for better connection performance
        },
        "command_timeout": 60,
    }
)

# Create async session factory
async_session_factory = sessionmaker(
    engine, 
    class_=AsyncSession,
    expire_on_commit=False
)

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions
    Automatically handles session lifecycle and rollback on errors
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions
    """
    async with get_db_session() as session:
        yield session

class DatabaseManager:
    """Database management utilities"""
    
    def __init__(self):
        self.engine = engine
        
    async def create_tables(self):
        """Create all database tables"""
        try:
            from .models import Base
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    async def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        try:
            from .models import Base
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            raise
    
    async def check_connection(self) -> bool:
        """Check database connection health"""
        try:
            async with get_db_session() as session:
                result = await session.execute("SELECT 1")
                return result.fetchone()[0] == 1
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    async def get_table_info(self) -> dict:
        """Get information about database tables"""
        try:
            async with get_db_session() as session:
                result = await session.execute("""
                    SELECT 
                        table_name,
                        table_type,
                        table_schema
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """)
                
                tables = []
                for row in result:
                    tables.append({
                        "name": row[0],
                        "type": row[1],
                        "schema": row[2]
                    })
                
                return {"tables": tables, "count": len(tables)}
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            return {"tables": [], "count": 0}

    async def cleanup_old_data(self, days: int = 30):
        """Clean up old data based on retention policy"""
        try:
            async with get_db_session() as session:
                from datetime import datetime, timedelta
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                # Clean up old data exports
                result = await session.execute(
                    "DELETE FROM data_exports WHERE created_at < :cutoff AND download_count = 0",
                    {"cutoff": cutoff_date}
                )
                
                # Clean up old user activities (keep recent ones)
                result = await session.execute(
                    "DELETE FROM user_activities WHERE created_at < :cutoff",
                    {"cutoff": cutoff_date}
                )
                
                await session.commit()
                logger.info(f"Cleaned up old data older than {days} days")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            raise

# Global database manager instance
db_manager = DatabaseManager()

# Database health check
async def health_check() -> dict:
    """Database health check for monitoring"""
    try:
        is_connected = await db_manager.check_connection()
        table_info = await db_manager.get_table_info()
        
        return {
            "database": "postgresql",
            "connected": is_connected,
            "tables_count": table_info["count"],
            "status": "healthy" if is_connected else "unhealthy"
        }
    except Exception as e:
        return {
            "database": "postgresql", 
            "connected": False,
            "error": str(e),
            "status": "unhealthy"
        }