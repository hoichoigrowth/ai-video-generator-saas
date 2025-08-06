import asyncio
from agents.base_agent import BaseAgent

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
    async def process(self, script_text: str):
        prompt = GEMINI_SCREENPLAY_PROMPT.format(script=script_text)
        llm = self.llms.get("gemini")
        return await asyncio.to_thread(self._run_with_retries, llm.invoke, prompt)