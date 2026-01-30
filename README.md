# Kalkulator Pengadaan Infrastruktur AI

Aplikasi web untuk menghitung kebutuhan infrastruktur GPU dan CPU untuk deployment AI berdasarkan model yang dipilih, jumlah user, dan concurrent user.

## Fitur

- ✅ **Perhitungan GPU**: Hitung kebutuhan GPU NVIDIA (H100, A100, L40S, dll)
- ✅ **Perhitungan CPU**: Hitung kebutuhan CPU server (Intel Xeon, AMD EPYC)
- ✅ **Perbandingan**: Bandingkan biaya dan performa GPU vs CPU
- ✅ **Database Model AI**: 13+ model AI populer (LLaMA, Mistral, Gemma, dll)
- ✅ **Estimasi Biaya**: Perhitungan biaya investasi per unit dan total
- ✅ **Visualisasi**: Chart perbandingan biaya dan performa
- ✅ **UI Premium**: Dark theme dengan glassmorphism dan animasi smooth

## Screenshot

![Kalkulator AI](screenshot.png)

## Teknologi

- **Backend**: Python Flask + Flask-CORS
- **Frontend**: HTML5, CSS3 (Vanilla), JavaScript (ES6+)
- **Visualisasi**: Chart.js
- **Design**: Glassmorphism, Dark Theme, Responsive

## Instalasi

### 1. Clone atau Download Project

```bash
cd /home/abdurraghib/Documents/KERJA/Kemenkomdigi/PDSI/as_an_ai_enthusiast/Kebutuhan_AI
```

### 2. Install Dependencies Python

```bash
pip install -r requirements.txt
```

### 3. Jalankan API Server

```bash
python api.py
```

Server akan berjalan di `http://localhost:5000`

### 4. Buka Aplikasi Web

Buka file `index.html` di browser, atau gunakan live server:

```bash
# Jika menggunakan Python
python -m http.server 8000
```

Kemudian buka `http://localhost:8000` di browser.

## Cara Penggunaan

1. **Pilih Tipe Infrastruktur**: GPU, CPU, atau Bandingkan keduanya
2. **Pilih Model AI**: Pilih dari 13+ model AI yang tersedia
3. **Masukkan Jumlah User**: Total user dan concurrent user
4. **Pilih Hardware**: Pilih GPU atau CPU yang diinginkan
5. **Klik "Hitung Kebutuhan"**: Lihat hasil perhitungan

## Struktur Project

```
Kebutuhan_AI/
├── api.py                 # Flask REST API
├── calculator.py          # Calculation engine
├── index.html            # Main HTML
├── styles.css            # Premium dark theme CSS
├── app.js                # Frontend JavaScript
├── requirements.txt      # Python dependencies
├── data/
│   ├── models.json       # AI models database
│   ├── gpus.json         # GPU specifications
│   └── cpus.json         # CPU specifications
└── README.md             # Documentation
```

## API Endpoints

### GET `/api/models`
Mendapatkan daftar semua model AI yang tersedia.

**Response:**
```json
[
  {
    "id": "llama-2-7b",
    "name": "LLaMA 2 7B",
    "parameters": "7B",
    "memory_required_gb": 14,
    "tokens_per_second_gpu": 150,
    "tokens_per_second_cpu": 8
  }
]
```

### GET `/api/gpus`
Mendapatkan daftar semua GPU yang tersedia.

**Response:**
```json
[
  {
    "id": "h100-80gb",
    "name": "NVIDIA H100 80GB",
    "vram_gb": 80,
    "price_usd": 30000,
    "tokens_per_second": 200
  }
]
```

### GET `/api/cpus`
Mendapatkan daftar semua CPU server yang tersedia.

**Response:**
```json
[
  {
    "id": "epyc-9654",
    "name": "AMD EPYC 9654 (96-Core)",
    "cores": 96,
    "price_per_server_usd": 25000,
    "tokens_per_second": 12
  }
]
```

### POST `/api/calculate`
Menghitung kebutuhan infrastruktur.

**Request Body:**
```json
{
  "infrastructure_type": "gpu",
  "model_id": "llama-2-7b",
  "total_users": 10000,
  "concurrent_users": 1000,
  "gpu_id": "h100-80gb"
}
```

**Response:**
```json
{
  "feasible": true,
  "infrastructure_type": "GPU",
  "required_units": 3,
  "cost_per_unit": 30000,
  "total_investment": 90000,
  "utilization_percent": 85.5,
  "throughput_per_unit": 12.5,
  "total_throughput": 37.5
}
```

## Metodologi Perhitungan

### GPU
```
Required GPUs = (Concurrent Users × Avg Tokens/Request × Safety Factor) / (GPU Throughput × Utilization Rate)
```

- Safety Factor: 1.3 (30% margin)
- Avg Tokens/Request: 100 tokens
- Request Rate: 1 request per 3 seconds per user

### CPU
```
Required CPU Servers = (Concurrent Users × Avg Tokens/Request × Safety Factor) / (CPU Throughput × Utilization Rate)
```

- Safety Factor: 1.4 (40% margin, higher due to lower performance)
- Memory overhead: 30% reserved for OS

## Customization

### Menambah Model AI Baru

Edit `data/models.json`:

```json
{
  "id": "new-model",
  "name": "New Model Name",
  "parameters": "13B",
  "memory_required_gb": 26,
  "context_length": 4096,
  "tokens_per_second_gpu": 100,
  "tokens_per_second_cpu": 5,
  "recommended_for": "Use case description"
}
```

### Menambah GPU Baru

Edit `data/gpus.json`:

```json
{
  "id": "new-gpu",
  "name": "GPU Name",
  "vram_gb": 80,
  "price_usd": 25000,
  "tokens_per_second": 180,
  "recommended_for": "Use case"
}
```

### Menambah CPU Baru

Edit `data/cpus.json`:

```json
{
  "id": "new-cpu",
  "name": "CPU Name",
  "cores": 64,
  "threads": 128,
  "recommended_ram_gb": 512,
  "price_per_server_usd": 20000,
  "tokens_per_second": 10,
  "recommended_for": "Use case"
}
```

## Troubleshooting

### API Server Tidak Berjalan

Pastikan Flask terinstall:
```bash
pip install Flask Flask-CORS
```

### CORS Error

Pastikan API server berjalan di `http://localhost:5000` dan Flask-CORS terinstall.

### Data Tidak Muncul

1. Cek console browser (F12) untuk error
2. Pastikan API server berjalan
3. Cek file JSON di folder `data/` valid

## License

© 2026 Kemenkomdigi - Internal Use

## Contact

Untuk pertanyaan atau support, hubungi tim PDSI Kemenkomdigi.
