"""
Custom Approval System - Replacing GoToHuman
Redis-based approval queue management with WebSocket notifications
"""

import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import redis.asyncio as redis
import logging

from database.connection import get_db_session
from database.models import ApprovalRequest, ApprovalStatus, WorkflowStage
from config.settings import settings
from core.exceptions import AIVideoGeneratorException

logger = logging.getLogger(__name__)

class ApprovalType(str, Enum):
    SCREENPLAY = "screenplay"
    SHOT_DIVISION = "shot_division" 
    CHARACTER_DESIGN = "character_design"
    SCENE_SELECTION = "scene_selection"
    VIDEO_APPROVAL = "video_approval"
    PRODUCTION_PLAN = "production_plan"

class ApprovalPriority(int, Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5

class ApprovalServiceError(AIVideoGeneratorException):
    """Approval service specific errors"""
    pass

class CustomApprovalService:
    """
    Custom approval system with Redis queue management
    Replaces GoToHuman with self-hosted solution
    """
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._initialized = False
        
        # Redis keys
        self.APPROVAL_QUEUE_KEY = "approval_queue"
        self.PENDING_APPROVALS_KEY = "pending_approvals"
        self.USER_ASSIGNMENTS_KEY = "user_assignments:{user_id}"
        self.NOTIFICATION_CHANNEL = "approval_notifications"
        
    async def initialize(self):
        """Initialize Redis connection"""
        if self._initialized:
            return
            
        try:
            self.redis_client = redis.from_url(settings.redis_url)
            await self.redis_client.ping()
            self._initialized = True
            logger.info("Approval service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize approval service: {e}")
            raise ApprovalServiceError(f"Initialization failed: {str(e)}")
    
    async def create_approval_request(
        self,
        project_id: str,
        stage: WorkflowStage,
        approval_type: ApprovalType,
        entity_id: str,
        title: str,
        description: str,
        approval_data: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
        assigned_to: Optional[str] = None,
        priority: ApprovalPriority = ApprovalPriority.NORMAL,
        due_date: Optional[datetime] = None
    ) -> str:
        """
        Create a new approval request
        Returns: approval_request_id
        """
        await self.initialize()
        
        try:
            approval_id = str(uuid.uuid4())
            
            # Create database record
            async with get_db_session() as session:
                approval_request = ApprovalRequest(
                    id=approval_id,
                    project_id=project_id,
                    stage=stage,
                    approval_type=approval_type.value,
                    entity_id=entity_id,
                    title=title,
                    description=description,
                    approval_data=approval_data,
                    options=options or {},
                    assigned_to=assigned_to,
                    priority=priority.value,
                    due_date=due_date,
                    status=ApprovalStatus.PENDING
                )
                
                session.add(approval_request)
                await session.commit()
            
            # Add to Redis queue
            queue_item = {
                "approval_id": approval_id,
                "project_id": project_id,
                "stage": stage.value,
                "type": approval_type.value,
                "title": title,
                "priority": priority.value,
                "created_at": datetime.utcnow().isoformat(),
                "assigned_to": assigned_to,
                "due_date": due_date.isoformat() if due_date else None
            }
            
            # Use priority scoring for queue ordering
            priority_score = self._calculate_priority_score(priority, datetime.utcnow(), due_date)
            
            await self.redis_client.zadd(
                self.APPROVAL_QUEUE_KEY,
                {json.dumps(queue_item): priority_score}
            )
            
            # Add to pending approvals set
            await self.redis_client.sadd(
                self.PENDING_APPROVALS_KEY,
                approval_id
            )
            
            # Assign to user if specified
            if assigned_to:
                await self.redis_client.sadd(
                    self.USER_ASSIGNMENTS_KEY.format(user_id=assigned_to),
                    approval_id
                )
            
            # Send notification
            await self._send_notification("approval_created", {
                "approval_id": approval_id,
                "project_id": project_id,
                "type": approval_type.value,
                "title": title,
                "assigned_to": assigned_to,
                "priority": priority.value
            })
            
            logger.info(f"Created approval request {approval_id} for project {project_id}")
            return approval_id
            
        except Exception as e:
            logger.error(f"Failed to create approval request: {e}")
            raise ApprovalServiceError(f"Failed to create approval: {str(e)}")
    
    async def get_pending_approvals(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        approval_type: Optional[ApprovalType] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get pending approval requests with optional filtering"""
        await self.initialize()
        
        try:
            # Get from Redis queue (ordered by priority)
            queue_items = await self.redis_client.zrevrange(
                self.APPROVAL_QUEUE_KEY, 
                0, limit - 1, 
                withscores=False
            )
            
            approvals = []
            for item in queue_items:
                queue_data = json.loads(item)
                approval_id = queue_data["approval_id"]
                
                # Apply filters
                if user_id and queue_data.get("assigned_to") != user_id:
                    continue
                    
                if project_id and queue_data["project_id"] != project_id:
                    continue
                    
                if approval_type and queue_data["type"] != approval_type.value:
                    continue
                
                # Get detailed data from database
                async with get_db_session() as session:
                    from sqlalchemy import select
                    result = await session.execute(
                        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
                    )
                    approval = result.scalar_one_or_none()
                    
                    if approval and approval.status == ApprovalStatus.PENDING:
                        approvals.append({
                            "id": approval.id,
                            "project_id": approval.project_id,
                            "stage": approval.stage.value,
                            "type": approval.approval_type,
                            "entity_id": approval.entity_id,
                            "title": approval.title,
                            "description": approval.description,
                            "approval_data": approval.approval_data,
                            "options": approval.options,
                            "priority": approval.priority,
                            "assigned_to": approval.assigned_to,
                            "created_at": approval.requested_at.isoformat(),
                            "due_date": approval.due_date.isoformat() if approval.due_date else None,
                            "queue_score": queue_data.get("priority", 0)
                        })
            
            return approvals
            
        except Exception as e:
            logger.error(f"Failed to get pending approvals: {e}")
            raise ApprovalServiceError(f"Failed to get approvals: {str(e)}")
    
    async def submit_approval_response(
        self,
        approval_id: str,
        user_id: str,
        approved: bool,
        selected_option: Optional[str] = None,
        feedback: Optional[str] = None,
        revision_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit approval response
        """
        await self.initialize()
        
        try:
            async with get_db_session() as session:
                from sqlalchemy import select, update
                
                # Get approval request
                result = await session.execute(
                    select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
                )
                approval = result.scalar_one_or_none()
                
                if not approval:
                    raise ApprovalServiceError("Approval request not found")
                
                if approval.status != ApprovalStatus.PENDING:
                    raise ApprovalServiceError("Approval request already processed")
                
                # Calculate response time
                response_time = (datetime.utcnow() - approval.requested_at).total_seconds()
                
                # Update approval status
                new_status = ApprovalStatus.APPROVED if approved else (
                    ApprovalStatus.REVISION_REQUESTED if revision_notes else ApprovalStatus.REJECTED
                )
                
                await session.execute(
                    update(ApprovalRequest)
                    .where(ApprovalRequest.id == approval_id)
                    .values(
                        status=new_status,
                        approved_at=datetime.utcnow(),
                        approved_by=user_id,
                        selected_option=selected_option,
                        feedback=feedback,
                        revision_notes=revision_notes,
                        response_time_seconds=int(response_time)
                    )
                )
                await session.commit()
            
            # Remove from Redis queue
            await self._remove_from_queue(approval_id)
            
            # Send notification
            await self._send_notification("approval_response", {
                "approval_id": approval_id,
                "project_id": approval.project_id,
                "approved": approved,
                "selected_option": selected_option,
                "user_id": user_id,
                "response_time": response_time
            })
            
            logger.info(f"Processed approval {approval_id}: approved={approved}")
            
            return {
                "approval_id": approval_id,
                "status": new_status.value,
                "approved": approved,
                "response_time": response_time,
                "processed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to submit approval response: {e}")
            raise ApprovalServiceError(f"Failed to submit response: {str(e)}")
    
    async def get_approval_history(
        self,
        project_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get approval history for a project"""
        try:
            async with get_db_session() as session:
                from sqlalchemy import select, desc
                
                result = await session.execute(
                    select(ApprovalRequest)
                    .where(ApprovalRequest.project_id == project_id)
                    .order_by(desc(ApprovalRequest.requested_at))
                    .limit(limit)
                )
                
                approvals = result.scalars().all()
                
                history = []
                for approval in approvals:
                    history.append({
                        "id": approval.id,
                        "stage": approval.stage.value,
                        "type": approval.approval_type,
                        "title": approval.title,
                        "status": approval.status.value,
                        "requested_at": approval.requested_at.isoformat(),
                        "approved_at": approval.approved_at.isoformat() if approval.approved_at else None,
                        "approved_by": approval.approved_by,
                        "selected_option": approval.selected_option,
                        "feedback": approval.feedback,
                        "response_time": approval.response_time_seconds
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"Failed to get approval history: {e}")
            raise ApprovalServiceError(f"Failed to get history: {str(e)}")
    
    async def reassign_approval(
        self,
        approval_id: str,
        new_assignee: str,
        reassigned_by: str,
        reason: Optional[str] = None
    ) -> bool:
        """Reassign approval to different user"""
        await self.initialize()
        
        try:
            async with get_db_session() as session:
                from sqlalchemy import select, update
                
                # Update database
                result = await session.execute(
                    select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
                )
                approval = result.scalar_one_or_none()
                
                if not approval or approval.status != ApprovalStatus.PENDING:
                    return False
                
                old_assignee = approval.assigned_to
                
                await session.execute(
                    update(ApprovalRequest)
                    .where(ApprovalRequest.id == approval_id)
                    .values(assigned_to=new_assignee)
                )
                await session.commit()
            
            # Update Redis assignments
            if old_assignee:
                await self.redis_client.srem(
                    self.USER_ASSIGNMENTS_KEY.format(user_id=old_assignee),
                    approval_id
                )
            
            await self.redis_client.sadd(
                self.USER_ASSIGNMENTS_KEY.format(user_id=new_assignee),
                approval_id
            )
            
            # Send notification
            await self._send_notification("approval_reassigned", {
                "approval_id": approval_id,
                "old_assignee": old_assignee,
                "new_assignee": new_assignee,
                "reassigned_by": reassigned_by,
                "reason": reason
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to reassign approval: {e}")
            return False
    
    async def cancel_approval(
        self,
        approval_id: str,
        cancelled_by: str,
        reason: str
    ) -> bool:
        """Cancel a pending approval request"""
        await self.initialize()
        
        try:
            async with get_db_session() as session:
                from sqlalchemy import update
                
                await session.execute(
                    update(ApprovalRequest)
                    .where(ApprovalRequest.id == approval_id)
                    .values(
                        status=ApprovalStatus.REJECTED,
                        approved_at=datetime.utcnow(),
                        approved_by=cancelled_by,
                        feedback=f"Cancelled: {reason}"
                    )
                )
                await session.commit()
            
            # Remove from queue
            await self._remove_from_queue(approval_id)
            
            # Send notification
            await self._send_notification("approval_cancelled", {
                "approval_id": approval_id,
                "cancelled_by": cancelled_by,
                "reason": reason
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel approval: {e}")
            return False
    
    async def get_user_workload(self, user_id: str) -> Dict[str, Any]:
        """Get user's current approval workload"""
        await self.initialize()
        
        try:
            # Get assigned approvals
            assigned_approvals = await self.redis_client.smembers(
                self.USER_ASSIGNMENTS_KEY.format(user_id=user_id)
            )
            
            # Get detailed stats from database
            async with get_db_session() as session:
                from sqlalchemy import select, func
                
                # Count by priority
                result = await session.execute(
                    select(
                        ApprovalRequest.priority,
                        func.count(ApprovalRequest.id)
                    )
                    .where(
                        ApprovalRequest.assigned_to == user_id,
                        ApprovalRequest.status == ApprovalStatus.PENDING
                    )
                    .group_by(ApprovalRequest.priority)
                )
                
                priority_counts = {row[0]: row[1] for row in result}
                
                # Get overdue count
                overdue_count = await session.scalar(
                    select(func.count(ApprovalRequest.id))
                    .where(
                        ApprovalRequest.assigned_to == user_id,
                        ApprovalRequest.status == ApprovalStatus.PENDING,
                        ApprovalRequest.due_date < datetime.utcnow()
                    )
                )
            
            return {
                "user_id": user_id,
                "total_pending": len(assigned_approvals),
                "priority_breakdown": priority_counts,
                "overdue_count": overdue_count or 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get user workload: {e}")
            return {"user_id": user_id, "total_pending": 0, "priority_breakdown": {}, "overdue_count": 0}
    
    def _calculate_priority_score(
        self, 
        priority: ApprovalPriority, 
        created_at: datetime, 
        due_date: Optional[datetime]
    ) -> float:
        """Calculate priority score for queue ordering"""
        base_score = priority.value * 1000
        
        # Age factor (older requests get higher priority)
        age_hours = (datetime.utcnow() - created_at).total_seconds() / 3600
        age_score = min(age_hours * 10, 500)  # Max 500 points for age
        
        # Due date factor
        due_score = 0
        if due_date:
            hours_until_due = (due_date - datetime.utcnow()).total_seconds() / 3600
            if hours_until_due < 0:  # Overdue
                due_score = 1000
            elif hours_until_due < 24:  # Due within 24 hours
                due_score = 500
            elif hours_until_due < 72:  # Due within 3 days
                due_score = 200
        
        return base_score + age_score + due_score
    
    async def _remove_from_queue(self, approval_id: str):
        """Remove approval from Redis queue"""
        try:
            # Find and remove from sorted set
            queue_items = await self.redis_client.zrange(self.APPROVAL_QUEUE_KEY, 0, -1)
            
            for item in queue_items:
                queue_data = json.loads(item)
                if queue_data["approval_id"] == approval_id:
                    await self.redis_client.zrem(self.APPROVAL_QUEUE_KEY, item)
                    break
            
            # Remove from pending set
            await self.redis_client.srem(self.PENDING_APPROVALS_KEY, approval_id)
            
            # Remove from user assignment
            async with get_db_session() as session:
                from sqlalchemy import select
                result = await session.execute(
                    select(ApprovalRequest.assigned_to).where(ApprovalRequest.id == approval_id)
                )
                assigned_to = result.scalar_one_or_none()
                
                if assigned_to:
                    await self.redis_client.srem(
                        self.USER_ASSIGNMENTS_KEY.format(user_id=assigned_to),
                        approval_id
                    )
            
        except Exception as e:
            logger.error(f"Failed to remove from queue: {e}")
    
    async def _send_notification(self, event_type: str, data: Dict[str, Any]):
        """Send notification via Redis pub/sub"""
        try:
            notification = {
                "event": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
            
            await self.redis_client.publish(
                self.NOTIFICATION_CHANNEL,
                json.dumps(notification)
            )
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    async def cleanup_expired_approvals(self):
        """Clean up expired approval requests"""
        await self.initialize()
        
        try:
            async with get_db_session() as session:
                from sqlalchemy import select, update
                
                # Find expired approvals
                expired = await session.execute(
                    select(ApprovalRequest)
                    .where(
                        ApprovalRequest.status == ApprovalStatus.PENDING,
                        ApprovalRequest.due_date < datetime.utcnow()
                    )
                )
                
                expired_approvals = expired.scalars().all()
                
                for approval in expired_approvals:
                    # Update to rejected
                    await session.execute(
                        update(ApprovalRequest)
                        .where(ApprovalRequest.id == approval.id)
                        .values(
                            status=ApprovalStatus.REJECTED,
                            approved_at=datetime.utcnow(),
                            feedback="Automatically rejected due to expiration"
                        )
                    )
                    
                    # Remove from queue
                    await self._remove_from_queue(str(approval.id))
                
                await session.commit()
                
                if expired_approvals:
                    logger.info(f"Cleaned up {len(expired_approvals)} expired approvals")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup expired approvals: {e}")

# Global approval service instance
approval_service = CustomApprovalService()

# Helper functions
async def create_screenplay_approval(
    project_id: str,
    screenplay_id: str,
    content: str,
    assigned_to: Optional[str] = None
) -> str:
    """Helper to create screenplay approval request"""
    return await approval_service.create_approval_request(
        project_id=project_id,
        stage=WorkflowStage.SCREENPLAY_GENERATION,
        approval_type=ApprovalType.SCREENPLAY,
        entity_id=screenplay_id,
        title="Screenplay Review Required",
        description="Please review the generated screenplay and approve or request revisions.",
        approval_data={"content": content[:1000] + "..." if len(content) > 1000 else content},
        assigned_to=assigned_to
    )

async def create_character_approval(
    project_id: str,
    character_id: str,
    character_designs: List[str],
    assigned_to: Optional[str] = None
) -> str:
    """Helper to create character design approval request"""
    return await approval_service.create_approval_request(
        project_id=project_id,
        stage=WorkflowStage.CHARACTER_DESIGN,
        approval_type=ApprovalType.CHARACTER_DESIGN,
        entity_id=character_id,
        title="Character Design Selection",
        description="Please select the best character design from the options.",
        approval_data={"designs": character_designs[:4]},  # Max 4 options
        options={"type": "single_select", "choices": character_designs},
        assigned_to=assigned_to
    )

async def create_scene_approval(
    project_id: str,
    scene_id: str,
    image_options: List[str],
    assigned_to: Optional[str] = None
) -> str:
    """Helper to create scene image approval request"""
    return await approval_service.create_approval_request(
        project_id=project_id,
        stage=WorkflowStage.SCENE_GENERATION,
        approval_type=ApprovalType.SCENE_SELECTION,
        entity_id=scene_id,
        title="Scene Image Selection",
        description="Please select the best scene image from the generated options.",
        approval_data={"images": image_options[:4]},  # Max 4 options
        options={"type": "single_select", "choices": image_options},
        assigned_to=assigned_to
    )