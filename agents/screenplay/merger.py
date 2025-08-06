import re
from typing import List, Dict

def extract_dialogue_blocks(screenplay: str) -> List[str]:
    """
    Extracts dialogue blocks (character + dialogue) from a screenplay.
    """
    pattern = re.compile(r"(^[A-Z][A-Z0-9_ ]+\n(?:\([^\)]*\)\n)?[\s\S]+?(?=\n\n|$))", re.MULTILINE)
    return pattern.findall(screenplay)

def extract_scene_headings(screenplay: str) -> List[str]:
    """
    Extracts scene headings (e.g., INT. or EXT.) from a screenplay.
    """
    pattern = re.compile(r"^(INT\.|EXT\.|I/E\.|EST\.).*", re.MULTILINE)
    return pattern.findall(screenplay)

def merge_screenplays(openai_version: str, claude_version: str, gemini_version: str) -> str:
    """
    Merges three screenplay versions into a consensus screenplay.
    - Prefers formatting that is most consistent across versions
    - Ensures all unique dialogue blocks are included
    - Validates the merged output
    """
    # 1. Extract scene headings and dialogue blocks from all versions
    all_versions = [openai_version, claude_version, gemini_version]
    scene_headings = set()
    dialogue_blocks = set()
    merged_lines = []

    for version in all_versions:
        scene_headings.update(extract_scene_headings(version))
        dialogue_blocks.update(extract_dialogue_blocks(version))

    # 2. Build merged screenplay: interleave scene headings and dialogue blocks
    #    Prefer the order from the OpenAI version, but fill in missing blocks from others
    openai_lines = openai_version.split("\n\n")
    used_dialogue = set()
    used_scenes = set()

    for block in openai_lines:
        block = block.strip()
        if not block:
            continue
        if block in scene_headings and block not in used_scenes:
            merged_lines.append(block)
            used_scenes.add(block)
        elif block in dialogue_blocks and block not in used_dialogue:
            merged_lines.append(block)
            used_dialogue.add(block)
        else:
            # If it's an action line or transition, just add it
            merged_lines.append(block)

    # Add any missing dialogue blocks from Claude and Gemini
    for block in dialogue_blocks:
        if block not in used_dialogue:
            merged_lines.append(block)
            used_dialogue.add(block)

    # 3. Validation: ensure all dialogue blocks are present
    for version in all_versions:
        for block in extract_dialogue_blocks(version):
            if block not in merged_lines:
                merged_lines.append(block)

    # 4. Final formatting: join with double newlines
    merged_screenplay = "\n\n".join(merged_lines)

    # 5. Output validation: check for at least one scene heading and dialogue
    if not extract_scene_headings(merged_screenplay):
        raise ValueError("Merged screenplay missing scene headings.")
    if not extract_dialogue_blocks(merged_screenplay):
        raise ValueError("Merged screenplay missing dialogue blocks.")

    return merged_screenplay
