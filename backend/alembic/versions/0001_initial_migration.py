"""Initial migration with all tables

Revision ID: 0001
Revises: 
Create Date: 2024-08-06 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    project_status_enum = postgresql.ENUM('CREATED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'PAUSED', name='projectstatus')
    workflow_stage_enum = postgresql.ENUM('INPUT', 'SCREENPLAY_GENERATION', 'SHOT_DIVISION', 'CHARACTER_DESIGN', 'SCENE_GENERATION', 'VIDEO_GENERATION', 'COMPLETED', name='workflowstage')
    approval_status_enum = postgresql.ENUM('PENDING', 'APPROVED', 'REJECTED', 'REVISION_REQUESTED', name='approvalstatus')
    shot_type_enum = postgresql.ENUM('WIDE', 'MEDIUM', 'CLOSE_UP', 'EXTREME_CLOSE_UP', 'ESTABLISHING', 'INSERT', 'CUTAWAY', 'REACTION', name='shottype')
    camera_movement_enum = postgresql.ENUM('STATIC', 'PAN', 'TILT', 'ZOOM', 'DOLLY', 'TRACK', 'HANDHELD', 'CRANE', name='cameramovement')
    
    project_status_enum.create(op.get_bind())
    workflow_stage_enum.create(op.get_bind())
    approval_status_enum.create(op.get_bind())
    shot_type_enum.create(op.get_bind())
    camera_movement_enum.create(op.get_bind())
    
    # Create projects table
    op.create_table('projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', project_status_enum, nullable=False),
        sa.Column('current_stage', workflow_stage_enum, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_status'), 'projects', ['status'], unique=False)
    op.create_index(op.f('ix_projects_current_stage'), 'projects', ['current_stage'], unique=False)
    op.create_index(op.f('ix_projects_created_at'), 'projects', ['created_at'], unique=False)
    
    # Create screenplays table
    op.create_table('screenplays',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_current_version', sa.Boolean(), nullable=False),
        sa.Column('approval_status', approval_status_enum, nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_screenplays_project_id'), 'screenplays', ['project_id'], unique=False)
    op.create_index(op.f('ix_screenplays_version'), 'screenplays', ['project_id', 'version'], unique=True)
    
    # Create screenplay_versions table
    op.create_table('screenplay_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('screenplay_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('changes_summary', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['screenplay_id'], ['screenplays.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create characters table
    op.create_table('characters',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('importance_level', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('age', sa.String(length=50), nullable=True),
        sa.Column('gender', sa.String(length=50), nullable=True),
        sa.Column('height', sa.String(length=50), nullable=True),
        sa.Column('build', sa.String(length=50), nullable=True),
        sa.Column('hair_color', sa.String(length=50), nullable=True),
        sa.Column('hair_style', sa.String(length=100), nullable=True),
        sa.Column('eye_color', sa.String(length=50), nullable=True),
        sa.Column('skin_tone', sa.String(length=50), nullable=True),
        sa.Column('distinctive_features', sa.Text(), nullable=True),
        sa.Column('clothing_style', sa.Text(), nullable=True),
        sa.Column('personality_traits', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('first_appearance_scene', sa.String(length=255), nullable=True),
        sa.Column('total_scenes', sa.Integer(), nullable=True),
        sa.Column('midjourney_prompt', sa.Text(), nullable=True),
        sa.Column('selected_image_path', sa.String(length=500), nullable=True),
        sa.Column('approval_status', approval_status_enum, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_characters_project_id'), 'characters', ['project_id'], unique=False)
    
    # Create shot_divisions table
    op.create_table('shot_divisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('screenplay_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('total_shots', sa.Integer(), nullable=False),
        sa.Column('estimated_duration', sa.Float(), nullable=True),
        sa.Column('approval_status', approval_status_enum, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('csv_export_path', sa.String(length=500), nullable=True),
        sa.Column('excel_export_path', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['screenplay_id'], ['screenplays.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create shots table
    op.create_table('shots',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shot_division_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shot_number', sa.Integer(), nullable=False),
        sa.Column('scene_heading', sa.String(length=500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('dialogue', sa.Text(), nullable=True),
        sa.Column('shot_type', shot_type_enum, nullable=True),
        sa.Column('camera_angle', sa.String(length=100), nullable=True),
        sa.Column('camera_movement', camera_movement_enum, nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('characters_present', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('props_needed', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('lighting_notes', sa.Text(), nullable=True),
        sa.Column('visual_style', sa.Text(), nullable=True),
        sa.Column('physics_notes', sa.Text(), nullable=True),
        sa.Column('continuity_notes', sa.Text(), nullable=True),
        sa.Column('midjourney_prompt', sa.Text(), nullable=True),
        sa.Column('selected_image_path', sa.String(length=500), nullable=True),
        sa.Column('video_status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['shot_division_id'], ['shot_divisions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shots_shot_division_id'), 'shots', ['shot_division_id'], unique=False)
    op.create_index(op.f('ix_shots_shot_number'), 'shots', ['shot_division_id', 'shot_number'], unique=True)
    
    # Create production_plans table
    op.create_table('production_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('visual_style', sa.String(length=255), nullable=True),
        sa.Column('aspect_ratio', sa.String(length=50), nullable=True),
        sa.Column('resolution', sa.String(length=50), nullable=True),
        sa.Column('frame_rate', sa.String(length=50), nullable=True),
        sa.Column('timeline_days', sa.Integer(), nullable=True),
        sa.Column('pre_production_days', sa.Integer(), nullable=False),
        sa.Column('production_days', sa.Integer(), nullable=False),
        sa.Column('post_production_days', sa.Integer(), nullable=False),
        sa.Column('estimated_budget', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('visual_consistency', sa.String(length=100), nullable=True),
        sa.Column('character_continuity', sa.String(length=100), nullable=True),
        sa.Column('physics_realism', sa.String(length=100), nullable=True),
        sa.Column('locations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('risk_assessment', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('pdf_export_path', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create approval_requests table
    op.create_table('approval_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stage', workflow_stage_enum, nullable=False),
        sa.Column('approval_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('approval_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('options', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', approval_status_enum, nullable=False),
        sa.Column('assigned_to', sa.String(length=255), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('requested_at', sa.DateTime(), nullable=False),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('approved_by', sa.String(length=255), nullable=True),
        sa.Column('selected_option', sa.String(length=255), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('revision_notes', sa.Text(), nullable=True),
        sa.Column('response_time_seconds', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_approval_requests_project_id'), 'approval_requests', ['project_id'], unique=False)
    op.create_index(op.f('ix_approval_requests_status'), 'approval_requests', ['status'], unique=False)
    op.create_index(op.f('ix_approval_requests_assigned_to'), 'approval_requests', ['assigned_to'], unique=False)
    
    # Create data_exports table
    op.create_table('data_exports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('export_type', sa.String(length=50), nullable=False),
        sa.Column('data_type', sa.String(length=50), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('record_count', sa.Integer(), nullable=True),
        sa.Column('download_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_exports_project_id'), 'data_exports', ['project_id'], unique=False)
    op.create_index(op.f('ix_data_exports_created_at'), 'data_exports', ['created_at'], unique=False)
    
    # Create user_activities table
    op.create_table('user_activities',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_activities_user_id'), 'user_activities', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_activities_created_at'), 'user_activities', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('user_activities')
    op.drop_table('data_exports')
    op.drop_table('approval_requests')
    op.drop_table('production_plans')
    op.drop_table('shots')
    op.drop_table('shot_divisions')
    op.drop_table('characters')
    op.drop_table('screenplay_versions')
    op.drop_table('screenplays')
    op.drop_table('projects')
    
    # Drop enum types
    postgresql.ENUM(name='cameramovement').drop(op.get_bind())
    postgresql.ENUM(name='shottype').drop(op.get_bind())
    postgresql.ENUM(name='approvalstatus').drop(op.get_bind())
    postgresql.ENUM(name='workflowstage').drop(op.get_bind())
    postgresql.ENUM(name='projectstatus').drop(op.get_bind())