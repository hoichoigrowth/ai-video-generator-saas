import asyncio
from agents.base_agent import BaseAgent

MERGE_SCREENPLAY_PROMPT = """
You are a screenplay consensus expert. Analyze the three screenplay versions and create the BEST possible final version.

Rules:
1. Combine the best elements from all three versions
2. Ensure ALL dialogue from the original is preserved
3. Use the best formatting approach
4. Maintain consistent character voices
5. Choose the most effective scene descriptions
6. Resolve any conflicts between versions intelligently

Original Script: {original_script}
OpenAI Screenplay: {openai_screenplay}
Claude Screenplay: {claude_screenplay}
Gemini Screenplay: {gemini_screenplay}

Provide the final, optimized screenplay.
"""

class ScreenplayMergerAgent(BaseAgent):
    async def process(self, original_script: str, openai_screenplay: str, claude_screenplay: str, gemini_screenplay: str):
        prompt = MERGE_SCREENPLAY_PROMPT.format(
            original_script=original_script,
            openai_screenplay=openai_screenplay,
            claude_screenplay=claude_screenplay,
            gemini_screenplay=gemini_screenplay
        )
        llm = self.llms.get("openai")
        return await asyncio.to_thread(self._run_with_retries, llm.invoke, prompt)