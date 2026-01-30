"""
Vercel Serverless API for AI Infrastructure Calculator
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import math
import urllib.request

# Get the base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_json(filename):
    """Load JSON file from data directory"""
    filepath = os.path.join(BASE_DIR, 'data', filename)
    with open(filepath, 'r') as f:
        return json.load(f)

def calculate_gpu_requirements(model, gpu, total_users, concurrent_users):
    model_memory = model['memory_required_gb']
    gpu_memory = gpu['vram_gb']
    
    if model_memory > gpu_memory:
        return {'error': f"Model requires {model_memory}GB but GPU only has {gpu_memory}GB VRAM", 'feasible': False}
    
    usable_memory = gpu_memory * 0.8
    instances_per_gpu = math.floor(usable_memory / model_memory)
    instances_per_gpu = max(1, instances_per_gpu)
    tokens_per_request = 100
    requests_per_second_per_instance = model['tokens_per_second_gpu'] / tokens_per_request
    requests_per_second_needed = concurrent_users / 3
    total_throughput_per_gpu = requests_per_second_per_instance * instances_per_gpu
    required_gpus_exact = requests_per_second_needed / total_throughput_per_gpu
    safety_factor = 1.3
    required_gpus = max(1, math.ceil(required_gpus_exact * safety_factor))
    cost_per_gpu = gpu['price_usd']
    total_cost = required_gpus * cost_per_gpu
    actual_utilization = (required_gpus_exact / required_gpus) * 100 if required_gpus > 0 else 0
    
    return {
        'feasible': True, 'infrastructure_type': 'GPU', 'model': model['name'], 'hardware': gpu['name'],
        'required_units': required_gpus, 'instances_per_unit': instances_per_gpu,
        'total_instances': required_gpus * instances_per_gpu, 'cost_per_unit': cost_per_gpu,
        'total_investment': total_cost, 'utilization_percent': round(actual_utilization, 1),
        'throughput_per_unit': round(total_throughput_per_gpu, 2),
        'total_throughput': round(total_throughput_per_gpu * required_gpus, 2),
        'concurrent_users': concurrent_users, 'total_users': total_users,
        'details': {'model_memory_gb': model_memory, 'gpu_memory_gb': gpu_memory,
                   'usable_memory_gb': round(usable_memory, 1), 'tokens_per_second': model['tokens_per_second_gpu'],
                   'safety_factor': safety_factor}
    }

def calculate_cpu_requirements(model, cpu, total_users, concurrent_users):
    model_memory = model['memory_required_gb']
    cpu_memory = cpu['recommended_ram_gb']
    
    if model_memory > cpu_memory:
        return {'error': f"Model requires {model_memory}GB but server only has {cpu_memory}GB RAM", 'feasible': False}
    
    usable_memory = cpu_memory * 0.7
    instances_per_server = max(1, math.floor(usable_memory / model_memory))
    tokens_per_request = 100
    requests_per_second_per_instance = model['tokens_per_second_cpu'] / tokens_per_request
    requests_per_second_needed = concurrent_users / 3
    total_throughput_per_server = requests_per_second_per_instance * instances_per_server
    required_servers_exact = requests_per_second_needed / total_throughput_per_server
    safety_factor = 1.4
    required_servers = max(1, math.ceil(required_servers_exact * safety_factor))
    cost_per_server = cpu['price_per_server_usd']
    total_cost = required_servers * cost_per_server
    actual_utilization = (required_servers_exact / required_servers) * 100 if required_servers > 0 else 0
    
    return {
        'feasible': True, 'infrastructure_type': 'CPU', 'model': model['name'], 'hardware': cpu['name'],
        'required_units': required_servers, 'instances_per_unit': instances_per_server,
        'total_instances': required_servers * instances_per_server, 'cost_per_unit': cost_per_server,
        'total_investment': total_cost, 'utilization_percent': round(actual_utilization, 1),
        'throughput_per_unit': round(total_throughput_per_server, 2),
        'total_throughput': round(total_throughput_per_server * required_servers, 2),
        'concurrent_users': concurrent_users, 'total_users': total_users,
        'details': {'model_memory_gb': model_memory, 'server_memory_gb': cpu_memory,
                   'usable_memory_gb': round(usable_memory, 1), 'cores': cpu['cores'], 'threads': cpu['threads'],
                   'tokens_per_second': model['tokens_per_second_cpu'], 'safety_factor': safety_factor}
    }


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_GET(self):
        path = self.path.split('?')[0]
        
        try:
            if path == '/api' or path == '/api/':
                self.send_json({'name': 'AI Infrastructure Calculator API', 'version': '1.0', 'status': 'running'})
            
            elif path == '/api/exchange-rate':
                try:
                    req = urllib.request.Request('https://api.exchangerate-api.com/v4/latest/USD')
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        data = json.loads(resp.read().decode())
                        rate = data.get('rates', {}).get('IDR', 15800)
                        self.send_json({'rate': rate, 'cached': False})
                except:
                    self.send_json({'rate': 15800, 'cached': True, 'fallback': True})
            
            elif path == '/api/models':
                models = load_json('models.json')
                self.send_json(models)
            
            elif path == '/api/gpus':
                gpus = load_json('gpus.json')
                self.send_json(gpus)
            
            elif path == '/api/cpus':
                cpus = load_json('cpus.json')
                self.send_json(cpus)
            
            else:
                self.send_json({'error': 'Not found', 'path': path}, 404)
        
        except Exception as e:
            self.send_json({'error': str(e)}, 500)
    
    def do_POST(self):
        path = self.path.split('?')[0]
        
        if path == '/api/calculate':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                data = json.loads(body.decode())
                
                infra_type = data.get('infrastructure_type', '').lower()
                model_id = data.get('model_id')
                total_users = int(data.get('total_users', 0))
                concurrent_users = int(data.get('concurrent_users', 0))
                
                models = {m['id']: m for m in load_json('models.json')}
                gpus = {g['id']: g for g in load_json('gpus.json')}
                cpus = {c['id']: c for c in load_json('cpus.json')}
                
                model = models.get(model_id)
                if not model:
                    self.send_json({'error': f'Model not found: {model_id}'}, 400)
                    return
                
                result = {}
                
                if infra_type == 'gpu':
                    gpu_id = data.get('gpu_id')
                    if gpu_id == 'all':
                        results = []
                        incompatible = []
                        for gid, gpu in gpus.items():
                            res = calculate_gpu_requirements(model, gpu, total_users, concurrent_users)
                            if res.get('feasible'):
                                res['cost_efficiency'] = res['total_investment'] / res['total_throughput'] if res['total_throughput'] > 0 else float('inf')
                                results.append(res)
                            else:
                                incompatible.append({'name': gpu['name'], 'vram': gpu['vram_gb'], 'reason': res.get('error')})
                        results.sort(key=lambda x: x['cost_efficiency'])
                        result = {'type': 'all_gpus', 'results': results, 'best_option': results[0] if results else None, 
                                 'total_options': len(results), 'incompatible': incompatible, 'total_gpus': len(gpus)}
                    else:
                        gpu = gpus.get(gpu_id)
                        if not gpu:
                            self.send_json({'error': f'GPU not found: {gpu_id}'}, 400)
                            return
                        result = calculate_gpu_requirements(model, gpu, total_users, concurrent_users)
                
                elif infra_type == 'cpu':
                    cpu_id = data.get('cpu_id')
                    if cpu_id == 'all':
                        results = []
                        incompatible = []
                        for cid, cpu in cpus.items():
                            res = calculate_cpu_requirements(model, cpu, total_users, concurrent_users)
                            if res.get('feasible'):
                                res['cost_efficiency'] = res['total_investment'] / res['total_throughput'] if res['total_throughput'] > 0 else float('inf')
                                results.append(res)
                            else:
                                incompatible.append({'name': cpu['name'], 'ram': cpu['recommended_ram_gb'], 'reason': res.get('error')})
                        results.sort(key=lambda x: x['cost_efficiency'])
                        result = {'type': 'all_cpus', 'results': results, 'best_option': results[0] if results else None,
                                 'total_options': len(results), 'incompatible': incompatible, 'total_cpus': len(cpus)}
                    else:
                        cpu = cpus.get(cpu_id)
                        if not cpu:
                            self.send_json({'error': f'CPU not found: {cpu_id}'}, 400)
                            return
                        result = calculate_cpu_requirements(model, cpu, total_users, concurrent_users)
                
                elif infra_type == 'both':
                    gpu = gpus.get(data.get('gpu_id'))
                    cpu = cpus.get(data.get('cpu_id'))
                    if not gpu or not cpu:
                        self.send_json({'error': 'Invalid GPU or CPU ID'}, 400)
                        return
                    result = {
                        'gpu': calculate_gpu_requirements(model, gpu, total_users, concurrent_users),
                        'cpu': calculate_cpu_requirements(model, cpu, total_users, concurrent_users)
                    }
                
                else:
                    self.send_json({'error': 'infrastructure_type must be gpu, cpu, or both'}, 400)
                    return
                
                self.send_json(result)
            
            except Exception as e:
                self.send_json({'error': str(e)}, 500)
        else:
            self.send_json({'error': 'Not found'}, 404)
