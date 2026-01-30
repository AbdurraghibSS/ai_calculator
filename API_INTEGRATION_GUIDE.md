# Panduan Integrasi API Eksternal untuk Harga Hardware

## Saat Ini: Simulasi dengan Variasi Harga

Aplikasi saat ini menggunakan **price_fetcher.py** yang mensimulasikan variasi harga ±5% dari harga base. Ini memberikan kesan harga yang "berubah" setiap 6 jam.

## Cara Mengintegrasikan API Real

### 1. PCPartPicker (Scraping)

PCPartPicker tidak memiliki API resmi, perlu web scraping:

```python
def fetch_from_pcpartpicker(self, product_name):
    from bs4 import BeautifulSoup
    
    url = f"https://pcpartpicker.com/search/?q={product_name}"
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Parse price dari HTML
    price_element = soup.find('td', class_='td__price')
    if price_element:
        price_text = price_element.text.strip()
        price = float(price_text.replace('$', '').replace(',', ''))
        return price
    return None
```

### 2. Newegg API (Memerlukan API Key)

Daftar di Newegg Developer Portal:

```python
def fetch_from_newegg(self, product_id):
    api_key = 'YOUR_NEWEGG_API_KEY'
    url = f"https://api.newegg.com/marketplace/productservice/product/price"
    
    headers = {
        'Authorization': api_key,
        'SecretKey': 'YOUR_SECRET_KEY',
        'Content-Type': 'application/json'
    }
    
    data = {'SellerPartNumber': [product_id]}
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        return result['ResponseBody']['PriceInfo'][0]['SellingPrice']
    return None
```

### 3. Amazon Product Advertising API

Memerlukan Amazon Associates account:

```python
def fetch_from_amazon(self, asin):
    from amazon_paapi import AmazonAPI
    
    amazon = AmazonAPI(
        key='YOUR_ACCESS_KEY',
        secret='YOUR_SECRET_KEY',
        tag='YOUR_ASSOCIATE_TAG',
        country='US'
    )
    
    product = amazon.get_items(asin)
    if product and product[0].offers:
        return product[0].offers.listings[0].price.amount
    return None
```

### 4. CamelCamelCamel API (Amazon Price Tracking)

```python
def fetch_from_camelcamelcamel(self, asin):
    api_key = 'YOUR_CAMELCAMELCAMEL_KEY'
    url = f"https://api.camelcamelcamel.com/products/{asin}"
    
    params = {'key': api_key}
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        return data['products'][0]['amazon']['current']
    return None
```

## Implementasi Hybrid (Recommended)

Edit `price_fetcher.py`:

```python
def _fetch_gpu_prices_fallback(self):
    """Fetch from multiple sources with fallback"""
    prices = {}
    
    # Mapping GPU IDs to product identifiers
    gpu_mappings = {
        'h100-80gb': {
            'name': 'NVIDIA H100 80GB',
            'newegg_id': 'N82E16814932516',
            'amazon_asin': 'B0XXXXXXXX'
        },
        # ... more mappings
    }
    
    for gpu_id, mapping in gpu_mappings.items():
        try:
            # Try Newegg first
            price = self.fetch_from_newegg(mapping['newegg_id'])
            
            # Fallback to Amazon
            if not price:
                price = self.fetch_from_amazon(mapping['amazon_asin'])
            
            # Fallback to scraping
            if not price:
                price = self.fetch_from_pcpartpicker(mapping['name'])
            
            # Use base price if all fail
            if price:
                prices[gpu_id] = int(price)
        except Exception as e:
            print(f"Error fetching {gpu_id}: {e}")
            continue
    
    return prices
```

## Dependencies Tambahan

Tambahkan ke `requirements.txt`:

```
beautifulsoup4==4.12.0
lxml==4.9.0
amazon-paapi==5.1.0
```

## Rate Limiting & Caching

Penting untuk menghindari banned:

```python
import time
from functools import lru_cache

class PriceFetcher:
    def __init__(self):
        self.last_request_time = {}
        self.min_request_interval = 2  # seconds
    
    def _rate_limit(self, source):
        """Ensure minimum interval between requests"""
        if source in self.last_request_time:
            elapsed = time.time() - self.last_request_time[source]
            if elapsed < self.min_request_interval:
                time.sleep(self.min_request_interval - elapsed)
        
        self.last_request_time[source] = time.time()
```

## Testing

Test dengan single product terlebih dahulu:

```python
# Test script
fetcher = PriceFetcher()
price = fetcher.fetch_from_newegg('N82E16814932516')
print(f"H100 Price: ${price}")
```

## Catatan Penting

1. **API Keys**: Simpan di environment variables, jangan hardcode
2. **Rate Limits**: Respect API rate limits (biasanya 1-5 req/sec)
3. **Caching**: Cache minimal 6 jam untuk mengurangi API calls
4. **Fallback**: Selalu sediakan fallback ke harga base
5. **Error Handling**: Handle network errors gracefully
6. **Legal**: Pastikan comply dengan Terms of Service setiap API/website
