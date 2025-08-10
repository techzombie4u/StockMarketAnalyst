/**
 * Fusion Dashboard JavaScript
 * Handles KPI + AI Verdict integration dashboard
 */

class FusionDashboard {
    constructor() {
        this.data = null;
        this.selectedTimeframe = '5D';
        this.selectedProduct = 'All';
        this.refreshInProgress = false;
        this.lastRefreshTime = 0;
        this.debounceDelay = 3000; // 3 seconds debounce

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadData();

        // Auto-refresh every 2 minutes if page is visible
        setInterval(() => {
            if (!document.hidden && !this.refreshInProgress) {
                this.loadData(false);
            }
        }, 120000);
    }

    setupEventListeners() {
        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.handleRefresh();
        });

        // Filters
        document.getElementById('timeframeFilter').addEventListener('change', (e) => {
            this.selectedTimeframe = e.target.value;
            this.filterData();
        });

        document.getElementById('productFilter').addEventListener('change', (e) => {
            this.selectedProduct = e.target.value;
            this.filterData();
        });

        // Export button
        document.getElementById('exportTopSignals').addEventListener('click', () => {
            this.exportTopSignals();
        });

        // Pinned view button
        document.getElementById('openPinnedView').addEventListener('click', () => {
            window.open('/prediction-tracker-interactive', '_blank');
        });
    }

    async handleRefresh() {
        const now = Date.now();
        if (now - this.lastRefreshTime < this.debounceDelay) {
            console.log('Refresh debounced - too soon');
            return;
        }

        this.lastRefreshTime = now;
        await this.loadData(true);
    }

    async loadData(forceRefresh = false) {
        if (this.refreshInProgress) return;

        this.refreshInProgress = true;
        this.showLoading(true);

        try {
            const url = `/api/fusion/dashboard${forceRefresh ? '?forceRefresh=true' : ''}`;
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            this.data = await response.json();

            if (this.data.disabled) {
                this.showDisabled();
                return;
            }

            this.renderDashboard();
            this.updateLastUpdated();

            console.log(`Fusion data loaded in ${this.data.generation_time_ms}ms (cache: ${this.data.cache_hit})`);

        } catch (error) {
            console.error('Error loading fusion data:', error);
            this.showError(error.message);
        } finally {
            this.refreshInProgress = false;
            this.showLoading(false);
        }
    }

    renderDashboard() {
        if (!this.data) return;

        this.renderMarketStatus();
        this.renderKPICards();
        this.renderVerdictSummary();
        this.renderTopSignals();
        this.renderPinnedSummary();
        this.renderAlerts();
    }

    renderMarketStatus() {
        const statusElement = document.getElementById('marketStatus');
        const session = this.data.market_session;

        const statusConfig = {
            'OPEN': { text: 'OPEN', class: 'bg-green-100 text-green-800' },
            'CLOSED': { text: 'CLOSED', class: 'bg-red-100 text-red-800' },
            'PRE_MARKET': { text: 'PRE-MARKET', class: 'bg-blue-100 text-blue-800' },
            'POST_MARKET': { text: 'POST-MARKET', class: 'bg-purple-100 text-purple-800' }
        };

        const config = statusConfig[session] || statusConfig['CLOSED'];
        statusElement.textContent = config.text;
        statusElement.className = `ml-4 px-2 py-1 text-xs rounded-full ${config.class}`;
    }

    renderKPICards() {
        this.renderKPICard('prediction', this.data.timeframes, 'prediction_kpis');
        this.renderKPICard('financial', this.data.timeframes, 'financial_kpis');
    }

    renderKPICard(cardType, timeframes, kpiField) {
        const tabsContainer = document.getElementById(`${cardType}KpiTabs`);
        const contentContainer = document.getElementById(`${cardType}KpiContent`);

        // Render tabs
        tabsContainer.innerHTML = '';
        timeframes.forEach((tf, index) => {
            const tab = document.createElement('button');
            tab.className = `px-3 py-1 text-xs rounded ${index === 0 ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-600'}`;
            tab.textContent = tf.timeframe;
            tab.addEventListener('click', () => {
                this.switchKPITab(cardType, tf.timeframe, timeframes, kpiField);
            });
            tabsContainer.appendChild(tab);
        });

        // Render initial content
        if (timeframes.length > 0) {
            this.renderKPIContent(contentContainer, timeframes[0][kpiField]);
        }
    }

    switchKPITab(cardType, timeframe, timeframes, kpiField) {
        // Update tab styles
        const tabs = document.getElementById(`${cardType}KpiTabs`).children;
        Array.from(tabs).forEach(tab => {
            if (tab.textContent === timeframe) {
                tab.className = 'px-3 py-1 text-xs rounded bg-blue-100 text-blue-800';
            } else {
                tab.className = 'px-3 py-1 text-xs rounded bg-gray-100 text-gray-600';
            }
        });

        // Update content
        const tf = timeframes.find(t => t.timeframe === timeframe);
        if (tf) {
            const contentContainer = document.getElementById(`${cardType}KpiContent`);
            this.renderKPIContent(contentContainer, tf[kpiField]);
        }
    }

    renderKPIContent(container, kpis) {
        container.innerHTML = '';

        kpis.forEach(kpi => {
            const kpiDiv = document.createElement('div');
            kpiDiv.className = 'flex justify-between items-center';

            const colorClasses = {
                'green': 'text-green-600',
                'amber': 'text-amber-600', 
                'red': 'text-red-600',
                'neutral': 'text-gray-600'
            };

            kpiDiv.innerHTML = `
                <div class="flex items-center">
                    <span class="text-sm font-medium">${kpi.name}</span>
                    <span class="ml-2 text-lg ${kpi.trend}">${kpi.trend}</span>
                </div>
                <div class="flex items-center space-x-2">
                    <span class="text-lg font-bold ${colorClasses[kpi.color]}">${kpi.value.toFixed(2)}</span>
                    ${kpi.target ? `<span class="text-xs text-gray-500">target: ${kpi.target.toFixed(2)}</span>` : ''}
                </div>
            `;

            // Add tooltip
            kpiDiv.title = kpi.description;

            container.appendChild(kpiDiv);
        });
    }

    renderVerdictSummary() {
        const container = document.getElementById('verdictSummary');
        container.innerHTML = '';

        Object.entries(this.data.product_breakdown).forEach(([product, breakdown]) => {
            const productDiv = document.createElement('div');
            productDiv.className = 'text-center';

            const verdictCounts = breakdown.verdict_distribution;
            const total = verdictCounts.STRONG_BUY + verdictCounts.BUY + verdictCounts.HOLD + 
                         verdictCounts.CAUTIOUS + verdictCounts.AVOID;

            productDiv.innerHTML = `
                <h3 class="font-medium text-gray-900 mb-2 capitalize">${product}</h3>
                <div class="space-y-2">
                    ${this.renderVerdictBars(verdictCounts, total)}
                </div>
                <div class="text-xs text-gray-500 mt-2">
                    ${breakdown.total_predictions} predictions, ${breakdown.success_rate.toFixed(1)}% success
                </div>
            `;

            container.appendChild(productDiv);
        });
    }

    renderVerdictBars(counts, total) {
        if (total === 0) return '<div class="text-gray-400">No data</div>';

        const verdicts = ['STRONG_BUY', 'BUY', 'HOLD', 'CAUTIOUS', 'AVOID'];
        const colors = ['bg-emerald-500', 'bg-green-500', 'bg-gray-500', 'bg-amber-500', 'bg-red-500'];

        return verdicts.map((verdict, i) => {
            const count = counts[verdict] || 0;
            const percentage = (count / total * 100).toFixed(0);

            return `
                <div class="flex items-center text-xs">
                    <div class="w-16 text-right mr-2">${verdict.replace('_', ' ')}</div>
                    <div class="flex-1 bg-gray-200 rounded-full h-4 relative">
                        <div class="${colors[i]} h-4 rounded-full" style="width: ${percentage}%"></div>
                    </div>
                    <div class="w-10 text-left ml-2">${count}</div>
                </div>
            `;
        }).join('');
    }

    renderTopSignals() {
        const tableBody = document.getElementById('topSignalsTable');
        tableBody.innerHTML = '';

        let signals = this.data.top_signals || [];

        // Apply filters
        if (this.selectedProduct !== 'All') {
            signals = signals.filter(s => s.product === this.selectedProduct);
        }

        signals.forEach(signal => {
            const row = document.createElement('tr');
            row.className = 'hover:bg-gray-50';

            const verdictClass = `verdict-${signal.ai_verdict_normalized}`;
            const outcomeClass = signal.outcome_status === 'MET' ? 'text-green-600' : 
                               signal.outcome_status === 'NOT_MET' ? 'text-red-600' : 'text-gray-600';

            row.innerHTML = `
                <td class="sticky-cols px-3 py-4">
                    <button class="text-yellow-500 hover:text-yellow-600" onclick="this.togglePin('${signal.symbol}')">
                        ${signal.is_pinned ? '📌' : '📍'}
                    </button>
                </td>
                <td class="sticky-cols px-3 py-4 font-medium">${signal.symbol}</td>
                <td class="sticky-cols px-3 py-4 capitalize">${signal.product}</td>
                <td class="px-3 py-4">${signal.timeframe}</td>
                <td class="px-3 py-4">
                    <span class="px-2 py-1 text-xs font-medium rounded ${verdictClass}">
                        ${signal.ai_verdict_normalized.replace('_', ' ')}
                    </span>
                </td>
                <td class="px-3 py-4">${signal.confidence.toFixed(1)}%</td>
                <td class="px-3 py-4">${signal.score.toFixed(1)}</td>
                <td class="px-3 py-4 ${outcomeClass}">${signal.outcome_status.replace('_', ' ')}</td>
                <td class="ai-verdict-cell" style="display: none;">
                    <span class="ai-verdict-badge">
                        ${signal.ai_verdict || 'N/A'}
                        ${signal.ai_confidence ? `(${Math.round(signal.ai_confidence * 100)}%)` : ''}
                    </span>
                </td>
            `;

            tableBody.appendChild(row);
        });

        if (signals.length === 0) {
            const emptyRow = document.createElement('tr');
            emptyRow.innerHTML = `
                <td colspan="8" class="px-3 py-8 text-center text-gray-500">
                    No signals match the current filters
                </td>
            `;
            tableBody.appendChild(emptyRow);
        }
    }

    renderPinnedSummary() {
        const container = document.getElementById('pinnedSummary');
        const summary = this.data.pinned_summary;

        container.innerHTML = `
            <div class="text-center">
                <div class="text-2xl font-bold text-gray-900">${summary.total}</div>
                <div class="text-sm text-gray-500">Total Pinned</div>
            </div>
            <div class="text-center">
                <div class="text-2xl font-bold text-green-600">${summary.met}</div>
                <div class="text-sm text-gray-500">Met</div>
            </div>
            <div class="text-center">
                <div class="text-2xl font-bold text-red-600">${summary.not_met}</div>
                <div class="text-sm text-gray-500">Not Met</div>
            </div>
            <div class="text-center">
                <div class="text-2xl font-bold text-blue-600">${summary.in_progress}</div>
                <div class="text-sm text-gray-500">In Progress</div>
            </div>
        `;

        if (summary.success_rate !== null) {
            container.innerHTML += `
                <div class="col-span-2 text-center pt-4 border-t">
                    <div class="text-lg font-semibold ${summary.success_rate >= 70 ? 'text-green-600' : summary.success_rate >= 50 ? 'text-amber-600' : 'text-red-600'}">
                        ${summary.success_rate.toFixed(1)}% Success Rate
                    </div>
                </div>
            `;
        }

        if (summary.total === 0) {
            container.innerHTML = `
                <div class="col-span-2 text-center text-gray-500">
                    <div class="mb-2">No pinned items yet</div>
                    <button onclick="window.open('/dashboard', '_blank')" class="text-blue-600 hover:text-blue-800 text-sm underline">
                        Go pin from Products pages
                    </button>
                </div>
            `;
        }
    }

    renderAlerts() {
        const container = document.getElementById('alertsList');
        const alerts = this.data.alerts || [];

        if (alerts.length === 0) {
            container.innerHTML = '<div class="text-gray-500 text-center py-4">No alerts</div>';
            return;
        }

        container.innerHTML = '';
        alerts.forEach(alert => {
            const alertDiv = document.createElement('div');

            const severityClasses = {
                'info': 'bg-blue-50 text-blue-800 border-blue-200',
                'warning': 'bg-amber-50 text-amber-800 border-amber-200', 
                'error': 'bg-red-50 text-red-800 border-red-200',
                'critical': 'bg-red-100 text-red-900 border-red-300'
            };

            const severityClass = severityClasses[alert.severity] || severityClasses['info'];

            alertDiv.className = `p-3 rounded-lg border ${severityClass}`;
            alertDiv.innerHTML = `
                <div class="flex justify-between items-start">
                    <div>
                        <div class="font-medium">${alert.message}</div>
                        <div class="text-xs opacity-75 mt-1">${alert.source} • ${new Date(alert.timestamp).toLocaleTimeString()}</div>
                    </div>
                    <div class="text-xs uppercase font-medium">${alert.severity}</div>
                </div>
            `;

            container.appendChild(alertDiv);
        });
    }

    filterData() {
        // Re-render components that need filtering
        this.renderTopSignals();
    }

    exportTopSignals() {
        if (!this.data || !this.data.top_signals) return;

        const headers = ['Symbol', 'Product', 'Timeframe', 'AI Verdict', 'Confidence', 'Score', 'Outcome'];
        const csvContent = [
            headers.join(','),
            ...this.data.top_signals.map(signal => [
                signal.symbol,
                signal.product,
                signal.timeframe,
                signal.ai_verdict_normalized.replace('_', ' '),
                signal.confidence.toFixed(1),
                signal.score.toFixed(1),
                signal.outcome_status.replace('_', ' ')
            ].join(','))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `fusion_top_signals_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
    }

    updateLastUpdated() {
        const element = document.getElementById('lastUpdated');
        if (this.data && this.data.last_updated_utc) {
            const date = new Date(this.data.last_updated_utc);
            element.textContent = `Updated: ${date.toLocaleTimeString()}`;
        }
    }

    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        const refreshIcon = document.getElementById('refreshIcon');

        if (show) {
            overlay.classList.remove('hidden');
            refreshIcon.style.animation = 'spin 1s linear infinite';
        } else {
            overlay.classList.add('hidden');
            refreshIcon.style.animation = '';
        }
    }

    showError(message) {
        console.error('Fusion Dashboard Error:', message);
        // Could add toast notification here
    }

    showDisabled() {
        document.querySelector('main').innerHTML = `
            <div class="text-center py-12">
                <div class="text-gray-500 mb-4">Fusion Dashboard is currently disabled</div>
                <button onclick="window.location.reload()" class="px-4 py-2 bg-blue-600 text-white rounded">
                    Check Again
                </button>
            </div>
        `;
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.fusionDashboard = new FusionDashboard();
});

// Pin toggle function
window.togglePin = async function(symbol) {
    try {
        const response = await fetch('/api/pin-stock', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol, action: 'toggle' })
        });

        if (response.ok) {
            // Refresh the signals table
            window.fusionDashboard.renderTopSignals();
        }
    } catch (error) {
        console.error('Error toggling pin:', error);
    }
};