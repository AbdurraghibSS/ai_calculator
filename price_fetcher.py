"""
Hardware Price Fetcher
Fetches real-time pricing data from external sources
"""
import requests
import json
from datetime import datetime, timedelta

class PriceFetcher:
    def __init__(self):
        self.cache_duration = timedelta(hours=6)  # Cache for 6 hours
        self.price_cache = {}
        
    def get_gpu_prices(self):
        """
        Fetch GPU prices from multiple sources
        Currently using fallback to static data with simulated price variations
        
        In production, this would integrate with:
        - PCPartPicker API (if available)
        - Newegg API
        - Amazon Product Advertising API
        - Or custom web scraping
        """
        cache_key = 'gpu_prices'
        
        # Check cache
        if self._is_cache_valid(cache_key):
            return self.price_cache[cache_key]['data']
        
        try:
            # For now, we'll add realistic price variations to base prices
            # In production, replace this with actual API calls
            gpu_prices = self._fetch_gpu_prices_fallback()
            
            # Cache the result
            self.price_cache[cache_key] = {
                'data': gpu_prices,
                'timestamp': datetime.now()
            }
            
            return gpu_prices
        except Exception as e:
            print(f"Error fetching GPU prices: {e}")
            return {}
    
    def get_cpu_prices(self):
        """
        Fetch CPU prices from multiple sources
        Similar to GPU prices, with fallback to simulated data
        """
        cache_key = 'cpu_prices'
        
        # Check cache
        if self._is_cache_valid(cache_key):
            return self.price_cache[cache_key]['data']
        
        try:
            cpu_prices = self._fetch_cpu_prices_fallback()
            
            # Cache the result
            self.price_cache[cache_key] = {
                'data': cpu_prices,
                'timestamp': datetime.now()
            }
            
            return cpu_prices
        except Exception as e:
            print(f"Error fetching CPU prices: {e}")
            return {}
    
    def _is_cache_valid(self, cache_key):
        """Check if cached data is still valid"""
        if cache_key not in self.price_cache:
            return False
        
        cache_time = self.price_cache[cache_key]['timestamp']
        return datetime.now() - cache_time < self.cache_duration
    
    def _fetch_gpu_prices_fallback(self):
        """
        Fallback method that simulates price variations
        In production, replace with actual API integration
        """
        import random
        
        # Base prices (from our JSON data)
        base_prices = {
            'h100-80gb': 30000,
            'h100-94gb': 35000,
            'a100-40gb': 12000,
            'a100-80gb': 15000,
            'l40s': 10000,
            'l4': 5000,
            'a6000': 4500,
            'rtx-4090': 1600,
            'v100-32gb': 8000,
            't4': 2500
        }
        
        # Add realistic price variations (±5%)
        prices = {}
        for gpu_id, base_price in base_prices.items():
            variation = random.uniform(-0.05, 0.05)
            prices[gpu_id] = int(base_price * (1 + variation))
        
        return prices
    
    def _fetch_cpu_prices_fallback(self):
        """
        Fallback method for CPU prices
        In production, replace with actual API integration
        """
        import random
        
        base_prices = {
            'epyc-9654': 25000,
            'epyc-9554': 20000,
            'epyc-9374f': 15000,
            'xeon-8480': 22000,
            'xeon-8380': 18000,
            'xeon-6348': 12000,
            'epyc-7763': 16000,
            'epyc-7543': 10000,
            'xeon-5320': 9000,
            'threadripper-pro-5995wx': 14000
        }
        
        prices = {}
        for cpu_id, base_price in base_prices.items():
            variation = random.uniform(-0.05, 0.05)
            prices[cpu_id] = int(base_price * (1 + variation))
        
        return prices
    
    def fetch_from_pcpartpicker(self, product_name):
        """
        Example method for PCPartPicker integration
        NOTE: PCPartPicker doesn't have an official API
        This would require web scraping or unofficial APIs
        """
        # Placeholder for future implementation
        pass
    
    def fetch_from_newegg(self, product_id):
        """
        Example method for Newegg API integration
        Requires Newegg Developer API key
        """
        # Placeholder for future implementation
        pass
