import asyncio
from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from core.utils import sanitize_prompt, generate_unique_id, get_utc_now
from core.exceptions import AgentProcessingError, ModelAPIError
import time

GEMINI_SCREENPLAY_PROMPT = """
Convert the following script into professional screenplay format using industry standards.

**FORMATTING REQUIREMENTS:**

**Scene Structure:**
- Scene headings: INT./EXT. LOCATION - TIME OF DAY
- Proper scene transitions (CUT TO:, FADE IN:, FADE OUT:, etc.)
- Clear location and time establishment

**Character Format:**
- CHARACTER NAMES in ALL CAPS (centered, 3.7" from left margin)
- Dialogue below character names (2.5" to 6.5" from left margin)
- Character introductions in ALL CAPS when first mentioned
- Age specifications in parentheses when provided

**Dialogue Standards:**
- Preserve exact wording, tone, and emotion
- Parentheticals for acting direction: (angry), (whispers), (crying)
- Voice-over: CHARACTER (V.O.)
- Off-screen: CHARACTER (O.S.)
- Phone/radio: CHARACTER (PHONE) or CHARACTER (RADIO)

**Action Lines:**
- Present tense, active voice
- 1.5" to 7.5" margins
- Describe only what can be seen/heard
- Character emotions through actions, not exposition
- Sound effects in ALL CAPS: PHONE RINGS, DOOR SLAMS

**Special Elements:**
- Montages with proper formatting
- Flashbacks clearly indicated
- Insert shots properly labeled
- Time cuts and location changes
- Background action and atmosphere

**Quality Standards:**
- Maintain original story pacing and rhythm
- Preserve cultural context and language nuances
- Ensure smooth narrative flow between scenes
- Convert non-English dialogue with cultural accuracy
- Balance dialogue with action for visual storytelling

**VERIFICATION CHECKLIST:**
□ All dialogue preserved exactly as written
□ All narration/voice-over converted properly
□ Scene headings properly formatted
□ Character names consistently capitalized
□ Action lines describe visual elements only
□ Proper margins and spacing throughout
□ Industry-standard transitions used
□ No content omitted or added
□ Story flow and pacing maintained
□ Professional presentation quality

**SCRIPT TO CONVERT:**
{script}

**OUTPUT INSTRUCTION:**
Return only the complete, professionally formatted screenplay. No additional text, explanations, or commentary.
"""

class GeminiScreenplayAgent(BaseAgent):
    """Google Gemini powered screenplay formatting agent with enhanced error handling"""
    
    async def process(self, script_text: str, custom_instructions: Optional[str] = None) -> Dict[str, Any]:
        """Process script text into screenplay format using Gemini"""
        processing_id = generate_unique_id()
        start_time = time.time()
        
        try:
            llm = self.llms.get("gemini")
            if not llm:
                raise AgentProcessingError("GeminiScreenplayAgent", "Gemini LLM not configured")
            
            # Sanitize and validate input
            sanitized_script = sanitize_prompt(script_text, max_length=8000)
            if len(sanitized_script) < 100:
                raise AgentProcessingError("GeminiScreenplayAgent", "Script text too short for processing")
            
            # Prepare prompt
            prompt = GEMINI_SCREENPLAY_PROMPT.format(script=sanitized_script)
            if custom_instructions:
                prompt += f"\n\nAdditional Instructions: {custom_instructions}"
            
            # Make the API call with retries
            self.logger.info(f"[{processing_id}] Starting Gemini screenplay processing")
            
            result = await asyncio.to_thread(
                self._run_with_retries, 
                llm.invoke, 
                prompt
            )
            
            processing_time = time.time() - start_time
            screenplay_content = result.content if hasattr(result, 'content') else str(result)
            
            # Extract metadata if available - Gemini metadata structure may vary
            usage_metadata = getattr(result, 'response_metadata', {})
            
            response_data = {
                "processing_id": processing_id,
                "content": screenplay_content,
                "provider": "gemini",
                "model": getattr(llm, 'model', 'gemini-pro'),
                "tokens_used": 0,  # Gemini doesn't always provide token counts
                "input_tokens": 0,
                "output_tokens": 0,
                "processing_time": processing_time,
                "timestamp": get_utc_now(),
                "success": True
            }
            
            self.logger.info(f"[{processing_id}] Gemini screenplay processing completed in {processing_time:.2f}s")
            return response_data
            
        except Exception as e:
            error_msg = f"Gemini screenplay formatting failed: {str(e)}"
            self.logger.error(f"[{processing_id}] {error_msg}")
            
            if "quota" in str(e).lower() or "rate_limit" in str(e).lower():
                raise ModelAPIError("gemini", f"Rate limit exceeded: {str(e)}")
            elif "api_key" in str(e).lower():
                raise ModelAPIError("gemini", f"Invalid API key: {str(e)}")
            else:
                raise AgentProcessingError("GeminiScreenplayAgent", error_msg)
    
    def estimate_cost(self, script_length: int) -> float:
        """Estimate API cost for processing script"""
        # Gemini Pro pricing (approximate)
        input_price_per_1k = 0.0005
        output_price_per_1k = 0.0015
        
        estimated_input_tokens = script_length / 3  # rough estimate
        estimated_output_tokens = script_length / 2  # screenplay tends to be longer
        
        input_cost = (estimated_input_tokens / 1000) * input_price_per_1k
        output_cost = (estimated_output_tokens / 1000) * output_price_per_1k
        
        return input_cost + output_cost