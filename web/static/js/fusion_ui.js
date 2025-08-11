// Fusion UI JavaScript for Dashboard, Equities, Options, Commodities
console.log('[FusionUI] DOM loaded, initializing...');

class FusionDashboard {
    constructor() {
        this.baseUrl = '';
        this.cache = new Map();
        this.init();
    }

    init() {
        this.loadDashboardData();
        this.loadPageSpecificData();
        this.setupEventListeners();

        // Auto-refresh every 30 seconds
        setInterval(() => this.loadDashboardData(), 30000);
    }

    async loadDashboardData(timeframe = 'all', forceRefresh = false) {
        console.log('[FusionUI] Loading fusion data, timeframe:', timeframe, 'force:', forceRefresh);

        try {
            const endpoint = `/api/fusion/dashboard${timeframe !== 'all' ? `?timeframe=${timeframe}` : ''}`;
            console.log('[FusionUI] Fetching from:', endpoint);

            const response = await fetch(endpoint);
            console.log('[FusionUI] Response status:', response.status);

            if (!response.ok) {
                const errorText = await response.text();
                console.log('[FusionUI] Response error:', errorText);
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }

            const data = await response.json();
            this.updateDashboardUI(data);

        } catch (error) {
            console.log('[FusionUI] Fetch error:', error);
            if (document.getElementById('dashboard-loading')) {
                document.getElementById('dashboard-loading').style.display = 'none';
            }
            // Show error message to user
            const errorDiv = document.createElement('div');
            errorDiv.className = 'bg-red-900 text-red-100 p-4 rounded-lg mb-4';
            errorDiv.innerHTML = '<h3 class="font-bold">Dashboard Loading Error</h3><p>Unable to load dashboard data. Please refresh the page.</p>';
            const container = document.querySelector('.space-y-6');
            if (container) {
                container.insertBefore(errorDiv, container.firstChild);
            }
        }
    }

    updateDashboardUI(data) {
        // Update main dashboard KPI cards (6 cards)
        const totalValue = document.getElementById('total-value');
        const totalPnl = document.getElementById('total-pnl');
        const activePositions = document.getElementById('active-positions');
        const winRate = document.getElementById('win-rate');
        const sharpeRatio = document.getElementById('sharpe-ratio');
        const maxDrawdown = document.getElementById('max-drawdown');
        const pinnedCount = document.getElementById('pinned-count');
        const lockedCount = document.getElementById('locked-count');

        if (totalValue) totalValue.textContent = `$${data.kpis.total_portfolio_value.toLocaleString()}`;
        if (totalPnl) totalPnl.textContent = `$${data.kpis.total_pnl.toLocaleString()}`;
        if (activePositions) activePositions.textContent = data.kpis.total_positions;
        if (winRate) winRate.textContent = `${(data.kpis.win_rate * 100).toFixed(1)}%`;
        if (sharpeRatio) sharpeRatio.textContent = data.kpis.sharpe_ratio.toFixed(2);
        if (maxDrawdown) maxDrawdown.textContent = `${(data.kpis.max_drawdown * 100).toFixed(1)}%`;
        if (pinnedCount) pinnedCount.textContent = data.summary.pinned_items;
        if (lockedCount) lockedCount.textContent = data.summary.locked_items;

        // Update Top Signals table
        const topSignalsTable = document.getElementById('top-signals-table');
        if (topSignalsTable && data.top_signals) {
            try {
                topSignalsTable.innerHTML = data.top_signals.map(signal => `
                    <tr>
                        <td>
                            <button onclick="window.fusionDashboard.pinItem('signal', '${signal.symbol}')" 
                                    class="pin-button">📌</button>
                        </td>
                        <td class="font-medium text-white">${signal.symbol}</td>
                        <td>${signal.product || 'Equity'}</td>
                        <td class="font-semibold">${signal.signal_score.toFixed(2)}</td>
                        <td>$${signal.current_price.toFixed(2)}</td>
                        <td>$${signal.target_price.toFixed(2)}</td>
                        <td class="${signal.potential_roi >= 0 ? 'text-green-400' : 'text-red-400'}">
                            ${(signal.potential_roi * 100).toFixed(1)}%
                        </td>
                        <td>
                            <span class="ai-verdict-badge ${signal.ai_verdict.toLowerCase()}">
                                ${signal.ai_verdict}
                            </span>
                        </td>
                        <td>${(signal.confidence * 100).toFixed(0)}%</td>
                    </tr>
                `).join('');
            } catch (error) {
                console.error('Error updating top signals table:', error);
                topSignalsTable.innerHTML = '<tr><td colspan="9" class="text-center text-red-400 py-4">Error loading signals</td></tr>';
            }
        }

        // Update alerts content
        const alertsContent = document.getElementById('alerts-content');
        if (alertsContent && data.summary.alerts) {
            if (data.summary.alerts.length === 0) {
                alertsContent.innerHTML = '<div class="text-sm text-gray-400">No active alerts</div>';
            } else {
                alertsContent.innerHTML = data.summary.alerts.map(alert => `
                    <div class="text-sm">
                        <span class="text-yellow-400">⚠️</span> ${alert.message}
                    </div>
                `).join('');
            }
        }

        // Update agent insights
        const agentInsights = document.getElementById('agent-insights');
        if (agentInsights && data.agent_insights) {
            agentInsights.innerHTML = data.agent_insights.map(insight => `
                <div class="text-sm">
                    <span class="text-blue-400">🤖</span> ${insight.message}
                </div>
            `).join('');
        }
    }

    async loadPageSpecificData() {
        const path = window.location.pathname;

        switch(path) {
            case '/equities':
                await this.loadEquitiesData();
                break;
            case '/options':
                await this.loadOptionsData();
                break;
            case '/commodities':
                await this.loadCommoditiesData();
                break;
        }
    }

    async loadEquitiesData() {
        try {
            const response = await fetch('/api/equities/positions');
            if (!response.ok) throw new Error('Failed to fetch equities data');

            const data = await response.json();
            this.updateEquitiesTable(data.positions);
        } catch (error) {
            console.error('Error loading equities:', error);
        }
    }

    updateEquitiesTable(positions) {
        const table = document.getElementById('equities-table');
        if (!table) return;

        table.innerHTML = positions.map(position => `
            <tr class="bg-slate-900 border-b border-slate-700">
                <td class="px-6 py-4 font-medium text-white">${position.symbol}</td>
                <td class="px-6 py-4">${position.quantity}</td>
                <td class="px-6 py-4">$${position.market_value.toLocaleString()}</td>
                <td class="px-6 py-4 ${position.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}">
                    $${position.unrealized_pnl.toLocaleString()}
                </td>
                <td class="px-6 py-4">
                    <button onclick="window.fusionDashboard.pinItem('equity', '${position.symbol}')" 
                            class="text-blue-400 hover:text-blue-300 mr-2">Pin</button>
                    <button onclick="window.fusionDashboard.lockItem('equity', '${position.symbol}')" 
                            class="text-red-400 hover:text-red-300">Lock</button>
                </td>
            </tr>
        `).join('');
    }

    async loadOptionsData(tabType = 'candidates') {
        try {
            const endpoint = tabType === 'candidates' ? '/api/options/candidates' : '/api/options/positions';
            const response = await fetch(endpoint);
            if (!response.ok) {
                // Fallback to strategies endpoint
                const fallbackResponse = await fetch('/api/options/strategies');
                if (!fallbackResponse.ok) throw new Error('Failed to fetch options data');
                const fallbackData = await fallbackResponse.json();
                this.updateOptionsTable(fallbackData.strategies || [], tabType);
                return;
            }

            const data = await response.json();
            this.updateOptionsTable(data[tabType] || [], tabType);

            // Update KPIs
            this.updateOptionsKPIs(data);
        } catch (error) {
            console.error('Error loading options:', error);
            this.showOptionsError();
        }
    }

    updateOptionsTable(optionsData, tabType) {
        const tableBody = document.getElementById('options-table-body');
        if (!tableBody) return;

        if (optionsData.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="13" class="text-center text-gray-400 py-8">
                        No ${tabType} found
                    </td>
                </tr>
            `;
            return;
        }

        tableBody.innerHTML = optionsData.map(option => `
            <tr>
                <td>
                    <button onclick="window.fusionDashboard.pinItem('option', '${option.symbol}')" 
                            class="pin-button">📌</button>
                </td>
                <td class="font-medium text-white">${option.symbol}</td>
                <td>${option.strategy || 'Long Call'}</td>
                <td>${option.expiry}</td>
                <td>$${option.strike}</td>
                <td class="${option.premium_change >= 0 ? 'text-green-400' : 'text-red-400'}">
                    $${option.premium}
                </td>
                <td>${option.delta?.toFixed(3) || '0.000'}</td>
                <td>${option.gamma?.toFixed(3) || '0.000'}</td>
                <td class="text-red-400">${option.theta?.toFixed(2) || '0.00'}</td>
                <td>${option.vega?.toFixed(3) || '0.000'}</td>
                <td>${(option.iv * 100)?.toFixed(1) || '0.0'}%</td>
                <td>${(option.probability * 100)?.toFixed(0) || '50'}%</td>
                <td>
                    <button class="action-button">Trade</button>
                </td>
            </tr>
        `).join('');
    }

    updateOptionsKPIs(data) {
        const kpis = data.kpis || {};

        const elements = {
            'options-total-premium': kpis.total_premium || 0,
            'options-net-pnl': kpis.net_pnl || 0,
            'options-delta': kpis.delta_exposure || 0,
            'options-theta': kpis.theta_decay || 0,
            'options-iv-rank': (kpis.iv_rank || 0) * 100,
            'options-margin': kpis.margin_required || 0
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                if (id.includes('pnl') || id.includes('premium') || id.includes('theta') || id.includes('margin')) {
                    element.textContent = `$${Math.abs(value).toLocaleString()}`;
                } else if (id.includes('rank')) {
                    element.textContent = `${value.toFixed(0)}%`;
                } else {
                    element.textContent = value.toFixed(2);
                }
            }
        });
    }

    showOptionsError() {
        const tableBody = document.getElementById('options-table-body');
        if (tableBody) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="13" class="text-center text-red-400 py-8">
                        Error loading options data. Please try again.
                    </td>
                </tr>
            `;
        }
    }

    async loadCommoditiesData() {
        try {
            const response = await fetch('/api/commodities/positions');
            if (!response.ok) throw new Error('Failed to fetch commodities data');

            const data = await response.json();
            this.updateCommoditiesTable(data.positions);
        } catch (error) {
            console.error('Error loading commodities:', error);
        }
    }

    updateCommoditiesTable(positions) {
        const table = document.getElementById('commodities-table');
        if (!table) return;

        table.innerHTML = positions.map(position => `
            <tr class="bg-slate-900 border-b border-slate-700">
                <td class="px-6 py-4 font-medium text-white">${position.commodity}</td>
                <td class="px-6 py-4">${position.quantity}</td>
                <td class="px-6 py-4">$${position.price.toLocaleString()}</td>
                <td class="px-6 py-4">$${position.market_value.toLocaleString()}</td>
                <td class="px-6 py-4 ${position.pnl >= 0 ? 'text-green-400' : 'text-red-400'}">
                    $${position.pnl.toLocaleString()}
                </td>
                <td class="px-6 py-4">
                    <button onclick="window.fusionDashboard.pinItem('commodity', '${position.commodity}')" 
                            class="text-blue-400 hover:text-blue-300 mr-2">Pin</button>
                    <button onclick="window.fusionDashboard.lockItem('commodity', '${position.commodity}')" 
                            class="text-red-400 hover:text-red-300">Lock</button>
                </td>
            </tr>
        `).join('');
    }

    async pinItem(type, symbol) {
        try {
            const response = await fetch('/api/pins', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    id: `${type}_${symbol}`,
                    type: type,
                    symbol: symbol
                })
            });

            if (response.ok) {
                console.log(`Pinned ${type} ${symbol}`);
                // Refresh dashboard to update pinned count
                this.loadDashboardData(true);
            }
        } catch (error) {
            console.error('Error pinning item:', error);
        }
    }

    async lockItem(type, symbol) {
        try {
            const response = await fetch('/api/locks', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    id: `${type}_${symbol}`,
                    type: type,
                    symbol: symbol
                })
            });

            if (response.ok) {
                console.log(`Locked ${type} ${symbol}`);
                // Refresh dashboard to update locked count
                this.loadDashboardData(true);
            }
        } catch (error) {
            console.error('Error locking item:', error);
        }
    }

    setupEventListeners() {
        // Force refresh button if it exists
        const refreshBtn = document.getElementById('force-refresh');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadDashboardData(true);
                this.loadPageSpecificData();
            });
        }

        // Pin/unpin functionality
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('pin-btn')) {
                const symbol = e.target.dataset.symbol;
                const type = e.target.dataset.type || 'equity';
                togglePin(type, symbol, e.target);
            }
        });

        async function togglePin(type, symbol, buttonElement) {
            try {
                const response = await fetch('/api/pins', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        items: [{ type: type, symbol: symbol }]
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    const isPinned = buttonElement.classList.toggle('pinned');
                    buttonElement.innerHTML = isPinned ? '★' : '☆';
                    buttonElement.title = isPinned ? 'Unpin item' : 'Pin item';

                    // Update pinned counter
                    loadPinnedCounts();
                }
            } catch (error) {
                console.error('Error toggling pin:', error);
            }
        }
    }

    showError(message) {
        console.error('FusionUI Error:', message);
        // Could add toast notifications here
    }
}

// Add CSS styles for AI verdict badges and signal styling
const style = document.createElement('style');
style.textContent = `
    .ai-verdict-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.375rem;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }

    .ai-verdict-badge.strong_buy {
        background-color: rgba(16, 185, 129, 0.2);
        color: #10b981;
    }

    .ai-verdict-badge.buy {
        background-color: rgba(34, 197, 94, 0.2);
        color: #22c55e;
    }

    .ai-verdict-badge.hold {
        background-color: rgba(245, 158, 11, 0.2);
        color: #f59e0b;
    }

    .ai-verdict-badge.cautious {
        background-color: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }

    .ai-verdict-badge.avoid {
        background-color: rgba(127, 29, 29, 0.3);
        color: #dc2626;
    }

    .pin-button {
        background: none;
        border: none;
        cursor: pointer;
        font-size: 1rem;
        padding: 0.25rem;
        opacity: 0.7;
        transition: opacity 0.15s ease;
    }

    .pin-button:hover {
        opacity: 1;
    }

    .pinned {
        color: #facc15; /* Tailwind yellow-300 */
    }
`;
document.head.appendChild(style);

// Global function for dashboard template compatibility
window.loadDashboardData = function(timeframe = 'all') {
    if (window.fusionDashboard) {
        window.fusionDashboard.loadDashboardData(timeframe, true);
    }
};

// Helper function to update pinned counts globally
function loadPinnedCounts() {
    if (window.fusionDashboard) {
        window.fusionDashboard.loadDashboardData(); // Reloads dashboard to get updated counts
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.fusionDashboard = new FusionDashboard();
});