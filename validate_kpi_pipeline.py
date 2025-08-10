
#!/usr/bin/env python3
import requests, time, sys, json

BASE="http://localhost:5000"
def must(ok, msg): 
    print(("✅" if ok else "❌"), msg)
    if not ok: sys.exit(1)

def main():
    print("🚀 KPI Pipeline Validation")
    r = requests.get(f"{BASE}/api/kpi/metrics"); must(r.status_code==200, "GET /api/kpi/metrics returns 200")
    data1 = r.json()
    must("timeframes" in data1, "timeframes key present")
    for tf in ["All","3D","5D","10D","15D","30D"]:
        must(tf in data1["timeframes"], f"{tf} present")
        sec = data1["timeframes"][tf]
        for grp in ["prediction_kpis","financial_kpis","risk_kpis"]:
            must(grp in sec, f"{tf}.{grp} present")

    t1 = data1.get("last_updated_utc")
    r2 = requests.post(f"{BASE}/api/kpi/recompute"); must(r2.status_code==200, "POST /api/kpi/recompute returns 200")
    data2 = r2.json()
    t2 = data2.get("last_updated_utc")
    must(t1 != t2, "Recompute updates timestamp")

    ks = data2.get("kill_switch", {})
    must("active" in ks and "reasons" in ks, "kill_switch structure present")

    print("\n🎉 KPI pipeline validation PASSED")
if __name__ == "__main__":
    main()
