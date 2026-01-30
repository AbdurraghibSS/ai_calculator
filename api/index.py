"""
Vercel Serverless API for AI Infrastructure Calculator
This file handles all API routes for Vercel deployment
"""
from flask import Flask, jsonify, request
import json
import os
import math
import requests

app = Flask(__name__)

# Get the base directory (parent of api folder)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Exchange rate cache
exchange_rate_cache = {'rate': 15800, 'timestamp': 0}


def load_json(filename):
    """Load JSON file from data directory"""
    filepath = os.path.join(BASE_DIR, 'data', filename)
    with open(filepath, 'r') as f:
        return json.load(f)


# Calculator functions
def calculate_gpu_requirements(model, gpu, total_users, concurrent_users):
    model_memory = model['memory_required_gb']
    gpu_memory = gpu['vram_gb']
    
    if model_memory > gpu_memory:
        return {
            'error': f"Model requires {model_memory}GB but GPU only has {gpu_memory}GB VRAM",
            'feasible': False
        }
    
    usable_memory = gpu_memory * 0.8
    instances_per_gpu = math.floor(usable_memory / model_memory)
    tokens_per_request = 100
    requests_per_second_per_instance = model['tokens_per_second_gpu'] / tokens_per_request
    requests_per_second_needed = concurrent_users / 3
    total_throughput_per_gpu = requests_per_second_per_instance * instances_per_gpu
    required_gpus_exact = requests_per_second_needed / total_throughput_per_gpu
    safety_factor = 1.3
    required_gpus = math.ceil(required_gpus_exact * safety_factor)
    required_gpus = max(1, required_gpus)
    cost_per_gpu = gpu['price_usd']
    total_cost = required_gpus * cost_per_gpu
    actual_utilization = (required_gpus_exact / required_gpus) * 100 if required_gpus > 0 else 0
    
    return {
        'feasible': True,
        'infrastructure_type': 'GPU',
        'model': model['name'],
        'hardware': gpu['name'],
        'required_units': required_gpus,
        'instances_per_unit': instances_per_gpu,
        'total_instances': required_gpus * instances_per_gpu,
        'cost_per_unit': cost_per_gpu,
        'total_investment': total_cost,
        'utilization_percent': round(actual_utilization, 1),
        'throughput_per_unit': round(total_throughput_per_gpu, 2),
        'total_throughput': round(total_throughput_per_gpu * required_gpus, 2),
        'concurrent_users': concurrent_users,
        'total_users': total_users,
        'details': {
            'model_memory_gb': model_memory,
            'gpu_memory_gb': gpu_memory,
            'usable_memory_gb': round(usable_memory, 1),
            'tokens_per_second': model['tokens_per_second_gpu'],
            'safety_factor': safety_factor
        }
    }


def calculate_cpu_requirements(model, cpu, total_users, concurrent_users):
    model_memory = model['memory_required_gb']
    cpu_memory = cpu['recommended_ram_gb']
    
    if model_memory > cpu_memory:
        return {
            'error': f"Model requires {model_memory}GB but server only has {cpu_memory}GB RAM",
            'feasible': False
        }
    
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
        'feasible': True,
        'infrastructure_type': 'CPU',
        'model': model['name'],
        'hardware': cpu['name'],
        'required_units': required_servers,
        'instances_per_unit': instances_per_server,
        'total_instances': required_servers * instances_per_server,
        'cost_per_unit': cost_per_server,
        'total_investment': total_cost,
        'utilization_percent': round(actual_utilization, 1),
        'throughput_per_unit': round(total_throughput_per_server, 2),
        'total_throughput': round(total_throughput_per_server * required_servers, 2),
        'concurrent_users': concurrent_users,
        'total_users': total_users,
        'details': {
            'model_memory_gb': model_memory,
            'server_memory_gb': cpu_memory,
            'usable_memory_gb': round(usable_memory, 1),
            'cores': cpu['cores'],
            'threads': cpu['threads'],
            'tokens_per_second': model['tokens_per_second_cpu'],
            'safety_factor': safety_factor
        }
    }


# CORS headers helper
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


@app.route('/api', methods=['GET'])
@app.route('/api/', methods=['GET'])
def index():
    response = jsonify({
        'name': 'AI Infrastructure Procurement Calculator API',
        'version': '1.0',
        'status': 'running'
    })
    return add_cors_headers(response)


@app.route('/api/exchange-rate', methods=['GET', 'OPTIONS'])
def get_exchange_rate():
    if request.method == 'OPTIONS':
        response = jsonify({})
        return add_cors_headers(response)
    
    import time
    global exchange_rate_cache
    
    current_time = time.time()
    if current_time - exchange_rate_cache['timestamp'] < 3600:
        response = jsonify({'rate': exchange_rate_cache['rate'], 'cached': True})
        return add_cors_headers(response)
    
    try:
        resp = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=5)
        data = resp.json()
        
        if 'rates' in data and 'IDR' in data['rates']:
            rate = data['rates']['IDR']
            exchange_rate_cache = {'rate': rate, 'timestamp': current_time}
            response = jsonify({'rate': rate, 'cached': False})
            return add_cors_headers(response)
    except:
        pass
    
    response = jsonify({'rate': exchange_rate_cache['rate'], 'cached': True, 'fallback': True})
    return add_cors_headers(response)


@app.route('/api/models', methods=['GET', 'OPTIONS'])
def get_models():
    if request.method == 'OPTIONS':
        response = jsonify({})
        return add_cors_headers(response)
    
    try:
        models = load_json('models.json')
        response = jsonify(models)
        return add_cors_headers(response)
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.status_code = 500
        return add_cors_headers(response)


@app.route('/api/gpus', methods=['GET', 'OPTIONS'])
def get_gpus():
    if request.method == 'OPTIONS':
        response = jsonify({})
        return add_cors_headers(response)
    
    try:
        gpus = load_json('gpus.json')
        response = jsonify(gpus)
        return add_cors_headers(response)
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.status_code = 500
        return add_cors_headers(response)


@app.route('/api/cpus', methods=['GET', 'OPTIONS'])
def get_cpus():
    if request.method == 'OPTIONS':
        response = jsonify({})
        return add_cors_headers(response)
    
    try:
        cpus = load_json('cpus.json')
        response = jsonify(cpus)
        return add_cors_headers(response)
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.status_code = 500
        return add_cors_headers(response)


@app.route('/api/calculate', methods=['POST', 'OPTIONS'])
def calculate():
    if request.method == 'OPTIONS':
        response = jsonify({})
        return add_cors_headers(response)
    
    try:
        data = request.get_json()
        
        required_fields = ['infrastructure_type', 'model_id', 'total_users', 'concurrent_users']
        for field in required_fields:
            if field not in data:
                response = jsonify({'error': f'Missing required field: {field}'})
                response.status_code = 400
                return add_cors_headers(response)
        
        infra_type = data['infrastructure_type'].lower()
        model_id = data['model_id']
        total_users = int(data['total_users'])
        concurrent_users = int(data['concurrent_users'])
        
        # Load data
        models = {m['id']: m for m in load_json('models.json')}
        gpus = {g['id']: g for g in load_json('gpus.json')}
        cpus = {c['id']: c for c in load_json('cpus.json')}
        
        model = models.get(model_id)
        if not model:
            response = jsonify({'error': f'Model not found: {model_id}'})
            response.status_code = 400
            return add_cors_headers(response)
        
        result = {}
        
        if infra_type == 'gpu':
            gpu_id = data.get('gpu_id')
            if not gpu_id:
                response = jsonify({'error': 'gpu_id required'})
                response.status_code = 400
                return add_cors_headers(response)
            
            if gpu_id == 'all':
                results = []
                incompatible = []
                for gid, gpu in gpus.items():
                    res = calculate_gpu_requirements(model, gpu, total_users, concurrent_users)
                    if res.get('feasible'):
                        res['cost_efficiency'] = res['total_investment'] / res['total_throughput'] if res['total_throughput'] > 0 else float('inf')
                        results.append(res)
                    else:
                        incompatible.append({'name': gpu['name'], 'vram': gpu['vram_gb'], 'reason': res.get('error', 'Tidak kompatibel')})
                results.sort(key=lambda x: x['cost_efficiency'])
                result = {'type': 'all_gpus', 'results': results, 'best_option': results[0] if results else None, 'total_options': len(results), 'incompatible': incompatible, 'total_gpus': len(gpus)}
            else:
                gpu = gpus.get(gpu_id)
                if not gpu:
                    response = jsonify({'error': f'GPU not found: {gpu_id}'})
                    response.status_code = 400
                    return add_cors_headers(response)
                result = calculate_gpu_requirements(model, gpu, total_users, concurrent_users)
        
        elif infra_type == 'cpu':
            cpu_id = data.get('cpu_id')
            if not cpu_id:
                response = jsonify({'error': 'cpu_id required'})
                response.status_code = 400
                return add_cors_headers(response)
            
            if cpu_id == 'all':
                results = []
                incompatible = []
                for cid, cpu in cpus.items():
                    res = calculate_cpu_requirements(model, cpu, total_users, concurrent_users)
                    if res.get('feasible'):
                        res['cost_efficiency'] = res['total_investment'] / res['total_throughput'] if res['total_throughput'] > 0 else float('inf')
                        results.append(res)
                    else:
                        incompatible.append({'name': cpu['name'], 'ram': cpu['recommended_ram_gb'], 'reason': res.get('error', 'Tidak kompatibel')})
                results.sort(key=lambda x: x['cost_efficiency'])
                result = {'type': 'all_cpus', 'results': results, 'best_option': results[0] if results else None, 'total_options': len(results), 'incompatible': incompatible, 'total_cpus': len(cpus)}
            else:
                cpu = cpus.get(cpu_id)
                if not cpu:
                    response = jsonify({'error': f'CPU not found: {cpu_id}'})
                    response.status_code = 400
                    return add_cors_headers(response)
                result = calculate_cpu_requirements(model, cpu, total_users, concurrent_users)
        
        elif infra_type == 'both':
            gpu_id = data.get('gpu_id')
            cpu_id = data.get('cpu_id')
            if not gpu_id or not cpu_id:
                response = jsonify({'error': 'Both gpu_id and cpu_id required'})
                response.status_code = 400
                return add_cors_headers(response)
            
            gpu = gpus.get(gpu_id)
            cpu = cpus.get(cpu_id)
            if not gpu or not cpu:
                response = jsonify({'error': 'Invalid GPU or CPU ID'})
                response.status_code = 400
                return add_cors_headers(response)
            
            gpu_result = calculate_gpu_requirements(model, gpu, total_users, concurrent_users)
            cpu_result = calculate_cpu_requirements(model, cpu, total_users, concurrent_users)
            result = {'gpu': gpu_result, 'cpu': cpu_result}
        
        else:
            response = jsonify({'error': 'infrastructure_type must be "gpu", "cpu", or "both"'})
            response.status_code = 400
            return add_cors_headers(response)
        
        response = jsonify(result)
        return add_cors_headers(response)
    
    except Exception as e:
        response = jsonify({'error': f'Server error: {str(e)}'})
        response.status_code = 500
        return add_cors_headers(response)


# Vercel handler
def handler(request):
    with app.test_client() as client:
        return client.open(request.path, method=request.method, data=request.data, headers=dict(request.headers))
