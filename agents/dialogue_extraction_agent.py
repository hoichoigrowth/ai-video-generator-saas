import asyncio
from agents.base_agent import BaseAgent

DIALOGUE_EXTRACTION_PROMPT = """
You are a dialogue extraction expert. Extract ALL dialogue from the script in a structured format for verification purposes.

Rules:
1. Extract every single line of dialogue
2. Include character names
3. Preserve exact wording
4. Number each dialogue line
5. Include stage directions that contain speech

Script = {script}

Output format:
{{
  "total_dialogue_count": X,
  "dialogues": [
    {{
      "id": 1,
      "character": "CHARACTER_NAME",
      "dialogue": "exact dialogue text",
      "context": "brief scene context"
    }}
  ]
}}
"""

class DialogueExtractionAgent(BaseAgent):
    async def process(self, script_text: str):
        prompt = DIALOGUE_EXTRACTION_PROMPT.format(script=script_text)
        llm = self.llms.get("openai")
        return await asyncio.to_thread(self._run_with_retries, llm.invoke, prompt)