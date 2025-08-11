
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

    async loadDashboardData(forceRefresh = false) {
        console.log('[FusionUI] Loading fusion data, force:', forceRefresh);
        
        try {
            const endpoint = '/api/fusion/dashboard';
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
            console.error('Error loading dashboard data:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    updateDashboardUI(data) {
        // Update KPI cards
        const totalValue = document.getElementById('total-value');
        const totalPnl = document.getElementById('total-pnl');
        const activePositions = document.getElementById('active-positions');
        const pinnedCount = document.getElementById('pinned-count');
        const lockedCount = document.getElementById('locked-count');

        if (totalValue) totalValue.textContent = `$${data.kpis.total_portfolio_value.toLocaleString()}`;
        if (totalPnl) totalPnl.textContent = `$${data.kpis.total_pnl.toLocaleString()}`;
        if (activePositions) activePositions.textContent = data.kpis.total_positions;
        if (pinnedCount) pinnedCount.textContent = data.summary.pinned_items;
        if (lockedCount) lockedCount.textContent = data.summary.locked_items;

        // Update recent activity
        const recentActivity = document.getElementById('recent-activity');
        if (recentActivity && data.recent_activity) {
            recentActivity.innerHTML = data.recent_activity.map(activity => `
                <div class="flex justify-between items-center py-2 border-b border-slate-700 last:border-b-0">
                    <div>
                        <p class="text-sm text-white">${activity.details}</p>
                        <p class="text-xs text-gray-400">${activity.symbol}</p>
                    </div>
                    <p class="text-xs text-gray-400">${new Date(activity.timestamp).toLocaleTimeString()}</p>
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
                    <button onclick="fusionDashboard.pinItem('equity', '${position.symbol}')" 
                            class="text-blue-400 hover:text-blue-300 mr-2">Pin</button>
                    <button onclick="fusionDashboard.lockItem('equity', '${position.symbol}')" 
                            class="text-red-400 hover:text-red-300">Lock</button>
                </td>
            </tr>
        `).join('');
    }

    async loadOptionsData() {
        try {
            const response = await fetch('/api/options/strategies');
            if (!response.ok) throw new Error('Failed to fetch options data');
            
            const data = await response.json();
            this.updateOptionsTable(data.strategies);
        } catch (error) {
            console.error('Error loading options:', error);
        }
    }

    updateOptionsTable(strategies) {
        const table = document.getElementById('options-table');
        if (!table) return;

        table.innerHTML = strategies.map(strategy => `
            <tr class="bg-slate-900 border-b border-slate-700">
                <td class="px-6 py-4 font-medium text-white">${strategy.name}</td>
                <td class="px-6 py-4">${strategy.symbol}</td>
                <td class="px-6 py-4">${strategy.expiry}</td>
                <td class="px-6 py-4 ${strategy.pnl >= 0 ? 'text-green-400' : 'text-red-400'}">
                    $${strategy.pnl.toLocaleString()}
                </td>
                <td class="px-6 py-4">${strategy.probability}%</td>
                <td class="px-6 py-4">
                    <button onclick="fusionDashboard.pinItem('option', '${strategy.symbol}')" 
                            class="text-blue-400 hover:text-blue-300 mr-2">Pin</button>
                    <button onclick="fusionDashboard.lockItem('option', '${strategy.symbol}')" 
                            class="text-red-400 hover:text-red-300">Lock</button>
                </td>
            </tr>
        `).join('');
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
                    <button onclick="fusionDashboard.pinItem('commodity', '${position.commodity}')" 
                            class="text-blue-400 hover:text-blue-300 mr-2">Pin</button>
                    <button onclick="fusionDashboard.lockItem('commodity', '${position.commodity}')" 
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
    }

    showError(message) {
        console.error('FusionUI Error:', message);
        // Could add toast notifications here
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.fusionDashboard = new FusionDashboard();
});
