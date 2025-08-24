import os
from typing import Optional
import PyPDF2
from docx import Document
import docx2txt

class FileProcessor:
    """Service to process different file types and extract text content."""
    
    @staticmethod
    def extract_text(file_path: str) -> Optional[str]:
        """
        Extract text content from various file types.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            Extracted text content or None if processing fails
        """
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.txt':
                return FileProcessor._read_txt(file_path)
            elif file_extension == '.md':
                return FileProcessor._read_txt(file_path)
            elif file_extension == '.rtf':
                return FileProcessor._read_txt(file_path)
            elif file_extension == '.doc':
                return FileProcessor._read_doc(file_path)
            elif file_extension == '.docx':
                return FileProcessor._read_docx(file_path)
            elif file_extension == '.pdf':
                return FileProcessor._read_pdf(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
                
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
            return None
    
    @staticmethod
    def _read_txt(file_path: str) -> str:
        """Read text from .txt, .md, or .rtf files."""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    @staticmethod
    def _read_doc(file_path: str) -> str:
        """Read text from .doc files using docx2txt."""
        try:
            return docx2txt.process(file_path)
        except Exception as e:
            print(f"Error reading .doc file: {str(e)}")
            return ""
    
    @staticmethod
    def _read_docx(file_path: str) -> str:
        """Read text from .docx files using python-docx."""
        try:
            doc = Document(file_path)
            text = []
            for paragraph in doc.paragraphs:
                text.append(paragraph.text)
            return '\n'.join(text)
        except Exception as e:
            print(f"Error reading .docx file: {str(e)}")
            return ""
    
    @staticmethod
    def _read_pdf(file_path: str) -> str:
        """Read text from .pdf files using PyPDF2."""
        try:
            text = []
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text.append(page.extract_text())
            return '\n'.join(text)
        except Exception as e:
            print(f"Error reading .pdf file: {str(e)}")
            return ""
    
    @staticmethod
    def get_file_info(file_path: str) -> dict:
        """
        Get basic information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        try:
            stat = os.stat(file_path)
            file_extension = os.path.splitext(file_path)[1].lower()
            
            return {
                "filename": os.path.basename(file_path),
                "extension": file_extension,
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created": stat.st_ctime,
                "modified": stat.st_mtime
            }
        except Exception as e:
            print(f"Error getting file info: {str(e)}")
            return {}

