"""
PostgreSQL database models replacing Google Docs, Sheets, and GoToHuman
Using SQLAlchemy with async support
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from datetime import datetime
import uuid
import enum

Base = declarative_base()

# Enums
class ProjectStatus(str, enum.Enum):
    CREATED = "created"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class WorkflowStage(str, enum.Enum):
    SCRIPT_INPUT = "script_input"
    SCREENPLAY_GENERATION = "screenplay_generation"
    SHOT_DIVISION = "shot_division"
    PRODUCTION_PLANNING = "production_planning"
    CHARACTER_DESIGN = "character_design"
    SCENE_GENERATION = "scene_generation"
    VIDEO_GENERATION = "video_generation"
    FINAL_SYNTHESIS = "final_synthesis"

class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"

class ShotType(str, enum.Enum):
    WIDE = "wide"
    MEDIUM = "medium"
    CLOSE_UP = "close_up"
    EXTREME_CLOSE_UP = "extreme_close_up"
    OVER_SHOULDER = "over_shoulder"
    POV = "pov"
    ESTABLISHING = "establishing"

class CameraMovement(str, enum.Enum):
    STATIC = "static"
    PAN = "pan"
    TILT = "tilt"
    ZOOM = "zoom"
    DOLLY = "dolly"
    TRACKING = "tracking"

# Core Project Model
class Project(Base):
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    user_id = Column(String(100), nullable=False, index=True)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.CREATED)
    current_stage = Column(SQLEnum(WorkflowStage), default=WorkflowStage.SCRIPT_INPUT)
    
    # Script content (replacing Google Docs storage)
    original_script = Column(Text)
    script_file_path = Column(String(500))  # MinIO path
    
    # Settings and metadata
    settings = Column(JSON, default=dict)
    project_metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    screenplays = relationship("Screenplay", back_populates="project", cascade="all, delete-orphan")
    shot_divisions = relationship("ShotDivision", back_populates="project", cascade="all, delete-orphan")
    characters = relationship("Character", back_populates="project", cascade="all, delete-orphan")
    production_plans = relationship("ProductionPlan", back_populates="project", cascade="all, delete-orphan")
    approvals = relationship("ApprovalRequest", back_populates="project", cascade="all, delete-orphan")

# Screenplay Models (Replacing Google Docs)
class Screenplay(Base):
    __tablename__ = "screenplays"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    
    # Content storage
    content = Column(Text)  # Final merged screenplay
    content_markdown = Column(Text)  # Markdown formatted version
    file_path = Column(String(500))  # MinIO storage path
    
    # Version control
    version = Column(Integer, default=1)
    is_current_version = Column(Boolean, default=True)
    previous_version_id = Column(UUID(as_uuid=True), ForeignKey("screenplays.id"))
    
    # Processing metadata
    ai_providers_used = Column(ARRAY(String))
    processing_metadata = Column(JSON, default=dict)
    quality_score = Column(Float)
    
    # Approval status
    approval_status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.PENDING)
    approved_at = Column(DateTime)
    approved_by = Column(String(100))
    approval_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="screenplays")
    versions = relationship("ScreenplayVersion", back_populates="screenplay", cascade="all, delete-orphan")
    previous_version = relationship("Screenplay", remote_side=[id])

class ScreenplayVersion(Base):
    __tablename__ = "screenplay_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    screenplay_id = Column(UUID(as_uuid=True), ForeignKey("screenplays.id"), nullable=False, index=True)
    
    provider = Column(String(50), nullable=False)  # openai, claude, gemini
    content = Column(Text, nullable=False)
    confidence_score = Column(Float)
    processing_time = Column(Float)
    tokens_used = Column(Integer)
    cost_estimate = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    screenplay = relationship("Screenplay", back_populates="versions")

# Shot Division Models (Replacing Google Sheets)
class ShotDivision(Base):
    __tablename__ = "shot_divisions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    screenplay_id = Column(UUID(as_uuid=True), ForeignKey("screenplays.id"), nullable=False)
    
    # Division metadata
    total_shots = Column(Integer, default=0)
    estimated_duration = Column(Float, default=0.0)
    target_duration = Column(Float)
    vertical_format = Column(Boolean, default=True)
    
    # Processing metadata
    division_algorithm = Column(String(50))
    processing_metadata = Column(JSON, default=dict)
    
    # Approval status
    approval_status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.PENDING)
    approved_at = Column(DateTime)
    approved_by = Column(String(100))
    approval_notes = Column(Text)
    
    # Export tracking
    csv_export_path = Column(String(500))  # MinIO path for CSV export
    excel_export_path = Column(String(500))  # MinIO path for Excel export
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="shot_divisions")
    shots = relationship("Shot", back_populates="shot_division", cascade="all, delete-orphan")

class Shot(Base):
    __tablename__ = "shots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shot_division_id = Column(UUID(as_uuid=True), ForeignKey("shot_divisions.id"), nullable=False, index=True)
    
    # Shot identification
    shot_number = Column(Integer, nullable=False)
    scene_heading = Column(String(200))
    
    # Shot content
    description = Column(Text, nullable=False)
    dialogue = Column(Text)
    
    # Technical specifications
    shot_type = Column(SQLEnum(ShotType), default=ShotType.MEDIUM)
    camera_angle = Column(String(100))
    camera_movement = Column(SQLEnum(CameraMovement), default=CameraMovement.STATIC)
    duration_seconds = Column(Float, default=3.0)
    
    # Production details
    lighting_notes = Column(Text)
    location = Column(String(200))
    characters_present = Column(ARRAY(String))
    props_needed = Column(ARRAY(String))
    
    # Visual style
    visual_style = Column(String(200))
    physics_notes = Column(Text)
    continuity_notes = Column(Text)
    
    # AI prompt data
    midjourney_prompt = Column(Text)
    midjourney_style_params = Column(JSON, default=dict)
    
    # Generated content
    generated_images = Column(ARRAY(String))  # MinIO paths
    selected_image_path = Column(String(500))  # MinIO path
    video_url = Column(String(500))  # MinIO path
    video_status = Column(String(50), default="pending")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    shot_division = relationship("ShotDivision", back_populates="shots")

# Character Models (Replacing Google Sheets character tracking)
class Character(Base):
    __tablename__ = "characters"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    
    # Character identification
    name = Column(String(100), nullable=False)
    importance_level = Column(String(20), default="supporting")  # main, supporting, background
    first_appearance_scene = Column(String(200))
    total_scenes = Column(Integer, default=1)
    
    # Character details
    description = Column(Text)
    age = Column(String(50))
    gender = Column(String(50))
    personality_traits = Column(ARRAY(String))
    
    # Physical attributes
    height = Column(String(20))
    build = Column(String(50))
    hair_color = Column(String(50))
    hair_style = Column(String(100))
    eye_color = Column(String(50))
    skin_tone = Column(String(50))
    distinctive_features = Column(Text)
    clothing_style = Column(String(200))
    
    # AI generation data
    midjourney_prompt = Column(Text)
    reference_images = Column(ARRAY(String))  # MinIO paths
    selected_image_path = Column(String(500))  # MinIO path
    cref_url = Column(String(500))  # Character reference for consistency
    
    # Approval status
    approval_status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.PENDING)
    approved_at = Column(DateTime)
    approved_by = Column(String(100))
    approval_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="characters")

# Production Planning Models (Replacing Google Sheets production data)
class ProductionPlan(Base):
    __tablename__ = "production_plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    shot_division_id = Column(UUID(as_uuid=True), ForeignKey("shot_divisions.id"), nullable=False)
    
    # Production design
    visual_style = Column(String(100), default="cinematic")
    color_palette = Column(ARRAY(String))
    mood_board_urls = Column(ARRAY(String))  # MinIO paths
    
    # Location data
    locations = Column(JSON, default=dict)  # Structured location data
    location_breakdown = Column(JSON, default=dict)  # location -> shot numbers
    
    # Lighting design
    lighting_setup = Column(JSON, default=dict)
    time_of_day = Column(String(50), default="day")
    weather_conditions = Column(String(50), default="clear")
    mood = Column(String(50), default="neutral")
    
    # Budget and timeline
    estimated_budget = Column(Float)
    timeline_days = Column(Integer)
    pre_production_days = Column(Integer, default=3)
    production_days = Column(Integer, default=7)
    post_production_days = Column(Integer, default=10)
    
    # Technical specifications
    aspect_ratio = Column(String(10), default="9:16")
    resolution = Column(String(20), default="1080x1920")
    frame_rate = Column(String(10), default="24fps")
    color_grading = Column(String(50), default="cinematic")
    ai_tools = Column(ARRAY(String))
    
    # Quality standards
    visual_consistency = Column(String(20), default="high")
    character_continuity = Column(String(20), default="strict")
    physics_realism = Column(String(20), default="high")
    
    # Risk assessment
    risk_assessment = Column(ARRAY(String))
    
    # Approval status
    approval_status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.PENDING)
    approved_at = Column(DateTime)
    approved_by = Column(String(100))
    approval_notes = Column(Text)
    
    # Export tracking
    csv_export_path = Column(String(500))  # MinIO path for CSV export
    pdf_export_path = Column(String(500))  # MinIO path for PDF export
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="production_plans")

# Scene/Image Prompt Models (Replacing Google Sheets prompt storage)
class ScenePrompt(Base):
    __tablename__ = "scene_prompts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    shot_id = Column(UUID(as_uuid=True), ForeignKey("shots.id"), nullable=False)
    
    # Prompt data
    midjourney_prompt = Column(Text, nullable=False)
    style_reference = Column(String(500))  # MinIO path
    character_references = Column(ARRAY(String))  # MinIO paths
    negative_prompt = Column(Text)
    
    # Generation parameters
    aspect_ratio = Column(String(10), default="9:16")
    style_params = Column(JSON, default=dict)  # --chaos, --seed, etc.
    quality_level = Column(String(20), default="standard")
    
    # Generated results
    generated_images = Column(ARRAY(String))  # MinIO paths
    selected_image_path = Column(String(500))  # MinIO path
    generation_metadata = Column(JSON, default=dict)
    
    # Processing status
    generation_status = Column(String(50), default="pending")
    processing_time = Column(Float)
    cost_estimate = Column(Float)
    
    # Human feedback
    human_feedback = Column(Text)
    revision_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Video Generation Prompts (Replacing Google Sheets video data)
class VideoPrompt(Base):
    __tablename__ = "video_prompts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    shot_id = Column(UUID(as_uuid=True), ForeignKey("shots.id"), nullable=False)
    scene_prompt_id = Column(UUID(as_uuid=True), ForeignKey("scene_prompts.id"))
    
    # Video generation data
    kling_prompt = Column(Text, nullable=False)
    source_image_path = Column(String(500), nullable=False)  # MinIO path
    
    # Video parameters
    duration = Column(Float, default=3.0)
    fps = Column(Integer, default=24)
    quality = Column(String(20), default="standard")
    camera_movement = Column(String(50))
    
    # Generated results
    video_path = Column(String(500))  # MinIO path
    thumbnail_path = Column(String(500))  # MinIO path
    generation_metadata = Column(JSON, default=dict)
    
    # Processing status
    generation_status = Column(String(50), default="pending")
    processing_time = Column(Float)
    cost_estimate = Column(Float)
    quality_score = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Custom Approval System (Replacing GoToHuman)
class ApprovalRequest(Base):
    __tablename__ = "approval_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    
    # Approval details
    stage = Column(SQLEnum(WorkflowStage), nullable=False)
    approval_type = Column(String(50), nullable=False)  # screenplay, shot_division, character, etc.
    entity_id = Column(UUID(as_uuid=True))  # ID of the entity being approved
    
    # Request data
    title = Column(String(200), nullable=False)
    description = Column(Text)
    approval_data = Column(JSON, default=dict)  # Content to review
    options = Column(JSON, default=dict)  # Multiple choice options (like 4 images)
    
    # Status and assignments
    status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.PENDING)
    assigned_to = Column(String(100))  # User ID
    priority = Column(Integer, default=1)  # 1-5 scale
    
    # Response data
    approved_at = Column(DateTime)
    approved_by = Column(String(100))
    selected_option = Column(String(100))  # Selected choice from options
    feedback = Column(Text)
    revision_notes = Column(Text)
    
    # Timing
    requested_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime)
    response_time_seconds = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="approvals")

# Data Export and Analytics Models
class DataExport(Base):
    __tablename__ = "data_exports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    
    # Export metadata
    export_type = Column(String(50), nullable=False)  # csv, excel, pdf, json
    data_type = Column(String(50), nullable=False)  # shots, characters, production_plan
    
    # Export details
    file_path = Column(String(500), nullable=False)  # MinIO path
    file_size = Column(Integer)
    record_count = Column(Integer)
    
    # Processing
    export_status = Column(String(50), default="pending")
    processing_time = Column(Float)
    
    # Access tracking
    download_count = Column(Integer, default=0)
    expires_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_downloaded = Column(DateTime)

# User Activity and Analytics
class UserActivity(Base):
    __tablename__ = "user_activities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), index=True)
    
    # Activity details
    activity_type = Column(String(100), nullable=False)
    entity_type = Column(String(50))  # project, screenplay, shot, etc.
    entity_id = Column(UUID(as_uuid=True))
    
    # Activity data
    description = Column(Text)
    project_metadata = Column(JSON, default=dict)
    
    # Context
    ip_address = Column(String(45))
    user_agent = Column(Text)
    session_id = Column(String(100))
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)