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

  // Defensive formatting helpers
  function fmtPct(v) {
    const n = Number.isFinite(Number(v)) ? Number(v) : 0;
    return n.toFixed(1);
  }

  function safeNum(v, d = 0) {
    const n = Number(v);
    return Number.isFinite(n) ? n : d;
  }

  async function fetchFusion(force = false) {
    const url = force ? '/api/fusion/dashboard?forceRefresh=true' : '/api/fusion/dashboard';
    console.log('[FusionUI] Fetching from:', url);

    try {
      const res = await fetch(url, {
        cache: 'no-store',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });

      console.log('[FusionUI] Response status:', res.status);

      if (!res.ok) {
        const txt = await res.text().catch(() => 'Unknown error');
        console.error('[FusionUI] Response error:', txt);
        throw new Error(`Fusion API ${res.status}: ${txt}`);
      }

      const data = await res.json();
      console.log('[FusionUI] Response data:', data);
      return data;
    } catch (error) {
      console.error('[FusionUI] Fetch error:', error);
      throw error;
    }
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
    return `<span class="badge bg-${cls}">${v || 'HOLD'}</span>`;
  }

  function renderPinnedSummary(pinned) {
    console.log('[FusionUI] Rendering pinned summary:', pinned);
    setText('pinnedTotal', pinned?.total ?? 0);
    setText('pinnedMet', pinned?.met ?? 0);
    setText('pinnedNotMet', pinned?.not_met ?? 0);
    setText('pinnedInProgress', pinned?.in_progress ?? 0);
  }

  function renderTopSignals(signals) {
    console.log('[FusionUI] Rendering top signals:', signals);
    const bodyId = 'resultsTbody';
    const body = sel(bodyId);
    if (!body) {
      console.warn('[FusionUI] Results tbody not found');
      return;
    }

    if (!signals || !signals.length) {
      setHTML(bodyId, `<tr><td colspan="9" class="text-center text-muted">No signals available</td></tr>`);
      return;
    }

    const rows = signals.map(s => {
      const conf = fmtPct(s.confidence ?? 0) + '%';
      const price = s.last_price != null ? s.last_price : (s.price || '-');
      const target = s.target_price != null ? s.target_price : '-';
      const roi = (s.roi_pct != null) ? `${fmtPct(s.roi_pct)}%` : '-';
      const score = fmtPct(s.score ?? 0);

      return `
        <tr>
          <td><input type="checkbox" disabled /></td>
          <td><strong>${s.symbol ?? '-'}</strong></td>
          <td>${s.state ?? s.product ?? 'equity'}</td>
          <td>${score}</td>
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
    setText('genTime', (data?.generation_time_ms ?? 0) + 'ms');
    setText('alertsCount', (data?.alerts?.length ?? 0));
  }

  async function loadFusion(force = false) {
    try {
      console.log('[FusionUI] Loading fusion data, force:', force);
      show('loadingSpinner');
      setText('statusText', force ? 'Refreshing…' : 'Loading…');

      const data = await fetchFusion(force);
      console.log('[FusionUI] Got data:', data);

      renderPinnedSummary(data?.pinned_summary);
      renderTopSignals(data?.top_signals);
      renderStatus(data);

      hide('loadingSpinner');
      setText('statusText', 'Ready');
      console.log('[FusionUI] Load completed successfully');
    } catch (err) {
      console.error('[FusionUI] Load error:', err);
      hide('loadingSpinner');
      setText('statusText', 'Error');

      const body = sel('resultsTbody');
      if (body) {
        body.innerHTML = `<tr><td colspan="9" class="text-danger text-center">Failed to load data: ${err.message}</td></tr>`;
      }

      // Also show error in pinned summary
      setText('pinnedTotal', 'Error');
      setText('pinnedMet', '-');
      setText('pinnedNotMet', '-');
      setText('pinnedInProgress', '-');
    }
  }

  function bindUI() {
    const refreshBtn = sel('refreshBtn');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => {
        console.log('[FusionUI] Manual refresh triggered');
        loadFusion(true);
      });
    } else {
      console.warn('[FusionUI] Refresh button not found');
    }
  }

  window.addEventListener('DOMContentLoaded', () => {
    console.log('[FusionUI] DOM loaded, initializing...');
    bindUI();
    // First paint
    setTimeout(() => loadFusion(false), 100);
  });
})();