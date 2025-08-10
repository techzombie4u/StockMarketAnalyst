// Initialize dashboard
document.addEventListener('DOMContentLoaded', async () => {
    try {
        setupAutoRefresh();
        setupVerdictControls();
        loadGoAheadPanel();
    } catch (error) {
        console.error('[ERROR]', getCurrentTime(), 'Failed to initialize dashboard:', error);
        showError('Failed to initialize dashboard');
    }
});

// Auto-refresh functionality
function setupAutoRefresh() {
    // Refresh every 5 minutes
    setInterval(async () => {
        try {
            await Promise.all([
                loadData(), // Assuming loadData() refreshes prediction tables
                loadVerdicts(),
                loadGoAheadPanel()
            ]);
            logInfo('Dashboard refreshed');
        } catch (error) {
            console.error('[ERROR]', getCurrentTime(), 'Auto-refresh failed:', error);
        }
    }, 5 * 60 * 1000); // 5 minutes
}

// Mock function for loading data (replace with actual implementation)
function loadData() {
    console.log('[INFO]', getCurrentTime(), 'Simulating data load...');
    // In a real application, this would fetch and update prediction tables
    return Promise.resolve();
}

// Mock function for showing errors
function showError(message) {
    console.error('[ERROR]', message);
    // In a real application, this would display an error message to the user
}

// Mock function for logging info
function logInfo(message) {
    console.log('[INFO]', getCurrentTime(), message);
}

// Mock function to get current time
function getCurrentTime() {
    return new Date().toLocaleTimeString();
}

// Add AI Verdict functionality to dashboard
Replacing
<old_str>
setupAutoRefresh();
    } catch (error) {
        console.error('[ERROR]', getCurrentTime(), 'Failed to initialize dashboard:', error);
        showError('Failed to initialize dashboard');
    }
});
</old_str>
with
<new_str>
setupAutoRefresh();
        setupVerdictControls();
        loadGoAheadPanel();
    } catch (error) {
        console.error('[ERROR]', getCurrentTime(), 'Failed to initialize dashboard:', error);
        showError('Failed to initialize dashboard');
    }
});
</new_str>
Add AI Verdict functionality to dashboard
Replacing
<old_str>
setupAutoRefresh();
    } catch (error) {
        console.error('[ERROR]', getCurrentTime(), 'Failed to initialize dashboard:', error);
        showError('Failed to initialize dashboard');
    }
});
</old_str>
with
<new_str>
setupAutoRefresh();
        setupVerdictControls();
        loadGoAheadPanel();
    } catch (error) {
        console.error('[ERROR]', getCurrentTime(), 'Failed to initialize dashboard:', error);
        showError('Failed to initialize dashboard');
    }
});
</new_str>
Add verdict management functions
Replacing
<old_str>
logInfo('📋 Initial data load completed');
}

// Auto-refresh functionality
function setupAutoRefresh() {
</old_str>
with
<new_str>
logInfo('📋 Initial data load completed');

    // Load AI verdicts for displayed stocks
    setTimeout(() => {
        loadVerdicts();
    }, 500);
}

// AI Verdict Management
let verdictCache = new Map();

function setupVerdictControls() {
    const runVerdictBtn = document.getElementById('runVerdictBtn');
    if (runVerdictBtn) {
        runVerdictBtn.addEventListener('click', () => {
            document.getElementById('verdictModal').style.display = 'flex';
        });
    }

    // Setup GoAhead tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            loadGoAheadPanel(e.target.dataset.tab);
        });
    });

    // Setup verdict cell clicks
    document.addEventListener('click', (e) => {
        if (e.target.closest('.verdict-cell')) {
            const cell = e.target.closest('.verdict-cell');
            openVerdictDrawer(cell.dataset.symbol, cell.dataset.product, cell.dataset.timeframe);
        }
    });
}

async function loadVerdicts() {
    try {
        const verdictCells = document.querySelectorAll('.verdict-cell');
        const promises = [];

        verdictCells.forEach(cell => {
            const symbol = cell.dataset.symbol;
            const product = cell.dataset.product;
            const timeframe = cell.dataset.timeframe;

            if (symbol && product && timeframe) {
                const cacheKey = `${product}-${timeframe}-${symbol}`;

                if (verdictCache.has(cacheKey)) {
                    updateVerdictCell(cell, verdictCache.get(cacheKey));
                } else {
                    promises.push(fetchVerdict(symbol, product, timeframe, cell));
                }
            }
        });

        await Promise.allSettled(promises);
        console.log('[INFO]', getCurrentTime(), `Loaded verdicts for ${promises.length} stocks`);
    } catch (error) {
        console.error('[ERROR]', getCurrentTime(), 'Error loading verdicts:', error);
    }
}

async function fetchVerdict(symbol, product, timeframe, cell) {
    try {
        const response = await fetch(`/api/agents/latest?agent=${product}&scope=product=${product}&timeframe=${timeframe}&symbol=${symbol}`);

        if (response.ok) {
            const data = await response.json();
            const cacheKey = `${product}-${timeframe}-${symbol}`;
            verdictCache.set(cacheKey, data);
            updateVerdictCell(cell, data);
        } else {
            updateVerdictCell(cell, null);
        }
    } catch (error) {
        console.warn('[WARN]', getCurrentTime(), `Failed to fetch verdict for ${symbol}:`, error);
        updateVerdictCell(cell, null);
    }
}

function updateVerdictCell(cell, verdictData) {
    const content = cell.querySelector('.verdict-content');

    if (!verdictData || !verdictData.output) {
        content.textContent = '—';
        content.className = 'verdict-content verdict-unknown';
        return;
    }

    const output = verdictData.output;
    const verdict = output.verdict || 'Unknown';
    const confidence = output.confidence || 0;

    content.textContent = `${verdict} (${confidence}%)`;

    // Apply styling based on confidence and verdict
    let className = 'verdict-content ';
    if (confidence >= 80 && isPositiveVerdict(verdict)) {
        className += 'verdict-positive';
    } else if (confidence >= 60) {
        className += 'verdict-cautious';
    } else {
        className += 'verdict-negative';
    }

    content.className = className;

    // Add tooltip with reasons
    if (output.reasons && output.reasons.length > 0) {
        const tooltip = output.reasons.slice(0, 2).join('; ');
        cell.title = tooltip;
    }
}

function isPositiveVerdict(verdict) {
    const positive = ['strong buy', 'buy', 'bullish', 'positive', 'strong'];
    return positive.some(term => verdict.toLowerCase().includes(term));
}

async function loadGoAheadPanel(tab = 'all') {
    try {
        const content = document.getElementById('goaheadContent');
        content.innerHTML = '<div class="loading">Loading recommendations...</div>';

        let agents = [];
        switch (tab) {
            case 'product':
                agents = ['equity', 'options', 'comm', 'new', 'sentiment'];
                break;
            case 'trainer':
                agents = ['trainer'];
                break;
            default:
                agents = ['dev', 'trainer', 'equity', 'options', 'comm', 'new', 'sentiment'];
        }

        const promises = agents.map(agent => 
            fetch(`/api/agents/history?agent=${agent}&limit=1`)
                .then(r => r.ok ? r.json() : null)
                .catch(() => null)
        );

        const results = await Promise.allSettled(promises);
        const agentData = [];

        results.forEach((result, index) => {
            if (result.status === 'fulfilled' && result.value && result.value.outputs && result.value.outputs.length > 0) {
                agentData.push({
                    agent: agents[index],
                    data: result.value.outputs[0]
                });
            }
        });

        renderGoAheadCards(agentData);

        // Show panel if we have data
        if (agentData.length > 0) {
            document.getElementById('goaheadPanel').style.display = 'block';
        }
    } catch (error) {
        console.error('[ERROR]', getCurrentTime(), 'Error loading GoAhead panel:', error);
        document.getElementById('goaheadContent').innerHTML = '<div class="error">Failed to load recommendations</div>';
    }
}

function renderGoAheadCards(agentData) {
    const content = document.getElementById('goaheadContent');

    if (agentData.length === 0) {
        content.innerHTML = '<div class="no-data">No recent recommendations available</div>';
        return;
    }

    const html = agentData.map(({ agent, data }) => {
        const output = data.output || {};
        const timestamp = new Date(data.timestamp || Date.now()).toLocaleString();
        const verdict = output.verdict || 'No verdict';
        const actions = output.actions || [];
        const risks = output.risk_flags || [];

        return `
            <div class="agent-card">
                <div class="agent-header">
                    <span class="agent-name">${capitalizeAgent(agent)}</span>
                    <span class="agent-timestamp">${timestamp}</span>
                </div>
                <div class="agent-verdict">${verdict}</div>
                <div class="agent-actions">
                    ${actions.slice(0, 2).map(action => `• ${action}`).join('<br>')}
                </div>
                ${risks.length > 0 ? risks.map(risk => `<span class="risk-badge">${risk}</span>`).join('') : ''}
            </div>
        `;
    }).join('');

    content.innerHTML = html;
}

function capitalizeAgent(agent) {
    return agent.charAt(0).toUpperCase() + agent.slice(1) + ' Agent';
}

// Modal functions
function closeVerdictModal() {
    document.getElementById('verdictModal').style.display = 'none';
}

async function runVerdicts() {
    try {
        const agent = document.getElementById('agentSelect').value;
        const timeframe = document.getElementById('timeframeSelect').value;
        const symbol = document.getElementById('symbolInput').value.trim();

        const payload = {
            agent_name: agent,
            scope: {
                product: agent === 'all' ? null : agent,
                timeframe: timeframe === 'all' ? null : timeframe,
                symbol: symbol || null
            }
        };

        const response = await fetch('/api/agents/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            showToast('Request sent — verdict will refresh in 1–2 mins', 'success');
            closeVerdictModal();

            // Refresh verdicts after a delay
            setTimeout(() => {
                verdictCache.clear();
                loadVerdicts();
            }, 5000);
        } else {
            showToast('Failed to run verdicts', 'error');
        }
    } catch (error) {
        console.error('[ERROR]', getCurrentTime(), 'Error running verdicts:', error);
        showToast('Error running verdicts', 'error');
    }
}

// Drawer functions
function closeVerdictDrawer() {
    const drawer = document.getElementById('verdictDrawer');
    drawer.classList.remove('open');
    setTimeout(() => {
        drawer.style.display = 'none';
    }, 300);
}

async function openVerdictDrawer(symbol, product, timeframe) {
    try {
        const drawer = document.getElementById('verdictDrawer');
        const content = document.getElementById('drawerContent');

        drawer.style.display = 'flex';
        setTimeout(() => drawer.classList.add('open'), 10);

        content.innerHTML = '<div class="loading">Loading verdict details...</div>';

        const response = await fetch(`/api/agents/latest?agent=${product}&scope=product=${product}&timeframe=${timeframe}&symbol=${symbol}`);

        if (response.ok) {
            const data = await response.json();
            renderVerdictDetails(content, data, symbol);
        } else {
            content.innerHTML = '<div class="error">Failed to load verdict details</div>';
        }
    } catch (error) {
        console.error('[ERROR]', getCurrentTime(), 'Error opening verdict drawer:', error);
        document.getElementById('drawerContent').innerHTML = '<div class="error">Error loading details</div>';
    }
}

function renderVerdictDetails(container, data, symbol) {
    if (!data || !data.output) {
        container.innerHTML = '<div class="no-data">No verdict data available</div>';
        return;
    }

    const output = data.output;
    const metadata = data.metadata || {};

    const html = `
        <div class="verdict-detail">
            <h4>Symbol</h4>
            <div class="content">${symbol}</div>
        </div>

        <div class="verdict-detail">
            <h4>Verdict</h4>
            <div class="content">${output.verdict || 'N/A'}</div>
        </div>

        <div class="verdict-detail">
            <h4>Confidence</h4>
            <div class="content">${output.confidence || 0}%</div>
        </div>

        <div class="verdict-detail">
            <h4>Reasons</h4>
            <div class="content">
                <ul class="reasons-list">
                    ${(output.reasons || []).map(reason => `<li>${reason}</li>`).join('')}
                </ul>
            </div>
        </div>

        <div class="verdict-detail">
            <h4>Insights</h4>
            <div class="content">
                <ul class="reasons-list">
                    ${(output.insights || []).map(insight => `<li>${insight}</li>`).join('')}
                </ul>
            </div>
        </div>

        <div class="verdict-detail">
            <h4>Suggested Actions</h4>
            <div class="content">
                <ul class="actions-list">
                    ${(output.actions || []).map(action => `<li>${action}</li>`).join('')}
                </ul>
            </div>
        </div>

        <div class="verdict-detail">
            <h4>Risk Flags</h4>
            <div class="content">
                ${(output.risk_flags || []).map(flag => `<span class="risk-badge">${flag}</span>`).join(' ') || 'None'}
            </div>
        </div>

        <div class="verdict-detail">
            <h4>Metadata</h4>
            <div class="content">
                Agent: ${metadata.agent_name || 'Unknown'}<br>
                Model: ${metadata.model || 'Unknown'}<br>
                Run Time: ${new Date(data.timestamp || Date.now()).toLocaleString()}
            </div>
        </div>
    `;

    container.innerHTML = html;
}

async function runSingleVerdict() {
    // Implementation would depend on current drawer context
    showToast('Running single verdict...', 'info');
    closeVerdictDrawer();
}

function showToast(message, type = 'info') {
    // Create and show a toast notification
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 4px;
        color: white;
        z-index: 2000;
        transition: opacity 0.3s ease;
    `;

    switch (type) {
        case 'success':
            toast.style.backgroundColor = '#28a745';
            break;
        case 'error':
            toast.style.backgroundColor = '#dc3545';
            break;
        case 'warning':
            toast.style.backgroundColor = '#ffc107';
            toast.style.color = '#212529';
            break;
        default:
            toast.style.backgroundColor = '#17a2b8';
    }

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

// Auto-refresh functionality
function setupAutoRefresh() {