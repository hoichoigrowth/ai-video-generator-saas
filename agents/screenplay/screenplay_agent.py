import asyncio
from typing import Dict, Any
from agents.base_agent import BaseAgent

# Exact prompt as used in n8n workflow for screenplay formatting
SCREENPLAY_PROMPT = (
    "You are a professional screenwriter. Format the following text into proper screenplay format, "
    "including scene headings, action lines, character names, dialogue, and transitions. "
    "Use industry-standard screenplay conventions.\n\nText:\n{script}"
)

class ScreenplayFormattingAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        # Use GPT-4, Claude 3, and Gemini models by default
        kwargs.setdefault("model_name_openai", "gpt-4")
        kwargs.setdefault("model_name_anthropic", "claude-3-opus-20240229")
        kwargs.setdefault("model_name_gemini", "gemini-pro")
        super().__init__(*args, **kwargs)

    async def process(self, script_text: str) -> Dict[str, Any]:
        """
        Formats the script using OpenAI GPT-4, Claude 3, and Gemini in parallel.
        Returns a dict with all three versions.
        """
        prompt = SCREENPLAY_PROMPT.format(script=script_text)
        tasks = []
        results = {}

        async def call_openai():
            llm = self.llms.get("openai")
            if not llm:
                return None
            try:
                return await asyncio.to_thread(self._run_with_retries, llm.invoke, prompt)
            except Exception as e:
                self.logger.error(f"OpenAI formatting failed: {e}")
                return None

        async def call_claude():
            llm = self.llms.get("claude")
            if not llm:
                return None
            try:
                return await asyncio.to_thread(self._run_with_retries, llm.invoke, prompt)
            except Exception as e:
                self.logger.error(f"Claude formatting failed: {e}")
                return None

        async def call_gemini():
            llm = self.llms.get("gemini")
            if not llm:
                return None
            try:
                return await asyncio.to_thread(self._run_with_retries, llm.invoke, prompt)
            except Exception as e:
                self.logger.error(f"Gemini formatting failed: {e}")
                return None

        tasks = [call_openai(), call_claude(), call_gemini()]
        openai_result, claude_result, gemini_result = await asyncio.gather(*tasks)

        results["openai_screenplay"] = openai_result
        results["claude_screenplay"] = claude_result
        results["gemini_screenplay"] = gemini_result
        return results
