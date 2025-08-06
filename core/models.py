from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

# Enums for status tracking
class ProjectStatus(str, Enum):
    CREATED = "created"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class WorkflowStage(str, Enum):
    SCRIPT_INPUT = "script_input"
    SCREENPLAY_GENERATION = "screenplay_generation"
    SHOT_DIVISION = "shot_division"
    PRODUCTION_PLANNING = "production_planning"
    CHARACTER_DESIGN = "character_design"
    SCENE_GENERATION = "scene_generation"
    VIDEO_GENERATION = "video_generation"
    FINAL_SYNTHESIS = "final_synthesis"

class ShotType(str, Enum):
    WIDE = "wide"
    MEDIUM = "medium"
    CLOSE_UP = "close_up"
    EXTREME_CLOSE_UP = "extreme_close_up"
    OVER_SHOULDER = "over_shoulder"
    POV = "pov"
    ESTABLISHING = "establishing"

class CameraMovement(str, Enum):
    STATIC = "static"
    PAN = "pan"
    TILT = "tilt"
    ZOOM = "zoom"
    DOLLY = "dolly"
    TRACKING = "tracking"

# Base model for MongoDB documents
class MongoModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Core project model
class Project(MongoModel):
    name: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.CREATED
    current_stage: WorkflowStage = WorkflowStage.SCRIPT_INPUT
    user_id: str
    script_content: Optional[str] = None
    script_file_path: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

# Screenplay models
class ScreenplayVersion(BaseModel):
    provider: str  # "openai", "claude", "gemini"
    content: str
    confidence_score: Optional[float] = None
    processing_time: Optional[float] = None
    tokens_used: Optional[int] = None

class Screenplay(MongoModel):
    project_id: str
    versions: List[ScreenplayVersion] = Field(default_factory=list)
    merged_content: Optional[str] = None
    approved_content: Optional[str] = None
    human_feedback: Optional[str] = None
    google_doc_url: Optional[str] = None

# Character models
class CharacterDesign(BaseModel):
    name: str
    description: str
    physical_attributes: Dict[str, Any] = Field(default_factory=dict)
    personality_traits: List[str] = Field(default_factory=list)
    midjourney_prompt: Optional[str] = None
    reference_images: List[str] = Field(default_factory=list)
    selected_image_url: Optional[str] = None
    cref_url: Optional[str] = None  # For character consistency

class Character(MongoModel):
    project_id: str
    name: str
    designs: List[CharacterDesign] = Field(default_factory=list)
    final_design: Optional[CharacterDesign] = None
    extraction_metadata: Dict[str, Any] = Field(default_factory=dict)

# Shot models
class Shot(BaseModel):
    shot_number: int
    scene_heading: str
    description: str
    dialogue: Optional[str] = None
    shot_type: ShotType
    camera_angle: Optional[str] = None
    camera_movement: CameraMovement = CameraMovement.STATIC
    duration_seconds: float = 3.0
    lighting_notes: Optional[str] = None
    location: Optional[str] = None
    characters_present: List[str] = Field(default_factory=list)
    props_needed: List[str] = Field(default_factory=list)
    
    # Image generation
    midjourney_prompt: Optional[str] = None
    generated_images: List[str] = Field(default_factory=list)
    selected_image_url: Optional[str] = None
    
    # Video generation
    kling_prompt: Optional[str] = None
    video_url: Optional[str] = None
    video_status: Optional[str] = None

class ShotDivision(MongoModel):
    project_id: str
    screenplay_id: str
    shots: List[Shot] = Field(default_factory=list)
    total_shots: int = 0
    estimated_duration: float = 0.0
    vertical_format: bool = True  # 9:16 aspect ratio
    human_approved: bool = False
    google_sheet_url: Optional[str] = None

# Production planning models
class ProductionDesign(BaseModel):
    locations: Dict[str, Any] = Field(default_factory=dict)
    color_palette: List[str] = Field(default_factory=list)
    visual_style: str = "cinematic"
    mood_board_urls: List[str] = Field(default_factory=list)

class LightingDesign(BaseModel):
    lighting_setup: Dict[str, Any] = Field(default_factory=dict)
    time_of_day: str = "day"
    weather_conditions: str = "clear"
    mood: str = "neutral"

class ProductionPlan(MongoModel):
    project_id: str
    shot_division_id: str
    production_design: ProductionDesign
    lighting_design: LightingDesign
    location_breakdown: Dict[str, List[int]] = Field(default_factory=dict)  # location -> shot numbers
    estimated_budget: Optional[float] = None
    timeline_days: Optional[int] = None
    human_approved: bool = False

# Scene generation models
class ScenePrompt(BaseModel):
    shot_number: int
    midjourney_prompt: str
    style_reference: Optional[str] = None
    character_references: List[str] = Field(default_factory=list)
    generated_images: List[str] = Field(default_factory=list)
    selected_image: Optional[str] = None
    human_feedback: Optional[str] = None

class SceneGeneration(MongoModel):
    project_id: str
    shot_division_id: str
    scene_prompts: List[ScenePrompt] = Field(default_factory=list)
    batch_processing_status: Dict[str, Any] = Field(default_factory=dict)
    human_approved: bool = False

# Video generation models
class VideoClip(BaseModel):
    shot_number: int
    kling_prompt: str
    source_image_url: str
    video_url: Optional[str] = None
    video_status: str = "pending"  # pending, processing, completed, failed
    processing_time: Optional[float] = None
    duration: float = 3.0
    quality_score: Optional[float] = None

class VideoGeneration(MongoModel):
    project_id: str
    scene_generation_id: str
    video_clips: List[VideoClip] = Field(default_factory=list)
    final_video_url: Optional[str] = None
    synthesis_status: str = "pending"
    total_duration: float = 0.0

# Human approval tracking
class ApprovalCheckpoint(BaseModel):
    stage: WorkflowStage
    data: Dict[str, Any]
    approved: bool = False
    feedback: Optional[str] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None

class HumanApproval(MongoModel):
    project_id: str
    checkpoints: List[ApprovalCheckpoint] = Field(default_factory=list)
    gotohuman_urls: Dict[str, str] = Field(default_factory=dict)  # stage -> approval URL
    current_pending: Optional[WorkflowStage] = None

# Pipeline state tracking
class PipelineState(MongoModel):
    project_id: str
    current_stage: WorkflowStage = WorkflowStage.SCRIPT_INPUT
    stage_data: Dict[str, Any] = Field(default_factory=dict)
    error_log: List[str] = Field(default_factory=list)
    processing_metrics: Dict[str, float] = Field(default_factory=dict)
    last_checkpoint: Optional[datetime] = None

# Response models for API
class ProjectResponse(BaseModel):
    id: str
    name: str
    status: ProjectStatus
    current_stage: WorkflowStage
    created_at: datetime
    updated_at: datetime
    progress_percentage: float = 0.0

class ScreenplayResponse(BaseModel):
    id: str
    project_id: str
    merged_content: Optional[str]
    approved_content: Optional[str]
    google_doc_url: Optional[str]
    human_approved: bool = False

class ShotDivisionResponse(BaseModel):
    id: str
    project_id: str
    total_shots: int
    estimated_duration: float
    human_approved: bool
    google_sheet_url: Optional[str]

class CharacterResponse(BaseModel):
    id: str
    name: str
    final_design: Optional[CharacterDesign]
    reference_images: List[str] = Field(default_factory=list)