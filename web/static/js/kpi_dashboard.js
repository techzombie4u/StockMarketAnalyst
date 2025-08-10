
/**
 * KPI Dashboard JavaScript
 * Handles timeframe filtering, KPI display, and GoAhead triggers
 */

class KPIDashboard {
    constructor() {
        this.currentTimeframe = 'All';
        this.currentProduct = 'all';
        this.kpiData = null;
        this.thresholds = null;
        this.refreshInterval = null;
        
        this.init();
    }
    
    init() {
        console.log('[KPI] Initializing KPI Dashboard');
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load thresholds
        this.loadThresholds();
        
        // Initial data load
        this.loadKPIData();
        
        // Set up auto-refresh
        this.setupAutoRefresh();
    }
    
    setupEventListeners() {
        // Timeframe tabs
        document.querySelectorAll('.timeframe-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const timeframe = e.target.dataset.timeframe;
                this.selectTimeframe(timeframe);
            });
        });
        
        // Product tabs
        document.querySelectorAll('.product-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const product = e.target.dataset.product;
                this.selectProduct(product);
            });
        });
        
        // Refresh button
        document.getElementById('refresh-btn').addEventListener('click', () => {
            this.manualRefresh();
        });
        
        // Set initial active tabs
        this.selectTimeframe('All');
        this.selectProduct('all');
    }
    
    selectTimeframe(timeframe) {
        this.currentTimeframe = timeframe;
        
        // Update tab appearance
        document.querySelectorAll('.timeframe-tab').forEach(tab => {
            tab.classList.remove('tab-active');
            if (tab.dataset.timeframe === timeframe) {
                tab.classList.add('tab-active');
            }
        });
        
        // Reload data
        this.loadKPIData();
    }
    
    selectProduct(product) {
        this.currentProduct = product;
        
        // Update tab appearance
        document.querySelectorAll('.product-tab').forEach(tab => {
            tab.classList.remove('tab-active');
            if (tab.dataset.product === product) {
                tab.classList.add('tab-active');
            }
        });
        
        // Update display
        this.updateDisplay();
    }
    
    async loadThresholds() {
        try {
            const response = await fetch('/api/kpi/thresholds');
            const data = await response.json();
            
            if (data.success) {
                this.thresholds = data.data;
                console.log('[KPI] Thresholds loaded:', this.thresholds);
            }
        } catch (error) {
            console.error('[KPI] Error loading thresholds:', error);
        }
    }
    
    async loadKPIData() {
        try {
            this.showLoading(true);
            
            const response = await fetch(`/api/kpi/summary?timeframe=${this.currentTimeframe}`);
            const data = await response.json();
            
            if (data.success) {
                this.kpiData = data.data;
                console.log('[KPI] Data loaded:', this.kpiData);
                this.updateDisplay();
                this.updateLastUpdated();
            } else {
                console.error('[KPI] API error:', data.error);
                this.showError(data.error);
            }
        } catch (error) {
            console.error('[KPI] Error loading KPI data:', error);
            this.showError('Failed to load KPI data');
        } finally {
            this.showLoading(false);
        }
    }
    
    updateDisplay() {
        if (!this.kpiData) return;
        
        // Get current data based on selected product
        let currentData;
        if (this.currentProduct === 'all') {
            currentData = this.kpiData.overall;
        } else {
            currentData = this.kpiData.by_product[this.currentProduct];
        }
        
        if (!currentData) {
            console.warn('[KPI] No data for current selection');
            return;
        }
        
        // Update KPI sections
        this.updatePredictionKPIs(currentData.prediction_quality);
        this.updateFinancialKPIs(currentData.financial);
        this.updateRiskKPIs(currentData.risk);
        
        // Update triggers
        this.updateTriggers(this.kpiData.triggers);
        
        // Update pinned stats (if available)
        this.updatePinnedStats();
        
        // Update summary table
        this.updateSummaryTable();
    }
    
    updatePredictionKPIs(predictionKPIs) {
        const container = document.getElementById('prediction-kpis');
        container.innerHTML = '';
        
        const kpis = [
            { key: 'hit_rate', label: 'Hit Rate', format: 'percentage', higherIsBetter: true },
            { key: 'brier_score', label: 'Brier Score', format: 'decimal', higherIsBetter: false },
            { key: 'calibration_error', label: 'Calibration Error', format: 'decimal', higherIsBetter: false },
            { key: 'top_decile_hit_rate', label: 'Top Decile Hit Rate', format: 'percentage', higherIsBetter: true },
            { key: 'top_decile_edge', label: 'Top Decile Edge', format: 'decimal', higherIsBetter: true }
        ];
        
        kpis.forEach(kpi => {
            const card = this.createKPICard(
                kpi.label,
                predictionKPIs[kpi.key],
                kpi.format,
                this.getKPIStatus(kpi.key, predictionKPIs[kpi.key], kpi.higherIsBetter),
                this.getTrendInfo(kpi.key, 'prediction_quality')
            );
            container.appendChild(card);
        });
    }
    
    updateFinancialKPIs(financialKPIs) {
        const container = document.getElementById('financial-kpis');
        container.innerHTML = '';
        
        const kpis = [
            { key: 'sharpe_ratio', label: 'Sharpe Ratio', format: 'decimal', higherIsBetter: true },
            { key: 'sortino_ratio', label: 'Sortino Ratio', format: 'decimal', higherIsBetter: true },
            { key: 'win_rate', label: 'Win Rate', format: 'percentage', higherIsBetter: true },
            { key: 'total_pnl', label: 'Total P&L', format: 'currency', higherIsBetter: true },
            { key: 'win_loss_expectancy', label: 'Win/Loss Expectancy', format: 'decimal', higherIsBetter: true }
        ];
        
        kpis.forEach(kpi => {
            const card = this.createKPICard(
                kpi.label,
                financialKPIs[kpi.key],
                kpi.format,
                this.getKPIStatus(kpi.key, financialKPIs[kpi.key], kpi.higherIsBetter),
                this.getTrendInfo(kpi.key, 'financial')
            );
            container.appendChild(card);
        });
    }
    
    updateRiskKPIs(riskKPIs) {
        const container = document.getElementById('risk-kpis');
        container.innerHTML = '';
        
        const kpis = [
            { key: 'max_drawdown', label: 'Max Drawdown', format: 'percentage', higherIsBetter: false },
            { key: 'var_95', label: 'VaR 95%', format: 'decimal', higherIsBetter: false },
            { key: 'var_99', label: 'VaR 99%', format: 'decimal', higherIsBetter: false },
            { key: 'avg_exposure', label: 'Avg Exposure', format: 'currency', higherIsBetter: false }
        ];
        
        kpis.forEach(kpi => {
            const card = this.createKPICard(
                kpi.label,
                riskKPIs[kpi.key],
                kpi.format,
                this.getKPIStatus(kpi.key, riskKPIs[kpi.key], kpi.higherIsBetter),
                this.getTrendInfo(kpi.key, 'risk')
            );
            container.appendChild(card);
        });
    }
    
    createKPICard(label, value, format, status, trendInfo) {
        const card = document.createElement('div');
        card.className = `kpi-card kpi-${status}`;
        
        const formattedValue = this.formatValue(value, format);
        const trendElement = trendInfo ? 
            `<span class="trend-${trendInfo.direction} ml-2">
                ${trendInfo.arrow} ${trendInfo.delta_pct > 0 ? '+' : ''}${trendInfo.delta_pct}%
            </span>` : '';
        
        card.innerHTML = `
            <div class="flex justify-between items-start">
                <div>
                    <h3 class="text-sm font-medium text-gray-600">${label}</h3>
                    <p class="text-2xl font-bold text-gray-900 mt-1">
                        ${formattedValue}
                        ${trendElement}
                    </p>
                </div>
                <div class="w-3 h-3 rounded-full bg-current opacity-20"></div>
            </div>
        `;
        
        return card;
    }
    
    formatValue(value, format) {
        if (value === null || value === undefined) return 'N/A';
        
        switch (format) {
            case 'percentage':
                return `${(value * 100).toFixed(1)}%`;
            case 'decimal':
                return value.toFixed(3);
            case 'currency':
                return `$${value.toLocaleString()}`;
            default:
                return value.toString();
        }
    }
    
    getKPIStatus(key, value, higherIsBetter) {
        if (!this.thresholds || value === null || value === undefined) {
            return 'neutral';
        }
        
        // Get threshold for this KPI
        let threshold = null;
        if (this.thresholds.targets[key]) {
            threshold = this.thresholds.targets[key][this.currentTimeframe] || 
                      this.thresholds.targets[key]['all'];
        }
        
        if (!threshold) return 'neutral';
        
        const warnBand = this.thresholds.warn_bands.pct;
        
        if (higherIsBetter) {
            if (value >= threshold) return 'good';
            if (value >= threshold * (1 - warnBand)) return 'warn';
            return 'bad';
        } else {
            if (value <= threshold) return 'good';
            if (value <= threshold * (1 + warnBand)) return 'warn';
            return 'bad';
        }
    }
    
    getTrendInfo(key, category) {
        if (!this.kpiData) return null;
        
        let currentData;
        if (this.currentProduct === 'all') {
            currentData = this.kpiData.overall;
        } else {
            currentData = this.kpiData.by_product[this.currentProduct];
        }
        
        const trendKey = `${category}_${key}`;
        return currentData?.trends?.[trendKey] || null;
    }
    
    updateTriggers(triggers) {
        const section = document.getElementById('triggers-section');
        const container = document.getElementById('triggers-container');
        
        if (!triggers || triggers.length === 0) {
            section.classList.add('hidden');
            return;
        }
        
        section.classList.remove('hidden');
        container.innerHTML = '';
        
        triggers.forEach(trigger => {
            const card = document.createElement('div');
            card.className = `trigger-card trigger-${trigger.severity}`;
            
            card.innerHTML = `
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <div class="flex items-center space-x-2 mb-2">
                            <span class="px-2 py-1 text-xs font-medium rounded-full 
                                       ${trigger.severity === 'high' ? 'bg-red-100 text-red-800' : 
                                         trigger.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' : 
                                         'bg-blue-100 text-blue-800'}">
                                ${trigger.type}
                            </span>
                            <span class="text-sm text-gray-600">${trigger.product}</span>
                            <span class="text-sm text-gray-600">${trigger.timeframe}</span>
                        </div>
                        <p class="text-gray-800">${trigger.reason}</p>
                        <p class="text-xs text-gray-500 mt-1">${new Date(trigger.timestamp).toLocaleString()}</p>
                    </div>
                    <button class="ml-4 px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm"
                            onclick="kpiDashboard.acknowledgeTrigger('${trigger.id}')">
                        Acknowledge
                    </button>
                </div>
            `;
            
            container.appendChild(card);
        });
    }
    
    updatePinnedStats() {
        // This would integrate with pinned symbols data from previous prompts
        const container = document.getElementById('pinned-stats-grid');
        container.innerHTML = `
            <div class="text-center py-4 col-span-4 text-gray-500">
                <i class="fas fa-info-circle"></i>
                Pinned stats integration pending
            </div>
        `;
    }
    
    updateSummaryTable() {
        if (!this.kpiData) return;
        
        const tbody = document.getElementById('kpi-summary-tbody');
        tbody.innerHTML = '';
        
        const timeframes = ['3D', '5D', '10D', '15D', '30D'];
        
        // This would require loading data for each timeframe
        // For now, just show current timeframe
        const currentData = this.currentProduct === 'all' ? 
                           this.kpiData.overall : 
                           this.kpiData.by_product[this.currentProduct];
        
        if (currentData) {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td class="px-4 py-2 font-medium">${this.currentTimeframe}</td>
                <td class="px-4 py-2">${this.formatValue(currentData.prediction_quality.hit_rate, 'percentage')}</td>
                <td class="px-4 py-2">${this.formatValue(currentData.prediction_quality.brier_score, 'decimal')}</td>
                <td class="px-4 py-2">${this.formatValue(currentData.financial.sharpe_ratio, 'decimal')}</td>
                <td class="px-4 py-2">${this.formatValue(currentData.risk.max_drawdown, 'percentage')}</td>
                <td class="px-4 py-2">${this.formatValue(currentData.risk.var_95, 'decimal')}</td>
            `;
            tbody.appendChild(row);
        }
    }
    
    updateLastUpdated() {
        if (!this.kpiData) return;
        
        const element = document.getElementById('last-updated');
        const autoTime = new Date(this.kpiData.last_auto_refresh).toLocaleString();
        const manualTime = this.kpiData.last_manual_refresh ? 
                          new Date(this.kpiData.last_manual_refresh).toLocaleString() : 
                          'Never';
        
        element.innerHTML = `Auto: ${autoTime} | Manual: ${manualTime}`;
    }
    
    async manualRefresh() {
        const button = document.getElementById('refresh-btn');
        const originalContent = button.innerHTML;
        
        try {
            button.innerHTML = '<div class="loading-spinner"></div> Refreshing...';
            button.disabled = true;
            
            const scope = this.currentProduct === 'all' ? 'overall' : 'product';
            const product = this.currentProduct === 'all' ? '' : this.currentProduct;
            
            const response = await fetch(`/api/kpi/recompute?scope=${scope}&timeframe=${this.currentTimeframe}&product=${product}`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                console.log('[KPI] Manual refresh successful');
                await this.loadKPIData();
            } else {
                console.error('[KPI] Manual refresh failed:', data.error);
                alert(`Refresh failed: ${data.error}`);
            }
        } catch (error) {
            console.error('[KPI] Manual refresh error:', error);
            alert('Refresh failed due to network error');
        } finally {
            button.innerHTML = originalContent;
            button.disabled = false;
        }
    }
    
    async acknowledgeTrigger(triggerId) {
        try {
            const response = await fetch('/api/kpi/triggers/acknowledge', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ trigger_id: triggerId })
            });
            
            const data = await response.json();
            
            if (data.success) {
                console.log('[KPI] Trigger acknowledged:', triggerId);
                // Remove trigger from display
                await this.loadKPIData();
            } else {
                console.error('[KPI] Acknowledge failed:', data.error);
            }
        } catch (error) {
            console.error('[KPI] Acknowledge error:', error);
        }
    }
    
    setupAutoRefresh() {
        // Auto-refresh every 5 minutes
        this.refreshInterval = setInterval(() => {
            console.log('[KPI] Auto-refreshing data');
            this.loadKPIData();
        }, 5 * 60 * 1000);
    }
    
    showLoading(show) {
        const loadingState = document.getElementById('loading-state');
        const mainContent = document.getElementById('main-content');
        
        if (show) {
            loadingState.classList.remove('hidden');
            mainContent.classList.add('hidden');
        } else {
            loadingState.classList.add('hidden');
            mainContent.classList.remove('hidden');
        }
    }
    
    showError(message) {
        const loadingState = document.getElementById('loading-state');
        loadingState.innerHTML = `
            <div class="text-center py-8">
                <i class="fas fa-exclamation-triangle text-red-500 text-4xl mb-4"></i>
                <p class="text-red-600">${message}</p>
                <button onclick="kpiDashboard.loadKPIData()" 
                        class="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                    Retry
                </button>
            </div>
        `;
        loadingState.classList.remove('hidden');
    }
    
    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    }
}

// Initialize dashboard when DOM is loaded
let kpiDashboard;
document.addEventListener('DOMContentLoaded', () => {
    kpiDashboard = new KPIDashboard();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (kpiDashboard) {
        kpiDashboard.destroy();
    }
});
