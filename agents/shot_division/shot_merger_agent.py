import asyncio
from agents.base_agent import BaseAgent

MERGE_SHOT_DIVISION_PROMPT = """
Here are the three LLM outputs from OpenAI, Claude, and Gemini respectively. Your task is to read them carefully and generate a **single complete and merged shot division** for the screenplay. Do not skip or miss any shot or dialogue that exists in any of the inputs.

Each scene and shot must have complete details, and the format should be clean, readable, and unified. No missing data. No truncated response. Your response must include all scenes and shots in one go.

**OPENAI ANALYSIS:**
{openai_analysis}

**CLAUDE ANALYSIS:**
{claude_analysis}

**GEMINI ANALYSIS:**
{gemini_analysis}
"""

class ShotMergerAgent(BaseAgent):
    async def process(self, openai_analysis: str, claude_analysis: str, gemini_analysis: str):
        prompt = MERGE_SHOT_DIVISION_PROMPT.format(
            openai_analysis=openai_analysis,
            claude_analysis=claude_analysis,
            gemini_analysis=gemini_analysis
        )
        llm = self.llms.get("openai")
        return await asyncio.to_thread(self._run_with_retries, llm.invoke, prompt)