"""
Flask API for AI Infrastructure Calculator
Provides REST endpoints for model, GPU, CPU data and calculations
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import requests
from calculator import InfrastructureCalculator
from price_fetcher import PriceFetcher

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize calculator and price fetcher
calc = InfrastructureCalculator()
price_fetcher = PriceFetcher()

# Exchange rate cache
exchange_rate_cache = {'rate': 15800, 'timestamp': 0}  # Default fallback rate


@app.route('/')
def index():
    """API information"""
    return jsonify({
        'name': 'AI Infrastructure Procurement Calculator API',
        'version': '1.0',
        'endpoints': {
            '/api/models': 'GET - List all AI models',
            '/api/gpus': 'GET - List all GPU options',
            '/api/cpus': 'GET - List all CPU options',
            '/api/exchange-rate': 'GET - Get USD to IDR exchange rate',
            '/api/calculate': 'POST - Calculate infrastructure requirements'
        }
    })


@app.route('/api/exchange-rate', methods=['GET'])
def get_exchange_rate():
    """Get current USD to IDR exchange rate"""
    import time
    
    global exchange_rate_cache
    
    # Cache for 1 hour (3600 seconds)
    current_time = time.time()
    if current_time - exchange_rate_cache['timestamp'] < 3600:
        return jsonify({
            'rate': exchange_rate_cache['rate'],
            'cached': True
        })
    
    try:
        # Using exchangerate-api.com (free tier, no API key needed)
        response = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=5)
        data = response.json()
        
        if 'rates' in data and 'IDR' in data['rates']:
            rate = data['rates']['IDR']
            exchange_rate_cache = {
                'rate': rate,
                'timestamp': current_time
            }
            return jsonify({
                'rate': rate,
                'cached': False
            })
        else:
            # Fallback to cached or default rate
            return jsonify({
                'rate': exchange_rate_cache['rate'],
                'cached': True,
                'fallback': True
            })
    except Exception as e:
        # Return cached or default rate on error
        return jsonify({
            'rate': exchange_rate_cache['rate'],
            'cached': True,
            'error': str(e)
        })


@app.route('/api/models', methods=['GET'])
def get_models():
    """Get all available AI models"""
    try:
        with open('data/models.json', 'r') as f:
            models = json.load(f)
        return jsonify(models)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/gpus', methods=['GET'])
def get_gpus():
    """Get all available GPU options with real-time pricing"""
    try:
        # Load base GPU data (specifications)
        with open('data/gpus.json', 'r') as f:
            gpus = json.load(f)
        
        # Fetch current prices
        current_prices = price_fetcher.get_gpu_prices()
        
        # Merge prices with specifications
        for gpu in gpus:
            if gpu['id'] in current_prices:
                gpu['price_usd'] = current_prices[gpu['id']]
                gpu['price_updated'] = True
            else:
                gpu['price_updated'] = False
        
        return jsonify(gpus)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cpus', methods=['GET'])
def get_cpus():
    """Get all available CPU options with real-time pricing"""
    try:
        # Load base CPU data (specifications)
        with open('data/cpus.json', 'r') as f:
            cpus = json.load(f)
        
        # Fetch current prices
        current_prices = price_fetcher.get_cpu_prices()
        
        # Merge prices with specifications
        for cpu in cpus:
            if cpu['id'] in current_prices:
                cpu['price_per_server_usd'] = current_prices[cpu['id']]
                cpu['price_updated'] = True
            else:
                cpu['price_updated'] = False
        
        return jsonify(cpus)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/calculate', methods=['POST'])
def calculate():
    """
    Calculate infrastructure requirements
    
    Request body:
    {
        "infrastructure_type": "gpu" or "cpu" or "both",
        "model_id": "llama-2-7b",
        "total_users": 10000,
        "concurrent_users": 1000,
        "gpu_id": "h100-80gb",  // required if type is gpu or both
        "cpu_id": "epyc-9654"   // required if type is cpu or both
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['infrastructure_type', 'model_id', 'total_users', 'concurrent_users']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        infra_type = data['infrastructure_type'].lower()
        model_id = data['model_id']
        total_users = int(data['total_users'])
        concurrent_users = int(data['concurrent_users'])
        
        # Validate user counts
        if total_users < 1 or concurrent_users < 1:
            return jsonify({'error': 'User counts must be positive'}), 400
        
        if concurrent_users > total_users:
            return jsonify({'error': 'Concurrent users cannot exceed total users'}), 400
        
        result = {}
        
        if infra_type == 'gpu':
            if 'gpu_id' not in data:
                return jsonify({'error': 'gpu_id required for GPU calculation'}), 400
            
            gpu_id = data['gpu_id']
            
            # Handle "all" option
            if gpu_id == 'all':
                result = calc.calculate_all_gpus(model_id, total_users, concurrent_users)
            else:
                result = calc.calculate_gpu_requirements(model_id, total_users, concurrent_users, gpu_id)
        
        elif infra_type == 'cpu':
            if 'cpu_id' not in data:
                return jsonify({'error': 'cpu_id required for CPU calculation'}), 400
            
            cpu_id = data['cpu_id']
            
            # Handle "all" option
            if cpu_id == 'all':
                result = calc.calculate_all_cpus(model_id, total_users, concurrent_users)
            else:
                result = calc.calculate_cpu_requirements(model_id, total_users, concurrent_users, cpu_id)
        
        elif infra_type == 'both':
            if 'gpu_id' not in data or 'cpu_id' not in data:
                return jsonify({'error': 'Both gpu_id and cpu_id required for comparison'}), 400
            
            gpu_id = data['gpu_id']
            cpu_id = data['cpu_id']
            result = calc.compare_options(model_id, total_users, concurrent_users, gpu_id, cpu_id)
        
        else:
            return jsonify({'error': 'infrastructure_type must be "gpu", "cpu", or "both"'}), 400
        
        return jsonify(result)
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


if __name__ == '__main__':
    print("Starting AI Infrastructure Calculator API...")
    print("API will be available at http://localhost:5001")
    print("\nEndpoints:")
    print("  GET  /api/models  - List AI models")
    print("  GET  /api/gpus    - List GPU options")
    print("  GET  /api/cpus    - List CPU options")
    print("  POST /api/calculate - Calculate requirements")
    print("\nPress Ctrl+C to stop the server")
    app.run(debug=True, host='0.0.0.0', port=5001)
