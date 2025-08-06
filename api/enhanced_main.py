from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
import asyncio
import uuid
from datetime import datetime
import logging

# Core imports
from core.models import *
from core.schemas import *
from core.exceptions import *
from core.utils import generate_unique_id, get_utc_now
from config.settings import settings

# Agent imports
from agents.screenplay.openai_screenplay_agent import OpenAIScreenplayAgent
from agents.screenplay.claude_screenplay_agent import ClaudeScreenplayAgent
from agents.screenplay.gemini_screenplay_agent import GeminiScreenplayAgent
from agents.screenplay.screenplay_merger_agent import ScreenplayMergerAgent
from agents.shot_division.openai_shot_division_agent import OpenAIShotDivisionAgent
from agents.dialogue_extraction_agent import DialogueExtractionAgent

# Service imports
from services.google_docs_service import GoogleDocsService
from services.google_sheets_service import GoogleSheetsService
from services.piapi_service import PiAPIService
from services.gotohuman_service import GoToHumanService

# Database imports
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
db_client: Optional[AsyncIOMotorClient] = None
redis_client: Optional[redis.Redis] = None
app_state = {"initialized": False}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    global db_client, redis_client
    
    try:
        # Initialize MongoDB
        db_client = AsyncIOMotorClient(settings.mongodb_uri)
        await db_client.admin.command('ping')
        logger.info("MongoDB connected successfully")
        
        # Initialize Redis
        redis_client = redis.from_url(settings.redis_url)
        await redis_client.ping()
        logger.info("Redis connected successfully")
        
        app_state["initialized"] = True
        logger.info("Application initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    
    yield
    
    # Shutdown
    if db_client:
        db_client.close()
    if redis_client:
        await redis_client.close()
    
    logger.info("Application shutdown complete")

# Initialize FastAPI app
app = FastAPI(
    title="AI Video Generator API",
    description="Production-ready API for AI-powered video generation from scripts",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Dependency injection
async def get_database():
    """Get database dependency"""
    if not db_client:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return db_client[settings.mongodb_db_name]

async def get_redis():
    """Get Redis dependency"""
    if not redis_client:
        raise HTTPException(status_code=500, detail="Redis not initialized")
    return redis_client

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify authentication token (implement your auth logic)"""
    # Implement your authentication logic here
    # For now, accept any token for development
    return {"user_id": "demo_user"}

# Error handlers
@app.exception_handler(AIVideoGeneratorException)
async def custom_exception_handler(request, exc: AIVideoGeneratorException):
    return JSONResponse(
        status_code=400,
        content=create_error_response(exc)
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "message": "Internal server error",
                "code": "INTERNAL_ERROR",
                "type": "InternalError"
            }
        }
    )

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": get_utc_now(),
        "version": "1.0.0",
        "initialized": app_state["initialized"]
    }

# Project Management Endpoints
@app.post("/api/v1/projects", response_model=APIResponse)
async def create_project(
    request: ProjectCreateRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_database),
    user = Depends(verify_token)
):
    """Create a new video generation project"""
    try:
        project_id = generate_unique_id()
        
        project = Project(
            id=project_id,
            name=request.name,
            description=request.description,
            user_id=request.user_id,
            settings=request.settings
        )
        
        # Save to database
        result = await db.projects.insert_one(project.dict(by_alias=True))
        
        # Initialize pipeline state
        pipeline_state = PipelineState(
            project_id=project_id,
            current_stage=WorkflowStage.SCRIPT_INPUT
        )
        await db.pipeline_states.insert_one(pipeline_state.dict(by_alias=True))
        
        return APIResponse(
            success=True,
            message="Project created successfully",
            data={
                "project_id": project_id,
                "status": project.status,
                "current_stage": project.current_stage
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/projects/{project_id}", response_model=ProjectStatusResponse)
async def get_project_status(
    project_id: str,
    db = Depends(get_database),
    user = Depends(verify_token)
):
    """Get project status and current stage"""
    try:
        project = await db.projects.find_one({"_id": project_id})
        if not project:
            raise ProjectNotFound(project_id)
        
        pipeline_state = await db.pipeline_states.find_one({"project_id": project_id})
        
        # Calculate progress percentage
        stages = [stage.value for stage in WorkflowStage]
        current_stage = pipeline_state.get("current_stage") if pipeline_state else WorkflowStage.SCRIPT_INPUT
        progress = (stages.index(current_stage) / len(stages)) * 100
        
        return ProjectStatusResponse(
            project_id=project_id,
            status=ProjectStatus(project.get("status", "created")),
            current_stage=WorkflowStage(current_stage),
            progress_percentage=progress,
            stage_data=pipeline_state.get("stage_data", {}) if pipeline_state else {},
            error_message=project.get("error_message")
        )
        
    except ProjectNotFound:
        raise
    except Exception as e:
        logger.error(f"Failed to get project status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/projects", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 50,
    db = Depends(get_database),
    user = Depends(verify_token)
):
    """List user projects"""
    try:
        cursor = db.projects.find({}).skip(skip).limit(limit)
        projects = []
        
        async for project in cursor:
            projects.append(ProjectResponse(
                id=project["_id"],
                name=project["name"],
                status=ProjectStatus(project.get("status", "created")),
                current_stage=WorkflowStage(project.get("current_stage", "script_input")),
                created_at=project["created_at"],
                updated_at=project["updated_at"]
            ))
        
        return projects
        
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Script Upload and Processing
@app.post("/api/v1/projects/{project_id}/script", response_model=APIResponse)
async def upload_script(
    project_id: str,
    background_tasks: BackgroundTasks,
    script_content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db = Depends(get_database),
    user = Depends(verify_token)
):
    """Upload script content or file to project"""
    try:
        project = await db.projects.find_one({"_id": project_id})
        if not project:
            raise ProjectNotFound(project_id)
        
        content = script_content
        
        # If file uploaded, read content
        if file and not content:
            if file.content_type not in ["text/plain", "text/markdown"]:
                raise InvalidFileFormat(file.filename, ["txt", "md"])
            
            content = (await file.read()).decode("utf-8")
        
        if not content:
            raise HTTPException(status_code=400, detail="No script content provided")
        
        if len(content) < 100:
            raise HTTPException(status_code=400, detail="Script content too short")
        
        # Update project with script content
        await db.projects.update_one(
            {"_id": project_id},
            {
                "$set": {
                    "script_content": content,
                    "current_stage": WorkflowStage.SCRIPT_INPUT.value,
                    "updated_at": get_utc_now()
                }
            }
        )
        
        # Update pipeline state
        await db.pipeline_states.update_one(
            {"project_id": project_id},
            {
                "$set": {
                    "stage_data.script_content": content,
                    "updated_at": get_utc_now()
                }
            }
        )
        
        return APIResponse(
            success=True,
            message="Script uploaded successfully",
            data={"content_length": len(content)}
        )
        
    except (ProjectNotFound, InvalidFileFormat):
        raise
    except Exception as e:
        logger.error(f"Failed to upload script: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Screenplay Generation Endpoints
@app.post("/api/v1/projects/{project_id}/screenplay/generate", response_model=APIResponse)
async def generate_screenplay(
    project_id: str,
    request: ScreenplayGenerationRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_database),
    user = Depends(verify_token)
):
    """Generate screenplay using multiple AI models"""
    try:
        project = await db.projects.find_one({"_id": project_id})
        if not project:
            raise ProjectNotFound(project_id)
        
        script_content = project.get("script_content")
        if not script_content:
            raise HTTPException(status_code=400, detail="No script content found. Upload script first.")
        
        # Start background task for screenplay generation
        background_tasks.add_task(
            process_screenplay_generation,
            project_id,
            script_content,
            request.use_providers,
            request.custom_prompt,
            db
        )
        
        return APIResponse(
            success=True,
            message="Screenplay generation started",
            data={"project_id": project_id, "providers": request.use_providers}
        )
        
    except ProjectNotFound:
        raise
    except Exception as e:
        logger.error(f"Failed to start screenplay generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/projects/{project_id}/screenplay", response_model=ScreenplayStatusResponse)
async def get_screenplay_status(
    project_id: str,
    db = Depends(get_database),
    user = Depends(verify_token)
):
    """Get screenplay generation status"""
    try:
        screenplay = await db.screenplays.find_one({"project_id": project_id})
        if not screenplay:
            return ScreenplayStatusResponse(
                screenplay_id="",
                project_id=project_id,
                processing_status="not_started"
            )
        
        # Calculate confidence scores
        confidence_scores = {}
        for version in screenplay.get("versions", []):
            provider = version.get("provider")
            score = version.get("confidence_score", 0.0)
            if provider:
                confidence_scores[provider] = score
        
        return ScreenplayStatusResponse(
            screenplay_id=screenplay["_id"],
            project_id=project_id,
            versions_count=len(screenplay.get("versions", [])),
            merged_available=bool(screenplay.get("merged_content")),
            google_doc_url=screenplay.get("google_doc_url"),
            processing_status="completed" if screenplay.get("merged_content") else "processing",
            confidence_scores=confidence_scores
        )
        
    except Exception as e:
        logger.error(f"Failed to get screenplay status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Shot Division Endpoints
@app.post("/api/v1/projects/{project_id}/shots/generate", response_model=APIResponse)
async def generate_shot_division(
    project_id: str,
    request: ShotDivisionRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_database),
    user = Depends(verify_token)
):
    """Generate shot division from screenplay"""
    try:
        # Verify screenplay exists
        screenplay = await db.screenplays.find_one({"project_id": project_id})
        if not screenplay or not screenplay.get("merged_content"):
            raise HTTPException(status_code=400, detail="No merged screenplay found. Generate screenplay first.")
        
        # Start background task
        background_tasks.add_task(
            process_shot_division,
            project_id,
            request.screenplay_id,
            screenplay.get("merged_content"),
            request.target_duration,
            request.shot_duration,
            request.vertical_format,
            db
        )
        
        return APIResponse(
            success=True,
            message="Shot division generation started",
            data={"project_id": project_id, "target_duration": request.target_duration}
        )
        
    except Exception as e:
        logger.error(f"Failed to start shot division: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/projects/{project_id}/shots", response_model=ShotDivisionStatusResponse)
async def get_shot_division_status(
    project_id: str,
    db = Depends(get_database),
    user = Depends(verify_token)
):
    """Get shot division status"""
    try:
        shot_division = await db.shot_divisions.find_one({"project_id": project_id})
        if not shot_division:
            return ShotDivisionStatusResponse(
                shot_division_id="",
                project_id=project_id
            )
        
        shots = shot_division.get("shots", [])
        completed_shots = len([s for s in shots if s.get("selected_image_url")])
        
        return ShotDivisionStatusResponse(
            shot_division_id=shot_division["_id"],
            project_id=project_id,
            total_shots=len(shots),
            completed_shots=completed_shots,
            estimated_duration=shot_division.get("estimated_duration", 0.0),
            google_sheet_url=shot_division.get("google_sheet_url"),
            human_approved=shot_division.get("human_approved", False)
        )
        
    except Exception as e:
        logger.error(f"Failed to get shot division status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task functions
async def process_screenplay_generation(
    project_id: str,
    script_content: str,
    providers: List[str],
    custom_prompt: Optional[str],
    db
):
    """Background task for screenplay generation"""
    try:
        # Initialize agents
        agents = {}
        if "openai" in providers:
            agents["openai"] = OpenAIScreenplayAgent(
                openai_api_key=settings.openai_api_key
            )
        if "claude" in providers:
            agents["claude"] = ClaudeScreenplayAgent(
                anthropic_api_key=settings.anthropic_api_key
            )
        if "gemini" in providers:
            agents["gemini"] = GeminiScreenplayAgent(
                google_api_key=settings.google_api_key
            )
        
        # Process in parallel
        tasks = []
        for provider, agent in agents.items():
            tasks.append(agent.process(script_content, custom_prompt))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect successful results
        versions = []
        for i, result in enumerate(results):
            provider = list(agents.keys())[i]
            if isinstance(result, Exception):
                logger.error(f"Provider {provider} failed: {result}")
                continue
            
            versions.append({
                "provider": provider,
                "content": result.get("content", ""),
                "confidence_score": 0.85,  # Default score
                "processing_time": result.get("processing_time", 0),
                "tokens_used": result.get("tokens_used", 0),
                "success": True
            })
        
        if not versions:
            raise AgentProcessingError("ScreenplayGeneration", "All providers failed")
        
        # Merge versions
        merger = ScreenplayMergerAgent(openai_api_key=settings.openai_api_key)
        merged_result = await merger.process(script_content, versions)
        
        # Save screenplay to database
        screenplay_id = generate_unique_id()
        screenplay = Screenplay(
            id=screenplay_id,
            project_id=project_id,
            versions=versions,
            merged_content=merged_result.get("content", ""),
            approved_content=merged_result.get("content", "")
        )
        
        await db.screenplays.insert_one(screenplay.dict(by_alias=True))
        
        # Update project stage
        await db.projects.update_one(
            {"_id": project_id},
            {
                "$set": {
                    "current_stage": WorkflowStage.SCREENPLAY_GENERATION.value,
                    "status": ProjectStatus.PROCESSING.value,
                    "updated_at": get_utc_now()
                }
            }
        )
        
        logger.info(f"Screenplay generation completed for project {project_id}")
        
    except Exception as e:
        logger.error(f"Screenplay generation failed for project {project_id}: {e}")
        await db.projects.update_one(
            {"_id": project_id},
            {
                "$set": {
                    "status": ProjectStatus.FAILED.value,
                    "error_message": str(e),
                    "updated_at": get_utc_now()
                }
            }
        )

async def process_shot_division(
    project_id: str,
    screenplay_id: str,
    screenplay_content: str,
    target_duration: float,
    shot_duration: float,
    vertical_format: bool,
    db
):
    """Background task for shot division"""
    try:
        # Initialize shot division agent
        agent = OpenAIShotDivisionAgent(openai_api_key=settings.openai_api_key)
        
        # Process shot division
        result = await agent.process(
            screenplay_content,
            target_duration,
            shot_duration,
            vertical_format
        )
        
        if not result.get("success"):
            raise AgentProcessingError("ShotDivision", "Shot division processing failed")
        
        # Save to database
        shot_division_id = generate_unique_id()
        shot_division = ShotDivision(
            id=shot_division_id,
            project_id=project_id,
            screenplay_id=screenplay_id,
            shots=result.get("shots", []),
            total_shots=result.get("total_shots", 0),
            estimated_duration=result.get("estimated_duration", 0.0),
            vertical_format=vertical_format
        )
        
        await db.shot_divisions.insert_one(shot_division.dict(by_alias=True))
        
        # Update project stage
        await db.projects.update_one(
            {"_id": project_id},
            {
                "$set": {
                    "current_stage": WorkflowStage.SHOT_DIVISION.value,
                    "updated_at": get_utc_now()
                }
            }
        )
        
        logger.info(f"Shot division completed for project {project_id}: {result.get('total_shots')} shots")
        
    except Exception as e:
        logger.error(f"Shot division failed for project {project_id}: {e}")
        await db.projects.update_one(
            {"_id": project_id},
            {
                "$set": {
                    "status": ProjectStatus.FAILED.value,
                    "error_message": str(e),
                    "updated_at": get_utc_now()
                }
            }
        )

# WebSocket for real-time updates
@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket, project_id: str):
    """WebSocket endpoint for real-time project updates"""
    await websocket.accept()
    
    try:
        # Subscribe to project updates
        while True:
            # In production, you'd implement proper pub/sub with Redis
            await asyncio.sleep(5)
            
            # Send periodic updates
            await websocket.send_json({
                "type": "ping",
                "project_id": project_id,
                "timestamp": get_utc_now().isoformat()
            })
    except Exception as e:
        logger.error(f"WebSocket error for project {project_id}: {e}")
    finally:
        await websocket.close()

# Additional endpoints would include:
# - Character extraction
# - Production planning
# - Scene generation
# - Video generation
# - Human approval workflows
# - Webhook handling

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "enhanced_main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )