import asyncio
import json
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent
from core.utils import sanitize_prompt, generate_unique_id, get_utc_now, extract_scene_headings
from core.exceptions import AgentProcessingError, ModelAPIError
from core.models import Shot, ShotType, CameraMovement
import time
import re

OPENAI_SHOT_DIVISION_PROMPT = """
You are a professional cinematographer specializing in vertical video content (9:16 aspect ratio) for AI-generated videos.

Analyze the screenplay and create a detailed shot division optimized for:
- Vertical video format (mobile-first viewing)
- AI video generation (Kling, Runway, Pika)
- Character consistency across shots
- Realistic physics and motion
- Dramatic storytelling for short-form content

**SCREENPLAY:**
{screenplay}

**TARGET SPECIFICATIONS:**
- Total duration: {target_duration} seconds
- Average shot length: {shot_duration} seconds
- Vertical format: 9:16 aspect ratio
- Character consistency: Required
- Physics realism: High priority

**OUTPUT FORMAT (JSON):**
Return a JSON object with this exact structure:
{{
  "shots": [
    {{
      "shot_number": 1,
      "scene_heading": "INT. BEDROOM - NIGHT",
      "description": "Close-up of SARAH's face as she awakens",
      "dialogue": "Where am I?",
      "shot_type": "close_up",
      "camera_angle": "slightly low",
      "camera_movement": "static",
      "duration_seconds": 3.0,
      "characters_present": ["SARAH"],
      "lighting_notes": "Soft moonlight through window",
      "location": "bedroom",
      "props_needed": ["bed", "pillow", "window"],
      "visual_style": "cinematic, moody",
      "physics_notes": "Natural head movement, realistic hair fall",
      "continuity_notes": "Sarah wearing white nightgown",
      "midjourney_style": "cinematic portrait, soft lighting, 9:16"
    }}
  ],
  "total_shots": 25,
  "estimated_duration": 75.0,
  "scene_breakdown": {{
    "INT. BEDROOM - NIGHT": [1, 2, 3],
    "EXT. GARDEN - DAY": [4, 5, 6, 7]
  }}
}}

**SHOT REQUIREMENTS:**
1. Each shot duration: 2-5 seconds
2. Clear character focus (max 2 characters per shot)
3. Vertical composition (important elements in center)
4. Realistic physics (gravity, momentum, lighting)
5. Consistent character appearance
6. Props and continuity tracking
7. Cinematic quality for AI generation

**IMPORTANT:**
- Return ONLY valid JSON, no additional text
- Use exact field names as shown
- Include all required fields for each shot
- Ensure shot numbers are sequential
- Match total duration to target
"""

class OpenAIShotDivisionAgent(BaseAgent):
    """OpenAI-powered shot division agent with structured output and validation"""
    
    async def process(
        self, 
        screenplay: str, 
        target_duration: float = 60.0,
        shot_duration: float = 3.0,
        vertical_format: bool = True,
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process screenplay into structured shot division"""
        processing_id = generate_unique_id()
        start_time = time.time()
        
        try:
            llm = self.llms.get("openai")
            if not llm:
                raise AgentProcessingError("OpenAIShotDivisionAgent", "OpenAI LLM not configured")
            
            # Sanitize and validate input
            sanitized_screenplay = sanitize_prompt(screenplay, max_length=8000)
            if len(sanitized_screenplay) < 200:
                raise AgentProcessingError("OpenAIShotDivisionAgent", "Screenplay too short for shot division")
            
            # Prepare prompt with parameters
            prompt = OPENAI_SHOT_DIVISION_PROMPT.format(
                screenplay=sanitized_screenplay,
                target_duration=target_duration,
                shot_duration=shot_duration
            )
            
            if custom_instructions:
                prompt += f"\n\nAdditional Instructions: {custom_instructions}"
            
            # Make the API call with retries
            self.logger.info(f"[{processing_id}] Starting OpenAI shot division processing")
            
            result = await asyncio.to_thread(
                self._run_with_retries, 
                llm.invoke, 
                prompt
            )
            
            processing_time = time.time() - start_time
            raw_content = result.content if hasattr(result, 'content') else str(result)
            
            # Parse JSON response
            try:
                # Clean the response (remove code blocks if present)
                json_content = self._extract_json_from_response(raw_content)
                shot_data = json.loads(json_content)
                
                # Validate and structure the response
                structured_shots = self._validate_and_structure_shots(shot_data)
                
            except (json.JSONDecodeError, KeyError) as e:
                self.logger.warning(f"[{processing_id}] JSON parsing failed, using fallback text parsing")
                structured_shots = self._fallback_text_parsing(raw_content, target_duration, shot_duration)
            
            # Extract metadata if available
            token_usage = getattr(result, 'response_metadata', {}).get('token_usage', {})
            
            response_data = {
                "processing_id": processing_id,
                "shots": structured_shots.get('shots', []),
                "total_shots": len(structured_shots.get('shots', [])),
                "estimated_duration": structured_shots.get('estimated_duration', 0.0),
                "scene_breakdown": structured_shots.get('scene_breakdown', {}),
                "provider": "openai",
                "model": getattr(llm, 'model_name', 'gpt-4'),
                "tokens_used": token_usage.get('total_tokens', 0),
                "processing_time": processing_time,
                "vertical_format": vertical_format,
                "raw_response": raw_content,
                "timestamp": get_utc_now(),
                "success": True
            }
            
            self.logger.info(f"[{processing_id}] Shot division completed: {len(structured_shots.get('shots', []))} shots in {processing_time:.2f}s")
            return response_data
            
        except Exception as e:
            error_msg = f"OpenAI shot division failed: {str(e)}"
            self.logger.error(f"[{processing_id}] {error_msg}")
            
            if "rate_limit" in str(e).lower():
                raise ModelAPIError("openai", f"Rate limit exceeded: {str(e)}")
            elif "api_key" in str(e).lower():
                raise ModelAPIError("openai", f"Invalid API key: {str(e)}")
            else:
                raise AgentProcessingError("OpenAIShotDivisionAgent", error_msg)
    
    def _extract_json_from_response(self, response: str) -> str:
        """Extract JSON from potentially formatted response"""
        # Remove code blocks if present
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*$', '', response)
        
        # Try to find JSON object boundaries
        start = response.find('{')
        end = response.rfind('}') + 1
        
        if start >= 0 and end > start:
            return response[start:end]
        
        return response.strip()
    
    def _validate_and_structure_shots(self, shot_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and structure shot data from AI response"""
        if 'shots' not in shot_data:
            raise ValueError("No shots found in response")
        
        structured_shots = []
        for shot_info in shot_data.get('shots', []):
            # Validate required fields and set defaults
            shot = {
                'shot_number': shot_info.get('shot_number', len(structured_shots) + 1),
                'scene_heading': shot_info.get('scene_heading', 'UNKNOWN SCENE'),
                'description': shot_info.get('description', ''),
                'dialogue': shot_info.get('dialogue'),
                'shot_type': self._validate_shot_type(shot_info.get('shot_type', 'medium')),
                'camera_angle': shot_info.get('camera_angle'),
                'camera_movement': self._validate_camera_movement(shot_info.get('camera_movement', 'static')),
                'duration_seconds': float(shot_info.get('duration_seconds', 3.0)),
                'characters_present': shot_info.get('characters_present', []),
                'lighting_notes': shot_info.get('lighting_notes'),
                'location': shot_info.get('location'),
                'props_needed': shot_info.get('props_needed', []),
                'visual_style': shot_info.get('visual_style'),
                'physics_notes': shot_info.get('physics_notes'),
                'continuity_notes': shot_info.get('continuity_notes'),
                'midjourney_style': shot_info.get('midjourney_style')
            }
            structured_shots.append(shot)
        
        total_duration = sum(shot['duration_seconds'] for shot in structured_shots)
        
        return {
            'shots': structured_shots,
            'total_shots': len(structured_shots),
            'estimated_duration': total_duration,
            'scene_breakdown': shot_data.get('scene_breakdown', {})
        }
    
    def _validate_shot_type(self, shot_type: str) -> str:
        """Validate shot type against enum values"""
        valid_types = [e.value for e in ShotType]
        return shot_type.lower() if shot_type.lower() in valid_types else 'medium'
    
    def _validate_camera_movement(self, movement: str) -> str:
        """Validate camera movement against enum values"""
        valid_movements = [e.value for e in CameraMovement]
        return movement.lower() if movement.lower() in valid_movements else 'static'
    
    def _fallback_text_parsing(self, content: str, target_duration: float, shot_duration: float) -> Dict[str, Any]:
        """Fallback text parsing when JSON parsing fails"""
        # Simple text-based shot extraction
        shots = []
        shot_number = 1
        
        # Look for numbered items or scene indicators
        lines = content.split('\n')
        current_shot = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this looks like a shot description
            if re.match(r'^\d+[.):]', line) or 'shot' in line.lower():
                if current_shot:
                    shots.append(current_shot)
                
                current_shot = {
                    'shot_number': shot_number,
                    'scene_heading': 'PARSED SCENE',
                    'description': line,
                    'dialogue': None,
                    'shot_type': 'medium',
                    'camera_angle': None,
                    'camera_movement': 'static',
                    'duration_seconds': shot_duration,
                    'characters_present': [],
                    'lighting_notes': None,
                    'location': None,
                    'props_needed': [],
                    'visual_style': None,
                    'physics_notes': None,
                    'continuity_notes': None,
                    'midjourney_style': None
                }
                shot_number += 1
        
        if current_shot:
            shots.append(current_shot)
        
        # If no shots found, create a basic division
        if not shots:
            estimated_shots = max(1, int(target_duration / shot_duration))
            for i in range(estimated_shots):
                shots.append({
                    'shot_number': i + 1,
                    'scene_heading': 'SCENE',
                    'description': f'Shot {i + 1} from screenplay',
                    'dialogue': None,
                    'shot_type': 'medium',
                    'camera_angle': None,
                    'camera_movement': 'static',
                    'duration_seconds': shot_duration,
                    'characters_present': [],
                    'lighting_notes': None,
                    'location': None,
                    'props_needed': [],
                    'visual_style': None,
                    'physics_notes': None,
                    'continuity_notes': None,
                    'midjourney_style': None
                })
        
        return {
            'shots': shots,
            'total_shots': len(shots),
            'estimated_duration': sum(shot['duration_seconds'] for shot in shots),
            'scene_breakdown': {}
        }