// API Configuration - use relative path for Vercel deployment
const API_BASE_URL = '';

// Global state
let models = [];
let gpus = [];
let cpus = [];
let costChart = null;
let performanceChart = null;
let exchangeRate = 15800; // Default fallback rate
let currency = 'IDR'; // Default to Rupiah

// Initialize app
document.addEventListener('DOMContentLoaded', async () => {
    await loadData();
    setupEventListeners();
});

// Load data from API
async function loadData() {
    try {
        // Load exchange rate
        const rateResponse = await fetch(`${API_BASE_URL}/api/exchange-rate`);
        const rateData = await rateResponse.json();
        exchangeRate = rateData.rate;

        // Load models
        const modelsResponse = await fetch(`${API_BASE_URL}/api/models`);
        models = await modelsResponse.json();
        populateModelSelect();

        // Load GPUs
        const gpusResponse = await fetch(`${API_BASE_URL}/api/gpus`);
        gpus = await gpusResponse.json();
        populateGPUSelect();

        // Load CPUs
        const cpusResponse = await fetch(`${API_BASE_URL}/api/cpus`);
        cpus = await cpusResponse.json();
        populateCPUSelect();
    } catch (error) {
        showError('Gagal memuat data. Pastikan API server berjalan di http://localhost:5001');
        console.error('Error loading data:', error);
    }
}

// Populate model select
function populateModelSelect() {
    const select = document.getElementById('modelId');
    select.innerHTML = '<option value="">Pilih model AI...</option>';

    models.forEach(model => {
        const option = document.createElement('option');
        option.value = model.id;
        option.textContent = `${model.name} (${model.parameters})`;
        select.appendChild(option);
    });
}

// Populate GPU select
function populateGPUSelect() {
    const select = document.getElementById('gpuId');
    select.innerHTML = '<option value="">Pilih GPU...</option>';

    // Add "All" option
    const allOption = document.createElement('option');
    allOption.value = 'all';
    allOption.textContent = '🔍 Hitung Semua GPU (Perbandingan)';
    select.appendChild(allOption);

    gpus.forEach(gpu => {
        const option = document.createElement('option');
        option.value = gpu.id;
        option.textContent = `${gpu.name} - ${gpu.vram_gb}GB VRAM - $${gpu.price_usd.toLocaleString()}`;
        select.appendChild(option);
    });
}

// Populate CPU select
function populateCPUSelect() {
    const select = document.getElementById('cpuId');
    select.innerHTML = '<option value="">Pilih CPU...</option>';

    // Add "All" option
    const allOption = document.createElement('option');
    allOption.value = 'all';
    allOption.textContent = '🔍 Hitung Semua CPU (Perbandingan)';
    select.appendChild(allOption);

    cpus.forEach(cpu => {
        const option = document.createElement('option');
        option.value = cpu.id;
        option.textContent = `${cpu.name} - ${cpu.cores} Cores - $${cpu.price_per_server_usd.toLocaleString()}`;
        select.appendChild(option);
    });
}

// Setup event listeners
function setupEventListeners() {
    // Infrastructure type change
    const infraTypeRadios = document.querySelectorAll('input[name="infraType"]');
    infraTypeRadios.forEach(radio => {
        radio.addEventListener('change', handleInfraTypeChange);
    });

    // Model selection change
    document.getElementById('modelId').addEventListener('change', handleModelChange);

    // GPU selection change
    document.getElementById('gpuId').addEventListener('change', handleGPUChange);

    // CPU selection change
    document.getElementById('cpuId').addEventListener('change', handleCPUChange);

    // Form submission
    document.getElementById('calculatorForm').addEventListener('submit', handleCalculate);
}

// Handle infrastructure type change
function handleInfraTypeChange(e) {
    const infraType = e.target.value;
    const gpuGroup = document.getElementById('gpuGroup');
    const cpuGroup = document.getElementById('cpuGroup');
    const gpuSelect = document.getElementById('gpuId');
    const cpuSelect = document.getElementById('cpuId');

    if (infraType === 'gpu') {
        gpuGroup.style.display = 'block';
        cpuGroup.style.display = 'none';
        gpuSelect.required = true;
        cpuSelect.required = false;
    } else if (infraType === 'cpu') {
        gpuGroup.style.display = 'none';
        cpuGroup.style.display = 'block';
        gpuSelect.required = false;
        cpuSelect.required = true;
    } else { // both
        gpuGroup.style.display = 'block';
        cpuGroup.style.display = 'block';
        gpuSelect.required = true;
        cpuSelect.required = true;
    }
}

// Handle model selection change
function handleModelChange(e) {
    const modelId = e.target.value;
    const infoBox = document.getElementById('modelInfo');

    if (!modelId) {
        infoBox.style.display = 'none';
        return;
    }

    const model = models.find(m => m.id === modelId);
    if (model) {
        infoBox.innerHTML = `
            <strong>${model.name}</strong><br>
            📊 Parameters: ${model.parameters} | 💾 Memory: ${model.memory_required_gb}GB<br>
            🎯 Recommended for: ${model.recommended_for}
        `;
        infoBox.style.display = 'block';
    }
}

// Handle GPU selection change
function handleGPUChange(e) {
    const gpuId = e.target.value;
    const infoBox = document.getElementById('gpuInfo');

    if (!gpuId) {
        infoBox.style.display = 'none';
        return;
    }

    const gpu = gpus.find(g => g.id === gpuId);
    if (gpu) {
        infoBox.innerHTML = `
            <strong>${gpu.name}</strong><br>
            💾 VRAM: ${gpu.vram_gb}GB | ⚡ ${gpu.fp16_tflops} TFLOPS (FP16)<br>
            💰 Price: $${gpu.price_usd.toLocaleString()} | 🎯 ${gpu.recommended_for}
        `;
        infoBox.style.display = 'block';
    }
}

// Handle CPU selection change
function handleCPUChange(e) {
    const cpuId = e.target.value;
    const infoBox = document.getElementById('cpuInfo');

    if (!cpuId) {
        infoBox.style.display = 'none';
        return;
    }

    const cpu = cpus.find(c => c.id === cpuId);
    if (cpu) {
        infoBox.innerHTML = `
            <strong>${cpu.name}</strong><br>
            🔧 ${cpu.cores} Cores / ${cpu.threads} Threads | 💾 Max RAM: ${cpu.max_ram_gb}GB<br>
            💰 Price per Server: $${cpu.price_per_server_usd.toLocaleString()} | 🎯 ${cpu.recommended_for}
        `;
        infoBox.style.display = 'block';
    }
}

// Handle calculate button
async function handleCalculate(e) {
    e.preventDefault();

    // Hide previous results and errors
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('errorMessage').style.display = 'none';

    // Show loading
    document.getElementById('loadingIndicator').style.display = 'block';

    // Get form values
    const infraType = document.querySelector('input[name="infraType"]:checked').value;
    const modelId = document.getElementById('modelId').value;
    const totalUsers = parseInt(document.getElementById('totalUsers').value);
    const concurrentUsers = parseInt(document.getElementById('concurrentUsers').value);
    const gpuId = document.getElementById('gpuId').value;
    const cpuId = document.getElementById('cpuId').value;

    // Prepare request
    const requestData = {
        infrastructure_type: infraType,
        model_id: modelId,
        total_users: totalUsers,
        concurrent_users: concurrentUsers
    };

    if (infraType === 'gpu' || infraType === 'both') {
        requestData.gpu_id = gpuId;
    }
    if (infraType === 'cpu' || infraType === 'both') {
        requestData.cpu_id = cpuId;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/calculate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Calculation failed');
        }

        // Display results
        displayResults(result, infraType);
    } catch (error) {
        showError(`Error: ${error.message}`);
    } finally {
        document.getElementById('loadingIndicator').style.display = 'none';
    }
}

// Display results
function displayResults(result, infraType) {
    // Cache for currency toggle
    lastResult = result;
    lastInfraType = infraType;

    const resultsSection = document.getElementById('resultsSection');
    const gpuResults = document.getElementById('gpuResults');
    const cpuResults = document.getElementById('cpuResults');
    const comparisonResults = document.getElementById('comparisonResults');

    // Hide all result sections first
    gpuResults.style.display = 'none';
    cpuResults.style.display = 'none';
    comparisonResults.style.display = 'none';

    // Check if it's an 'all' type result
    if (result.type === 'all_gpus') {
        displayAllGPUResults(result);
        comparisonResults.style.display = 'block';
    } else if (result.type === 'all_cpus') {
        displayAllCPUResults(result);
        comparisonResults.style.display = 'block';
    } else if (infraType === 'gpu') {
        displayGPUResults(result);
        gpuResults.style.display = 'block';
    } else if (infraType === 'cpu') {
        displayCPUResults(result);
        cpuResults.style.display = 'block';
    } else { // both
        displayGPUResults(result.gpu);
        displayCPUResults(result.cpu);
        displayComparison(result);
        gpuResults.style.display = 'block';
        cpuResults.style.display = 'block';
        comparisonResults.style.display = 'block';
    }

    resultsSection.style.display = 'block';

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Display GPU results
function displayGPUResults(result) {
    if (!result.feasible) {
        showError(result.error);
        return;
    }

    document.getElementById('gpuCount').textContent = result.required_units;
    document.getElementById('gpuCostPerUnit').textContent = formatCurrency(result.cost_per_unit);
    document.getElementById('gpuTotalCost').textContent = formatCurrency(result.total_investment);
    document.getElementById('gpuUtilization').textContent = `${result.utilization_percent}%`;

    // Display details
    const detailsHtml = `
        <div class="info-box">
            <strong>ℹ️ Penjelasan Metrik:</strong>
            <ul>
                <li><strong>Utilisasi ${result.utilization_percent}%</strong> - Hardware bekerja pada ${result.utilization_percent}% kapasitas. Sisanya (${(100 - result.utilization_percent).toFixed(1)}%) adalah buffer untuk traffic spike dan failover.</li>
                <li><strong>Throughput</strong> - Jumlah request yang dapat diproses per detik. Semakin tinggi semakin baik.</li>
                <li><strong>Instance per GPU</strong> - Jumlah model AI yang bisa berjalan paralel dalam 1 GPU berdasarkan VRAM yang tersedia.</li>
            </ul>
        </div>
        <div class="detail-grid">
            <div class="detail-item">
                <div class="detail-label">Model</div>
                <div class="detail-value">${result.model}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">GPU</div>
                <div class="detail-value">${result.hardware}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Instance per GPU</div>
                <div class="detail-value">${result.instances_per_unit}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Total Instance</div>
                <div class="detail-value">${result.total_instances}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Throughput per GPU</div>
                <div class="detail-value">${result.throughput_per_unit} req/s</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Total Throughput</div>
                <div class="detail-value">${result.total_throughput} req/s</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Model Memory</div>
                <div class="detail-value">${result.details.model_memory_gb}GB</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">GPU VRAM</div>
                <div class="detail-value">${result.details.gpu_memory_gb}GB</div>
            </div>
        </div>
    `;
    document.getElementById('gpuDetails').innerHTML = detailsHtml;
}

// Display CPU results
function displayCPUResults(result) {
    if (!result.feasible) {
        showError(result.error);
        return;
    }

    document.getElementById('cpuCount').textContent = result.required_units;
    document.getElementById('cpuCostPerUnit').textContent = formatCurrency(result.cost_per_unit);
    document.getElementById('cpuTotalCost').textContent = formatCurrency(result.total_investment);
    document.getElementById('cpuUtilization').textContent = `${result.utilization_percent}%`;

    // Display details
    const detailsHtml = `
        <div class="info-box">
            <strong>ℹ️ Penjelasan Metrik:</strong>
            <ul>
                <li><strong>Utilisasi ${result.utilization_percent}%</strong> - Server bekerja pada ${result.utilization_percent}% kapasitas. Sisanya (${(100 - result.utilization_percent).toFixed(1)}%) adalah buffer untuk traffic spike dan failover.</li>
                <li><strong>Throughput</strong> - Jumlah request yang dapat diproses per detik. CPU umumnya lebih lambat dari GPU untuk AI inference.</li>
                <li><strong>Instance per Server</strong> - Jumlah model AI yang bisa berjalan paralel dalam 1 server berdasarkan RAM yang tersedia.</li>
            </ul>
        </div>
        <div class="detail-grid">
            <div class="detail-item">
                <div class="detail-label">Model</div>
                <div class="detail-value">${result.model}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">CPU Server</div>
                <div class="detail-value">${result.hardware}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Instance per Server</div>
                <div class="detail-value">${result.instances_per_unit}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Total Instance</div>
                <div class="detail-value">${result.total_instances}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Throughput per Server</div>
                <div class="detail-value">${result.throughput_per_unit} req/s</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Total Throughput</div>
                <div class="detail-value">${result.total_throughput} req/s</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">CPU Cores</div>
                <div class="detail-value">${result.details.cores} / ${result.details.threads} threads</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Server RAM</div>
                <div class="detail-value">${result.details.server_memory_gb}GB</div>
            </div>
        </div>
    `;
    document.getElementById('cpuDetails').innerHTML = detailsHtml;
}

// Display comparison
function displayComparison(result) {
    // Show recommendation
    if (result.recommendation) {
        document.getElementById('recommendation').innerHTML = `
            <strong>💡 Rekomendasi:</strong> ${result.recommendation}
        `;
    }

    // Create cost comparison chart
    createCostChart(result.gpu, result.cpu);

    // Create performance comparison chart
    createPerformanceChart(result.gpu, result.cpu);
}

// Create cost comparison chart
function createCostChart(gpuResult, cpuResult) {
    const ctx = document.getElementById('costChart');

    if (costChart) {
        costChart.destroy();
    }

    costChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['GPU', 'CPU'],
            datasets: [{
                label: 'Total Investment (USD)',
                data: [gpuResult.total_investment, cpuResult.total_investment],
                backgroundColor: [
                    'rgba(99, 102, 241, 0.6)',
                    'rgba(139, 92, 246, 0.6)'
                ],
                borderColor: [
                    'rgba(99, 102, 241, 1)',
                    'rgba(139, 92, 246, 1)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Perbandingan Biaya Investasi',
                    color: '#ffffff',
                    font: { size: 16, weight: 'bold' }
                },
                legend: {
                    labels: { color: '#ffffff' }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#a0aec0',
                        callback: function (value) {
                            return '$' + value.toLocaleString();
                        }
                    },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                x: {
                    ticks: { color: '#a0aec0' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                }
            }
        }
    });
}

// Create performance comparison chart
function createPerformanceChart(gpuResult, cpuResult) {
    const ctx = document.getElementById('performanceChart');

    if (performanceChart) {
        performanceChart.destroy();
    }

    performanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['GPU', 'CPU'],
            datasets: [{
                label: 'Total Throughput (req/s)',
                data: [gpuResult.total_throughput, cpuResult.total_throughput],
                backgroundColor: [
                    'rgba(16, 185, 129, 0.6)',
                    'rgba(245, 158, 11, 0.6)'
                ],
                borderColor: [
                    'rgba(16, 185, 129, 1)',
                    'rgba(245, 158, 11, 1)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Perbandingan Performa',
                    color: '#ffffff',
                    font: { size: 16, weight: 'bold' }
                },
                legend: {
                    labels: { color: '#ffffff' }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#a0aec0',
                        callback: function (value) {
                            return value.toFixed(2) + ' req/s';
                        }
                    },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                x: {
                    ticks: { color: '#a0aec0' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                }
            }
        }
    });
}

// Utility: Format currency
function formatCurrency(amount) {
    if (currency === 'IDR') {
        const idrAmount = amount * exchangeRate;

        // Use compact format for large numbers
        if (idrAmount >= 1000000000) {
            return 'Rp ' + (idrAmount / 1000000000).toFixed(2) + ' M';
        } else if (idrAmount >= 1000000) {
            return 'Rp ' + (idrAmount / 1000000).toFixed(1) + ' Jt';
        } else {
            return 'Rp ' + idrAmount.toLocaleString('id-ID', { maximumFractionDigits: 0 });
        }
    }
    return '$' + amount.toLocaleString('en-US');
}

// Store last results for currency toggle
let lastResult = null;
let lastInfraType = null;

// Toggle currency
function toggleCurrency() {
    currency = currency === 'USD' ? 'IDR' : 'USD';

    // Update button label
    const label = document.getElementById('currencyLabel');
    if (currency === 'IDR') {
        label.textContent = '💱 Tampilkan dalam Dollar';
    } else {
        label.textContent = '💱 Tampilkan dalam Rupiah';
    }

    // Re-render results if they exist
    if (lastResult && lastInfraType) {
        displayResults(lastResult, lastInfraType);
    }
}

// Display all GPU results
function displayAllGPUResults(data) {
    const container = document.getElementById('comparisonResults');

    let html = '<div class="glass-card">';
    html += '<h2>🔍 Perbandingan Semua GPU</h2>';
    html += `<p class="info-text">Menampilkan ${data.total_options} dari ${data.total_gpus} GPU yang kompatibel dengan model ini, diurutkan berdasarkan efisiensi biaya</p>`;

    // Show incompatible warning if any
    if (data.incompatible && data.incompatible.length > 0) {
        html += '<div class="warning-box">';
        html += `<strong>⚠️ ${data.incompatible.length} GPU tidak kompatibel:</strong> `;
        html += '<ul>';
        data.incompatible.forEach(gpu => {
            html += `<li>${gpu.name} (${gpu.vram}GB VRAM) - ${gpu.reason}</li>`;
        });
        html += '</ul>';
        html += '</div>';
    }

    if (data.best_option) {
        const best = data.best_option;

        // Recommendation banner
        html += `<div class="recommendation-banner">`;
        html += `<div class="recommendation-icon">💡</div>`;
        html += `<div class="recommendation-content">`;
        html += `<div class="recommendation-title">Rekomendasi Terbaik: ${best.hardware}</div>`;
        html += `<div class="recommendation-subtitle">Efisiensi biaya terbaik dengan performa optimal</div>`;
        html += '</div></div>';

        // Statistics cards
        html += '<div class="stats-grid">';

        html += '<div class="stat-card stat-primary">';
        html += '<div class="stat-icon">🎮</div>';
        html += '<div class="stat-content">';
        html += '<div class="stat-label">Jumlah GPU Dibutuhkan</div>';
        html += `<div class="stat-value">${best.required_units}</div>`;
        html += '</div></div>';

        html += '<div class="stat-card stat-success">';
        html += '<div class="stat-icon">💰</div>';
        html += '<div class="stat-content">';
        html += '<div class="stat-label">Biaya per GPU</div>';
        html += `<div class="stat-value">${formatCurrency(best.cost_per_unit)}</div>`;
        html += '</div></div>';

        html += '<div class="stat-card stat-info">';
        html += '<div class="stat-icon">💵</div>';
        html += '<div class="stat-content">';
        html += '<div class="stat-label">Total Investasi</div>';
        html += `<div class="stat-value">${formatCurrency(best.total_investment)}</div>`;
        html += '</div></div>';

        html += '<div class="stat-card stat-warning">';
        html += '<div class="stat-icon">📊</div>';
        html += '<div class="stat-content">';
        html += '<div class="stat-label">Utilisasi</div>';
        html += `<div class="stat-value">${best.utilization_percent}%</div>`;
        html += '</div></div>';

        html += '</div>'; // End stats-grid

        // Technical details
        html += '<div class="detail-section">';
        html += '<h3>Detail Teknis</h3>';
        html += '<div class="detail-grid">';

        html += `<div class="detail-item"><div class="detail-label">Model</div><div class="detail-value">${best.model}</div></div>`;
        html += `<div class="detail-item"><div class="detail-label">GPU</div><div class="detail-value">${best.hardware}</div></div>`;
        html += `<div class="detail-item"><div class="detail-label">Instance per GPU</div><div class="detail-value">${best.instances_per_unit}</div></div>`;
        html += `<div class="detail-item"><div class="detail-label">Total Instance</div><div class="detail-value">${best.total_instances}</div></div>`;
        html += `<div class="detail-item"><div class="detail-label">Throughput per GPU</div><div class="detail-value">${best.throughput_per_unit} req/s</div></div>`;
        html += `<div class="detail-item"><div class="detail-label">Total Throughput</div><div class="detail-value">${best.total_throughput} req/s</div></div>`;
        html += `<div class="detail-item"><div class="detail-label">Model Memory</div><div class="detail-value">${best.details.model_memory_gb}GB</div></div>`;
        html += `<div class="detail-item"><div class="detail-label">GPU VRAM</div><div class="detail-value">${best.details.gpu_memory_gb}GB</div></div>`;

        html += '</div></div>'; // End detail-section
    }

    // Comparison table
    html += '<div class="detail-section">';
    html += '<h3>🔍 Perbandingan Semua GPU</h3>';

    // Add explanation box
    html += '<div class="info-box">';
    html += '<strong>ℹ️ Cara Membaca Tabel:</strong>';
    html += '<ul>';
    html += '<li><strong>Rank</strong> - Peringkat berdasarkan efisiensi biaya (🥇 = terbaik)</li>';
    html += '<li><strong>Utilisasi</strong> - Persentase kapasitas yang digunakan. Ideal: 70-85%. Sisanya adalah buffer untuk traffic spike.</li>';
    html += '<li><strong>Efisiensi</strong> - Biaya per request/detik. Semakin rendah semakin baik (lebih hemat).</li>';
    html += '<li><strong>Instance</strong> - Jumlah model AI yang bisa berjalan paralel berdasarkan VRAM tersedia.</li>';
    html += '</ul>';
    html += '</div>';

    html += '<div class="comparison-table"><table><thead><tr>';
    html += '<th>Rank</th><th>GPU</th><th>Jumlah</th><th>Instance</th><th>Biaya per Unit</th><th>Total Investasi</th><th>Throughput</th><th>Utilisasi</th><th>Efisiensi</th>';
    html += '</tr></thead><tbody>';

    data.results.forEach((result, index) => {
        const rowClass = index === 0 ? 'best-option' : '';
        const rank = index + 1;
        const rankBadge = rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : rank;

        html += `<tr class="${rowClass}">`;
        html += `<td><strong>${rankBadge}</strong></td>`;
        html += `<td><strong>${result.hardware}</strong><br><small>${result.details.gpu_memory_gb}GB VRAM</small></td>`;
        html += `<td>${result.required_units}</td>`;
        html += `<td>${result.total_instances}<br><small>(${result.instances_per_unit}/GPU)</small></td>`;
        html += `<td>${formatCurrency(result.cost_per_unit)}</td>`;
        html += `<td><strong>${formatCurrency(result.total_investment)}</strong></td>`;
        html += `<td>${result.total_throughput.toFixed(2)} req/s<br><small>(${result.throughput_per_unit.toFixed(2)}/GPU)</small></td>`;
        html += `<td><div class="utilization-bar"><div class="utilization-fill" style="width: ${result.utilization_percent}%"></div><span>${result.utilization_percent}%</span></div></td>`;
        html += `<td>${formatCurrency(result.cost_efficiency)}/req/s</td>`;
        html += '</tr>';
    });

    html += '</tbody></table></div></div>'; // End comparison table
    html += '</div>'; // End glass-card

    container.innerHTML = html;
}

// Display all CPU results
function displayAllCPUResults(data) {
    const container = document.getElementById('comparisonResults');

    let html = '<div class="glass-card">';
    html += '<h2>🔍 Perbandingan Semua CPU</h2>';
    html += `<p class="info-text">Menampilkan ${data.total_options} dari ${data.total_cpus} CPU yang kompatibel dengan model ini, diurutkan berdasarkan efisiensi biaya</p>`;

    // Show incompatible warning if any
    if (data.incompatible && data.incompatible.length > 0) {
        html += '<div class="warning-box">';
        html += `<strong>⚠️ ${data.incompatible.length} CPU tidak kompatibel:</strong> `;
        html += '<ul>';
        data.incompatible.forEach(cpu => {
            html += `<li>${cpu.name} (${cpu.ram}GB RAM) - ${cpu.reason}</li>`;
        });
        html += '</ul>';
        html += '</div>';
    }

    if (data.best_option) {
        const best = data.best_option;

        // Recommendation banner
        html += `<div class="recommendation-banner">`;
        html += `<div class="recommendation-icon">💡</div>`;
        html += `<div class="recommendation-content">`;
        html += `<div class="recommendation-title">Rekomendasi Terbaik: ${best.hardware}</div>`;
        html += `<div class="recommendation-subtitle">Efisiensi biaya terbaik dengan performa optimal</div>`;
        html += `</div></div>`;

        // Statistics cards
        html += '<div class="stats-grid">';

        html += '<div class="stat-card stat-primary">';
        html += '<div class="stat-icon">🖥️</div>';
        html += '<div class="stat-content">';
        html += '<div class="stat-label">Jumlah Server Dibutuhkan</div>';
        html += `<div class="stat-value">${best.required_units}</div>`;
        html += '</div></div>';

        html += '<div class="stat-card stat-success">';
        html += '<div class="stat-icon">💰</div>';
        html += '<div class="stat-content">';
        html += '<div class="stat-label">Biaya per Server</div>';
        html += `<div class="stat-value">${formatCurrency(best.cost_per_unit)}</div>`;
        html += '</div></div>';

        html += '<div class="stat-card stat-info">';
        html += '<div class="stat-icon">💵</div>';
        html += '<div class="stat-content">';
        html += '<div class="stat-label">Total Investasi</div>';
        html += `<div class="stat-value">${formatCurrency(best.total_investment)}</div>`;
        html += '</div></div>';

        html += '<div class="stat-card stat-warning">';
        html += '<div class="stat-icon">📊</div>';
        html += '<div class="stat-content">';
        html += '<div class="stat-label">Utilisasi</div>';
        html += `<div class="stat-value">${best.utilization_percent}%</div>`;
        html += '</div></div>';

        html += '</div>'; // End stats-grid

        // Technical details
        html += '<div class="detail-section">';
        html += '<h3>Detail Teknis</h3>';
        html += '<div class="detail-grid">';

        html += `<div class="detail-item"><div class="detail-label">Model</div><div class="detail-value">${best.model}</div></div>`;
        html += `<div class="detail-item"><div class="detail-label">CPU Server</div><div class="detail-value">${best.hardware}</div></div>`;
        html += `<div class="detail-item"><div class="detail-label">Instance per Server</div><div class="detail-value">${best.instances_per_unit}</div></div>`;
        html += `<div class="detail-item"><div class="detail-label">Total Instance</div><div class="detail-value">${best.total_instances}</div></div>`;
        html += `<div class="detail-item"><div class="detail-label">Throughput per Server</div><div class="detail-value">${best.throughput_per_unit} req/s</div></div>`;
        html += `<div class="detail-item"><div class="detail-label">Total Throughput</div><div class="detail-value">${best.total_throughput} req/s</div></div>`;
        html += `<div class="detail-item"><div class="detail-label">CPU Cores</div><div class="detail-value">${best.details.cores} / ${best.details.threads} threads</div></div>`;
        html += `<div class="detail-item"><div class="detail-label">Server RAM</div><div class="detail-value">${best.details.server_memory_gb}GB</div></div>`;

        html += '</div></div>'; // End detail-section
    }

    // Comparison table
    html += '<div class="detail-section">';
    html += '<h3>🔍 Perbandingan Semua CPU</h3>';

    // Add explanation box
    html += '<div class="info-box">';
    html += '<strong>ℹ️ Cara Membaca Tabel:</strong>';
    html += '<ul>';
    html += '<li><strong>Rank</strong> - Peringkat berdasarkan efisiensi biaya (🥇 = terbaik)</li>';
    html += '<li><strong>Utilisasi</strong> - Persentase kapasitas yang digunakan. Ideal: 70-85%. Sisanya adalah buffer untuk traffic spike.</li>';
    html += '<li><strong>Efisiensi</strong> - Biaya per request/detik. Semakin rendah semakin baik (lebih hemat).</li>';
    html += '<li><strong>Instance</strong> - Jumlah model AI yang bisa berjalan paralel berdasarkan RAM tersedia.</li>';
    html += '</ul>';
    html += '</div>';

    html += '<div class="comparison-table"><table><thead><tr>';
    html += '<th>Rank</th><th>CPU Server</th><th>Jumlah</th><th>Instance</th><th>Biaya per Server</th><th>Total Investasi</th><th>Throughput</th><th>Utilisasi</th><th>Efisiensi</th>';
    html += '</tr></thead><tbody>';

    data.results.forEach((result, index) => {
        const rowClass = index === 0 ? 'best-option' : '';
        const rank = index + 1;
        const rankBadge = rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : rank;

        html += `<tr class="${rowClass}">`;
        html += `<td><strong>${rankBadge}</strong></td>`;
        html += `<td><strong>${result.hardware}</strong><br><small>${result.details.cores}C/${result.details.threads}T</small></td>`;
        html += `<td>${result.required_units}</td>`;
        html += `<td>${result.total_instances}<br><small>(${result.instances_per_unit}/server)</small></td>`;
        html += `<td>${formatCurrency(result.cost_per_unit)}</td>`;
        html += `<td><strong>${formatCurrency(result.total_investment)}</strong></td>`;
        html += `<td>${result.total_throughput.toFixed(2)} req/s<br><small>(${result.throughput_per_unit.toFixed(2)}/server)</small></td>`;
        html += `<td><div class="utilization-bar"><div class="utilization-fill" style="width: ${result.utilization_percent}%"></div><span>${result.utilization_percent}%</span></div></td>`;
        html += `<td>${formatCurrency(result.cost_efficiency)}/req/s</td>`;
        html += '</tr>';
    });

    html += '</tbody></table></div></div>'; // End comparison table
    html += '</div>'; // End glass-card

    container.innerHTML = html;
}

// Show error message
function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    errorDiv.scrollIntoView({ behavior: 'smooth' });
}
