import asyncio
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent
from core.utils import sanitize_prompt, generate_unique_id, get_utc_now, validate_screenplay_format
from core.exceptions import AgentProcessingError, ModelAPIError
import time
import difflib
import re

MERGE_SCREENPLAY_PROMPT = """
You are an expert screenplay editor tasked with creating the definitive version from multiple AI-generated screenplays.

**MERGE OBJECTIVES:**
1. Preserve ALL original dialogue and story elements
2. Select the best formatting from available versions
3. Ensure consistent character development and voice
4. Choose the most cinematic and effective scene descriptions
5. Resolve formatting conflicts intelligently
6. Maintain proper screenplay structure throughout
7. Ensure smooth narrative flow and pacing

**QUALITY CRITERIA:**
- Industry-standard formatting (scene headings, character names, dialogue)
- Consistent character voice and development
- Clear, visual action lines
- Proper pacing and scene transitions
- Preservation of original story intent and tone

**SOURCE MATERIAL:**
Original Script: {original_script}

**VERSIONS TO MERGE:**
{versions_content}

**INSTRUCTIONS:**
Analyze all versions and create the highest quality final screenplay that combines the best elements while maintaining perfect formatting and storytelling flow. Return only the complete, final screenplay with no additional commentary.
"""

class ScreenplayMergerAgent(BaseAgent):
    """Advanced screenplay merger using AI consensus and quality scoring"""
    
    async def process(
        self, 
        original_script: str, 
        screenplay_versions: List[Dict[str, Any]],
        merge_strategy: str = "consensus"
    ) -> Dict[str, Any]:
        """Merge multiple screenplay versions into optimal final version"""
        processing_id = generate_unique_id()
        start_time = time.time()
        
        try:
            # Validate inputs
            if not screenplay_versions or len(screenplay_versions) < 2:
                raise AgentProcessingError("ScreenplayMergerAgent", "At least 2 screenplay versions required")
            
            # Filter successful versions
            valid_versions = [v for v in screenplay_versions if v.get('success') and v.get('content')]
            if not valid_versions:
                raise AgentProcessingError("ScreenplayMergerAgent", "No valid screenplay versions to merge")
            
            self.logger.info(f"[{processing_id}] Merging {len(valid_versions)} screenplay versions")
            
            if merge_strategy == "consensus":
                merged_result = await self._consensus_merge(original_script, valid_versions, processing_id)
            elif merge_strategy == "quality_score":
                merged_result = await self._quality_score_merge(original_script, valid_versions, processing_id)
            elif merge_strategy == "best_elements":
                merged_result = await self._best_elements_merge(original_script, valid_versions, processing_id)
            else:
                # Default to consensus
                merged_result = await self._consensus_merge(original_script, valid_versions, processing_id)
            
            processing_time = time.time() - start_time
            
            # Validate final result
            validation_issues = validate_screenplay_format(merged_result)
            
            response_data = {
                "processing_id": processing_id,
                "content": merged_result,
                "merge_strategy": merge_strategy,
                "versions_merged": len(valid_versions),
                "version_providers": [v.get('provider') for v in valid_versions],
                "processing_time": processing_time,
                "validation_issues": validation_issues,
                "quality_score": self._calculate_quality_score(merged_result),
                "timestamp": get_utc_now(),
                "success": len(validation_issues) == 0
            }
            
            self.logger.info(f"[{processing_id}] Screenplay merge completed in {processing_time:.2f}s")
            return response_data
            
        except Exception as e:
            error_msg = f"Screenplay merge failed: {str(e)}"
            self.logger.error(f"[{processing_id}] {error_msg}")
            raise AgentProcessingError("ScreenplayMergerAgent", error_msg)
    
    async def _consensus_merge(
        self, 
        original_script: str, 
        versions: List[Dict[str, Any]], 
        processing_id: str
    ) -> str:
        """Merge using AI consensus approach"""
        llm = self.llms.get("openai") or self.llms.get("claude")
        if not llm:
            raise AgentProcessingError("ScreenplayMergerAgent", "No LLM available for consensus merge")
        
        # Build versions text
        versions_text = ""
        for i, version in enumerate(versions, 1):
            versions_text += f"\n\nVERSION {i} ({version.get('provider', 'unknown').upper()}):\n"
            versions_text += version.get('content', '')
        
        prompt = MERGE_SCREENPLAY_PROMPT.format(
            original_script=sanitize_prompt(original_script, 2000),
            versions_content=versions_text[:8000]
        )
        
        result = await asyncio.to_thread(
            self._run_with_retries, 
            llm.invoke, 
            prompt
        )
        
        return result.content if hasattr(result, 'content') else str(result)
    
    async def _quality_score_merge(
        self, 
        original_script: str, 
        versions: List[Dict[str, Any]], 
        processing_id: str
    ) -> str:
        """Select version with highest quality score"""
        best_version = None
        highest_score = -1
        
        for version in versions:
            content = version.get('content', '')
            score = self._calculate_quality_score(content)
            
            if score > highest_score:
                highest_score = score
                best_version = version
        
        if best_version:
            self.logger.info(f"[{processing_id}] Selected {best_version.get('provider')} version with score {highest_score}")
            return best_version.get('content', '')
        
        # Fallback to first version
        return versions[0].get('content', '')
    
    async def _best_elements_merge(
        self, 
        original_script: str, 
        versions: List[Dict[str, Any]], 
        processing_id: str
    ) -> str:
        """Merge best elements from each version"""
        # This is a simplified approach - in production, you'd want more sophisticated merging
        contents = [v.get('content', '') for v in versions]
        
        # Find common structure
        scene_patterns = []
        for content in contents:
            scenes = re.findall(r'^(INT\.|EXT\.).*$', content, re.MULTILINE)
            scene_patterns.append(scenes)
        
        # Use version with most complete scene structure
        scene_counts = [len(scenes) for scenes in scene_patterns]
        best_idx = scene_counts.index(max(scene_counts))
        
        self.logger.info(f"[{processing_id}] Selected version {best_idx} with {max(scene_counts)} scenes")
        return contents[best_idx]
    
    def _calculate_quality_score(self, screenplay: str) -> float:
        """Calculate quality score for a screenplay"""
        score = 0.0
        
        # Check for proper formatting
        if re.search(r'^(INT\.|EXT\.)', screenplay, re.MULTILINE):
            score += 20  # Has scene headings
        
        # Check for character names
        character_names = re.findall(r'^\s*([A-Z][A-Z\s]+)\s*$', screenplay, re.MULTILINE)
        score += min(len(set(character_names)) * 5, 30)  # Up to 30 points for characters
        
        # Check for dialogue
        dialogue_lines = re.findall(r'^\s*[a-z].*[.!?]\s*$', screenplay, re.MULTILINE | re.IGNORECASE)
        score += min(len(dialogue_lines) * 0.5, 25)  # Up to 25 points for dialogue
        
        # Check for proper transitions
        transitions = re.findall(r'(FADE IN:|FADE OUT:|CUT TO:|DISSOLVE TO:)', screenplay)
        score += min(len(transitions) * 2, 10)  # Up to 10 points for transitions
        
        # Length factor (reasonable length gets points)
        length_score = min(len(screenplay) / 100, 15)  # Up to 15 points for length
        score += length_score
        
        return min(score, 100.0)  # Cap at 100
    
    # Legacy method for backward compatibility
    async def process_legacy(self, original_script: str, openai_screenplay: str, claude_screenplay: str, gemini_screenplay: str):
        """Legacy method for backward compatibility"""
        versions = []
        if openai_screenplay:
            versions.append({"provider": "openai", "content": openai_screenplay, "success": True})
        if claude_screenplay:
            versions.append({"provider": "claude", "content": claude_screenplay, "success": True})
        if gemini_screenplay:
            versions.append({"provider": "gemini", "content": gemini_screenplay, "success": True})
        
        result = await self.process(original_script, versions)
        return result.get('content', '')