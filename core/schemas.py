from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from .models import ProjectStatus, WorkflowStage, ShotType, CameraMovement

# Request schemas
class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    user_id: str = Field(..., min_length=1)
    settings: Dict[str, Any] = Field(default_factory=dict)

class ScriptUploadRequest(BaseModel):
    project_id: str
    content: Optional[str] = None  # Either content or file_path
    file_path: Optional[str] = None
    
    @validator('content', 'file_path')
    def validate_script_input(cls, v, values):
        content = values.get('content')
        file_path = values.get('file_path')
        if not content and not file_path:
            raise ValueError('Either content or file_path must be provided')
        return v

class ScreenplayGenerationRequest(BaseModel):
    project_id: str
    use_providers: List[str] = Field(default=["openai", "claude", "gemini"])
    custom_prompt: Optional[str] = None
    format_requirements: Dict[str, Any] = Field(default_factory=dict)

class ShotDivisionRequest(BaseModel):
    project_id: str
    screenplay_id: str
    target_duration: Optional[float] = Field(default=60.0, gt=0)
    shot_duration: Optional[float] = Field(default=3.0, gt=0)
    vertical_format: bool = True
    custom_instructions: Optional[str] = None

class CharacterExtractionRequest(BaseModel):
    project_id: str
    screenplay_id: str
    extract_physical_descriptions: bool = True
    generate_midjourney_prompts: bool = True

class ProductionPlanningRequest(BaseModel):
    project_id: str
    shot_division_id: str
    budget_range: Optional[str] = None
    timeline_preference: Optional[str] = None
    location_preferences: Dict[str, Any] = Field(default_factory=dict)

class SceneGenerationRequest(BaseModel):
    project_id: str
    shot_division_id: str
    style_references: List[str] = Field(default_factory=list)
    quality_level: str = Field(default="standard")  # standard, high, premium
    batch_size: int = Field(default=5, gt=0, le=20)

class VideoGenerationRequest(BaseModel):
    project_id: str
    scene_generation_id: str
    video_quality: str = Field(default="standard")
    duration_per_shot: float = Field(default=3.0, gt=0, le=10)
    include_audio: bool = False

class HumanApprovalRequest(BaseModel):
    project_id: str
    stage: WorkflowStage
    approved: bool
    feedback: Optional[str] = None
    selected_options: Dict[str, Any] = Field(default_factory=dict)

# Response schemas
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ProjectStatusResponse(BaseModel):
    project_id: str
    status: ProjectStatus
    current_stage: WorkflowStage
    progress_percentage: float = 0.0
    stage_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    estimated_completion: Optional[datetime] = None

class ScreenplayStatusResponse(BaseModel):
    screenplay_id: str
    project_id: str
    versions_count: int = 0
    merged_available: bool = False
    google_doc_url: Optional[str] = None
    processing_status: str = "pending"
    confidence_scores: Dict[str, float] = Field(default_factory=dict)

class ShotDivisionStatusResponse(BaseModel):
    shot_division_id: str
    project_id: str
    total_shots: int = 0
    completed_shots: int = 0
    estimated_duration: float = 0.0
    google_sheet_url: Optional[str] = None
    human_approved: bool = False

class CharacterStatusResponse(BaseModel):
    characters: List[Dict[str, Any]] = Field(default_factory=list)
    extraction_complete: bool = False
    designs_generated: int = 0
    approved_designs: int = 0

class ProductionPlanStatusResponse(BaseModel):
    production_plan_id: str
    project_id: str
    locations_count: int = 0
    design_complete: bool = False
    budget_estimated: bool = False
    human_approved: bool = False

class SceneGenerationStatusResponse(BaseModel):
    scene_generation_id: str
    project_id: str
    total_scenes: int = 0
    generated_scenes: int = 0
    approved_scenes: int = 0
    batch_status: Dict[str, str] = Field(default_factory=dict)

class VideoGenerationStatusResponse(BaseModel):
    video_generation_id: str
    project_id: str
    total_clips: int = 0
    completed_clips: int = 0
    failed_clips: int = 0
    final_video_url: Optional[str] = None
    synthesis_complete: bool = False

class ApprovalStatusResponse(BaseModel):
    project_id: str
    pending_approvals: List[WorkflowStage] = Field(default_factory=list)
    completed_approvals: List[WorkflowStage] = Field(default_factory=list)
    gotohuman_urls: Dict[str, str] = Field(default_factory=dict)
    current_checkpoint: Optional[WorkflowStage] = None

# Webhook schemas
class WebhookPayload(BaseModel):
    project_id: str
    stage: WorkflowStage
    event_type: str  # "stage_complete", "approval_needed", "error", "progress_update"
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class GoToHumanWebhookPayload(BaseModel):
    project_id: str
    approval_id: str
    stage: WorkflowStage
    approved: bool
    feedback: Optional[str] = None
    selected_data: Dict[str, Any] = Field(default_factory=dict)
    user_id: Optional[str] = None

# Pipeline configuration schemas
class PipelineConfig(BaseModel):
    screenplay_providers: List[str] = Field(default=["openai", "claude", "gemini"])
    shot_division_providers: List[str] = Field(default=["openai", "claude"])
    default_shot_duration: float = 3.0
    vertical_format: bool = True
    auto_approve_stages: List[WorkflowStage] = Field(default_factory=list)
    quality_settings: Dict[str, str] = Field(default_factory=dict)
    retry_settings: Dict[str, int] = Field(default_factory=lambda: {
        "max_retries": 3,
        "retry_delay": 2
    })

class ModelSettings(BaseModel):
    openai_model: str = "gpt-4"
    claude_model: str = "claude-3-opus-20240229" 
    gemini_model: str = "gemini-pro"
    temperature: float = 0.7
    max_tokens: int = 4000
    timeout_seconds: int = 120

# Validation schemas
class ShotValidationSchema(BaseModel):
    shot_number: int = Field(..., gt=0)
    scene_heading: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    shot_type: ShotType
    camera_movement: CameraMovement = CameraMovement.STATIC
    duration_seconds: float = Field(..., gt=0, le=30)

class CharacterValidationSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=10)
    physical_attributes: Dict[str, Any] = Field(default_factory=dict)

class PromptValidationSchema(BaseModel):
    content: str = Field(..., min_length=10, max_length=1000)
    style_tags: List[str] = Field(default_factory=list)
    aspect_ratio: str = Field(default="9:16")
    
    @validator('aspect_ratio')
    def validate_aspect_ratio(cls, v):
        valid_ratios = ["9:16", "16:9", "1:1", "4:5"]
        if v not in valid_ratios:
            raise ValueError(f'aspect_ratio must be one of {valid_ratios}')
        return v

# Batch processing schemas
class BatchProcessingRequest(BaseModel):
    project_id: str
    batch_type: str  # "scenes", "videos", "characters"
    items: List[Dict[str, Any]]
    priority: int = Field(default=1, ge=1, le=5)
    callback_url: Optional[str] = None

class BatchProcessingStatus(BaseModel):
    batch_id: str
    project_id: str
    batch_type: str
    total_items: int
    completed_items: int
    failed_items: int
    status: str  # "queued", "processing", "completed", "failed"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_summary: Optional[str] = None