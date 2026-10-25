"""Independent recompute: re-derive headline numbers with pandas straight from data/clean/*.csv (no SQL) and compare to key_numbers.json."""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
K = json.load(open(ROOT / "outputs" / "key_numbers.json"))
n = pd.read_csv(ROOT / "data/clean/nyfed_long.csv")
w = n.pivot_table(index=["year", "quarter"], columns=["series_group", "series"], values="value")
a = pd.DataFrame({"stock": w[("pct_balance_90plus", "auto")], "f90": w[("flow_into_90plus", "auto")], "f30": w[("flow_into_30plus", "auto")], "bal": w[("debt_balance", "auto")]}).dropna(subset=["stock"])
last = a.iloc[-1]
checks = {
    "stock90_latest": last.stock,
    "flow90_latest": last.f90,
    "roll_latest": last.f90 / last.f30,
    "persistence_latest": last.stock / last.f90,
    "seriously_delinquent_bn_latest": last.bal * 1000 * last.stock / 100,
    "flow90_vs_2019_pct": 100 * (last.f90 / a.loc[2019].f90.mean() - 1),
    "stock90_peak": a.stock.max(),
}
ok = True
for k, v in checks.items():
    good = abs(v - K[k]) < 0.06 if "bn" in k or "pct" in k else abs(v - K[k]) < 0.002
    ok &= good
    print(f"{'PASS' if good else 'FAIL'} {k}: pandas={v:.4f} sql/json={K[k]:.4f}")
assert ok
