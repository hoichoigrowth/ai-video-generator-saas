import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
import logging
import time
from core.exceptions import PiAPIError
from core.utils import generate_unique_id, make_http_request
import json

logger = logging.getLogger(__name__)

class PiAPIService:
    """Enhanced PiAPI service for Midjourney and video generation"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.piapi.ai"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=aiohttp.ClientTimeout(total=300)  # 5 minute timeout
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generate_midjourney_image(
        self, 
        prompt: str, 
        aspect_ratio: str = "9:16",
        style: str = "raw",
        quality: str = "standard",
        chaos: int = 0,
        seed: Optional[int] = None,
        style_reference: Optional[str] = None,
        character_reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate image using Midjourney via PiAPI"""
        try:
            # Prepare Midjourney parameters
            mj_params = [f"--ar {aspect_ratio}"]
            
            if style != "raw":
                mj_params.append(f"--style {style}")
            if quality != "standard":
                mj_params.append(f"--quality {quality}")
            if chaos > 0:
                mj_params.append(f"--chaos {chaos}")
            if seed:
                mj_params.append(f"--seed {seed}")
            if style_reference:
                mj_params.append(f"--sref {style_reference}")
            if character_reference:
                mj_params.append(f"--cref {character_reference}")
            
            # Build full prompt
            full_prompt = f"{prompt} {' '.join(mj_params)}"
            
            request_data = {
                "model": "midjourney",
                "prompt": full_prompt,
                "process_mode": "fast",  # or "relax" for slower/cheaper
                "aspect_ratio": aspect_ratio
            }
            
            logger.info(f"Generating Midjourney image with prompt: {full_prompt[:100]}...")
            
            # Mock response for development
            if not self.api_key or self.api_key == "demo_key":
                await asyncio.sleep(2)  # Simulate API delay
                return {
                    "task_id": f"mj_{generate_unique_id()[:8]}",
                    "status": "completed",
                    "image_urls": [
                        f"https://mock-cdn.example.com/midjourney_{generate_unique_id()[:8]}.jpg"
                    ],
                    "prompt": full_prompt,
                    "aspect_ratio": aspect_ratio,
                    "processing_time": 2.0,
                    "mock": True
                }
            
            # Make API request
            if not self.session:
                async with self:
                    return await self._make_midjourney_request(request_data)
            else:
                return await self._make_midjourney_request(request_data)
                
        except Exception as e:
            logger.error(f"Midjourney generation failed: {e}")
            raise PiAPIError(f"Image generation failed: {str(e)}")
    
    async def _make_midjourney_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make the actual Midjourney API request"""
        start_time = time.time()
        
        try:
            # Submit generation request
            async with self.session.post(f"{self.base_url}/midjourney/generate", json=request_data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise PiAPIError(f"API request failed with status {response.status}: {error_text}")
                
                result = await response.json()
                task_id = result.get("task_id")
                
                if not task_id:
                    raise PiAPIError("No task ID returned from API")
            
            # Poll for completion
            max_polls = 60  # 5 minutes with 5-second intervals
            for attempt in range(max_polls):
                await asyncio.sleep(5)
                
                async with self.session.get(f"{self.base_url}/midjourney/status/{task_id}") as response:
                    if response.status != 200:
                        continue
                    
                    status_result = await response.json()
                    status = status_result.get("status")
                    
                    if status == "completed":
                        processing_time = time.time() - start_time
                        return {
                            "task_id": task_id,
                            "status": "completed",
                            "image_urls": status_result.get("image_urls", []),
                            "prompt": request_data["prompt"],
                            "aspect_ratio": request_data["aspect_ratio"],
                            "processing_time": processing_time,
                            "metadata": status_result.get("metadata", {})
                        }
                    elif status == "failed":
                        raise PiAPIError(f"Generation failed: {status_result.get('error', 'Unknown error')}")
            
            raise PiAPIError("Generation timed out after 5 minutes")
            
        except aiohttp.ClientError as e:
            raise PiAPIError(f"HTTP client error: {str(e)}")
    
    async def generate_kling_video(
        self, 
        prompt: str,
        image_url: Optional[str] = None,
        duration: float = 5.0,
        aspect_ratio: str = "9:16",
        fps: int = 24,
        quality: str = "standard"
    ) -> Dict[str, Any]:
        """Generate video using Kling via PiAPI"""
        try:
            request_data = {
                "model": "kling",
                "prompt": prompt,
                "duration": duration,
                "aspect_ratio": aspect_ratio,
                "fps": fps,
                "quality": quality
            }
            
            if image_url:
                request_data["image_url"] = image_url
            
            logger.info(f"Generating Kling video with prompt: {prompt[:100]}...")
            
            # Mock response for development
            if not self.api_key or self.api_key == "demo_key":
                await asyncio.sleep(int(duration * 2))  # Simulate longer processing
                return {
                    "task_id": f"kling_{generate_unique_id()[:8]}",
                    "status": "completed",
                    "video_url": f"https://mock-cdn.example.com/kling_{generate_unique_id()[:8]}.mp4",
                    "thumbnail_url": f"https://mock-cdn.example.com/thumb_{generate_unique_id()[:8]}.jpg",
                    "prompt": prompt,
                    "duration": duration,
                    "aspect_ratio": aspect_ratio,
                    "processing_time": duration * 2,
                    "mock": True
                }
            
            # Make API request
            if not self.session:
                async with self:
                    return await self._make_kling_request(request_data)
            else:
                return await self._make_kling_request(request_data)
                
        except Exception as e:
            logger.error(f"Kling video generation failed: {e}")
            raise PiAPIError(f"Video generation failed: {str(e)}")
    
    async def _make_kling_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make the actual Kling API request"""
        start_time = time.time()
        
        try:
            # Submit generation request
            async with self.session.post(f"{self.base_url}/kling/generate", json=request_data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise PiAPIError(f"API request failed with status {response.status}: {error_text}")
                
                result = await response.json()
                task_id = result.get("task_id")
                
                if not task_id:
                    raise PiAPIError("No task ID returned from API")
            
            # Poll for completion (videos take longer)
            max_polls = 120  # 10 minutes with 5-second intervals
            for attempt in range(max_polls):
                await asyncio.sleep(5)
                
                async with self.session.get(f"{self.base_url}/kling/status/{task_id}") as response:
                    if response.status != 200:
                        continue
                    
                    status_result = await response.json()
                    status = status_result.get("status")
                    
                    if status == "completed":
                        processing_time = time.time() - start_time
                        return {
                            "task_id": task_id,
                            "status": "completed",
                            "video_url": status_result.get("video_url"),
                            "thumbnail_url": status_result.get("thumbnail_url"),
                            "prompt": request_data["prompt"],
                            "duration": request_data["duration"],
                            "aspect_ratio": request_data["aspect_ratio"],
                            "processing_time": processing_time,
                            "metadata": status_result.get("metadata", {})
                        }
                    elif status == "failed":
                        raise PiAPIError(f"Generation failed: {status_result.get('error', 'Unknown error')}")
                    elif status == "processing":
                        progress = status_result.get("progress", 0)
                        logger.info(f"Kling video generation progress: {progress}%")
            
            raise PiAPIError("Video generation timed out after 10 minutes")
            
        except aiohttp.ClientError as e:
            raise PiAPIError(f"HTTP client error: {str(e)}")
    
    async def get_task_status(self, task_id: str, model: str = "midjourney") -> Dict[str, Any]:
        """Get status of a generation task"""
        try:
            if not self.api_key or self.api_key == "demo_key":
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "mock": True
                }
            
            endpoint = f"{self.base_url}/{model}/status/{task_id}"
            
            if not self.session:
                response_data = await make_http_request(
                    "GET", 
                    endpoint, 
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                return response_data.get("data", {})
            else:
                async with self.session.get(endpoint) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise PiAPIError(f"Status check failed with status {response.status}")
                        
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            raise PiAPIError(f"Status check failed: {str(e)}")
    
    async def batch_generate_images(
        self, 
        prompts: List[Dict[str, Any]],
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """Generate multiple images concurrently with rate limiting"""
        try:
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def generate_single(prompt_data):
                async with semaphore:
                    return await self.generate_midjourney_image(**prompt_data)
            
            tasks = [generate_single(prompt_data) for prompt_data in prompts]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle exceptions
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Batch generation failed for prompt {i}: {result}")
                    processed_results.append({
                        "error": str(result),
                        "prompt_index": i,
                        "success": False
                    })
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Batch image generation failed: {e}")
            raise PiAPIError(f"Batch generation failed: {str(e)}")
    
    async def estimate_cost(
        self, 
        image_count: int = 0, 
        video_count: int = 0,
        video_duration_total: float = 0.0
    ) -> Dict[str, float]:
        """Estimate API costs for generation requests"""
        # These are example pricing - adjust based on actual PiAPI rates
        image_cost_per_generation = 0.20  # $0.20 per Midjourney image
        video_cost_per_second = 0.50      # $0.50 per second of Kling video
        
        image_cost = image_count * image_cost_per_generation
        video_cost = video_duration_total * video_cost_per_second
        
        return {
            "image_cost": image_cost,
            "video_cost": video_cost,
            "total_estimated_cost": image_cost + video_cost,
            "image_count": image_count,
            "video_count": video_count,
            "video_duration_total": video_duration_total
        }
    
    # Legacy methods for backward compatibility
    async def generate_image(self, prompt: str, aspect_ratio: str = "9:16") -> str:
        """Legacy method for backward compatibility"""
        result = await self.generate_midjourney_image(prompt, aspect_ratio)
        return result.get("image_urls", [""])[0]
    
    async def generate_video(self, prompt: str, aspect_ratio: str = "9:16") -> str:
        """Legacy method for backward compatibility"""
        result = await self.generate_kling_video(prompt, aspect_ratio=aspect_ratio)
        return result.get("video_url", "")