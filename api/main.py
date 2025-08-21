from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import uuid
import shutil
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our services
from services.file_processor import FileProcessor
from services.llm_service import LLMService

# --- In-memory project store for demo (replace with DB in prod) ---
PROJECTS: Dict[str, Dict] = {}
UPLOAD_DIR = "uploads"
RESULTS_DIR = "results"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

app = FastAPI()

# Initialize LLM service
llm_service = LLMService()

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Templates ---
templates = Jinja2Templates(directory="frontend/templates")

# --- Models ---
class ProjectCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectStatusResponse(BaseModel):
    project_id: str
    status: str
    checkpoint: Optional[str] = None
    error: Optional[str] = None

class FileTextResponse(BaseModel):
    project_id: str
    filename: str
    text_content: str
    file_info: dict
    success: bool
    error: Optional[str] = None

class GenerateScreenplayRequest(BaseModel):
    script_text: str
    agent: str = "openai"

class GenerateScreenplayResponse(BaseModel):
    project_id: str
    screenplay: str
    agent_used: str
    generated_at: str
    success: bool
    error: Optional[str] = None

# --- Frontend Routes ---
@app.get("/", response_class=HTMLResponse)
async def get_frontend(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- File Upload Endpoint ---
@app.post("/upload-script/")
async def upload_script(file: UploadFile = File(...)):
    # Allow .doc, .docx, .pdf, and .txt files
    allowed_extensions = ('.txt', '.md', '.rtf', '.doc', '.docx', '.pdf')
    if not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(
            status_code=400, 
            detail=f"Only these file types are allowed: {', '.join(allowed_extensions)}"
        )
    
    project_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{project_id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Get file information
    file_info = FileProcessor.get_file_info(file_path)
    
    PROJECTS[project_id] = {
        "id": project_id,
        "name": file.filename,
        "status": "uploaded",
        "file_path": file_path,
        "file_info": file_info,
        "checkpoint": "input",
        "result_path": None,
        "error": None
    }
    
    return {"project_id": project_id, "filename": file.filename, "file_info": file_info}

# --- Extract Text from Uploaded File ---
@app.get("/extract-text/{project_id}", response_model=FileTextResponse)
async def extract_text(project_id: str):
    """Extract text content from an uploaded file."""
    project = PROJECTS.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    
    if not project.get("file_path"):
        raise HTTPException(status_code=400, detail="No file uploaded for this project.")
    
    try:
        # Extract text using our file processor
        text_content = FileProcessor.extract_text(project["file_path"])
        
        if text_content is None:
            return FileTextResponse(
                project_id=project_id,
                filename=project["name"],
                text_content="",
                file_info=project.get("file_info", {}),
                success=False,
                error="Failed to extract text from file"
            )
        
        return FileTextResponse(
            project_id=project_id,
            filename=project["name"],
            text_content=text_content,
            file_info=project.get("file_info", {}),
            success=True
        )
        
    except Exception as e:
        return FileTextResponse(
            project_id=project_id,
            filename=project["name"],
            text_content="",
            file_info=project.get("file_info", {}),
            success=False,
            error=str(e)
        )

# --- Generate Screenplay Endpoint ---
@app.post("/generate-screenplay/{project_id}", response_model=GenerateScreenplayResponse)
async def generate_screenplay(project_id: str, req: GenerateScreenplayRequest):
    """Generate a professionally formatted screenplay using real LLM APIs."""
    project = PROJECTS.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    
    try:
        # Use the LLM service to generate the screenplay
        result = await llm_service.generate_screenplay(req.script_text, req.agent)
        
        # Store the generated screenplay in project
        project["screenplay"] = result["screenplay"]
        project["screenplay_agent"] = result["agent_used"]
        project["screenplay_generated_at"] = result["generated_at"]
        project["screenplay_success"] = result["success"]
        if not result["success"]:
            project["screenplay_error"] = result.get("error")
        
        return GenerateScreenplayResponse(
            project_id=project_id,
            screenplay=result["screenplay"],
            agent_used=result["agent_used"],
            generated_at=result["generated_at"],
            success=result["success"],
            error=result.get("error")
        )
        
    except Exception as e:
        return GenerateScreenplayResponse(
            project_id=project_id,
            screenplay="",
            agent_used=req.agent,
            generated_at=datetime.now().isoformat(),
            success=False,
            error=str(e)
        )

# --- Project Creation/Management ---
@app.post("/projects/", response_model=ProjectStatusResponse)
async def create_project(req: ProjectCreateRequest):
    project_id = str(uuid.uuid4())
    PROJECTS[project_id] = {
        "id": project_id,
        "name": req.name,
        "description": req.description,
        "status": "created",
        "checkpoint": "input",
        "file_path": None,
        "result_path": None,
        "error": None
    }
    return ProjectStatusResponse(project_id=project_id, status="created")

@app.get("/projects/{project_id}", response_model=ProjectStatusResponse)
async def get_project_status(project_id: str):
    project = PROJECTS.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return ProjectStatusResponse(
        project_id=project_id,
        status=project["status"],
        checkpoint=project.get("checkpoint"),
        error=project.get("error")
    )

@app.get("/projects/", response_model=List[ProjectStatusResponse])
async def list_projects():
    return [ProjectStatusResponse(
        project_id=p["id"],
        status=p["status"],
        checkpoint=p.get("checkpoint"),
        error=p.get("error")
    ) for p in PROJECTS.values()]

# --- Webhook for Human Approval ---
@app.post("/webhook/approval/{project_id}")
async def webhook_approval(project_id: str, request: Request):
    project = PROJECTS.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    data = await request.json()
    approved = data.get("approved")
    checkpoint = data.get("checkpoint")
    if approved:
        project["checkpoint"] = checkpoint
        project["status"] = "approved"
    else:
        project["status"] = "paused"
    return {"status": project["status"], "checkpoint": project["checkpoint"]}

# --- WebSocket for Real-Time Updates ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, project_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[project_id] = websocket

    def disconnect(self, project_id: str):
        self.active_connections.pop(project_id, None)

    async def send_update(self, project_id: str, message: str):
        ws = self.active_connections.get(project_id)
        if ws:
            await ws.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    await manager.connect(project_id, websocket)
    try:
        while True:
            await asyncio.sleep(10)  # Keep alive
    except WebSocketDisconnect:
        manager.disconnect(project_id)

# --- Status Checking Endpoint ---
@app.get("/status/{project_id}", response_model=ProjectStatusResponse)
async def status(project_id: str):
    project = PROJECTS.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return ProjectStatusResponse(
        project_id=project_id,
        status=project["status"],
        checkpoint=project.get("checkpoint"),
        error=project.get("error")
    )

# --- Download Endpoints ---
@app.get("/download/{project_id}")
async def download_result(project_id: str):
    project = PROJECTS.get(project_id)
    if not project or not project.get("result_path"):
        raise HTTPException(status_code=404, detail="Result not found.")
    return FileResponse(project["result_path"], filename=os.path.basename(project["result_path"]))

# --- Error Handling ---
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    return JSONResponse(status_code=500, content={"detail": str(exc)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
