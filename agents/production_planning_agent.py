import asyncio
import json
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent
from core.utils import sanitize_prompt, generate_unique_id, get_utc_now
from core.exceptions import AgentProcessingError, ModelAPIError
from core.models import ProductionDesign, LightingDesign
import time
import re

PRODUCTION_PLANNING_PROMPT = """
You are a professional film production designer and cinematographer. Analyze the screenplay and shot division to create a comprehensive production plan for AI video generation.

**SCREENPLAY:**
{screenplay}

**SHOT DIVISION:**
{shot_division}

**PRODUCTION REQUIREMENTS:**
- Budget Range: {budget_range}
- Timeline Preference: {timeline_preference}
- Location Preferences: {location_preferences}

**OUTPUT FORMAT (JSON):**
Return a JSON object with this exact structure:
{{
  "production_design": {{
    "locations": {{
      "location_name": {{
        "type": "interior/exterior",
        "description": "detailed description",
        "mood": "atmosphere description",
        "color_palette": ["color1", "color2", "color3"],
        "key_props": ["prop1", "prop2"],
        "lighting_requirements": "natural/artificial/mixed",
        "shots_using_location": [1, 2, 3]
      }}
    }},
    "color_palette": ["primary_color", "secondary_color", "accent_color"],
    "visual_style": "cinematic/realistic/stylized/etc",
    "mood_board_concepts": [
      "concept description 1",
      "concept description 2"
    ]
  }},
  "lighting_design": {{
    "lighting_setup": {{
      "time_of_day": "day/night/golden_hour/blue_hour",
      "weather_conditions": "sunny/cloudy/rainy/stormy",
      "mood": "bright/moody/dramatic/soft",
      "key_lighting": "natural/studio/mixed",
      "lighting_notes": "specific lighting instructions"
    }},
    "scene_specific_lighting": {{
      "scene_name": {{
        "lighting_type": "soft/hard/dramatic",
        "color_temperature": "warm/cool/neutral",
        "special_requirements": "additional notes"
      }}
    }}
  }},
  "location_breakdown": {{
    "location_name": [1, 2, 3, 4]
  }},
  "timeline_estimate": {{
    "pre_production_days": 5,
    "production_days": 10,
    "post_production_days": 15,
    "total_days": 30
  }},
  "budget_estimate": {{
    "ai_generation_costs": 500.0,
    "editing_costs": 300.0,
    "misc_costs": 200.0,
    "total_estimated": 1000.0
  }},
  "technical_specifications": {{
    "aspect_ratio": "9:16",
    "resolution": "1080x1920",
    "frame_rate": "24fps",
    "color_grading": "cinematic/natural/stylized",
    "ai_tools": ["Midjourney", "Kling", "Runway"]
  }},
  "risk_assessment": [
    "potential issue 1",
    "potential issue 2"
  ],
  "quality_standards": {{
    "visual_consistency": "high/medium/low",
    "character_continuity": "strict/moderate/flexible",
    "physics_realism": "high/medium/low"
  }}
}}

**ANALYSIS GUIDELINES:**
1. **Location Analysis:**
   - Identify all unique locations from shot division
   - Analyze location requirements and complexity
   - Consider AI generation feasibility
   - Plan for location consistency across shots

2. **Visual Design:**
   - Create cohesive color palette
   - Define visual style and mood
   - Ensure consistency with story tone
   - Consider vertical video format requirements

3. **Lighting Strategy:**
   - Plan lighting for each scene/location
   - Consider time of day and mood requirements
   - Ensure AI-generation compatibility
   - Maintain visual consistency

4. **Timeline Planning:**
   - Realistic timeline for AI generation workflow
   - Account for human approval checkpoints
   - Include revision and refinement time
   - Consider parallel processing opportunities

5. **Budget Estimation:**
   - AI API costs for image/video generation
   - Editing and post-production requirements
   - Potential revision costs
   - Contingency budget

**IMPORTANT:**
- Return ONLY valid JSON, no additional text
- Focus on AI video generation workflow
- Consider vertical video format (9:16)
- Prioritize visual consistency and quality
- Include realistic timelines and budgets
"""

class ProductionPlanningAgent(BaseAgent):
    """AI-powered production planning and design agent"""
    
    async def process(
        self, 
        screenplay: str,
        shot_division: List[Dict[str, Any]],
        budget_range: Optional[str] = "medium",
        timeline_preference: Optional[str] = "standard",
        location_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create comprehensive production plan"""
        processing_id = generate_unique_id()
        start_time = time.time()
        
        try:
            llm = self.llms.get("openai") or self.llms.get("claude")
            if not llm:
                raise AgentProcessingError("ProductionPlanningAgent", "No LLM configured")
            
            # Prepare inputs
            sanitized_screenplay = sanitize_prompt(screenplay, max_length=8000)
            shot_division_text = self._format_shot_division(shot_division)
            location_prefs = location_preferences or {}
            
            # Prepare prompt
            prompt = PRODUCTION_PLANNING_PROMPT.format(
                screenplay=sanitized_screenplay,
                shot_division=shot_division_text,
                budget_range=budget_range,
                timeline_preference=timeline_preference,
                location_preferences=json.dumps(location_prefs, indent=2)
            )
            
            # Make the API call with retries
            self.logger.info(f"[{processing_id}] Starting production planning")
            
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
                plan_data = json.loads(json_content)
                
                # Validate and structure the response
                structured_plan = self._validate_and_structure_plan(plan_data)
                
            except (json.JSONDecodeError, KeyError) as e:
                self.logger.warning(f"[{processing_id}] JSON parsing failed, using fallback planning")
                structured_plan = self._fallback_production_planning(
                    shot_division, budget_range, timeline_preference
                )
            
            response_data = {
                "processing_id": processing_id,
                "production_design": structured_plan.get("production_design", {}),
                "lighting_design": structured_plan.get("lighting_design", {}),
                "location_breakdown": structured_plan.get("location_breakdown", {}),
                "timeline_estimate": structured_plan.get("timeline_estimate", {}),
                "budget_estimate": structured_plan.get("budget_estimate", {}),
                "technical_specifications": structured_plan.get("technical_specifications", {}),
                "risk_assessment": structured_plan.get("risk_assessment", []),
                "quality_standards": structured_plan.get("quality_standards", {}),
                "metadata": {
                    "total_locations": len(structured_plan.get("location_breakdown", {})),
                    "total_shots": len(shot_division),
                    "processing_time": processing_time,
                    "budget_range": budget_range,
                    "timeline_preference": timeline_preference
                },
                "timestamp": get_utc_now(),
                "success": True
            }
            
            self.logger.info(f"[{processing_id}] Production planning completed in {processing_time:.2f}s")
            return response_data
            
        except Exception as e:
            error_msg = f"Production planning failed: {str(e)}"
            self.logger.error(f"[{processing_id}] {error_msg}")
            raise AgentProcessingError("ProductionPlanningAgent", error_msg)
    
    def _format_shot_division(self, shot_division: List[Dict[str, Any]]) -> str:
        """Format shot division for prompt"""
        formatted_shots = []
        for shot in shot_division[:20]:  # Limit to first 20 shots for prompt size
            shot_info = f"Shot {shot.get('shot_number', '?')}: {shot.get('description', 'No description')}"
            if shot.get('location'):
                shot_info += f" | Location: {shot['location']}"
            if shot.get('characters_present'):
                shot_info += f" | Characters: {', '.join(shot['characters_present'])}"
            formatted_shots.append(shot_info)
        
        return "\n".join(formatted_shots)
    
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
    
    def _validate_and_structure_plan(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and structure production plan data"""
        # Ensure all required sections exist with defaults
        structured_plan = {
            "production_design": self._validate_production_design(
                plan_data.get("production_design", {})
            ),
            "lighting_design": self._validate_lighting_design(
                plan_data.get("lighting_design", {})
            ),
            "location_breakdown": plan_data.get("location_breakdown", {}),
            "timeline_estimate": self._validate_timeline(
                plan_data.get("timeline_estimate", {})
            ),
            "budget_estimate": self._validate_budget(
                plan_data.get("budget_estimate", {})
            ),
            "technical_specifications": self._validate_technical_specs(
                plan_data.get("technical_specifications", {})
            ),
            "risk_assessment": plan_data.get("risk_assessment", []),
            "quality_standards": self._validate_quality_standards(
                plan_data.get("quality_standards", {})
            )
        }
        
        return structured_plan
    
    def _validate_production_design(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """Validate production design data"""
        return {
            "locations": design.get("locations", {}),
            "color_palette": design.get("color_palette", ["#2C3E50", "#E74C3C", "#F39C12"]),
            "visual_style": design.get("visual_style", "cinematic"),
            "mood_board_concepts": design.get("mood_board_concepts", [])
        }
    
    def _validate_lighting_design(self, lighting: Dict[str, Any]) -> Dict[str, Any]:
        """Validate lighting design data"""
        return {
            "lighting_setup": lighting.get("lighting_setup", {
                "time_of_day": "day",
                "weather_conditions": "clear",
                "mood": "natural",
                "key_lighting": "natural",
                "lighting_notes": "Standard daylight setup"
            }),
            "scene_specific_lighting": lighting.get("scene_specific_lighting", {})
        }
    
    def _validate_timeline(self, timeline: Dict[str, Any]) -> Dict[str, Any]:
        """Validate timeline estimate"""
        return {
            "pre_production_days": timeline.get("pre_production_days", 3),
            "production_days": timeline.get("production_days", 7),
            "post_production_days": timeline.get("post_production_days", 10),
            "total_days": timeline.get("total_days", 20)
        }
    
    def _validate_budget(self, budget: Dict[str, Any]) -> Dict[str, Any]:
        """Validate budget estimate"""
        return {
            "ai_generation_costs": budget.get("ai_generation_costs", 300.0),
            "editing_costs": budget.get("editing_costs", 200.0),
            "misc_costs": budget.get("misc_costs", 100.0),
            "total_estimated": budget.get("total_estimated", 600.0)
        }
    
    def _validate_technical_specs(self, specs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate technical specifications"""
        return {
            "aspect_ratio": specs.get("aspect_ratio", "9:16"),
            "resolution": specs.get("resolution", "1080x1920"),
            "frame_rate": specs.get("frame_rate", "24fps"),
            "color_grading": specs.get("color_grading", "cinematic"),
            "ai_tools": specs.get("ai_tools", ["Midjourney", "Kling"])
        }
    
    def _validate_quality_standards(self, standards: Dict[str, Any]) -> Dict[str, Any]:
        """Validate quality standards"""
        return {
            "visual_consistency": standards.get("visual_consistency", "high"),
            "character_continuity": standards.get("character_continuity", "strict"),
            "physics_realism": standards.get("physics_realism", "high")
        }
    
    def _fallback_production_planning(
        self, 
        shot_division: List[Dict[str, Any]], 
        budget_range: str, 
        timeline_preference: str
    ) -> Dict[str, Any]:
        """Fallback production planning when AI parsing fails"""
        # Extract unique locations
        locations = {}
        location_breakdown = {}
        
        for shot in shot_division:
            location = shot.get('location', 'UNKNOWN_LOCATION')
            if location not in locations:
                locations[location] = {
                    "type": "interior",
                    "description": f"Location for {location}",
                    "mood": "neutral",
                    "color_palette": ["#2C3E50", "#E74C3C", "#F39C12"],
                    "key_props": [],
                    "lighting_requirements": "natural",
                    "shots_using_location": []
                }
                location_breakdown[location] = []
            
            locations[location]["shots_using_location"].append(shot.get('shot_number', 0))
            location_breakdown[location].append(shot.get('shot_number', 0))
        
        # Budget mapping
        budget_multipliers = {"low": 0.5, "medium": 1.0, "high": 2.0}
        multiplier = budget_multipliers.get(budget_range, 1.0)
        
        # Timeline mapping
        timeline_multipliers = {"fast": 0.7, "standard": 1.0, "extended": 1.5}
        time_multiplier = timeline_multipliers.get(timeline_preference, 1.0)
        
        return {
            "production_design": {
                "locations": locations,
                "color_palette": ["#2C3E50", "#E74C3C", "#F39C12"],
                "visual_style": "cinematic",
                "mood_board_concepts": ["Professional cinematic style", "Consistent character design"]
            },
            "lighting_design": {
                "lighting_setup": {
                    "time_of_day": "day",
                    "weather_conditions": "clear",
                    "mood": "natural",
                    "key_lighting": "natural",
                    "lighting_notes": "Standard production lighting"
                },
                "scene_specific_lighting": {}
            },
            "location_breakdown": location_breakdown,
            "timeline_estimate": {
                "pre_production_days": int(3 * time_multiplier),
                "production_days": int(7 * time_multiplier),
                "post_production_days": int(10 * time_multiplier),
                "total_days": int(20 * time_multiplier)
            },
            "budget_estimate": {
                "ai_generation_costs": 300.0 * multiplier,
                "editing_costs": 200.0 * multiplier,
                "misc_costs": 100.0 * multiplier,
                "total_estimated": 600.0 * multiplier
            },
            "technical_specifications": {
                "aspect_ratio": "9:16",
                "resolution": "1080x1920",
                "frame_rate": "24fps",
                "color_grading": "cinematic",
                "ai_tools": ["Midjourney", "Kling"]
            },
            "risk_assessment": [
                "AI generation consistency challenges",
                "Character continuity across shots",
                "Timeline dependencies on AI processing"
            ],
            "quality_standards": {
                "visual_consistency": "high",
                "character_continuity": "strict",
                "physics_realism": "high"
            }
        }