"""
MinIO/S3 Storage Service - Replacing Google Docs and file storage
Handles document storage, versioning, and file management
"""

import asyncio
import aiofiles
import tempfile
import os
from typing import Optional, List, Dict, Any, BinaryIO
from datetime import datetime, timedelta
from minio import Minio
from minio.error import S3Error
import logging
from pathlib import Path
import uuid
import mimetypes
from urllib.parse import urlparse

from config.settings import settings
from core.exceptions import AIVideoGeneratorException

logger = logging.getLogger(__name__)

class StorageError(AIVideoGeneratorException):
    """Storage service specific errors"""
    pass

class MinIOStorageService:
    """
    MinIO storage service for documents, images, and videos
    Replaces Google Docs file storage with self-hosted solution
    """
    
    def __init__(self):
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        self.bucket_name = settings.minio_bucket_name
        self._initialized = False
    
    async def initialize(self):
        """Initialize MinIO client and ensure bucket exists"""
        if self._initialized:
            return
            
        try:
            # Run sync operations in thread pool
            loop = asyncio.get_event_loop()
            
            # Check if bucket exists, create if not
            bucket_exists = await loop.run_in_executor(
                None, self.client.bucket_exists, self.bucket_name
            )
            
            if not bucket_exists:
                await loop.run_in_executor(
                    None, self.client.make_bucket, self.bucket_name
                )
                logger.info(f"Created MinIO bucket: {self.bucket_name}")
            
            # Set bucket policy for public read access to images/videos (optional)
            # await self._set_public_policy()
            
            self._initialized = True
            logger.info("MinIO storage service initialized successfully")
            
        except S3Error as e:
            logger.error(f"MinIO initialization failed: {e}")
            raise StorageError(f"Failed to initialize storage: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during MinIO init: {e}")
            raise StorageError(f"Storage initialization error: {str(e)}")
    
    async def store_screenplay(
        self, 
        project_id: str, 
        screenplay_id: str,
        content: str,
        version: int = 1,
        content_type: str = "text/plain"
    ) -> Dict[str, str]:
        """
        Store screenplay content as file
        Returns storage paths for both text and markdown versions
        """
        await self.initialize()
        
        try:
            # Generate file paths
            base_path = f"projects/{project_id}/screenplays/{screenplay_id}"
            text_path = f"{base_path}/v{version}/screenplay.txt"
            markdown_path = f"{base_path}/v{version}/screenplay.md"
            
            # Create temporary files
            async with aiofiles.tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                await temp_file.write(content)
                temp_file_path = temp_file.name
            
            # Upload text version
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.client.fput_object,
                self.bucket_name,
                text_path,
                temp_file_path,
                content_type
            )
            
            # Convert to markdown and upload
            markdown_content = self._convert_to_markdown(content)
            async with aiofiles.tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as temp_md_file:
                await temp_md_file.write(markdown_content)
                temp_md_path = temp_md_file.name
            
            await loop.run_in_executor(
                None,
                self.client.fput_object,
                self.bucket_name,
                markdown_path,
                temp_md_path,
                "text/markdown"
            )
            
            # Clean up temp files
            os.unlink(temp_file_path)
            os.unlink(temp_md_path)
            
            logger.info(f"Stored screenplay {screenplay_id} version {version}")
            
            return {
                "text_path": text_path,
                "markdown_path": markdown_path,
                "text_url": self._get_presigned_url(text_path),
                "markdown_url": self._get_presigned_url(markdown_path)
            }
            
        except Exception as e:
            logger.error(f"Failed to store screenplay: {e}")
            raise StorageError(f"Screenplay storage failed: {str(e)}")
    
    async def get_screenplay(self, file_path: str) -> str:
        """Retrieve screenplay content from storage"""
        await self.initialize()
        
        try:
            loop = asyncio.get_event_loop()
            
            # Create temporary file to download content
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Download file
            await loop.run_in_executor(
                None,
                self.client.fget_object,
                self.bucket_name,
                file_path,
                temp_path
            )
            
            # Read content
            async with aiofiles.open(temp_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            # Clean up
            os.unlink(temp_path)
            
            return content
            
        except S3Error as e:
            logger.error(f"Failed to retrieve screenplay: {e}")
            raise StorageError(f"Screenplay retrieval failed: {str(e)}")
    
    async def store_image(
        self, 
        project_id: str, 
        image_data: bytes,
        filename: str,
        category: str = "scenes"  # scenes, characters, storyboard
    ) -> Dict[str, str]:
        """Store image file and return access information"""
        await self.initialize()
        
        try:
            # Generate unique filename
            file_extension = Path(filename).suffix.lower()
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = f"projects/{project_id}/{category}/{unique_filename}"
            
            # Detect content type
            content_type = mimetypes.guess_type(filename)[0] or 'image/jpeg'
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(image_data)
                temp_path = temp_file.name
            
            # Upload to MinIO
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.client.fput_object,
                self.bucket_name,
                file_path,
                temp_path,
                content_type
            )
            
            # Clean up
            os.unlink(temp_path)
            
            return {
                "file_path": file_path,
                "url": self._get_presigned_url(file_path),
                "public_url": self._get_public_url(file_path),
                "content_type": content_type
            }
            
        except Exception as e:
            logger.error(f"Failed to store image: {e}")
            raise StorageError(f"Image storage failed: {str(e)}")
    
    async def store_video(
        self, 
        project_id: str, 
        video_data: bytes,
        filename: str
    ) -> Dict[str, str]:
        """Store video file and return access information"""
        await self.initialize()
        
        try:
            # Generate unique filename
            file_extension = Path(filename).suffix.lower()
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = f"projects/{project_id}/videos/{unique_filename}"
            
            # Detect content type
            content_type = mimetypes.guess_type(filename)[0] or 'video/mp4'
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(video_data)
                temp_path = temp_file.name
            
            # Upload to MinIO
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.client.fput_object,
                self.bucket_name,
                file_path,
                temp_path,
                content_type
            )
            
            # Clean up
            os.unlink(temp_path)
            
            return {
                "file_path": file_path,
                "url": self._get_presigned_url(file_path),
                "public_url": self._get_public_url(file_path),
                "content_type": content_type
            }
            
        except Exception as e:
            logger.error(f"Failed to store video: {e}")
            raise StorageError(f"Video storage failed: {str(e)}")
    
    async def store_export_file(
        self, 
        project_id: str, 
        file_data: bytes,
        filename: str,
        export_type: str = "csv"
    ) -> Dict[str, str]:
        """Store exported data files (CSV, Excel, PDF)"""
        await self.initialize()
        
        try:
            # Generate path
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            safe_filename = filename.replace(" ", "_").replace("/", "_")
            file_path = f"projects/{project_id}/exports/{timestamp}_{safe_filename}"
            
            # Detect content type
            content_type_map = {
                "csv": "text/csv",
                "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "pdf": "application/pdf",
                "json": "application/json"
            }
            content_type = content_type_map.get(export_type, "application/octet-stream")
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(file_data)
                temp_path = temp_file.name
            
            # Upload to MinIO
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.client.fput_object,
                self.bucket_name,
                file_path,
                temp_path,
                content_type
            )
            
            # Clean up
            os.unlink(temp_path)
            
            return {
                "file_path": file_path,
                "url": self._get_presigned_url(file_path, expires=timedelta(days=7)),
                "content_type": content_type,
                "size": len(file_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to store export file: {e}")
            raise StorageError(f"Export file storage failed: {str(e)}")
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from storage"""
        await self.initialize()
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.client.remove_object,
                self.bucket_name,
                file_path
            )
            
            logger.info(f"Deleted file: {file_path}")
            return True
            
        except S3Error as e:
            if e.code == 'NoSuchKey':
                logger.warning(f"File not found for deletion: {file_path}")
                return True  # Already deleted
            logger.error(f"Failed to delete file: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting file: {e}")
            return False
    
    async def list_project_files(self, project_id: str, category: str = None) -> List[Dict[str, Any]]:
        """List all files for a project"""
        await self.initialize()
        
        try:
            prefix = f"projects/{project_id}/"
            if category:
                prefix += f"{category}/"
            
            loop = asyncio.get_event_loop()
            objects = await loop.run_in_executor(
                None,
                lambda: list(self.client.list_objects(self.bucket_name, prefix=prefix, recursive=True))
            )
            
            files = []
            for obj in objects:
                files.append({
                    "path": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "etag": obj.etag,
                    "content_type": obj.content_type,
                    "url": self._get_presigned_url(obj.object_name)
                })
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list project files: {e}")
            raise StorageError(f"File listing failed: {str(e)}")
    
    async def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file information without downloading"""
        await self.initialize()
        
        try:
            loop = asyncio.get_event_loop()
            stat = await loop.run_in_executor(
                None,
                self.client.stat_object,
                self.bucket_name,
                file_path
            )
            
            return {
                "path": file_path,
                "size": stat.size,
                "last_modified": stat.last_modified,
                "etag": stat.etag,
                "content_type": stat.content_type,
                "metadata": stat.metadata,
                "url": self._get_presigned_url(file_path)
            }
            
        except S3Error as e:
            if e.code == 'NoSuchKey':
                return None
            logger.error(f"Failed to get file info: {e}")
            raise StorageError(f"File info retrieval failed: {str(e)}")
    
    def _get_presigned_url(self, file_path: str, expires: timedelta = timedelta(hours=24)) -> str:
        """Generate presigned URL for file access"""
        try:
            return self.client.presigned_get_object(
                self.bucket_name,
                file_path,
                expires=expires
            )
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return ""
    
    def _get_public_url(self, file_path: str) -> str:
        """Generate public URL (if bucket is public)"""
        if settings.minio_secure:
            protocol = "https"
        else:
            protocol = "http"
        
        return f"{protocol}://{settings.minio_endpoint}/{self.bucket_name}/{file_path}"
    
    def _convert_to_markdown(self, screenplay_content: str) -> str:
        """Convert screenplay text to markdown format"""
        lines = screenplay_content.split('\n')
        markdown_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                markdown_lines.append('')
                continue
            
            # Scene headings
            if line.upper().startswith(('INT.', 'EXT.', 'FADE IN:', 'FADE OUT:')):
                markdown_lines.append(f"## {line}")
            
            # Character names (all caps)
            elif line.isupper() and len(line) < 50 and not line.startswith(('INT.', 'EXT.')):
                markdown_lines.append(f"**{line}**")
            
            # Regular lines
            else:
                markdown_lines.append(line)
        
        return '\n'.join(markdown_lines)
    
    async def cleanup_old_files(self, days: int = 30):
        """Clean up old temporary files and exports"""
        await self.initialize()
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # List objects in exports folder
            loop = asyncio.get_event_loop()
            objects = await loop.run_in_executor(
                None,
                lambda: list(self.client.list_objects(self.bucket_name, prefix="exports/", recursive=True))
            )
            
            deleted_count = 0
            for obj in objects:
                if obj.last_modified < cutoff_date:
                    await loop.run_in_executor(
                        None,
                        self.client.remove_object,
                        self.bucket_name,
                        obj.object_name
                    )
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old files")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old files: {e}")

# Global storage service instance
storage_service = MinIOStorageService()

# Helper functions for common operations
async def store_screenplay_file(project_id: str, screenplay_id: str, content: str, version: int = 1) -> Dict[str, str]:
    """Helper function to store screenplay"""
    return await storage_service.store_screenplay(project_id, screenplay_id, content, version)

async def get_screenplay_content(file_path: str) -> str:
    """Helper function to retrieve screenplay"""
    return await storage_service.get_screenplay(file_path)

async def store_project_image(project_id: str, image_data: bytes, filename: str, category: str = "scenes") -> Dict[str, str]:
    """Helper function to store project images"""
    return await storage_service.store_image(project_id, image_data, filename, category)

async def store_project_video(project_id: str, video_data: bytes, filename: str) -> Dict[str, str]:
    """Helper function to store project videos"""
    return await storage_service.store_video(project_id, video_data, filename)