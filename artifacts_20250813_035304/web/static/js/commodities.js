
class CommoditiesManager {
  constructor() {
    this.selectedSymbol = 'GOLD';
    this.seasonalityEnabled = false;
    this.init();
  }

  init() {
    this.loadCommoditiesData();
    this.loadCorrelations();
    this.setupEventListeners();
  }

  setupEventListeners() {
    const seasonalityToggle = document.getElementById('seasonality-toggle');
    if (seasonalityToggle) {
      seasonalityToggle.addEventListener('change', (e) => {
        this.seasonalityEnabled = e.target.checked;
        this.loadCommodityDetail();
      });
    }
  }

  async loadCommoditiesData() {
    try {
      const response = await fetch('/api/commodities/signals');
      const data = await response.json();
      this.renderCommoditiesTable(data);
    } catch (error) {
      console.error('Failed to load commodities data:', error);
      document.getElementById('commodities-table').innerHTML = 'Failed to load data';
    }
  }

  async loadCorrelations() {
    try {
      const response = await fetch(`/api/commodities/correlations?symbol=${this.selectedSymbol}`);
      const data = await response.json();
      this.renderCorrelationsPanel(data);
    } catch (error) {
      console.error('Failed to load correlations:', error);
      document.getElementById('correlations-panel').innerHTML = 'Failed to load correlations';
    }
  }

  async loadCommodityDetail() {
    if (!this.seasonalityEnabled) return;
    
    try {
      const response = await fetch(`/api/commodities/${this.selectedSymbol}/detail?tf=30D`);
      const data = await response.json();
      console.log('Commodity detail loaded:', data);
      // Seasonality visualization would be implemented here
    } catch (error) {
      console.error('Failed to load commodity detail:', error);
    }
  }

  renderCommoditiesTable(signals) {
    const tableContainer = document.getElementById('commodities-table');
    if (!tableContainer) return;

    let html = `
      <table class="w-full">
        <thead>
          <tr class="text-xs text-muted border-b border-outline">
            <th class="text-left py-2">Commodity</th>
            <th class="text-left py-2">Price</th>
            <th class="text-left py-2">Change%</th>
            <th class="text-left py-2">Volume</th>
            <th class="text-left py-2">Signal</th>
            <th class="text-left py-2">Strength</th>
            <th class="text-left py-2">Verdict</th>
          </tr>
        </thead>
        <tbody>
    `;

    signals.forEach(signal => {
      const changeClass = signal.atrPct >= 0 ? 'text-success' : 'text-danger';
      html += `
        <tr class="border-b border-outline hover:bg-surface cursor-pointer" onclick="commoditiesManager.selectSymbol('${signal.ticker}')">
          <td class="py-2 text-sm">${signal.ticker}</td>
          <td class="py-2 text-sm">₹65,000</td>
          <td class="py-2 text-sm ${changeClass}">+${(signal.atrPct * 100).toFixed(1)}%</td>
          <td class="py-2 text-sm">1.2M</td>
          <td class="py-2 text-sm">${signal.verdict}</td>
          <td class="py-2 text-sm">${(signal.confidence * 100).toFixed(0)}%</td>
          <td class="py-2">
            <span class="verdict-badge verdict-${signal.verdict.toLowerCase()}">${signal.verdict}</span>
          </td>
        </tr>
      `;
    });

    html += '</tbody></table>';
    tableContainer.innerHTML = html;
  }

  renderCorrelationsPanel(correlations) {
    const panel = document.getElementById('correlations-panel');
    if (!panel) return;

    let html = `
      <div class="space-y-3">
        <div class="text-xs font-medium text-muted mb-2">${this.selectedSymbol} Correlations</div>
    `;

    Object.entries(correlations).forEach(([key, value]) => {
      const corrClass = value > 0 ? 'text-success' : 'text-danger';
      html += `
        <div class="flex justify-between items-center">
          <span class="text-xs text-on-surface">${key.toUpperCase()}</span>
          <span class="text-xs ${corrClass}">${value.toFixed(2)}</span>
        </div>
      `;
    });

    html += '</div>';
    panel.innerHTML = html;
  }

  selectSymbol(symbol) {
    this.selectedSymbol = symbol;
    this.loadCorrelations();
    if (this.seasonalityEnabled) {
      this.loadCommodityDetail();
    }
  }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.commoditiesManager = new CommoditiesManager();
});
