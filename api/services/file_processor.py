import os
import json
import asyncio
from typing import Dict, Any, Optional
import PyPDF2
import docx2txt
from PIL import Image
import io

class FileProcessor:
    def __init__(self):
        self.supported_types = {
            'text/plain': self.process_text,
            'application/pdf': self.process_pdf,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': self.process_docx,
            'image/jpeg': self.process_image,
            'image/png': self.process_image,
            'image/gif': self.process_image,
        }
    
    async def process_file(self, file_path: str, content_type: str) -> Dict[str, Any]:
        """Process a file based on its content type"""
        processor = self.supported_types.get(content_type)
        if not processor:
            return {
                'status': 'error',
                'message': f'Unsupported file type: {content_type}'
            }
        
        try:
            result = await processor(file_path)
            return {
                'status': 'success',
                'data': result
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def process_text(self, file_path: str) -> Dict[str, Any]:
        """Process text files"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {
            'type': 'text',
            'content': content,
            'word_count': len(content.split())
        }
    
    async def process_pdf(self, file_path: str) -> Dict[str, Any]:
        """Process PDF files"""
        text = ""
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                text += page.extract_text()
        return {
            'type': 'pdf',
            'content': text,
            'page_count': len(pdf_reader.pages),
            'word_count': len(text.split())
        }
    
    async def process_docx(self, file_path: str) -> Dict[str, Any]:
        """Process DOCX files"""
        text = docx2txt.process(file_path)
        return {
            'type': 'docx',
            'content': text,
            'word_count': len(text.split())
        }
    
    async def process_image(self, file_path: str) -> Dict[str, Any]:
        """Process image files"""
        with Image.open(file_path) as img:
            return {
                'type': 'image',
                'format': img.format,
                'size': img.size,
                'mode': img.mode
            }
    
    def get_text_from_file(self, file_path: str, content_type: str) -> Optional[str]:
        """Extract text content from a file"""
        if content_type == 'text/plain':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif content_type == 'application/pdf':
            text = ""
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text += page.extract_text()
            return text
        elif content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            return docx2txt.process(file_path)
        return None
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """Get file information"""
        file_stats = os.stat(file_path)
        return {
            'size': file_stats.st_size,
            'created': file_stats.st_ctime,
            'modified': file_stats.st_mtime,
            'extension': os.path.splitext(file_path)[1]
        }
    
    @staticmethod
    def extract_text(file_path: str) -> Optional[str]:
        """Extract text from a file based on its extension"""
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext in ['.txt', '.md', '.rtf']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif ext == '.pdf':
                text = ""
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                        text += page.extract_text()
                return text
            elif ext in ['.doc', '.docx']:
                return docx2txt.process(file_path)
        except Exception as e:
            print(f"Error extracting text: {e}")
            return None
        
        return None