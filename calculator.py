"""
AI Infrastructure Calculator
Calculates GPU and CPU requirements based on model specifications and user load
"""
import json
import math


class InfrastructureCalculator:
    def __init__(self):
        self.load_data()
    
    def load_data(self):
        """Load model, GPU, and CPU data from JSON files"""
        with open('data/models.json', 'r') as f:
            self.models = {m['id']: m for m in json.load(f)}
        
        with open('data/gpus.json', 'r') as f:
            self.gpus = {g['id']: g for g in json.load(f)}
        
        with open('data/cpus.json', 'r') as f:
            self.cpus = {c['id']: c for c in json.load(f)}
    
    def calculate_gpu_requirements(self, model_id, total_users, concurrent_users, gpu_id):
        """
        Calculate GPU requirements for AI inference
        
        Args:
            model_id: ID of the AI model
            total_users: Total number of users
            concurrent_users: Number of concurrent users
            gpu_id: ID of the GPU to use
            
        Returns:
            dict with calculation results
        """
        model = self.models.get(model_id)
        gpu = self.gpus.get(gpu_id)
        
        if not model or not gpu:
            return {
                'error': f'Model atau GPU tidak valid. Model: {model_id}, GPU: {gpu_id}',
                'feasible': False
            }
        
        # Check if model fits in GPU memory
        model_memory = model['memory_required_gb']
        gpu_memory = gpu['vram_gb']
        
        if model_memory > gpu_memory:
            return {
                'error': f"Model requires {model_memory}GB but GPU only has {gpu_memory}GB VRAM",
                'feasible': False
            }
        
        # Calculate how many model instances can fit on one GPU
        # Reserve 20% for overhead
        usable_memory = gpu_memory * 0.8
        instances_per_gpu = math.floor(usable_memory / model_memory)
        
        # Calculate throughput
        tokens_per_request = 100  # Average tokens per request
        requests_per_second_per_instance = model['tokens_per_second_gpu'] / tokens_per_request
        
        # Total requests per second needed for concurrent users
        # Assume each concurrent user makes 1 request every 3 seconds
        requests_per_second_needed = concurrent_users / 3
        
        # Calculate required GPUs
        total_throughput_per_gpu = requests_per_second_per_instance * instances_per_gpu
        required_gpus_exact = requests_per_second_needed / total_throughput_per_gpu
        
        # Add 30% safety margin and round up
        safety_factor = 1.3
        required_gpus = math.ceil(required_gpus_exact * safety_factor)
        
        # Ensure at least 1 GPU
        required_gpus = max(1, required_gpus)
        
        # Calculate costs
        cost_per_gpu = gpu['price_usd']
        total_cost = required_gpus * cost_per_gpu
        
        # Calculate utilization
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
    
    def calculate_cpu_requirements(self, model_id, total_users, concurrent_users, cpu_id):
        """
        Calculate CPU server requirements for AI inference
        
        Args:
            model_id: ID of the AI model
            total_users: Total number of users
            concurrent_users: Number of concurrent users
            cpu_id: ID of the CPU to use
            
        Returns:
            dict with calculation results
        """
        model = self.models.get(model_id)
        cpu = self.cpus.get(cpu_id)
        
        if not model or not cpu:
            return {
                'error': f'Model atau CPU tidak valid. Model: {model_id}, CPU: {cpu_id}',
                'feasible': False
            }
        
        # Check if model fits in CPU memory
        model_memory = model['memory_required_gb']
        cpu_memory = cpu['recommended_ram_gb']
        
        if model_memory > cpu_memory:
            return {
                'error': f"Model requires {model_memory}GB but server only has {cpu_memory}GB RAM",
                'feasible': False
            }
        
        # Calculate how many model instances can fit on one server
        # Reserve 30% for OS and overhead
        usable_memory = cpu_memory * 0.7
        instances_per_server = math.floor(usable_memory / model_memory)
        
        # Ensure at least 1 instance
        instances_per_server = max(1, instances_per_server)
        
        # Calculate throughput
        tokens_per_request = 100  # Average tokens per request
        requests_per_second_per_instance = model['tokens_per_second_cpu'] / tokens_per_request
        
        # Total requests per second needed for concurrent users
        # Assume each concurrent user makes 1 request every 3 seconds
        requests_per_second_needed = concurrent_users / 3
        
        # Calculate required servers
        total_throughput_per_server = requests_per_second_per_instance * instances_per_server
        required_servers_exact = requests_per_second_needed / total_throughput_per_server
        
        # Add 40% safety margin (higher than GPU due to lower performance)
        safety_factor = 1.4
        required_servers = math.ceil(required_servers_exact * safety_factor)
        
        # Ensure at least 1 server
        required_servers = max(1, required_servers)
        
        # Calculate costs
        cost_per_server = cpu['price_per_server_usd']
        total_cost = required_servers * cost_per_server
        
        # Calculate utilization
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
    
    def compare_options(self, model_id, total_users, concurrent_users, gpu_id, cpu_id):
        """
        Compare GPU vs CPU options side by side
        
        Returns:
            dict with both calculations
        """
        gpu_result = self.calculate_gpu_requirements(model_id, total_users, concurrent_users, gpu_id)
        cpu_result = self.calculate_cpu_requirements(model_id, total_users, concurrent_users, cpu_id)
        
        comparison = {
            'gpu': gpu_result,
            'cpu': cpu_result
        }
        
        # Add recommendation
        if gpu_result['feasible'] and cpu_result['feasible']:
            gpu_cost = gpu_result['total_investment']
            cpu_cost = cpu_result['total_investment']
            gpu_throughput = gpu_result['total_throughput']
            cpu_throughput = cpu_result['total_throughput']
            
            # Calculate cost per throughput
            gpu_cost_efficiency = gpu_cost / gpu_throughput if gpu_throughput > 0 else float('inf')
            cpu_cost_efficiency = cpu_cost / cpu_throughput if cpu_throughput > 0 else float('inf')
            
            if gpu_cost_efficiency < cpu_cost_efficiency * 0.7:
                comparison['recommendation'] = 'GPU - Significantly better performance per dollar'
            elif gpu_cost_efficiency < cpu_cost_efficiency:
                comparison['recommendation'] = 'GPU - Better performance per dollar'
            elif cpu_cost_efficiency < gpu_cost_efficiency * 0.9:
                comparison['recommendation'] = 'CPU - More cost effective'
            else:
                comparison['recommendation'] = 'GPU - Higher performance, CPU - Lower initial cost'
        
        return comparison
    
    def calculate_all_gpus(self, model_id, total_users, concurrent_users):
        """
        Calculate requirements for all available GPUs
        
        Returns:
            dict with all GPU calculations sorted by cost efficiency
        """
        results = []
        incompatible = []
        
        for gpu_id, gpu_data in self.gpus.items():
            try:
                result = self.calculate_gpu_requirements(model_id, total_users, concurrent_users, gpu_id)
                if result.get('feasible', False):
                    # Add cost efficiency metric
                    result['cost_efficiency'] = result['total_investment'] / result['total_throughput'] if result['total_throughput'] > 0 else float('inf')
                    results.append(result)
                else:
                    # Track incompatible GPUs
                    incompatible.append({
                        'name': gpu_data['name'],
                        'vram': gpu_data['vram_gb'],
                        'reason': result.get('error', 'Tidak kompatibel')
                    })
            except Exception as e:
                print(f"Error calculating for GPU {gpu_id}: {e}")
                continue
        
        # Sort by cost efficiency (lower is better)
        results.sort(key=lambda x: x['cost_efficiency'])
        
        return {
            'type': 'all_gpus',
            'results': results,
            'best_option': results[0] if results else None,
            'total_options': len(results),
            'incompatible': incompatible,
            'total_gpus': len(self.gpus)
        }
    
    def calculate_all_cpus(self, model_id, total_users, concurrent_users):
        """
        Calculate requirements for all available CPUs
        
        Returns:
            dict with all CPU calculations sorted by cost efficiency
        """
        results = []
        incompatible = []
        
        for cpu_id, cpu_data in self.cpus.items():
            try:
                result = self.calculate_cpu_requirements(model_id, total_users, concurrent_users, cpu_id)
                if result.get('feasible', False):
                    # Add cost efficiency metric
                    result['cost_efficiency'] = result['total_investment'] / result['total_throughput'] if result['total_throughput'] > 0 else float('inf')
                    results.append(result)
                else:
                    # Track incompatible CPUs
                    incompatible.append({
                        'name': cpu_data['name'],
                        'ram': cpu_data['recommended_ram_gb'],
                        'reason': result.get('error', 'Tidak kompatibel')
                    })
            except Exception as e:
                print(f"Error calculating for CPU {cpu_id}: {e}")
                continue
        
        # Sort by cost efficiency (lower is better)
        results.sort(key=lambda x: x['cost_efficiency'])
        
        return {
            'type': 'all_cpus',
            'results': results,
            'best_option': results[0] if results else None,
            'total_options': len(results),
            'incompatible': incompatible,
            'total_cpus': len(self.cpus)
        }

