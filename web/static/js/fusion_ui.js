
// web/static/js/fusion_ui.js
(function () {
  const sel = (id) => document.getElementById(id);

  // Safely set text/html only if element exists
  function setText(id, value) {
    const el = sel(id);
    if (el) el.textContent = value;
  }
  function setHTML(id, html) {
    const el = sel(id);
    if (el) el.innerHTML = html;
  }
  function show(id) {
    const el = sel(id);
    if (el) el.style.display = '';
  }
  function hide(id) {
    const el = sel(id);
    if (el) el.style.display = 'none';
  }

  async function fetchFusion(force = false) {
    const url = force ? '/api/fusion/dashboard?forceRefresh=true' : '/api/fusion/dashboard';
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) {
      const txt = await res.text().catch(() => '');
      throw new Error(`Fusion API ${res.status}: ${txt}`);
    }
    return res.json();
  }

  function verdictBadge(v) {
    const m = {
      STRONG_BUY: 'success',
      BUY: 'primary',
      HOLD: 'secondary',
      CAUTIOUS: 'warning',
      AVOID: 'danger'
    };
    const cls = m[v] || 'secondary';
    return `<span class="badge bg-${cls}">${v}</span>`;
  }

  function renderPinnedSummary(pinned) {
    // pinned = { total, met, not_met, in_progress }
    setText('pinnedTotal', pinned?.total ?? 0);
    setText('pinnedMet', pinned?.met ?? 0);
    setText('pinnedNotMet', pinned?.not_met ?? 0);
    setText('pinnedInProgress', pinned?.in_progress ?? 0);
  }

  function renderTopSignals(signals) {
    // signals: [{ symbol, ai_verdict_normalized, confidence, target_price, last_price }]
    const bodyId = 'resultsTbody';
    const body = sel(bodyId);
    if (!body) return;

    if (!signals || !signals.length) {
      setHTML(bodyId, `<tr><td colspan="9" class="text-center text-muted">No signals</td></tr>`);
      return;
    }

    const rows = signals.map(s => {
      const conf = (s.confidence ?? 0).toFixed(1) + '%';
      const price = s.last_price != null ? s.last_price : '-';
      const target = s.target_price != null ? s.target_price : '-';
      const roi = (s.roi_pct != null) ? `${(s.roi_pct).toFixed(1)}%` : '-';

      return `
        <tr>
          <td><input type="checkbox" disabled /></td>
          <td>${s.symbol ?? '-'}</td>
          <td>${s.state ?? '-'}</td>
          <td>${(s.score ?? 0).toFixed ? (s.score).toFixed(1) : (s.score ?? '-')}</td>
          <td>${price}</td>
          <td>${target}</td>
          <td>${roi}</td>
          <td>${verdictBadge(s.ai_verdict_normalized ?? 'HOLD')}</td>
          <td>${conf}</td>
        </tr>`;
    }).join('');
    setHTML(bodyId, rows);
  }

  function renderStatus(data) {
    setText('statusText', 'Ready');
    setText('lastUpdated', data?.last_updated_utc ?? '-');
    setText('genTime', (data?.generation_time_ms ?? 0).toFixed(1) + 'ms');
    setText('alertsCount', (data?.alerts?.length ?? 0));
  }

  async function loadFusion(force = false) {
    try {
      show('loadingSpinner');
      setText('statusText', force ? 'Refreshing…' : 'Loading…');
      const data = await fetchFusion(force);

      renderPinnedSummary(data?.pinned_summary);
      renderTopSignals(data?.top_signals);
      renderStatus(data);

      hide('loadingSpinner');
      setText('statusText', 'Ready');
    } catch (err) {
      console.error('[FusionUI] Load error:', err);
      hide('loadingSpinner');
      setText('statusText', 'Error');
      const body = sel('resultsTbody');
      if (body) {
        body.innerHTML = `<tr><td colspan="9" class="text-danger">Failed to load data: ${err.message}</td></tr>`;
      }
    }
  }

  function bindUI() {
    const refreshBtn = sel('refreshBtn');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => loadFusion(true));
    }
  }

  window.addEventListener('DOMContentLoaded', () => {
    bindUI();
    // First paint
    loadFusion(false);
    // Optional auto-refresh every 5 minutes
    // setInterval(() => loadFusion(true), 5 * 60 * 1000);
  });
})();
