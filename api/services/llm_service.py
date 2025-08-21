import os
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from openai import AsyncOpenAI
import anthropic
import google.generativeai as genai

class LLMService:
    def __init__(self):
        # Initialize API clients
        self.openai_client = None
        self.anthropic_client = None
        
        # Set up OpenAI
        if os.getenv('OPENAI_API_KEY'):
            self.openai_client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Set up Anthropic
        if os.getenv('ANTHROPIC_API_KEY'):
            self.anthropic_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
        # Set up Google Gemini
        if os.getenv('GOOGLE_API_KEY'):
            genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
    
    def get_professional_screenplay_prompt(self) -> str:
        """Get the professional screenplay formatting prompt"""
        return """Convert the following script into professional screenplay format using industry standards.

FORMATTING REQUIREMENTS:

Scene Structure:
- Scene headings: INT./EXT. LOCATION - TIME OF DAY
- Proper scene transitions (CUT TO:, FADE IN:, FADE OUT:, etc.)
- Clear location and time establishment

Character Format:
- CHARACTER NAMES in ALL CAPS (centered, 3.7" from left margin)
- Dialogue below character names (2.5" to 6.5" from left margin)
- Character introductions in ALL CAPS when first mentioned
- Age specifications in parentheses when provided

Dialogue Standards:
- Preserve exact wording, tone, and emotion
- Parentheticals for acting direction: (angry), (whispers), (crying)
- Voice-over: CHARACTER (V.O.)
- Off-screen: CHARACTER (O.S.)
- Phone/radio: CHARACTER (PHONE) or CHARACTER (RADIO)

Action Lines:
- Present tense, active voice
- 1.5" to 7.5" margins
- Describe only what can be seen/heard
- Character emotions through actions, not exposition
- Sound effects in ALL CAPS: PHONE RINGS, DOOR SLAMS

Special Elements:
- Montages with proper formatting
- Flashbacks clearly indicated
- Insert shots properly labeled
- Time cuts and location changes
- Background action and atmosphere

Quality Standards:
- Maintain original story pacing and rhythm
- Preserve cultural context and language nuances
- Ensure smooth narrative flow between scenes
- Convert non-English dialogue with cultural accuracy
- Balance dialogue with action for visual storytelling

VERIFICATION CHECKLIST:
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

OUTPUT INSTRUCTION:
Return only the complete, professionally formatted screenplay. No additional text, explanations, or commentary."""

    async def generate_screenplay_openai(self, script_text: str) -> str:
        """Generate screenplay using OpenAI GPT-4"""
        if not self.openai_client:
            raise Exception("OpenAI API key not configured")
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.get_professional_screenplay_prompt()},
                    {"role": "user", "content": f"Transform this script into a professionally formatted screenplay:\n\n{script_text}"}
                ],
                max_tokens=4000,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def generate_screenplay_anthropic(self, script_text: str) -> str:
        """Generate screenplay using Anthropic Claude"""
        if not self.anthropic_client:
            raise Exception("Anthropic API key not configured")
        
        try:
            message = await asyncio.to_thread(
                self.anthropic_client.messages.create,
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                temperature=0.3,
                system=self.get_professional_screenplay_prompt(),
                messages=[
                    {"role": "user", "content": f"Transform this script into a professionally formatted screenplay:\n\n{script_text}"}
                ]
            )
            return message.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    async def generate_screenplay_gemini(self, script_text: str) -> str:
        """Generate screenplay using Google Gemini"""
        if not os.getenv('GOOGLE_API_KEY'):
            raise Exception("Google API key not configured")
        
        try:
            model = genai.GenerativeModel('gemini-pro')
            prompt = f"{self.get_professional_screenplay_prompt()}\n\nTransform this script into a professionally formatted screenplay:\n\n{script_text}"
            
            response = await asyncio.to_thread(model.generate_content, prompt)
            return response.text
        except Exception as e:
            raise Exception(f"Google API error: {str(e)}")
    
    async def generate_screenplay(self, script_text: str, agent: str) -> Dict[str, Any]:
        """Generate screenplay using the specified LLM agent"""
        agent_lower = agent.lower()
        
        try:
            if agent_lower in ["gpt-4", "openai"]:
                screenplay = await self.generate_screenplay_openai(script_text)
            elif agent_lower == "claude":
                screenplay = await self.generate_screenplay_anthropic(script_text)
            elif agent_lower == "gemini":
                screenplay = await self.generate_screenplay_gemini(script_text)
            else:
                raise Exception(f"Unsupported LLM agent: {agent}")
            
            return {
                'screenplay': screenplay,
                'agent_used': agent,
                'generated_at': datetime.now().isoformat(),
                'success': True,
                'script_length': len(script_text),
                'screenplay_length': len(screenplay)
            }
            
        except Exception as e:
            # Fallback to simulation if API fails
            fallback_screenplay = self._generate_fallback_screenplay(script_text, agent, str(e))
            return {
                'screenplay': fallback_screenplay,
                'agent_used': f"{agent} (Fallback)",
                'generated_at': datetime.now().isoformat(),
                'success': False,
                'error': str(e),
                'script_length': len(script_text),
                'screenplay_length': len(fallback_screenplay)
            }
    
    def _generate_fallback_screenplay(self, script_text: str, agent: str, error: str) -> str:
        """Generate a fallback screenplay when API calls fail"""
        return f"""FADE IN:

INT. SYSTEM ERROR - CONTINUOUS

[API ERROR OCCURRED]

The {agent} API encountered an error: {error}

However, here's the source script formatted as closely as possible to screenplay standards:

{self._format_as_basic_screenplay(script_text)}

[Note: This is a fallback formatting. For full professional screenplay generation, please ensure API keys are properly configured.]

FADE OUT.

---
Fallback generated by: AI Video Generator
Original Script Length: {len(script_text)} characters
Error: {error}
Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    
    def _format_as_basic_screenplay(self, script_text: str) -> str:
        """Basic screenplay formatting for fallback"""
        lines = script_text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('')
                continue
            
            # Simple heuristics for basic formatting
            if line.isupper() or any(word in line.upper() for word in ['INT.', 'EXT.', 'FADE', 'CUT']):
                formatted_lines.append(line.upper())
            elif line.endswith(':') and len(line.split()) <= 3:
                formatted_lines.append(f"                    {line.upper().replace(':', '')}")
            else:
                formatted_lines.append(f"          {line}")
        
        return '\n'.join(formatted_lines)