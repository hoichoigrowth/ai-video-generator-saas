import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from core.exceptions import AIVideoGeneratorException
from core.utils import generate_unique_id

logger = logging.getLogger(__name__)

class N8NWorkflowParser:
    """Enhanced n8n workflow parser for AI video generation pipeline conversion"""
    
    def __init__(self, workflow_path: Optional[str] = None, workflow_data: Optional[Dict] = None):
        if workflow_data:
            self.workflow = workflow_data
        elif workflow_path:
            try:
                with open(workflow_path, 'r', encoding='utf-8') as f:
                    self.workflow = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.error(f"Failed to load workflow: {e}")
                raise AIVideoGeneratorException(f"Invalid workflow file: {str(e)}")
        else:
            raise AIVideoGeneratorException("Either workflow_path or workflow_data must be provided")
        
        self.nodes = self.workflow.get('nodes', [])
        self.connections = self.workflow.get('connections', {})
        self.metadata = {
            'total_nodes': len(self.nodes),
            'workflow_name': self.workflow.get('name', 'Unnamed Workflow'),
            'created': self.workflow.get('createdAt'),
            'updated': self.workflow.get('updatedAt')
        }

    def extract_ai_prompts(self) -> List[Dict[str, Any]]:
        """Extract AI prompts from workflow nodes"""
        prompts = []
        ai_node_types = [
            'openai', 'claude', 'gemini', 'anthropic', 'chatgpt', 'gpt',
            'langchain', 'huggingface', 'cohere', 'ai'
        ]
        
        for node in self.nodes:
            node_type = node.get('type', '').lower()
            parameters = node.get('parameters', {})
            
            # Check if it's an AI node
            is_ai_node = any(ai_type in node_type for ai_type in ai_node_types)
            has_prompt = 'prompt' in parameters or 'message' in parameters or 'text' in parameters
            
            if is_ai_node or has_prompt:
                prompt_data = {
                    'node_id': node.get('id', generate_unique_id()),
                    'node_name': node.get('name', 'Unnamed Node'),
                    'node_type': node_type,
                    'prompts': [],
                    'model': parameters.get('model', 'unknown'),
                    'temperature': parameters.get('temperature'),
                    'max_tokens': parameters.get('maxTokens', parameters.get('max_tokens'))
                }
                
                # Extract various prompt fields
                for prompt_field in ['prompt', 'message', 'text', 'systemMessage', 'userMessage']:
                    if prompt_field in parameters:
                        prompt_data['prompts'].append({
                            'type': prompt_field,
                            'content': parameters[prompt_field]
                        })
                
                if prompt_data['prompts']:
                    prompts.append(prompt_data)
        
        return prompts
    
    def extract_workflow_stages(self) -> List[Dict[str, Any]]:
        """Extract workflow stages based on AI video generation pipeline"""
        stages = []
        stage_keywords = {
            'script_input': ['script', 'input', 'text', 'story', 'content'],
            'screenplay': ['screenplay', 'format', 'dialogue', 'scene'],
            'shot_division': ['shot', 'scene', 'break', 'divide', 'cut'],
            'character_extraction': ['character', 'cast', 'person', 'actor'],
            'production_planning': ['production', 'plan', 'schedule', 'timeline'],
            'scene_generation': ['image', 'midjourney', 'dall-e', 'stable', 'picture'],
            'video_generation': ['video', 'kling', 'runway', 'pika', 'motion'],
            'human_approval': ['approve', 'human', 'review', 'check', 'confirm']
        }
        
        for node in self.nodes:
            node_name = node.get('name', '').lower()
            node_type = node.get('type', '').lower()
            parameters = node.get('parameters', {})
            
            stage_detected = None
            confidence = 0
            
            # Check for stage keywords in node name and type
            for stage, keywords in stage_keywords.items():
                matches = sum(1 for keyword in keywords if keyword in node_name or keyword in node_type)
                if matches > confidence:
                    confidence = matches
                    stage_detected = stage
            
            # Check parameters for additional context
            prompt_text = str(parameters.get('prompt', '')).lower()
            for stage, keywords in stage_keywords.items():
                matches = sum(1 for keyword in keywords if keyword in prompt_text)
                if matches > confidence:
                    confidence = matches
                    stage_detected = stage
            
            if stage_detected and confidence > 0:
                stages.append({
                    'node_id': node.get('id', generate_unique_id()),
                    'node_name': node.get('name'),
                    'stage': stage_detected,
                    'confidence': confidence,
                    'node_type': node_type,
                    'parameters': parameters
                })
        
        return sorted(stages, key=lambda x: x['confidence'], reverse=True)
    
    def extract_api_integrations(self) -> List[Dict[str, Any]]:
        """Extract API calls and integrations"""
        api_calls = []
        http_node_types = ['httprequest', 'webhook', 'http request', 'api call']
        
        for node in self.nodes:
            node_type = node.get('type', '').lower()
            parameters = node.get('parameters', {})
            
            if any(http_type in node_type for http_type in http_node_types):
                url = parameters.get('url', '')
                
                # Detect service type from URL
                service_type = 'unknown'
                if 'docs.google' in url:
                    service_type = 'google_docs'
                elif 'sheets.google' in url:
                    service_type = 'google_sheets'
                elif 'openai' in url or 'api.openai' in url:
                    service_type = 'openai'
                elif 'anthropic' in url or 'claude' in url:
                    service_type = 'anthropic'
                elif 'midjourney' in url or 'discord' in url:
                    service_type = 'midjourney'
                elif 'piapi' in url:
                    service_type = 'piapi'
                elif 'gotohuman' in url:
                    service_type = 'gotohuman'
                
                api_calls.append({
                    'node_id': node.get('id', generate_unique_id()),
                    'node_name': node.get('name'),
                    'service_type': service_type,
                    'url': url,
                    'method': parameters.get('method', 'GET'),
                    'headers': parameters.get('headers', {}),
                    'body': parameters.get('body'),
                    'authentication': parameters.get('authentication', {}),
                    'node_type': node_type
                })
        
        return api_calls
    
    def extract_human_approval_points(self) -> List[Dict[str, Any]]:
        """Extract human approval/intervention points"""
        approval_points = []
        approval_keywords = ['approve', 'human', 'review', 'check', 'confirm', 'manual', 'wait']
        
        for node in self.nodes:
            node_name = node.get('name', '').lower()
            node_type = node.get('type', '').lower()
            
            if any(keyword in node_name or keyword in node_type for keyword in approval_keywords):
                approval_points.append({
                    'node_id': node.get('id', generate_unique_id()),
                    'node_name': node.get('name'),
                    'node_type': node_type,
                    'approval_type': self._classify_approval_type(node_name, node_type),
                    'parameters': node.get('parameters', {})
                })
        
        return approval_points
    
    def _classify_approval_type(self, node_name: str, node_type: str) -> str:
        """Classify the type of human approval required"""
        if 'webhook' in node_type or 'http' in node_type:
            return 'webhook_approval'
        elif 'email' in node_name or 'email' in node_type:
            return 'email_approval'
        elif 'slack' in node_name or 'discord' in node_name:
            return 'chat_approval'
        elif 'form' in node_name or 'form' in node_type:
            return 'form_approval'
        else:
            return 'manual_approval'
    
    def extract_data_transformations(self) -> List[Dict[str, Any]]:
        """Extract data transformation and processing nodes"""
        transformations = []
        transform_types = ['set', 'function', 'code', 'javascript', 'python', 'split', 'merge', 'filter']
        
        for node in self.nodes:
            node_type = node.get('type', '').lower()
            
            if any(transform in node_type for transform in transform_types):
                transformations.append({
                    'node_id': node.get('id', generate_unique_id()),
                    'node_name': node.get('name'),
                    'transformation_type': node_type,
                    'code': node.get('parameters', {}).get('jsCode', node.get('parameters', {}).get('code')),
                    'fields': node.get('parameters', {}).get('values', {}),
                    'parameters': node.get('parameters', {})
                })
        
        return transformations
    
    def build_execution_flow(self) -> List[Dict[str, Any]]:
        """Build execution flow graph from connections"""
        flow = []
        
        for source_node, connections in self.connections.items():
            source = next((n for n in self.nodes if n['name'] == source_node), None)
            
            if not source:
                continue
            
            for output_type, targets in connections.items():
                for target in targets:
                    target_node = next((n for n in self.nodes if n['name'] == target['node']), None)
                    
                    if target_node:
                        flow.append({
                            'from_node_id': source.get('id', generate_unique_id()),
                            'from_node_name': source.get('name'),
                            'from_node_type': source.get('type'),
                            'to_node_id': target_node.get('id', generate_unique_id()),
                            'to_node_name': target_node.get('name'),
                            'to_node_type': target_node.get('type'),
                            'output_type': output_type,
                            'target_index': target.get('index', 0)
                        })
        
        return flow
    
    def generate_pipeline_config(self) -> Dict[str, Any]:
        """Generate pipeline configuration from n8n workflow"""
        stages = self.extract_workflow_stages()
        api_integrations = self.extract_api_integrations()
        approval_points = self.extract_human_approval_points()
        
        # Map stages to our pipeline configuration
        pipeline_config = {
            'workflow_metadata': self.metadata,
            'stages': {},
            'integrations': {},
            'approval_checkpoints': [],
            'execution_flow': self.build_execution_flow()
        }
        
        # Process stages
        for stage in stages:
            stage_name = stage['stage']
            if stage_name not in pipeline_config['stages']:
                pipeline_config['stages'][stage_name] = []
            
            pipeline_config['stages'][stage_name].append({
                'node_name': stage['node_name'],
                'node_type': stage['node_type'],
                'confidence': stage['confidence'],
                'parameters': stage['parameters']
            })
        
        # Process API integrations
        for api in api_integrations:
            service = api['service_type']
            if service not in pipeline_config['integrations']:
                pipeline_config['integrations'][service] = []
            
            pipeline_config['integrations'][service].append({
                'node_name': api['node_name'],
                'url': api['url'],
                'method': api['method'],
                'authentication': api.get('authentication', {})
            })
        
        # Process approval points
        pipeline_config['approval_checkpoints'] = [
            {
                'stage': self._map_approval_to_stage(point['node_name']),
                'type': point['approval_type'],
                'node_name': point['node_name'],
                'parameters': point['parameters']
            }
            for point in approval_points
        ]
        
        return pipeline_config
    
    def _map_approval_to_stage(self, node_name: str) -> str:
        """Map approval node to pipeline stage"""
        node_name_lower = node_name.lower()
        
        if 'screenplay' in node_name_lower:
            return 'screenplay_generation'
        elif 'shot' in node_name_lower:
            return 'shot_division'
        elif 'character' in node_name_lower:
            return 'character_design'
        elif 'scene' in node_name_lower or 'image' in node_name_lower:
            return 'scene_generation'
        elif 'video' in node_name_lower:
            return 'video_generation'
        else:
            return 'general_approval'
    
    def parse_all(self) -> Dict[str, Any]:
        """Parse all workflow components"""
        return {
            'metadata': self.metadata,
            'ai_prompts': self.extract_ai_prompts(),
            'workflow_stages': self.extract_workflow_stages(),
            'api_integrations': self.extract_api_integrations(),
            'human_approvals': self.extract_human_approval_points(),
            'data_transformations': self.extract_data_transformations(),
            'execution_flow': self.build_execution_flow(),
            'pipeline_config': self.generate_pipeline_config()
        }

# Example usage:
# parser = N8NWorkflowParser('workflow.json')
# parsed = parser.parse_all()
# print(json.dumps(parsed, indent=2))
