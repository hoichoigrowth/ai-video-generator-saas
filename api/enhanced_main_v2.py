"""
Enhanced FastAPI application with self-hosted services
Replaces Google Docs, Google Sheets, and GoToHuman with PostgreSQL, MinIO, and custom approval system
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, Request, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, UUID4
from typing import List, Dict, Optional, Any
import asyncio
import json
import uuid
import logging
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

# Database and services
from database.connection import get_db_session, db_manager, health_check
from database.models import *
from services.storage_service import storage_service
from services.approval_service import approval_service, ApprovalType, ApprovalPriority
from services.export_service import export_service
from config.settings import settings
from core.exceptions import AIVideoGeneratorException

# Agent imports
from agents.screenplay.screenplay_merger_agent import ScreenplayMergerAgent
from agents.shot_division.shot_merger_agent import ShotMergerAgent
from core.pipeline import VideoGenerationPipeline

logger = logging.getLogger(__name__)

# Startup and shutdown handlers
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    try:
        await db_manager.create_tables()
        await storage_service.initialize()
        await approval_service.initialize()
        logger.info("Application initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Application shutting down")

# FastAPI app with lifespan
app = FastAPI(
    title="AI Video Generator - Self-Hosted",
    description="AI Video Generation SaaS with self-hosted PostgreSQL, MinIO, and custom approval system",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: str
    current_stage: str
    created_at: str
    updated_at: str
    settings: Dict[str, Any]
    metadata: Dict[str, Any]

class ScreenplayUpload(BaseModel):
    project_id: str
    content: str
    version: Optional[int] = 1

class ApprovalRequest(BaseModel):
    project_id: str
    stage: str
    approval_type: str
    title: str
    description: str
    approval_data: Dict[str, Any]
    assigned_to: Optional[str] = None
    priority: Optional[int] = 2
    due_date: Optional[datetime] = None

class ApprovalResponse(BaseModel):
    approval_id: str
    approved: bool
    selected_option: Optional[str] = None
    feedback: Optional[str] = None
    revision_notes: Optional[str] = None

class ExportRequest(BaseModel):
    project_id: str
    export_type: str  # csv, excel, pdf, json
    data_type: str    # shot_division, characters, production_plan, project_summary

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, project_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[project_id] = websocket

    def disconnect(self, project_id: str):
        self.active_connections.pop(project_id, None)

    async def send_update(self, project_id: str, message: str):
        websocket = self.active_connections.get(project_id)
        if websocket:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send websocket message: {e}")
                self.disconnect(project_id)

manager = ConnectionManager()

# Health Check Endpoints
@app.get("/health")
async def health_check_endpoint():
    """Application health check"""
    return await health_check()

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check for all services"""
    health_status = {
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Database health
    db_health = await health_check()
    health_status["services"]["database"] = db_health
    
    # Storage service health
    try:
        await storage_service.initialize()
        health_status["services"]["storage"] = {"status": "healthy", "service": "minio"}
    except Exception as e:
        health_status["services"]["storage"] = {"status": "unhealthy", "error": str(e)}
    
    # Approval service health
    try:
        await approval_service.initialize()
        health_status["services"]["approval"] = {"status": "healthy", "service": "redis"}
    except Exception as e:
        health_status["services"]["approval"] = {"status": "unhealthy", "error": str(e)}
    
    return health_status

# Project Management Endpoints
@app.post("/api/v1/projects", response_model=ProjectResponse)
async def create_project(project_data: ProjectCreate):
    """Create a new AI video generation project"""
    try:
        async with get_db_session() as session:
            project = Project(
                name=project_data.name,
                description=project_data.description,
                settings=project_data.settings,
                status=ProjectStatus.CREATED,
                current_stage=WorkflowStage.INPUT
            )
            
            session.add(project)
            await session.commit()
            await session.refresh(project)
            
            logger.info(f"Created project {project.id}: {project.name}")
            
            return ProjectResponse(
                id=str(project.id),
                name=project.name,
                description=project.description,
                status=project.status.value,
                current_stage=project.current_stage.value,
                created_at=project.created_at.isoformat(),
                updated_at=project.updated_at.isoformat(),
                settings=project.settings or {},
                metadata=project.metadata or {}
            )
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=500, detail=f"Project creation failed: {str(e)}")

@app.get("/api/v1/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """Get project details"""
    try:
        async with get_db_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()
            
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            
            return ProjectResponse(
                id=str(project.id),
                name=project.name,
                description=project.description,
                status=project.status.value,
                current_stage=project.current_stage.value,
                created_at=project.created_at.isoformat(),
                updated_at=project.updated_at.isoformat(),
                settings=project.settings or {},
                metadata=project.metadata or {}
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve project: {str(e)}")

@app.get("/api/v1/projects", response_model=List[ProjectResponse])
async def list_projects(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)):
    """List all projects with pagination"""
    try:
        async with get_db_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Project)
                .order_by(Project.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            projects = result.scalars().all()
            
            return [
                ProjectResponse(
                    id=str(project.id),
                    name=project.name,
                    description=project.description,
                    status=project.status.value,
                    current_stage=project.current_stage.value,
                    created_at=project.created_at.isoformat(),
                    updated_at=project.updated_at.isoformat(),
                    settings=project.settings or {},
                    metadata=project.metadata or {}
                ) for project in projects
            ]
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list projects: {str(e)}")

# File Upload and Storage Endpoints
@app.post("/api/v1/projects/{project_id}/upload-script")
async def upload_script(project_id: str, file: UploadFile = File(...)):
    """Upload initial script file using MinIO storage"""
    try:
        # Validate file
        if not file.filename or not file.filename.lower().endswith(('.txt', '.md', '.rtf', '.doc', '.docx')):
            raise HTTPException(status_code=400, detail="Only text-based script files are allowed")
        
        # Read file content
        content = await file.read()
        
        # Store in MinIO
        storage_result = await storage_service.store_screenplay(
            project_id=project_id,
            screenplay_id=str(uuid.uuid4()),
            content=content.decode('utf-8'),
            version=1
        )
        
        # Update project status
        async with get_db_session() as session:
            from sqlalchemy import update
            await session.execute(
                update(Project)
                .where(Project.id == project_id)
                .values(
                    current_stage=WorkflowStage.SCREENPLAY_GENERATION,
                    status=ProjectStatus.IN_PROGRESS,
                    updated_at=datetime.utcnow()
                )
            )
            await session.commit()
        
        return {
            "message": "Script uploaded successfully",
            "storage_paths": storage_result,
            "next_stage": "screenplay_generation"
        }
        
    except Exception as e:
        logger.error(f"Failed to upload script: {e}")
        raise HTTPException(status_code=500, detail=f"Script upload failed: {str(e)}")

@app.post("/api/v1/projects/{project_id}/screenplay")
async def store_screenplay(project_id: str, screenplay: ScreenplayUpload):
    """Store screenplay content in MinIO with versioning"""
    try:
        # Create screenplay record in database
        async with get_db_session() as session:
            screenplay_record = Screenplay(
                project_id=project_id,
                version=screenplay.version,
                content=screenplay.content,
                is_current_version=True,
                approval_status=ApprovalStatus.PENDING
            )
            
            session.add(screenplay_record)
            await session.commit()
            await session.refresh(screenplay_record)
        
        # Store in MinIO
        storage_result = await storage_service.store_screenplay(
            project_id=project_id,
            screenplay_id=str(screenplay_record.id),
            content=screenplay.content,
            version=screenplay.version
        )
        
        return {
            "screenplay_id": str(screenplay_record.id),
            "version": screenplay.version,
            "storage_paths": storage_result,
            "status": "stored"
        }
        
    except Exception as e:
        logger.error(f"Failed to store screenplay: {e}")
        raise HTTPException(status_code=500, detail=f"Screenplay storage failed: {str(e)}")

# Approval System Endpoints
@app.post("/api/v1/approvals")
async def create_approval_request(approval_request: ApprovalRequest):
    """Create approval request using custom approval system"""
    try:
        approval_id = await approval_service.create_approval_request(
            project_id=approval_request.project_id,
            stage=WorkflowStage(approval_request.stage),
            approval_type=ApprovalType(approval_request.approval_type),
            entity_id=str(uuid.uuid4()),  # Generate entity ID
            title=approval_request.title,
            description=approval_request.description,
            approval_data=approval_request.approval_data,
            assigned_to=approval_request.assigned_to,
            priority=ApprovalPriority(approval_request.priority),
            due_date=approval_request.due_date
        )
        
        # Send WebSocket notification
        await manager.send_update(
            approval_request.project_id,
            json.dumps({
                "type": "approval_requested",
                "approval_id": approval_id,
                "title": approval_request.title
            })
        )
        
        return {"approval_id": approval_id, "status": "created"}
        
    except Exception as e:
        logger.error(f"Failed to create approval request: {e}")
        raise HTTPException(status_code=500, detail=f"Approval creation failed: {str(e)}")

@app.get("/api/v1/approvals/pending")
async def get_pending_approvals(
    user_id: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    approval_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100)
):
    """Get pending approvals with filtering"""
    try:
        approval_type_enum = ApprovalType(approval_type) if approval_type else None
        approvals = await approval_service.get_pending_approvals(
            user_id=user_id,
            project_id=project_id,
            approval_type=approval_type_enum,
            limit=limit
        )
        return approvals
    except Exception as e:
        logger.error(f"Failed to get pending approvals: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get approvals: {str(e)}")

@app.post("/api/v1/approvals/{approval_id}/respond")
async def respond_to_approval(approval_id: str, response: ApprovalResponse):
    """Submit approval response"""
    try:
        result = await approval_service.submit_approval_response(
            approval_id=approval_id,
            user_id=response.user_id if hasattr(response, 'user_id') else "system",
            approved=response.approved,
            selected_option=response.selected_option,
            feedback=response.feedback,
            revision_notes=response.revision_notes
        )
        
        # Send WebSocket notification
        if 'project_id' in result:
            await manager.send_update(
                result['project_id'],
                json.dumps({
                    "type": "approval_response",
                    "approval_id": approval_id,
                    "approved": response.approved
                })
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to respond to approval: {e}")
        raise HTTPException(status_code=500, detail=f"Approval response failed: {str(e)}")

# Export Endpoints (replacing Google Sheets)
@app.post("/api/v1/exports")
async def create_export(export_request: ExportRequest):
    """Create data export (CSV, Excel, PDF)"""
    try:
        if export_request.data_type == "shot_division":
            if export_request.export_type == "csv":
                result = await export_service.export_shot_division_csv(export_request.project_id)
            elif export_request.export_type == "excel":
                result = await export_service.export_shot_division_excel(export_request.project_id)
            else:
                raise HTTPException(status_code=400, detail="Invalid export type for shot division")
                
        elif export_request.data_type == "characters":
            if export_request.export_type == "csv":
                result = await export_service.export_characters_csv(export_request.project_id)
            else:
                raise HTTPException(status_code=400, detail="Invalid export type for characters")
                
        elif export_request.data_type == "production_plan":
            if export_request.export_type == "pdf":
                result = await export_service.export_production_plan_pdf(export_request.project_id)
            else:
                raise HTTPException(status_code=400, detail="Invalid export type for production plan")
                
        elif export_request.data_type == "project_summary":
            if export_request.export_type == "json":
                result = await export_service.export_project_summary_json(export_request.project_id)
            else:
                raise HTTPException(status_code=400, detail="Invalid export type for project summary")
        else:
            raise HTTPException(status_code=400, detail="Invalid data type")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create export: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/api/v1/projects/{project_id}/exports")
async def get_export_history(project_id: str):
    """Get export history for a project"""
    try:
        history = await export_service.get_export_history(project_id)
        return history
    except Exception as e:
        logger.error(f"Failed to get export history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get export history: {str(e)}")

# WebSocket for Real-time Updates
@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """WebSocket endpoint for real-time project updates"""
    await manager.connect(project_id, websocket)
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(30)
            await websocket.ping()
    except WebSocketDisconnect:
        manager.disconnect(project_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(project_id)

# File Download Endpoints
@app.get("/api/v1/files/{file_path:path}")
async def download_file(file_path: str):
    """Download file from MinIO storage"""
    try:
        file_info = await storage_service.get_file_info(file_path)
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Return presigned URL for download
        return {"download_url": file_info["url"], "file_info": file_info}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get file: {e}")
        raise HTTPException(status_code=500, detail=f"File download failed: {str(e)}")

# AI Pipeline Endpoints
@app.post("/api/v1/projects/{project_id}/generate-screenplay")
async def generate_screenplay(project_id: str, background_tasks: BackgroundTasks):
    """Start screenplay generation using multi-LLM consensus"""
    try:
        # Get project
        async with get_db_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()
            
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
        
        # Start pipeline in background
        background_tasks.add_task(run_screenplay_generation, project_id)
        
        return {
            "message": "Screenplay generation started",
            "project_id": project_id,
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start screenplay generation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start generation: {str(e)}")

async def run_screenplay_generation(project_id: str):
    """Background task for screenplay generation"""
    try:
        # Update project status
        async with get_db_session() as session:
            from sqlalchemy import update
            await session.execute(
                update(Project)
                .where(Project.id == project_id)
                .values(
                    current_stage=WorkflowStage.SCREENPLAY_GENERATION,
                    status=ProjectStatus.IN_PROGRESS
                )
            )
            await session.commit()
        
        # Send WebSocket update
        await manager.send_update(
            project_id,
            json.dumps({
                "type": "stage_update",
                "stage": "screenplay_generation",
                "status": "started"
            })
        )
        
        # Initialize screenplay merger agent
        merger = ScreenplayMergerAgent()
        
        # Simulate screenplay generation (replace with actual pipeline)
        await asyncio.sleep(5)  # Simulate processing time
        
        # Create approval request
        await approval_service.create_approval_request(
            project_id=project_id,
            stage=WorkflowStage.SCREENPLAY_GENERATION,
            approval_type=ApprovalType.SCREENPLAY,
            entity_id=str(uuid.uuid4()),
            title="Screenplay Review Required",
            description="Please review the generated screenplay",
            approval_data={"content": "Generated screenplay content..."},
            priority=ApprovalPriority.NORMAL
        )
        
    except Exception as e:
        logger.error(f"Screenplay generation failed: {e}")
        await manager.send_update(
            project_id,
            json.dumps({
                "type": "error",
                "stage": "screenplay_generation",
                "error": str(e)
            })
        )

# Error Handlers
@app.exception_handler(AIVideoGeneratorException)
async def ai_video_generator_exception_handler(request: Request, exc: AIVideoGeneratorException):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "type": "ai_video_generator_error"}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": "server_error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.enhanced_main_v2:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )