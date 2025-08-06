from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import uuid
import shutil
import asyncio
import json

# --- In-memory project store for demo (replace with DB in prod) ---
PROJECTS: Dict[str, Dict] = {}
UPLOAD_DIR = "uploads"
RESULTS_DIR = "results"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

app = FastAPI()

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class ProjectCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectStatusResponse(BaseModel):
    project_id: str
    status: str
    checkpoint: Optional[str] = None
    error: Optional[str] = None

# --- File Upload Endpoint ---
@app.post("/upload-script/")
async def upload_script(file: UploadFile = File(...)):
    if not file.filename.endswith(('.txt', '.md', '.rtf')):
        raise HTTPException(status_code=400, detail="Only text-based scripts are allowed.")
    project_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{project_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    PROJECTS[project_id] = {
        "id": project_id,
        "name": file.filename,
        "status": "uploaded",
        "file_path": file_path,
        "checkpoint": "input",
        "result_path": None,
        "error": None
    }
    return {"project_id": project_id, "filename": file.filename}

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
