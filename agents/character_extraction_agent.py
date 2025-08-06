import asyncio
import json
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent
from core.utils import sanitize_prompt, generate_unique_id, get_utc_now, extract_character_names
from core.exceptions import AgentProcessingError, ModelAPIError
from core.models import CharacterDesign
import time
import re

CHARACTER_EXTRACTION_PROMPT = """
You are a professional character designer and casting director. Analyze the screenplay and extract detailed character information for AI image generation.

**SCREENPLAY:**
{screenplay}

**EXTRACTION OBJECTIVES:**
1. Identify ALL characters (speaking and non-speaking)
2. Extract physical descriptions from text
3. Infer character traits from dialogue and actions
4. Create detailed character profiles
5. Generate Midjourney prompts for character consistency

**OUTPUT FORMAT (JSON):**
Return a JSON object with this exact structure:
{{
  "characters": [
    {{
      "name": "CHARACTER_NAME",
      "description": "Brief character description",
      "physical_attributes": {{
        "age": "estimated age or age range",
        "gender": "male/female/other",
        "height": "short/medium/tall",
        "build": "slim/medium/athletic/heavy",
        "hair_color": "color",
        "hair_style": "style description",
        "eye_color": "color",
        "skin_tone": "description",
        "distinctive_features": "scars, tattoos, etc.",
        "clothing_style": "typical attire"
      }},
      "personality_traits": [
        "trait1", "trait2", "trait3"
      ],
      "midjourney_prompt": "detailed prompt for consistent character generation",
      "importance_level": "main/supporting/background",
      "first_appearance_scene": "scene where character first appears",
      "total_scenes": "estimated number of scenes"
    }}
  ],
  "total_characters": 0,
  "main_characters": 0,
  "character_relationships": {{
    "CHARACTER1": ["related_character1", "related_character2"],
    "CHARACTER2": ["related_character3"]
  }}
}}

**CHARACTER ANALYSIS GUIDELINES:**
- Extract explicit physical descriptions from screenplay
- Infer characteristics from dialogue style and content
- Consider character actions and motivations
- Create consistent visual representation prompts
- Prioritize main speaking characters
- Include background characters if visually important

**MIDJOURNEY PROMPT REQUIREMENTS:**
- Professional portrait style
- Consistent physical features
- Age-appropriate appearance
- Detailed facial features for recognition
- Style: "cinematic portrait, professional headshot, detailed face"
- Include specific features for character consistency
- Use --seed parameter suggestion for consistency

**IMPORTANT:**
- Return ONLY valid JSON, no additional text
- Include all required fields for each character
- Ensure character names match screenplay exactly
- Focus on visual consistency for AI generation
"""

class CharacterExtractionAgent(BaseAgent):
    """AI-powered character extraction and design generation agent"""
    
    async def process(
        self, 
        screenplay: str, 
        extract_physical: bool = True,
        generate_midjourney: bool = True,
        include_background: bool = False
    ) -> Dict[str, Any]:
        """Extract character information from screenplay"""
        processing_id = generate_unique_id()
        start_time = time.time()
        
        try:
            llm = self.llms.get("openai") or self.llms.get("claude")
            if not llm:
                raise AgentProcessingError("CharacterExtractionAgent", "No LLM configured")
            
            # Sanitize and validate input
            sanitized_screenplay = sanitize_prompt(screenplay, max_length=10000)
            if len(sanitized_screenplay) < 200:
                raise AgentProcessingError("CharacterExtractionAgent", "Screenplay too short for character extraction")
            
            # Prepare prompt
            prompt = CHARACTER_EXTRACTION_PROMPT.format(screenplay=sanitized_screenplay)
            
            # Make the API call with retries
            self.logger.info(f"[{processing_id}] Starting character extraction processing")
            
            result = await asyncio.to_thread(
                self._run_with_retries, 
                llm.invoke, 
                prompt
            )
            
            processing_time = time.time() - start_time
            raw_content = result.content if hasattr(result, 'content') else str(result)
            
            # Parse JSON response
            try:
                json_content = self._extract_json_from_response(raw_content)
                character_data = json.loads(json_content)
                
                # Validate and structure the response
                structured_characters = self._validate_and_structure_characters(character_data)
                
            except (json.JSONDecodeError, KeyError) as e:
                self.logger.warning(f"[{processing_id}] JSON parsing failed, using fallback text parsing")
                structured_characters = self._fallback_character_parsing(raw_content, screenplay)
            
            # Enhance with additional analysis
            if extract_physical:
                structured_characters = await self._enhance_physical_descriptions(
                    structured_characters, screenplay, processing_id
                )
            
            response_data = {
                "processing_id": processing_id,
                "characters": structured_characters.get("characters", []),
                "total_characters": len(structured_characters.get("characters", [])),
                "main_characters": len([c for c in structured_characters.get("characters", []) 
                                     if c.get("importance_level") == "main"]),
                "character_relationships": structured_characters.get("character_relationships", {}),
                "extraction_metadata": {
                    "extract_physical": extract_physical,
                    "generate_midjourney": generate_midjourney,
                    "include_background": include_background,
                    "processing_time": processing_time,
                    "screenplay_length": len(screenplay)
                },
                "timestamp": get_utc_now(),
                "success": True
            }
            
            self.logger.info(f"[{processing_id}] Character extraction completed: {len(structured_characters.get('characters', []))} characters in {processing_time:.2f}s")
            return response_data
            
        except Exception as e:
            error_msg = f"Character extraction failed: {str(e)}"
            self.logger.error(f"[{processing_id}] {error_msg}")
            raise AgentProcessingError("CharacterExtractionAgent", error_msg)
    
    def _extract_json_from_response(self, response: str) -> str:
        """Extract JSON from potentially formatted response"""
        # Remove code blocks if present
        response = re.sub(r'```json\\s*', '', response)
        response = re.sub(r'```\\s*$', '', response)
        
        # Try to find JSON object boundaries
        start = response.find('{')
        end = response.rfind('}') + 1
        
        if start >= 0 and end > start:
            return response[start:end]
        
        return response.strip()
    
    def _validate_and_structure_characters(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and structure character data from AI response"""
        if 'characters' not in character_data:
            raise ValueError("No characters found in response")
        
        structured_characters = []
        for char_info in character_data.get('characters', []):
            # Validate required fields and set defaults
            character = {
                'name': char_info.get('name', 'UNKNOWN'),
                'description': char_info.get('description', ''),
                'physical_attributes': self._validate_physical_attributes(
                    char_info.get('physical_attributes', {})
                ),
                'personality_traits': char_info.get('personality_traits', []),
                'midjourney_prompt': char_info.get('midjourney_prompt', ''),
                'importance_level': self._validate_importance_level(
                    char_info.get('importance_level', 'supporting')
                ),
                'first_appearance_scene': char_info.get('first_appearance_scene'),
                'total_scenes': char_info.get('total_scenes', 1)
            }
            structured_characters.append(character)
        
        return {
            'characters': structured_characters,
            'total_characters': len(structured_characters),
            'character_relationships': character_data.get('character_relationships', {})
        }
    
    def _validate_physical_attributes(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize physical attributes"""
        return {
            'age': attributes.get('age', 'unknown'),
            'gender': attributes.get('gender', 'unknown'),
            'height': attributes.get('height', 'medium'),
            'build': attributes.get('build', 'medium'),
            'hair_color': attributes.get('hair_color', 'brown'),
            'hair_style': attributes.get('hair_style', 'short'),
            'eye_color': attributes.get('eye_color', 'brown'),
            'skin_tone': attributes.get('skin_tone', 'medium'),
            'distinctive_features': attributes.get('distinctive_features', ''),
            'clothing_style': attributes.get('clothing_style', 'casual')
        }
    
    def _validate_importance_level(self, level: str) -> str:
        """Validate character importance level"""
        valid_levels = ['main', 'supporting', 'background']
        return level.lower() if level.lower() in valid_levels else 'supporting'
    
    def _fallback_character_parsing(self, content: str, screenplay: str) -> Dict[str, Any]:
        """Fallback character parsing when JSON parsing fails"""
        # Use basic character name extraction
        character_names = extract_character_names(screenplay)
        
        characters = []
        for i, name in enumerate(character_names):
            characters.append({
                'name': name,
                'description': f'Character extracted from screenplay',
                'physical_attributes': {
                    'age': 'unknown',
                    'gender': 'unknown',
                    'height': 'medium',
                    'build': 'medium',
                    'hair_color': 'brown',
                    'hair_style': 'short',
                    'eye_color': 'brown',
                    'skin_tone': 'medium',
                    'distinctive_features': '',
                    'clothing_style': 'casual'
                },
                'personality_traits': [],
                'midjourney_prompt': f'portrait of {name}, cinematic lighting, detailed face',
                'importance_level': 'main' if i < 3 else 'supporting',
                'first_appearance_scene': 'Scene 1',
                'total_scenes': 1
            })
        
        return {
            'characters': characters,
            'total_characters': len(characters),
            'character_relationships': {}
        }
    
    async def _enhance_physical_descriptions(
        self, 
        characters: Dict[str, Any], 
        screenplay: str, 
        processing_id: str
    ) -> Dict[str, Any]:
        """Enhance character descriptions with additional analysis"""
        # This could be extended to use additional AI calls for more detailed analysis
        # For now, return as-is
        return characters
    
    def generate_character_reference_sheet(self, character: Dict[str, Any]) -> Dict[str, str]:
        """Generate character reference information for consistency"""
        attributes = character.get('physical_attributes', {})
        
        # Create detailed Midjourney prompt
        prompt_parts = [
            f"portrait of {character.get('name', 'character')}",
            f"{attributes.get('age', 'adult')} {attributes.get('gender', 'person')}",
            f"{attributes.get('hair_color', 'brown')} {attributes.get('hair_style', 'hair')}",
            f"{attributes.get('eye_color', 'brown')} eyes",
            f"{attributes.get('skin_tone', 'medium')} skin tone",
            f"{attributes.get('build', 'medium')} build"
        ]
        
        if attributes.get('distinctive_features'):
            prompt_parts.append(attributes['distinctive_features'])
        
        prompt_parts.extend([
            "professional headshot",
            "cinematic lighting",
            "detailed facial features",
            "high quality",
            "--ar 9:16",
            "--style raw"
        ])
        
        return {
            'midjourney_prompt': ', '.join(prompt_parts),
            'style_reference': 'cinematic portrait photography',
            'consistency_notes': f"Always include: {attributes.get('hair_color')} hair, {attributes.get('eye_color')} eyes, {attributes.get('skin_tone')} skin tone",
            'clothing_reference': attributes.get('clothing_style', 'casual attire')
        }