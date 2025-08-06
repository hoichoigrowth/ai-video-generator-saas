import re
import hashlib
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union
import asyncio
import aiohttp
from pathlib import Path
import json
import logging

# Logging setup
logger = logging.getLogger(__name__)

def generate_unique_id() -> str:
    """Generate a unique identifier"""
    return str(uuid.uuid4())

def generate_hash(content: str) -> str:
    """Generate SHA-256 hash of content"""
    return hashlib.sha256(content.encode()).hexdigest()

def get_utc_now() -> datetime:
    """Get current UTC datetime"""
    return datetime.now(timezone.utc)

def calculate_progress_percentage(current_stage: str, total_stages: List[str]) -> float:
    """Calculate progress percentage based on current stage"""
    if current_stage not in total_stages:
        return 0.0
    
    current_index = total_stages.index(current_stage)
    return (current_index / len(total_stages)) * 100

def extract_scene_headings(screenplay: str) -> List[str]:
    """Extract scene headings from screenplay text"""
    # Pattern for standard screenplay scene headings
    pattern = r'^(INT\.|EXT\.|FADE IN:|FADE OUT:).*$'
    headings = re.findall(pattern, screenplay, re.MULTILINE | re.IGNORECASE)
    return [heading.strip() for heading in headings]

def extract_character_names(screenplay: str) -> List[str]:
    """Extract character names from screenplay text"""
    # Pattern for character names (uppercase lines that are not scene headings or transitions)
    lines = screenplay.split('\n')
    character_names = set()
    
    scene_heading_pattern = r'^(INT\.|EXT\.|FADE|CUT TO:|DISSOLVE TO:)'
    transition_pattern = r'^(CUT TO:|FADE TO:|DISSOLVE TO:|FADE IN:|FADE OUT:)'
    
    for line in lines:
        line = line.strip()
        # Check if line is all caps and not a scene heading or transition
        if (line.isupper() and 
            not re.match(scene_heading_pattern, line, re.IGNORECASE) and
            not re.match(transition_pattern, line, re.IGNORECASE) and
            len(line) > 1 and len(line) < 30):
            character_names.add(line)
    
    return list(character_names)

def extract_dialogue_from_screenplay(screenplay: str) -> Dict[str, List[str]]:
    """Extract dialogue by character from screenplay"""
    lines = screenplay.split('\n')
    dialogue_by_character = {}
    current_character = None
    
    for line in lines:
        line = line.strip()
        
        # Check if this is a character name
        if line.isupper() and len(line) > 1 and len(line) < 30:
            # Verify it's not a scene heading or transition
            if not any(line.startswith(prefix) for prefix in 
                      ['INT.', 'EXT.', 'FADE', 'CUT TO:', 'DISSOLVE TO:']):
                current_character = line
                if current_character not in dialogue_by_character:
                    dialogue_by_character[current_character] = []
        
        # Check if this is dialogue (not empty, not all caps, follows a character)
        elif current_character and line and not line.isupper():
            # Skip action lines (parentheticals and scene descriptions)
            if not line.startswith('(') and not line.endswith(')'):
                dialogue_by_character[current_character].append(line)
    
    return dialogue_by_character

def validate_screenplay_format(screenplay: str) -> List[str]:
    """Validate screenplay format and return list of issues"""
    issues = []
    
    if not screenplay or len(screenplay.strip()) < 100:
        issues.append("Screenplay too short")
    
    # Check for scene headings
    scene_headings = extract_scene_headings(screenplay)
    if not scene_headings:
        issues.append("No scene headings found")
    
    # Check for character names
    characters = extract_character_names(screenplay)
    if not characters:
        issues.append("No character names found")
    
    # Check for dialogue
    dialogue = extract_dialogue_from_screenplay(screenplay)
    if not dialogue:
        issues.append("No dialogue found")
    
    return issues

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{int(minutes)}m {remaining_seconds:.1f}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{int(hours)}h {int(minutes)}m"

def calculate_estimated_duration(shots: List[Dict[str, Any]]) -> float:
    """Calculate estimated total duration from shots"""
    total_duration = 0.0
    for shot in shots:
        duration = shot.get('duration_seconds', 3.0)
        total_duration += duration
    return total_duration

def clean_filename(filename: str) -> str:
    """Clean filename for safe file system usage"""
    # Remove or replace invalid characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple underscores
    cleaned = re.sub(r'_+', '_', cleaned)
    # Trim and remove leading/trailing underscores
    return cleaned.strip('_')

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks of specified size"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

async def make_http_request(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Union[Dict, str]] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """Make async HTTP request with error handling"""
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.request(method, url, headers=headers, json=data if isinstance(data, dict) else None, data=data if isinstance(data, str) else None) as response:
                content = await response.text()
                
                if response.content_type == 'application/json':
                    return {
                        'status': response.status,
                        'data': json.loads(content),
                        'headers': dict(response.headers)
                    }
                else:
                    return {
                        'status': response.status,
                        'data': content,
                        'headers': dict(response.headers)
                    }
    except asyncio.TimeoutError:
        raise Exception(f"Request timeout after {timeout} seconds")
    except aiohttp.ClientError as e:
        raise Exception(f"HTTP client error: {str(e)}")
    except Exception as e:
        raise Exception(f"Request failed: {str(e)}")

def sanitize_prompt(prompt: str, max_length: int = 1000) -> str:
    """Sanitize prompt for AI model consumption"""
    # Remove excessive whitespace
    sanitized = re.sub(r'\s+', ' ', prompt.strip())
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rsplit(' ', 1)[0] + '...'
    
    # Remove potentially problematic characters
    sanitized = re.sub(r'[^\w\s\-.,!?:;()\'"]+', '', sanitized)
    
    return sanitized

def merge_dictionaries(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dictionaries(result[key], value)
        else:
            result[key] = value
    
    return result

def extract_urls_from_text(text: str) -> List[str]:
    """Extract URLs from text"""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(url_pattern, text)

def validate_aspect_ratio(width: int, height: int, target_ratio: str = "9:16") -> bool:
    """Validate if dimensions match target aspect ratio"""
    target_ratios = {
        "9:16": 9/16,
        "16:9": 16/9,
        "1:1": 1/1,
        "4:5": 4/5
    }
    
    if target_ratio not in target_ratios:
        return False
    
    actual_ratio = width / height
    target = target_ratios[target_ratio]
    
    # Allow 5% tolerance
    tolerance = 0.05
    return abs(actual_ratio - target) <= tolerance

def estimate_processing_time(
    stage: str,
    content_length: int,
    complexity_factor: float = 1.0
) -> float:
    """Estimate processing time for different stages"""
    base_times = {
        "screenplay_generation": 30,  # seconds per 1000 characters
        "shot_division": 20,
        "character_extraction": 15,
        "production_planning": 25,
        "scene_generation": 60,  # per scene
        "video_generation": 120   # per clip
    }
    
    base_time = base_times.get(stage, 30)
    content_factor = content_length / 1000
    
    return base_time * content_factor * complexity_factor

def create_midjourney_prompt(
    description: str,
    style: str = "cinematic",
    aspect_ratio: str = "9:16",
    additional_params: Optional[List[str]] = None
) -> str:
    """Create formatted Midjourney prompt"""
    prompt_parts = [description]
    
    # Add style
    if style:
        prompt_parts.append(f"--style {style}")
    
    # Add aspect ratio
    if aspect_ratio:
        prompt_parts.append(f"--ar {aspect_ratio}")
    
    # Add additional parameters
    if additional_params:
        prompt_parts.extend(additional_params)
    
    return " ".join(prompt_parts)

def create_kling_prompt(
    scene_description: str,
    duration: float = 3.0,
    camera_movement: str = "static",
    additional_instructions: Optional[str] = None
) -> str:
    """Create formatted Kling video generation prompt"""
    prompt_parts = [
        f"Create a {duration}-second video:",
        scene_description
    ]
    
    if camera_movement != "static":
        prompt_parts.append(f"Camera movement: {camera_movement}")
    
    if additional_instructions:
        prompt_parts.append(additional_instructions)
    
    return " ".join(prompt_parts)

class RetryMixin:
    """Mixin class for retry functionality"""
    
    @staticmethod
    async def retry_with_backoff(
        coro,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0
    ):
        """Retry coroutine with exponential backoff"""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return await coro
            except Exception as e:
                last_exception = e
                if attempt == max_retries - 1:
                    break
                
                delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
        
        raise last_exception

def safe_dict_get(dictionary: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """Safely get nested dictionary value using dot notation"""
    keys = key_path.split('.')
    value = dictionary
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value

def validate_video_url(url: str) -> bool:
    """Validate if URL points to a video file"""
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv']
    return any(url.lower().endswith(ext) for ext in video_extensions)

def validate_image_url(url: str) -> bool:
    """Validate if URL points to an image file"""
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']
    return any(url.lower().endswith(ext) for ext in image_extensions)