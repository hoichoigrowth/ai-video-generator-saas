#!/usr/bin/env python3
"""
AI Video Generator - Complete Application
A modern FastAPI application with frontend serving
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict, List, Optional
import asyncio
import uuid
import json
import os
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Video Generator",
    description="Professional Script-to-Video Generation Platform",
    version="2.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (replace with database in production)
projects_db: Dict[str, dict] = {}
websocket_connections: Dict[str, WebSocket] = {}

# Progress stages
PROGRESS_STAGES = [
    "input",
    "screenplay_formatted", 
    "screenplay_merged",
    "shots_broken",
    "characters_extracted",
    "image_prompts_generated",
    "final"
]

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, project_id: str):
        await websocket.accept()
        self.active_connections[project_id] = websocket
        logger.info(f"WebSocket connected for project: {project_id}")

    def disconnect(self, project_id: str):
        if project_id in self.active_connections:
            del self.active_connections[project_id]
            logger.info(f"WebSocket disconnected for project: {project_id}")

    async def send_update(self, project_id: str, message: dict):
        if project_id in self.active_connections:
            try:
                await self.active_connections[project_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the main dashboard"""
    html_path = Path(__file__).parent / "frontend" / "templates" / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(), status_code=200)
    else:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI Video Generator</title>
            <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@300;400;500;700&display=swap" rel="stylesheet">
            <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@3.4.1/dist/tailwind.min.css" rel="stylesheet">
        </head>
        <body class="bg-white font-['Google_Sans'] min-h-screen">
            <!-- Header -->
            <header class="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div class="flex items-center justify-between h-16">
                        <div class="flex items-center space-x-3">
                            <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                                <span class="material-icons text-white text-xl">smart_display</span>
                            </div>
                            <div>
                                <h1 class="text-xl font-medium text-gray-900">AI Video Generator</h1>
                            </div>
                        </div>
                        <div class="flex items-center space-x-4">
                            <button class="p-2 text-gray-400 hover:text-gray-500 hover:bg-gray-100 rounded-full transition-all">
                                <span class="material-icons text-xl">help_outline</span>
                            </button>
                            <button class="p-2 text-gray-400 hover:text-gray-500 hover:bg-gray-100 rounded-full transition-all">
                                <span class="material-icons text-xl">settings</span>
                            </button>
                            <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                                <span class="text-white text-sm font-medium">U</span>
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            <!-- Main Content -->
            <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <!-- Hero Section -->
                <div class="text-center mb-16">
                    <h2 class="text-5xl font-light text-gray-900 mb-6">
                        Transform scripts into professional videos
                    </h2>
                    <p class="text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
                        Upload your script and let AI create a complete video production pipeline with intelligent character extraction, shot breakdown, and visual generation.
                    </p>
                </div>

                <!-- Project Creation Card -->
                <div class="max-w-2xl mx-auto mb-16">
                    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
                        <div class="mb-8">
                            <h3 class="text-2xl font-normal text-gray-900 mb-2">Create a new project</h3>
                            <p class="text-gray-600">Upload your script and let AI handle the rest</p>
                        </div>

                        <!-- Project Creation Form -->
                        <form id="project-form" class="space-y-6">
                            <div class="google-input-container">
                                <input 
                                    id="project-name" 
                                    type="text" 
                                    required 
                                    class="google-input peer"
                                    placeholder=" "
                                />
                                <label for="project-name" class="google-label">Project name</label>
                            </div>

                            <!-- File Upload Area -->
                            <div class="space-y-2">
                                <label class="block text-sm font-medium text-gray-700">
                                    Script file
                                </label>
                                <div 
                                    id="drop-zone" 
                                    class="group border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 hover:bg-blue-50 transition-all duration-200 cursor-pointer"
                                >
                                    <div class="flex flex-col items-center">
                                        <span class="material-icons text-gray-400 text-4xl mb-4 group-hover:text-blue-500 transition-colors">
                                            upload_file
                                        </span>
                                        <p class="text-base text-gray-700 mb-1">Drag and drop or click to upload</p>
                                        <p class="text-sm text-gray-500">TXT, DOC, DOCX, PDF files</p>
                                    </div>
                                </div>
                                <input type="file" id="file-input" class="hidden" accept=".txt,.md,.doc,.docx,.pdf">
                            </div>

                            <button 
                                type="submit" 
                                class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 shadow-sm hover:shadow-md"
                            >
                                <span class="flex items-center justify-center">
                                    <span class="material-icons mr-2 text-lg">play_circle_filled</span>
                                    Create project
                                </span>
                            </button>
                        </form>
                    </div>
                </div>

                <!-- Features Grid -->
                <div class="grid md:grid-cols-3 gap-6 mb-16">
                    <div class="bg-white rounded-lg p-6 shadow-sm border border-gray-100 hover:shadow-md transition-all duration-300">
                        <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                            <span class="material-icons text-blue-600 text-2xl">auto_fix_high</span>
                        </div>
                        <h3 class="text-lg font-medium text-gray-900 mb-2">Smart script analysis</h3>
                        <p class="text-gray-600 leading-relaxed">AI-powered screenplay formatting and intelligent character extraction from any script format.</p>
                    </div>

                    <div class="bg-white rounded-lg p-6 shadow-sm border border-gray-100 hover:shadow-md transition-all duration-300">
                        <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                            <span class="material-icons text-green-600 text-2xl">palette</span>
                        </div>
                        <h3 class="text-lg font-medium text-gray-900 mb-2">Visual generation</h3>
                        <p class="text-gray-600 leading-relaxed">Automated scene visualization and character design using state-of-the-art AI models.</p>
                    </div>

                    <div class="bg-white rounded-lg p-6 shadow-sm border border-gray-100 hover:shadow-md transition-all duration-300">
                        <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                            <span class="material-icons text-purple-600 text-2xl">movie_creation</span>
                        </div>
                        <h3 class="text-lg font-medium text-gray-900 mb-2">Video production</h3>
                        <p class="text-gray-600 leading-relaxed">Complete video generation pipeline with professional-grade output quality.</p>
                    </div>
                </div>

                <!-- Status Section -->
                <div id="status-section" class="hidden max-w-4xl mx-auto">
                    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
                        <div class="flex items-center justify-between mb-8">
                            <div>
                                <h3 class="text-2xl font-normal text-gray-900">Project progress</h3>
                                <p class="text-gray-600 mt-1">Your AI video generation pipeline</p>
                            </div>
                            <div id="project-status-badge" class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-50 text-blue-700 border border-blue-200">
                                <span class="material-icons text-sm mr-1">hourglass_empty</span>
                                Processing
                            </div>
                        </div>
                        
                        <!-- Progress Steps -->
                        <div class="space-y-4 mb-8">
                            <div class="progress-step completed" id="step-input">
                                <div class="flex items-center">
                                    <div class="step-circle">
                                        <span class="material-icons text-white text-sm">check</span>
                                    </div>
                                    <div class="ml-4">
                                        <h4 class="font-medium text-gray-900">Input received</h4>
                                        <p class="text-sm text-gray-500">Script uploaded and validated</p>
                                    </div>
                                </div>
                            </div>

                            <div class="progress-step" id="step-screenplay">
                                <div class="flex items-center">
                                    <div class="step-circle">
                                        <span class="material-icons text-gray-400 text-sm">description</span>
                                    </div>
                                    <div class="ml-4">
                                        <h4 class="font-medium text-gray-700">Screenplay formatting</h4>
                                        <p class="text-sm text-gray-500">Converting to professional screenplay format</p>
                                    </div>
                                </div>
                            </div>

                            <div class="progress-step" id="step-shots">
                                <div class="flex items-center">
                                    <div class="step-circle">
                                        <span class="material-icons text-gray-400 text-sm">video_camera_back</span>
                                    </div>
                                    <div class="ml-4">
                                        <h4 class="font-medium text-gray-700">Shot breakdown</h4>
                                        <p class="text-sm text-gray-500">Analyzing scenes and creating shot list</p>
                                    </div>
                                </div>
                            </div>

                            <div class="progress-step" id="step-characters">
                                <div class="flex items-center">
                                    <div class="step-circle">
                                        <span class="material-icons text-gray-400 text-sm">people</span>
                                    </div>
                                    <div class="ml-4">
                                        <h4 class="font-medium text-gray-700">Character extraction</h4>
                                        <p class="text-sm text-gray-500">Identifying characters and relationships</p>
                                    </div>
                                </div>
                            </div>

                            <div class="progress-step" id="step-final">
                                <div class="flex items-center">
                                    <div class="step-circle">
                                        <span class="material-icons text-gray-400 text-sm">movie</span>
                                    </div>
                                    <div class="ml-4">
                                        <h4 class="font-medium text-gray-700">Video generation</h4>
                                        <p class="text-sm text-gray-500">Creating final video production</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Current Status -->
                        <div id="current-status" class="bg-gray-50 rounded-lg p-4 border border-gray-200">
                            <div class="flex items-center">
                                <span class="material-icons text-blue-600 mr-2 animate-spin">refresh</span>
                                <p class="text-gray-700">Ready to process your script...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </main>

            <!-- Footer -->
            <footer class="bg-gray-50 border-t border-gray-200 mt-20">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div class="text-center text-gray-500">
                        <p class="text-sm">&copy; 2024 AI Video Generator. Built with advanced AI technology.</p>
                        <div class="flex items-center justify-center mt-4 space-x-6 text-xs">
                            <span class="flex items-center">
                                <span class="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                                All systems operational
                            </span>
                            <span>•</span>
                            <span>Privacy Policy</span>
                            <span>•</span>
                            <span>Terms of Service</span>
                        </div>
                    </div>
                </div>
            </footer>

            <style>
                /* Google Input Styles */
                .google-input-container {
                    position: relative;
                    margin-bottom: 1.5rem;
                }

                .google-input {
                    width: 100%;
                    padding: 16px 16px 8px 16px;
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                    background: transparent;
                    font-size: 16px;
                    outline: none;
                    transition: all 0.2s ease;
                }

                .google-input:focus {
                    border-color: #1976d2;
                    box-shadow: 0 0 0 1px #1976d2;
                }

                .google-label {
                    position: absolute;
                    top: 16px;
                    left: 16px;
                    font-size: 16px;
                    color: #757575;
                    transition: all 0.2s ease;
                    pointer-events: none;
                    background: white;
                    padding: 0 4px;
                }

                .google-input:focus + .google-label,
                .google-input:not(:placeholder-shown) + .google-label {
                    top: -8px;
                    left: 12px;
                    font-size: 12px;
                    color: #1976d2;
                }

                /* Progress Step Styles */
                .progress-step .step-circle {
                    width: 2rem;
                    height: 2rem;
                    border-radius: 50%;
                    background: #f5f5f5;
                    border: 2px solid #e0e0e0;
                    display: flex;
                    items-center: center;
                    justify-content: center;
                    transition: all 0.3s ease;
                }

                .progress-step.completed .step-circle {
                    background: #1976d2;
                    border-color: #1976d2;
                }

                .progress-step.active .step-circle {
                    background: #1976d2;
                    border-color: #1976d2;
                    animation: pulse-google 1.5s infinite;
                }

                .progress-step.active .step-circle .material-icons {
                    color: white;
                    animation: spin 1s linear infinite;
                }

                @keyframes pulse-google {
                    0%, 100% { box-shadow: 0 0 0 0 rgba(25, 118, 210, 0.4); }
                    50% { box-shadow: 0 0 0 8px rgba(25, 118, 210, 0); }
                }

                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }

                /* Material Design Elevation */
                .elevation-1 { box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .elevation-2 { box-shadow: 0 4px 8px rgba(0,0,0,0.12); }
                .elevation-3 { box-shadow: 0 8px 16px rgba(0,0,0,0.15); }

                /* Ripple Effect */
                .ripple {
                    position: relative;
                    overflow: hidden;
                    transform: translate3d(0, 0, 0);
                }

                .ripple:before {
                    content: "";
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    width: 0;
                    height: 0;
                    border-radius: 50%;
                    background: rgba(255, 255, 255, 0.5);
                    transition: width 0.6s, height 0.6s, top 0.6s, left 0.6s;
                    transform: translate(-50%, -50%);
                }

                .ripple:active:before {
                    width: 300px;
                    height: 300px;
                }

                /* Smooth transitions for all interactive elements */
                button, .group, .hover\\:shadow-md {
                    transition: all 0.2s cubic-bezier(0.4, 0.0, 0.2, 1);
                }

                /* Custom scrollbar */
                ::-webkit-scrollbar {
                    width: 8px;
                }

                ::-webkit-scrollbar-track {
                    background: #f1f1f1;
                }

                ::-webkit-scrollbar-thumb {
                    background: #c1c1c1;
                    border-radius: 4px;
                }

                ::-webkit-scrollbar-thumb:hover {
                    background: #a8a8a8;
                }
            </style>

            <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
            <script>
                let currentProjectId = null;
                let ws = null;

                // File upload handling
                const dropZone = document.getElementById('drop-zone');
                const fileInput = document.getElementById('file-input');
                let selectedFile = null;

                dropZone.addEventListener('click', () => fileInput.click());

                dropZone.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    dropZone.classList.add('border-blue-400', 'bg-blue-50');
                });

                dropZone.addEventListener('dragleave', () => {
                    dropZone.classList.remove('border-blue-400', 'bg-blue-50');
                });

                dropZone.addEventListener('drop', (e) => {
                    e.preventDefault();
                    dropZone.classList.remove('border-blue-400', 'bg-blue-50');
                    if (e.dataTransfer.files.length > 0) {
                        selectedFile = e.dataTransfer.files[0];
                        updateDropZone();
                    }
                });

                fileInput.addEventListener('change', (e) => {
                    if (e.target.files.length > 0) {
                        selectedFile = e.target.files[0];
                        updateDropZone();
                    }
                });

                function updateDropZone() {
                    if (selectedFile) {
                        dropZone.innerHTML = `
                            <div class="flex items-center justify-center">
                                <svg class="w-8 h-8 text-green-500 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                </svg>
                                <div>
                                    <p class="text-lg text-gray-700 font-medium">${selectedFile.name}</p>
                                    <p class="text-sm text-gray-500">${(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                                </div>
                            </div>
                        `;
                        dropZone.classList.add('border-green-400', 'bg-green-50');
                    }
                }

                // Project form submission
                document.getElementById('project-form').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    
                    const projectName = document.getElementById('project-name').value;
                    if (!projectName || !selectedFile) {
                        alert('Please enter a project name and select a file.');
                        return;
                    }

                    try {
                        // Create project
                        const projectResponse = await axios.post('/api/projects', {
                            name: projectName,
                            description: 'AI Video Generation Project'
                        });

                        currentProjectId = projectResponse.data.project_id;

                        // Upload file
                        const formData = new FormData();
                        formData.append('file', selectedFile);
                        formData.append('project_id', currentProjectId);

                        const uploadResponse = await axios.post('/api/upload-script', formData, {
                            headers: { 'Content-Type': 'multipart/form-data' }
                        });

                        if (uploadResponse.data.success) {
                            showStatusSection();
                            connectWebSocket(currentProjectId);
                            
                            // Start processing
                            await axios.post(`/api/projects/${currentProjectId}/start-processing`);
                        }

                    } catch (error) {
                        console.error('Error:', error);
                        alert('Failed to create project. Please try again.');
                    }
                });

                function showStatusSection() {
                    document.getElementById('status-section').classList.remove('hidden');
                    document.querySelector('main').scrollIntoView({ behavior: 'smooth', block: 'end' });
                }

                function connectWebSocket(projectId) {
                    ws = new WebSocket(`ws://localhost:8001/ws/${projectId}`);
                    
                    ws.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        updateProgress(data);
                    };
                }

                function updateProgress(data) {
                    const { stage, status, message } = data;
                    
                    // Update status message
                    document.getElementById('current-status').innerHTML = `
                        <p class="text-blue-800 font-medium">${message}</p>
                    `;

                    // Update progress dots
                    if (stage) {
                        const stageElement = document.getElementById(`stage-${stage}`);
                        if (stageElement) {
                            stageElement.className = `stage-dot ${status}`;
                        }
                    }
                }

                // Health check on page load
                window.addEventListener('load', async () => {
                    try {
                        const response = await axios.get('/health');
                        console.log('API Status:', response.data);
                    } catch (error) {
                        console.error('API not available:', error);
                    }
                });
            </script>
        </body>
        </html>
        """, status_code=200)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "AI Video Generator",
        "version": "2.0.0"
    }

@app.post("/api/projects")
async def create_project(project_data: dict):
    """Create a new project"""
    project_id = str(uuid.uuid4())
    project = {
        "id": project_id,
        "name": project_data.get("name", "Untitled Project"),
        "description": project_data.get("description", ""),
        "created_at": datetime.utcnow().isoformat(),
        "status": "created",
        "current_stage": "input",
        "progress": {
            "input": "completed",
            "screenplay": "pending",
            "shots": "pending", 
            "characters": "pending",
            "final": "pending"
        }
    }
    
    projects_db[project_id] = project
    logger.info(f"Created project: {project_id}")
    
    return {"project_id": project_id, "status": "created"}

@app.post("/api/upload-script")
async def upload_script(file: UploadFile = File(...), project_id: str = Form(...)):
    """Upload script file"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Save file
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    file_path = upload_dir / f"{project_id}_{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Update project
    projects_db[project_id].update({
        "script_file": str(file_path),
        "script_filename": file.filename,
        "status": "script_uploaded"
    })
    
    logger.info(f"Uploaded script for project: {project_id}")
    
    return {"success": True, "filename": file.filename}

@app.post("/api/projects/{project_id}/start-processing")
async def start_processing(project_id: str):
    """Start the AI processing pipeline"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Start background processing
    asyncio.create_task(process_project(project_id))
    
    return {"success": True, "message": "Processing started"}

async def process_project(project_id: str):
    """Background task to process the project"""
    project = projects_db[project_id]
    
    stages = [
        ("screenplay", "Generating screenplay format..."),
        ("shots", "Breaking down shots..."), 
        ("characters", "Extracting characters..."),
        ("final", "Generating final video...")
    ]
    
    for stage, message in stages:
        # Update status
        project["current_stage"] = stage
        project["progress"][stage] = "active"
        
        # Send WebSocket update
        await manager.send_update(project_id, {
            "stage": stage,
            "status": "active", 
            "message": message
        })
        
        # Simulate processing time
        await asyncio.sleep(3)
        
        # Complete stage
        project["progress"][stage] = "completed"
        
        await manager.send_update(project_id, {
            "stage": stage,
            "status": "completed",
            "message": f"Completed: {message}"
        })
        
        await asyncio.sleep(1)
    
    # Mark project as completed
    project["status"] = "completed"
    project["current_stage"] = "final"
    
    await manager.send_update(project_id, {
        "stage": "final",
        "status": "completed",
        "message": "Project completed successfully!"
    })

@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket, project_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(project_id)

@app.get("/api/projects")
async def list_projects():
    """List all projects"""
    return {"projects": list(projects_db.values())}

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Get project details"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return projects_db[project_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")