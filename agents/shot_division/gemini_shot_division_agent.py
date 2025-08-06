import asyncio
from agents.base_agent import BaseAgent

GEMINI_SHOT_DIVISION_PROMPT = """
Create a comprehensive shot division for this screenplay, optimized for AI-generated vertical videos with ultra-realistic physics and character consistency.

SCREENPLAY TO ANALYZE:
{screenplay}

OUTPUT REQUIREMENTS:

Break down every scene into individual shots
Each shot must contain only one character
Include all essential fields for each shot
Optimize composition for vertical video format (9:16)
Ensure compatibility with AI generation tools (Midjourney, Kling, Veo 3)
Maintain strict character and prop consistency
Include physics and realism notes (gravity, wind, reflections, etc.)
Emphasize dramatic storytelling suitable for short-form content

FORMAT:
Provide a detailed breakdown with clear scene divisions and numbered shots. Include specific notes about:
-Character appearance and facial cues
-Physical interactions and realistic motion
-Props and their continuity
-Visual style and tone per shot

This shot division will serve as the final production foundation for AI video generation.
"""

class GeminiShotDivisionAgent(BaseAgent):
    async def process(self, screenplay: str):
        prompt = GEMINI_SHOT_DIVISION_PROMPT.format(screenplay=screenplay)
        llm = self.llms.get("gemini")
        return await asyncio.to_thread(self._run_with_retries, llm.invoke, prompt)