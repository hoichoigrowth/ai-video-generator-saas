import asyncio
from typing import Dict, Any, Optional, List
import logging
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from core.exceptions import GoogleDocsError
from core.utils import generate_unique_id
import json

logger = logging.getLogger(__name__)

class GoogleDocsService:
    """Enhanced Google Docs service for screenplay and document management"""
    
    def __init__(self, credentials_path: Optional[str] = None, token_info: Optional[Dict] = None):
        self.credentials_path = credentials_path
        self.token_info = token_info
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Docs API service"""
        try:
            # In production, implement proper OAuth2 flow
            # For now, assume service account or valid credentials
            if self.token_info:
                credentials = Credentials.from_authorized_user_info(self.token_info)
                self.service = build('docs', 'v1', credentials=credentials)
            else:
                # Mock service for development
                logger.warning("Google Docs service running in mock mode")
                self.service = None
        except Exception as e:
            logger.error(f"Failed to initialize Google Docs service: {e}")
            raise GoogleDocsError(f"Service initialization failed: {str(e)}")
    
    async def create_screenplay_doc(
        self, 
        title: str, 
        screenplay_content: str,
        project_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new Google Doc for screenplay with proper formatting"""
        try:
            if not self.service:
                # Mock response for development
                doc_id = f"mock_doc_{generate_unique_id()[:8]}"
                return {
                    "document_id": doc_id,
                    "document_url": f"https://docs.google.com/document/d/{doc_id}/edit",
                    "title": title,
                    "created": True,
                    "mock": True
                }
            
            # Create document
            document_body = {
                'title': title
            }
            
            doc = self.service.documents().create(body=document_body).execute()
            document_id = doc.get('documentId')
            
            # Format and insert screenplay content
            await self._format_screenplay_content(document_id, screenplay_content)
            
            # Add metadata as comments or document properties
            if metadata:
                await self._add_document_metadata(document_id, metadata, project_id)
            
            document_url = f"https://docs.google.com/document/d/{document_id}/edit"
            
            logger.info(f"Created Google Doc for project {project_id}: {document_id}")
            
            return {
                "document_id": document_id,
                "document_url": document_url,
                "title": title,
                "created": True,
                "content_length": len(screenplay_content)
            }
            
        except HttpError as e:
            logger.error(f"Google Docs API error: {e}")
            raise GoogleDocsError(f"Failed to create document: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating document: {e}")
            raise GoogleDocsError(f"Document creation failed: {str(e)}")
    
    async def update_screenplay_doc(
        self, 
        document_id: str, 
        new_content: str,
        preserve_comments: bool = True
    ) -> Dict[str, Any]:
        """Update existing screenplay document with new content"""
        try:
            if not self.service:
                # Mock response for development
                return {
                    "document_id": document_id,
                    "updated": True,
                    "content_length": len(new_content),
                    "mock": True
                }
            
            # Get current document to preserve structure
            doc = self.service.documents().get(documentId=document_id).execute()
            
            # Clear existing content (keeping title)
            await self._clear_document_content(document_id)
            
            # Insert new formatted content
            await self._format_screenplay_content(document_id, new_content)
            
            logger.info(f"Updated Google Doc: {document_id}")
            
            return {
                "document_id": document_id,
                "updated": True,
                "content_length": len(new_content),
                "document_url": f"https://docs.google.com/document/d/{document_id}/edit"
            }
            
        except HttpError as e:
            logger.error(f"Google Docs API error updating document: {e}")
            raise GoogleDocsError(f"Failed to update document: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error updating document: {e}")
            raise GoogleDocsError(f"Document update failed: {str(e)}")
    
    async def _format_screenplay_content(self, document_id: str, content: str):
        """Format screenplay content with proper styles"""
        if not self.service:
            return
        
        try:
            # Split content into lines for formatting
            lines = content.split('\\n')
            requests = []
            
            # Insert content
            requests.append({
                'insertText': {
                    'location': {'index': 1},
                    'text': content
                }
            })
            
            # Apply formatting (simplified version)
            # In production, you'd apply specific screenplay formatting
            requests.extend(self._generate_screenplay_formatting_requests(content))
            
            # Execute batch update
            self.service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()
            
        except Exception as e:
            logger.error(f"Error formatting screenplay content: {e}")
            # Continue without formatting rather than failing
    
    def _generate_screenplay_formatting_requests(self, content: str) -> List[Dict[str, Any]]:
        """Generate formatting requests for screenplay elements"""
        requests = []
        
        # This is a simplified version - in production you'd implement
        # full screenplay formatting with proper styles for:
        # - Scene headings (bold, uppercase)
        # - Character names (centered, uppercase)
        # - Dialogue (indented)
        # - Action lines (standard)
        # - Transitions (right-aligned)
        
        # For now, just apply basic formatting
        requests.append({
            'updateTextStyle': {
                'range': {
                    'startIndex': 1,
                    'endIndex': len(content) + 1
                },
                'textStyle': {
                    'fontSize': {'magnitude': 12, 'unit': 'PT'},
                    'fontFamily': 'Courier New'
                },
                'fields': 'fontSize,fontFamily'
            }
        })
        
        return requests
    
    async def _clear_document_content(self, document_id: str):
        """Clear document content while preserving structure"""
        if not self.service:
            return
        
        try:
            # Get document to find content length
            doc = self.service.documents().get(documentId=document_id).execute()
            content_length = len(doc.get('body', {}).get('content', []))
            
            if content_length > 1:
                # Delete all content except the first character (title)
                requests = [{
                    'deleteContentRange': {
                        'range': {
                            'startIndex': 1,
                            'endIndex': content_length
                        }
                    }
                }]
                
                self.service.documents().batchUpdate(
                    documentId=document_id,
                    body={'requests': requests}
                ).execute()
                
        except Exception as e:
            logger.error(f"Error clearing document content: {e}")
    
    async def _add_document_metadata(
        self, 
        document_id: str, 
        metadata: Dict[str, Any],
        project_id: str
    ):
        """Add metadata to document as comments or properties"""
        if not self.service:
            return
        
        try:
            # Add project information as a comment at the beginning
            metadata_text = f"Project ID: {project_id}\\n"
            metadata_text += f"Generated: {metadata.get('timestamp', 'Unknown')}\\n"
            metadata_text += f"Version: {metadata.get('version', '1.0')}\\n"
            
            if metadata.get('providers'):
                metadata_text += f"AI Providers: {', '.join(metadata['providers'])}\\n"
            
            # In production, you might add this as a header or footer
            # For now, we'll skip adding metadata to keep it simple
            
        except Exception as e:
            logger.error(f"Error adding document metadata: {e}")
    
    async def get_document_info(self, document_id: str) -> Dict[str, Any]:
        """Get document information and stats"""
        try:
            if not self.service:
                return {
                    "document_id": document_id,
                    "title": "Mock Document",
                    "mock": True
                }
            
            doc = self.service.documents().get(documentId=document_id).execute()
            
            return {
                "document_id": document_id,
                "title": doc.get('title', 'Untitled'),
                "revision_id": doc.get('revisionId'),
                "document_url": f"https://docs.google.com/document/d/{document_id}/edit",
                "created_time": doc.get('createdTime'),
                "modified_time": doc.get('modifiedTime')
            }
            
        except HttpError as e:
            logger.error(f"Error getting document info: {e}")
            raise GoogleDocsError(f"Failed to get document info: {str(e)}")
    
    async def share_document(
        self, 
        document_id: str, 
        email_addresses: List[str],
        role: str = "reader"
    ) -> Dict[str, Any]:
        """Share document with specified users"""
        try:
            if not self.service:
                return {
                    "document_id": document_id,
                    "shared_with": email_addresses,
                    "role": role,
                    "mock": True
                }
            
            # Use Drive API to share the document
            drive_service = build('drive', 'v3', credentials=self.service._http.credentials)
            
            for email in email_addresses:
                permission = {
                    'type': 'user',
                    'role': role,
                    'emailAddress': email
                }
                
                drive_service.permissions().create(
                    fileId=document_id,
                    body=permission,
                    sendNotificationEmail=True
                ).execute()
            
            return {
                "document_id": document_id,
                "shared_with": email_addresses,
                "role": role,
                "success": True
            }
            
        except HttpError as e:
            logger.error(f"Error sharing document: {e}")
            raise GoogleDocsError(f"Failed to share document: {str(e)}")
    
    async def create_doc(self, title: str, content: str) -> str:
        """Legacy method for backward compatibility"""
        result = await self.create_screenplay_doc(title, content, "legacy_project")
        return result.get("document_id", "")
    
    async def update_doc(self, doc_id: str, content: str) -> bool:
        """Legacy method for backward compatibility"""
        try:
            await self.update_screenplay_doc(doc_id, content)
            return True
        except Exception:
            return False