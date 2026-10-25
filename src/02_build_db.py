"""Step 2: load tidy files into SQLite, run the SQL validation suite, and export analysis tables.

Outputs:
  data/autocredit.db                      SQLite database
  outputs/validation_report.csv           one row per check, pass/fail with detail
  outputs/tables/*.csv                    analysis views, ready for Power BI
"""
import re
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "autocredit.db"
OUT = ROOT / "outputs"
(OUT / "tables").mkdir(parents=True, exist_ok=True)

if DB.exists():
    DB.unlink()
con = sqlite3.connect(DB)
con.executescript((ROOT / "sql" / "01_schema.sql").read_text())

nyfed = pd.read_csv(ROOT / "data/clean/nyfed_long.csv")
nyfed[["sheet", "series_group", "series", "year", "quarter", "value", "unit", "period_end"]].to_sql(
    "nyfed_long", con, if_exists="append", index=False)
fred = pd.read_csv(ROOT / "data/clean/fred_monthly.csv")
fred.to_sql("fred_monthly", con, if_exists="append", index=False)

# ---- validation suite --------------------------------------------------------------
text = (ROOT / "sql" / "02_validation.sql").read_text()
blocks = re.split(r"(?m)^-- check: ", text)[1:]
rows = []
for b in blocks:
    header, sql = b.split("\n", 1)
    name, what = [x.strip() for x in header.split("|", 1)]
    sql = "\n".join(l for l in sql.split("\n") if not l.startswith("--"))
    off, detail = con.execute(sql).fetchone()
    rows.append(dict(check=name, proves=what, offending_rows=off, detail=detail, status="PASS" if off == 0 else "FAIL"))
val = pd.DataFrame(rows)
val.to_csv(OUT / "validation_report.csv", index=False)
print(val[["check", "status", "offending_rows", "detail"]].to_string(index=False))
print(f"\n{(val.status=='PASS').sum()} of {len(val)} checks passed")

# ---- analysis views ----------------------------------------------------------------
con.executescript((ROOT / "sql" / "03_analysis.sql").read_text())
for v in ["v_auto_panel_wow", "v_decomp_to_latest", "v_age_breadth", "v_vintage_price_ratio"]:
    pd.read_sql(f"SELECT * FROM {v}", con).to_csv(OUT / "tables" / f"{v}.csv", index=False)
con.commit()
con.close()
