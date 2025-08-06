import os
import json
import asyncio
from typing import Optional, Dict, Any
from agents.screenplay.screenplay_agent import ScreenplayFormattingAgent
from agents.screenplay.merger import merge_screenplays, extract_scene_headings
from config.settings import settings
from agents.dialogue_extraction_agent import DialogueExtractionAgent
from agents.screenplay.openai_screenplay_agent import OpenAIScreenplayAgent
from agents.screenplay.claude_screenplay_agent import ClaudeScreenplayAgent
from agents.screenplay.gemini_screenplay_agent import GeminiScreenplayAgent
from agents.screenplay.screenplay_merger_agent import ScreenplayMergerAgent
from agents.shot_division.openai_shot_division_agent import OpenAIShotDivisionAgent
from agents.shot_division.claude_shot_division_agent import ClaudeShotDivisionAgent
from agents.shot_division.gemini_shot_division_agent import GeminiShotDivisionAgent
from agents.shot_division.shot_merger_agent import ShotMergerAgent
from services.google_docs_service import GoogleDocsService
from services.google_sheets_service import GoogleSheetsService
from services.piapi_service import PiAPIService
from services.gotohuman_service import GoToHumanService

CHECKPOINTS = [
    "input",
    "screenplay_formatted",
    "screenplay_merged",
    "shots_broken",
    "characters_extracted",
    "image_prompts_generated",
    "final"
]

STATE_FILE = "pipeline_state.json"

class PipelineState:
    def __init__(self, state_file: str = STATE_FILE):
        self.state_file = state_file
        self.state = self.load_state()

    def load_state(self) -> Dict[str, Any]:
        if os.path.exists(self.state_file):
            with open(self.state_file, "r") as f:
                return json.load(f)
        return {"checkpoint": "input"}

    def save_state(self):
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)

    def set_checkpoint(self, checkpoint: str, data: Optional[Dict[str, Any]] = None):
        self.state["checkpoint"] = checkpoint
        if data:
            self.state[checkpoint] = data
        self.save_state()

    def get_checkpoint(self) -> str:
        return self.state.get("checkpoint", "input")

    def get_data(self, checkpoint: str) -> Optional[Dict[str, Any]]:
        return self.state.get(checkpoint)

async def human_approval(checkpoint: str, data: Any):
    print(f"\n--- Checkpoint: {checkpoint} ---")
    print(f"Data: {str(data)[:1000]}...\n")
    input("Approve and continue? (Press Enter to continue)")

async def break_into_shots(screenplay: str) -> list:
    # Simple shot breaking: split by scene headings
    scenes = extract_scene_headings(screenplay)
    shots = []
    for scene in scenes:
        shots.append({"scene_heading": scene})
    return shots

async def extract_characters(screenplay: str) -> list:
    # Extract character names (all-caps lines not scene headings)
    import re
    pattern = re.compile(r"^([A-Z][A-Z0-9_ ]+)$", re.MULTILINE)
    all_caps = set(pattern.findall(screenplay))
    scene_headings = set(extract_scene_headings(screenplay))
    characters = list(all_caps - scene_headings)
    return characters

async def generate_image_prompts(shots: list, screenplay: str) -> list:
    # For each shot, generate a simple prompt (could be replaced with LLM call)
    prompts = []
    for shot in shots:
        scene = shot.get("scene_heading", "")
        prompt = f"Generate a cinematic image for: {scene}"
        prompts.append({"scene": scene, "prompt": prompt})
    return prompts

async def run_pipeline(script_text: Optional[str] = None, script_path: Optional[str] = None, resume: bool = True):
    state = PipelineState()
    checkpoint = state.get_checkpoint() if resume else "input"

    # 1. Input
    if checkpoint == "input":
        if script_text:
            text = script_text
        elif script_path and os.path.exists(script_path):
            with open(script_path, "r") as f:
                text = f.read()
        else:
            raise ValueError("No script text or file provided.")
        state.set_checkpoint("input", {"script": text})
        await human_approval("input", text)
        checkpoint = "screenplay_formatted"

    # 2. Screenplay formatting (3 models)
    if checkpoint == "screenplay_formatted":
        agent = ScreenplayFormattingAgent(
            openai_api_key=settings.openai_api_key,
            anthropic_api_key=settings.anthropic_api_key,
            google_api_key=settings.google_api_key
        )
        text = state.get_data("input")["script"]
        formatted = await agent.process(text)
        state.set_checkpoint("screenplay_formatted", formatted)
        await human_approval("screenplay_formatted", formatted)
        checkpoint = "screenplay_merged"

    # 3. Merge outputs
    if checkpoint == "screenplay_merged":
        formatted = state.get_data("screenplay_formatted")
        merged = merge_screenplays(
            formatted["openai_screenplay"],
            formatted["claude_screenplay"],
            formatted["gemini_screenplay"]
        )
        state.set_checkpoint("screenplay_merged", {"merged": merged})
        await human_approval("screenplay_merged", merged)
        checkpoint = "shots_broken"

    # 4. Break into shots
    if checkpoint == "shots_broken":
        merged = state.get_data("screenplay_merged")["merged"]
        shots = await break_into_shots(merged)
        state.set_checkpoint("shots_broken", {"shots": shots})
        await human_approval("shots_broken", shots)
        checkpoint = "characters_extracted"

    # 5. Extract characters
    if checkpoint == "characters_extracted":
        merged = state.get_data("screenplay_merged")["merged"]
        characters = await extract_characters(merged)
        state.set_checkpoint("characters_extracted", {"characters": characters})
        await human_approval("characters_extracted", characters)
        checkpoint = "image_prompts_generated"

    # 6. Generate image prompts
    if checkpoint == "image_prompts_generated":
        shots = state.get_data("shots_broken")["shots"]
        merged = state.get_data("screenplay_merged")["merged"]
        prompts = await generate_image_prompts(shots, merged)
        state.set_checkpoint("image_prompts_generated", {"prompts": prompts})
        await human_approval("image_prompts_generated", prompts)
        checkpoint = "final"

    # 7. Final step (ready for next pipeline stages)
    if checkpoint == "final":
        print("Pipeline complete. Ready for video generation.")
        return state.state

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AI Video Generation Pipeline")
    parser.add_argument("--script_path", type=str, help="Path to script file", default=None)
    parser.add_argument("--resume", action="store_true", help="Resume from last checkpoint")
    args = parser.parse_args()
    asyncio.run(run_pipeline(script_path=args.script_path, resume=args.resume))
