"""
Database initialization script
Creates all tables and adds initial data
"""

import asyncio
import logging
from datetime import datetime
from sqlalchemy import text
from database.connection import engine, get_db_session, db_manager
from database.models import *
from config.settings import settings

logger = logging.getLogger(__name__)

async def create_tables():
    """Create all database tables"""
    try:
        await db_manager.create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise

async def create_extensions():
    """Create PostgreSQL extensions if needed"""
    try:
        async with get_db_session() as session:
            # Enable UUID extension
            await session.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
            await session.commit()
            logger.info("PostgreSQL extensions created")
    except Exception as e:
        logger.error(f"Failed to create extensions: {e}")
        raise

async def create_initial_data():
    """Create initial data for the application"""
    try:
        async with get_db_session() as session:
            # Check if we already have data
            result = await session.execute(text("SELECT COUNT(*) FROM projects"))
            count = result.scalar()
            
            if count > 0:
                logger.info("Initial data already exists, skipping creation")
                return
            
            # Create a demo project
            demo_project = Project(
                name="Demo AI Video Project",
                description="Sample project to demonstrate the AI video generation workflow",
                status=ProjectStatus.CREATED,
                current_stage=WorkflowStage.INPUT,
                settings={
                    "video_format": "mp4",
                    "resolution": "1080p",
                    "aspect_ratio": "9:16",
                    "target_duration": 60
                },
                metadata={
                    "created_by": "system",
                    "demo": True
                }
            )
            
            session.add(demo_project)
            await session.commit()
            await session.refresh(demo_project)
            
            logger.info(f"Created demo project: {demo_project.id}")
            
            # Create initial workflow stages data
            workflow_info = [
                ("INPUT", "Initial script upload and processing"),
                ("SCREENPLAY_GENERATION", "AI-powered screenplay generation using multiple LLMs"),
                ("SHOT_DIVISION", "Automatic shot division for vertical video format"),
                ("CHARACTER_DESIGN", "Character extraction and design generation"),
                ("SCENE_GENERATION", "Scene image generation using Midjourney"),
                ("VIDEO_GENERATION", "Final video generation using Kling AI"),
                ("COMPLETED", "Project completed and ready for delivery")
            ]
            
            # Log workflow stages (for reference)
            for stage, description in workflow_info:
                logger.info(f"Workflow stage: {stage} - {description}")
            
            logger.info("Initial data created successfully")
            
    except Exception as e:
        logger.error(f"Failed to create initial data: {e}")
        raise

async def create_indexes():
    """Create additional database indexes for performance"""
    try:
        async with get_db_session() as session:
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)",
                "CREATE INDEX IF NOT EXISTS idx_projects_stage ON projects(current_stage)",
                "CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_screenplays_project_id ON screenplays(project_id)",
                "CREATE INDEX IF NOT EXISTS idx_screenplays_version ON screenplays(project_id, version)",
                "CREATE INDEX IF NOT EXISTS idx_characters_project_id ON characters(project_id)",
                "CREATE INDEX IF NOT EXISTS idx_shots_division_id ON shots(shot_division_id)",
                "CREATE INDEX IF NOT EXISTS idx_shots_shot_number ON shots(shot_division_id, shot_number)",
                "CREATE INDEX IF NOT EXISTS idx_approvals_project_id ON approval_requests(project_id)",
                "CREATE INDEX IF NOT EXISTS idx_approvals_status ON approval_requests(status)",
                "CREATE INDEX IF NOT EXISTS idx_approvals_assigned_to ON approval_requests(assigned_to)",
                "CREATE INDEX IF NOT EXISTS idx_exports_project_id ON data_exports(project_id)",
                "CREATE INDEX IF NOT EXISTS idx_exports_created_at ON data_exports(created_at)"
            ]
            
            for index_sql in indexes:
                await session.execute(text(index_sql))
            
            await session.commit()
            logger.info("Database indexes created successfully")
            
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")
        raise

async def verify_database():
    """Verify database setup is working correctly"""
    try:
        # Test basic connectivity
        is_connected = await db_manager.check_connection()
        if not is_connected:
            raise Exception("Database connection failed")
        
        # Get table information
        table_info = await db_manager.get_table_info()
        logger.info(f"Database verification successful: {table_info['count']} tables found")
        
        # Test a simple query
        async with get_db_session() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM projects"))
            count = result.scalar()
            logger.info(f"Projects table contains {count} records")
        
        logger.info("Database verification completed successfully")
        
    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        raise

async def main():
    """Main initialization function"""
    logger.info("Starting database initialization...")
    
    try:
        # Step 1: Create extensions
        await create_extensions()
        
        # Step 2: Create all tables
        await create_tables()
        
        # Step 3: Create indexes
        await create_indexes()
        
        # Step 4: Create initial data
        await create_initial_data()
        
        # Step 5: Verify everything is working
        await verify_database()
        
        logger.info("Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    finally:
        # Cleanup
        if engine:
            await engine.dispose()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the initialization
    asyncio.run(main())