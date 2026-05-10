// ─── THREE.JS 3D BACKGROUND SETUP ──────────────────────────────────────────
const canvas = document.getElementById('webgl-canvas');
const scene = new THREE.Scene();

// Camera
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.z = 30;
camera.position.y = 10;
camera.lookAt(0, 0, 0);

// Renderer
const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

// Particle System
const particleCount = 4000;
const geometry = new THREE.BufferGeometry();
const positions = new Float32Array(particleCount * 3);
const colors = new Float32Array(particleCount * 3);

// Default color (Blueish)
const baseColor = new THREE.Color(0x4f46e5); 

for (let i = 0; i < particleCount; i++) {
    // Spread particles in a wide cylinder/plane
    const x = (Math.random() - 0.5) * 100;
    const y = (Math.random() - 0.5) * 40 - 10;
    const z = (Math.random() - 0.5) * 100;

    positions[i * 3] = x;
    positions[i * 3 + 1] = y;
    positions[i * 3 + 2] = z;

    colors[i * 3] = baseColor.r;
    colors[i * 3 + 1] = baseColor.g;
    colors[i * 3 + 2] = baseColor.b;
}

geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

// Add texture to particles for glow
const canvasTexture = document.createElement('canvas');
canvasTexture.width = 16;
canvasTexture.height = 16;
const ctxTex = canvasTexture.getContext('2d');
const gradient = ctxTex.createRadialGradient(8, 8, 0, 8, 8, 8);
gradient.addColorStop(0, 'rgba(255,255,255,1)');
gradient.addColorStop(1, 'rgba(255,255,255,0)');
ctxTex.fillStyle = gradient;
ctxTex.fillRect(0, 0, 16, 16);
const texture = new THREE.CanvasTexture(canvasTexture);

const material = new THREE.PointsMaterial({
    size: 0.5,
    vertexColors: true,
    map: texture,
    transparent: true,
    opacity: 0.8,
    blending: THREE.AdditiveBlending,
    depthWrite: false
});

const particles = new THREE.Points(geometry, material);
scene.add(particles);

// Animation Loop
let particleSpeed = 0.02; // Base rotation speed
let particleYDirection = 0; // 0 = stable, 1 = up (BUY), -1 = down (SELL)
const clock = new THREE.Clock();

function animate() {
    requestAnimationFrame(animate);
    const elapsedTime = clock.getElapsedTime();

    // Rotate slowly
    particles.rotation.y += particleSpeed * 0.05;

    // Animate individual particles based on trend
    const positions = particles.geometry.attributes.position.array;
    for (let i = 0; i < particleCount; i++) {
        const i3 = i * 3;
        // Float effect
        positions[i3 + 1] += Math.sin(elapsedTime + positions[i3]) * 0.01;
        
        // Trend effect (up or down)
        if (particleYDirection !== 0) {
            positions[i3 + 1] += particleYDirection * (Math.random() * 0.05);
            // Reset if too high or low
            if (positions[i3 + 1] > 20) positions[i3 + 1] = -30;
            if (positions[i3 + 1] < -30) positions[i3 + 1] = 20;
        }
    }
    particles.geometry.attributes.position.needsUpdate = true;

    renderer.render(scene, camera);
}
animate();

// Handle Resize
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});


// ─── UI & LOGIC ──────────────────────────────────────────────────────────

const analyzeBtn = document.getElementById('analyze-btn');
const tickerInput = document.getElementById('ticker-input');
const pills = document.querySelectorAll('.pill');

// Update particles based on signal
function update3DTheme(signal) {
    const colAttr = particles.geometry.attributes.color.array;
    let targetColor = new THREE.Color(0x4f46e5); // default
    
    if (signal === 'BUY') {
        targetColor = new THREE.Color(0x10b981); // Green
        particleYDirection = 1; // Flow up
        particleSpeed = 0.08;
    } else if (signal === 'SELL') {
        targetColor = new THREE.Color(0xef4444); // Red
        particleYDirection = -1; // Flow down
        particleSpeed = 0.08;
    } else if (signal === 'HOLD') {
        targetColor = new THREE.Color(0xf59e0b); // Yellow
        particleYDirection = 0; // Float
        particleSpeed = 0.02;
    }

    // Tween colors smoothly
    for (let i = 0; i < particleCount; i++) {
        colAttr[i * 3] = targetColor.r;
        colAttr[i * 3 + 1] = targetColor.g;
        colAttr[i * 3 + 2] = targetColor.b;
    }
    particles.geometry.attributes.color.needsUpdate = true;
}

// Format numbers
function formatPrice(num, ticker) {
    if (isNaN(num)) return "--";
    const isIndian = ticker && (ticker.toUpperCase().endsWith('.NS') || ticker.toUpperCase().endsWith('.BO'));
    const currency = isIndian ? 'INR' : 'USD';
    const locale = isIndian ? 'en-IN' : 'en-US';
    return new Intl.NumberFormat(locale, { style: 'currency', currency: currency }).format(num);
}

let priceChartInstance = null;

// Render Chart
function renderChart(historyData, ticker) {
    const ctx = document.getElementById('priceChart').getContext('2d');
    
    if (priceChartInstance) {
        priceChartInstance.destroy();
    }

    if (!historyData || historyData.length === 0) return;

    const labels = historyData.map(d => d.date);
    const data = historyData.map(d => d.close);
    
    // Determine color based on trend
    const first = data[0];
    const last = data[data.length - 1];
    const color = last >= first ? '#10b981' : '#ef4444';
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, `${color}66`); // 40% opacity
    gradient.addColorStop(1, `${color}00`);

    priceChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Close Price',
                data: data,
                borderColor: color,
                backgroundColor: gradient,
                borderWidth: 2,
                pointRadius: 0,
                pointHitRadius: 10,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(16, 20, 32, 0.9)',
                    titleColor: '#94a3b8',
                    bodyColor: '#f8fafc',
                    borderColor: 'rgba(99, 179, 237, 0.3)',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    display: false, // Hide x axis for cleaner look
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#94a3b8' }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

// Fetch and Analyze
async function analyzeStock(ticker) {
    if (!ticker) return;
    
    document.getElementById('loading-overlay').classList.remove('hidden');
    
    try {
        // Fetch Prediction
        const predRes = await fetch('/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol: ticker })
        });
        const predData = await predRes.json();
        
        if (predData.error) throw new Error(predData.error);

        // Fetch History
        const histRes = await fetch(`/history/${ticker}`);
        const histData = await histRes.json();

        // Update UI Text
        document.getElementById('stock-name').textContent = predData.company_name || getCompanyName(ticker);
        document.getElementById('stock-ticker').textContent = predData.ticker || ticker.toUpperCase();
        
        document.getElementById('current-price').textContent = formatPrice(predData.current_price, predData.ticker);
        document.getElementById('predicted-price').textContent = formatPrice(predData.predicted_price, predData.ticker);
        
        const pctEl = document.getElementById('pct-change');
        pctEl.textContent = `${predData.pct_change >= 0 ? '▲' : '▼'} ${Math.abs(predData.pct_change).toFixed(2)}%`;
        pctEl.className = predData.pct_change >= 0 ? 'positive' : 'negative';

        document.getElementById('confidence').textContent = `${predData.confidence.toFixed(1)}%`;
        document.getElementById('conf-bar').style.width = `${predData.confidence}%`;

        document.getElementById('explanation-text').textContent = predData.explanation;
        
        // Show signal badge
        const badge = document.getElementById('signal-badge');
        badge.classList.remove('hidden', 'signal-BUY', 'signal-SELL', 'signal-HOLD');
        badge.classList.add(`signal-${predData.signal}`);
        document.getElementById('signal-text').textContent = predData.signal;

        // Show technical stats
        document.getElementById('tech-stats').classList.remove('hidden');
        document.getElementById('val-rsi').textContent = predData.rsi.toFixed(1);
        document.getElementById('val-sent').textContent = predData.sentiment.toFixed(3);
        document.getElementById('val-macd').textContent = predData.macd_histogram.toFixed(4);

        // Update 3D Theme
        update3DTheme(predData.signal);

        // Render Chart
        if (histData.data) {
            renderChart(histData.data, ticker);
        }

    } catch (err) {
        alert("Error analyzing stock: " + err.message);
    } finally {
        document.getElementById('loading-overlay').classList.add('hidden');
    }
}

// Helpers
const companyNames = {
    "AAPL": "Apple Inc.",
    "TSLA": "Tesla",
    "NVDA": "Nvidia",
    "RELIANCE.NS": "Reliance Ind.",
    "TCS.NS": "TCS",
    "HDFCBANK.NS": "HDFC Bank"
};
function getCompanyName(ticker) {
    return companyNames[ticker.toUpperCase()] || "Company Analysis";
}

// Events
analyzeBtn.addEventListener('click', () => {
    const val = tickerInput.value.trim();
    if (val) analyzeStock(val);
});

tickerInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        const val = tickerInput.value.trim();
        if (val) analyzeStock(val);
    }
});

pills.forEach(pill => {
    pill.addEventListener('click', () => {
        const ticker = pill.getAttribute('data-ticker');
        tickerInput.value = ticker;
        analyzeStock(ticker);
    });
});
