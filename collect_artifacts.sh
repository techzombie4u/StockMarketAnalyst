#!/usr/bin/env bash
set -euo pipefail

# ---------- Config ----------
BASE_URL="${BASE_URL:-http://localhost:5000}"
SYMBOL_EQ="${SYMBOL_EQ:-RELIANCE}"
SYMBOL_OPT="${SYMBOL_OPT:-RELIANCE}"
RUN_COVERAGE="${RUN_COVERAGE:-false}"    # set to "true" to run pytest coverage if no coverage.xml
ART_DIR="artifacts_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$ART_DIR"

echo "▶ Collecting artifacts into: $ART_DIR"
echo "   BASE_URL = $BASE_URL"
echo "   Symbols  = equity:$SYMBOL_EQ  options:$SYMBOL_OPT"

# ---------- Utils ----------
have_cmd() { command -v "$1" >/dev/null 2>&1; }

save_json_py() {
  # $1=url  $2=outfile
  python - "$1" "$2" <<'PY'
import sys, json, urllib.request
url, out = sys.argv[1], sys.argv[2]
try:
    with urllib.request.urlopen(url, timeout=10) as r:
        data = r.read()
    # try prettify JSON
    try:
        obj = json.loads(data.decode("utf-8"))
        data = json.dumps(obj, indent=2).encode("utf-8")
    except Exception:
        pass
    open(out, "wb").write(data)
    print(f"saved {out}")
except Exception as e:
    open(out, "w").write(f'{{"error":"{e}","url":"{url}"}}')
    print(f"warn: failed {url} -> {out}: {e}")
PY
}

save_json() {
  # $1=url  $2=outfile
  if have_cmd curl; then
    if have_cmd jq; then
      curl -fsS "$1" | jq '.' > "$2" || { echo "{\"error\":\"fetch failed\",\"url\":\"$1\"}" > "$2"; }
    else
      curl -fsS "$1" -o "$2" || { echo "{\"error\":\"fetch failed\",\"url\":\"$1\"}" > "$2"; }
    fi
  else
    save_json_py "$1" "$2"
  fi
}

post_json_py() {
  # $1=url  $2=json_payload  $3=outfile
  python - "$1" "$2" "$3" <<'PY'
import sys, json, urllib.request
url, payload, out = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    data = payload.encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        body = r.read()
    try:
        obj = json.loads(body.decode("utf-8"))
        body = json.dumps(obj, indent=2).encode("utf-8")
    except Exception:
        pass
    open(out, "wb").write(body)
    print(f"saved {out}")
except Exception as e:
    open(out, "w").write(f'{{"error":"{e}","url":"{url}"}}')
    print(f"warn: failed POST {url} -> {out}: {e}")
PY
}

# ---------- Runtime evidence ----------
echo "▶ Hitting /health and /metrics"
save_json     "$BASE_URL/health"                      "$ART_DIR/health.json"      || true
save_json     "$BASE_URL/metrics"                     "$ART_DIR/metrics_pre.json" || true

echo "▶ Sampling key API endpoints"
# Fusion & KPI
save_json     "$BASE_URL/api/fusion/dashboard?timeframe=All"           "$ART_DIR/sample__api_fusion_dashboard_All.json" || true
save_json     "$BASE_URL/api/kpi/summary?timeframe=5D"                  "$ART_DIR/sample__api_kpi_summary_5D.json"       || true

# Equities
save_json     "$BASE_URL/api/equity/analyze/$SYMBOL_EQ"                 "$ART_DIR/sample__api_equity_analyze_${SYMBOL_EQ}.json" || true
save_json     "$BASE_URL/api/equity/recommendations?count=10"           "$ART_DIR/sample__api_equity_recommendations_10.json"   || true

# Options
save_json     "$BASE_URL/api/options/short-strangle/$SYMBOL_OPT"        "$ART_DIR/sample__api_options_short_strangle_${SYMBOL_OPT}.json" || true

# Agents (best-effort; some stacks use /api/agents, /api/agents/kpis, /api/agents/runs)
save_json     "$BASE_URL/api/agents"                                    "$ART_DIR/sample__api_agents_list.json" || true
save_json     "$BASE_URL/api/agents/kpis"                               "$ART_DIR/sample__api_agents_kpis.json" || true
save_json     "$BASE_URL/api/agents/runs"                               "$ART_DIR/sample__api_agents_runs.json" || true

# Pins (best-effort; GET + POST toggle demo payload)
save_json     "$BASE_URL/api/pins"                                      "$ART_DIR/sample__api_pins_get.json" || true
post_json_py  "$BASE_URL/api/pins"        '{"type":"EQUITY","symbol":"TEST","reason":"collector"}' "$ART_DIR/sample__api_pins_post.json" || true
save_json     "$BASE_URL/api/pins"                                      "$ART_DIR/sample__api_pins_get_after.json" || true

# Capture post-metrics (to show delta)
save_json     "$BASE_URL/metrics"                     "$ART_DIR/metrics_post.json" || true

# ---------- Code pointers (routes) ----------
echo "▶ Enumerating routes from a live app (best-effort)"
python - "$BASE_URL" "$ART_DIR/routes.json" <<'PY'
import sys, json, urllib.request
base, out = sys.argv[1], sys.argv[2]
# Try a special endpoint if you have one, else fallback: scrape minimal list
candidates = [
    f"{base}/__routes__",               # optional introspection
    f"{base}/api/fusion/dashboard?timeframe=All",
    f"{base}/api/kpi/summary?timeframe=All",
    f"{base}/api/equity/recommendations?count=1",
    f"{base}/api/options/short-strangle/RELIANCE",
    f"{base}/api/agents",
]
routes = []
for u in candidates:
    try:
        with urllib.request.urlopen(u, timeout=5) as r:
            routes.append({"url": u, "status": r.status})
    except Exception as e:
        routes.append({"url": u, "error": str(e)})
open(out, "w").write(json.dumps({"base": base, "routes": routes}, indent=2))
PY
echo "saved $ART_DIR/routes.json"

# ---------- Coverage (optional auto-run) ----------
if [[ -f "coverage.xml" ]]; then
  echo "▶ Found existing coverage.xml"
  cp coverage.xml "$ART_DIR/coverage.xml" || true
elif [[ "$RUN_COVERAGE" == "true" ]]; then
  echo "▶ Running pytest to generate coverage.xml"
  if ! have_cmd pytest; then
    echo "⚠ pytest not found. Skipping coverage generation."
  else
    # ensure pytest-cov exists
    if ! python -c "import pytest_cov" 2>/dev/null; then
      pip -q install pytest-cov >/dev/null 2>&1 || true
    fi
    export PYTHONPATH="$PYTHONPATH:$PWD:$PWD/src"
    pytest --maxfail=1 --disable-warnings -q --cov=src --cov-report=xml > "$ART_DIR/pytest_cov_term.txt" || true
    [[ -f coverage.xml ]] && cp coverage.xml "$ART_DIR/coverage.xml" || true
  fi
fi

# ---------- Bundle sources & persistent state ----------
echo "▶ Adding web/ and data/persistent/"
if [[ -d "web" ]]; then
  mkdir -p "$ART_DIR/web"
  cp -r web/* "$ART_DIR/web/" || true
else
  echo "ℹ web/ not found"
fi

mkdir -p "$ART_DIR/persistent"
if compgen -G "data/persistent/*.json" > /dev/null; then
  cp data/persistent/*.json "$ART_DIR/persistent/" || true
else
  echo "ℹ no data/persistent/*.json found"
fi

# ---------- Zip (with Python fallback) ----------
ZIP_NAME="next_artifacts.zip"
if have_cmd zip; then
  (cd "$ART_DIR" && zip -qr "../$ZIP_NAME" .)
else
  echo "▶ zip not found; using Python zipfile"
  python - "$ART_DIR" "$ZIP_NAME" <<'PY'
import sys, os, zipfile
src, out = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(src):
        for f in files:
            p = os.path.join(root, f)
            z.write(p, os.path.relpath(p, src))
print(out)
PY
fi

echo "✅ Done. Bundle: $ZIP_NAME"
echo "   Folder: $ART_DIR"
