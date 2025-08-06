import json
from typing import Dict, List, Any

class N8NWorkflowParser:
    def __init__(self, workflow_path: str):
        with open(workflow_path, 'r') as f:
            self.workflow = json.load(f)
        self.nodes = self.workflow.get('nodes', [])
        self.connections = self.workflow.get('connections', {})

    def extract_prompts(self) -> List[Dict[str, Any]]:
        prompts = []
        for node in self.nodes:
            if node.get('type', '').lower().startswith('ai') or 'prompt' in node.get('parameters', {}):
                prompt = node['parameters'].get('prompt')
                if prompt:
                    prompts.append({
                        'node': node['name'],
                        'prompt': prompt
                    })
        return prompts

    def extract_api_calls(self) -> List[Dict[str, Any]]:
        api_calls = []
        for node in self.nodes:
            if node.get('type', '').lower() in ['httprequest', 'webhook', 'apicall', 'http request']:
                api_calls.append({
                    'node': node['name'],
                    'url': node['parameters'].get('url'),
                    'method': node['parameters'].get('method', 'GET'),
                    'body': node['parameters'].get('body')
                })
        return api_calls

    def extract_node_connections(self) -> List[Dict[str, Any]]:
        connections = []
        for source, targets in self.connections.items():
            for conn_type, target_list in targets.items():
                for target in target_list:
                    connections.append({
                        'from': source,
                        'to': target['node'],
                        'type': conn_type
                    })
        return connections

    def extract_data_flow(self) -> List[Dict[str, Any]]:
        # Data flow: for each node, what data is passed to the next
        data_flow = []
        for conn in self.extract_node_connections():
            from_node = next((n for n in self.nodes if n['name'] == conn['from']), None)
            to_node = next((n for n in self.nodes if n['name'] == conn['to']), None)
            if from_node and to_node:
                data_flow.append({
                    'from': from_node['name'],
                    'to': to_node['name'],
                    'from_type': from_node.get('type'),
                    'to_type': to_node.get('type'),
                    'from_output': from_node.get('parameters', {}).get('output', None),
                    'to_input': to_node.get('parameters', {}).get('input', None)
                })
        return data_flow

    def parse_all(self) -> Dict[str, Any]:
        return {
            'prompts': self.extract_prompts(),
            'api_calls': self.extract_api_calls(),
            'connections': self.extract_node_connections(),
            'data_flow': self.extract_data_flow()
        }

# Example usage:
# parser = N8NWorkflowParser('workflow.json')
# parsed = parser.parse_all()
# print(json.dumps(parsed, indent=2))
