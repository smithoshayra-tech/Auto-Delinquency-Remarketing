"""Step 1: parse the raw public files into tidy tables and write a cleaning log.

Inputs (data/raw):
  nyfed_hhdc_2026q2_workbook_as_markdown.md   NY Fed Household Debt and Credit workbook, 2026 Q2 release
  fred_macro_vehicle_raw.csv                  FRED series (St. Louis Fed), one wide CSV

Outputs (data/clean):
  nyfed_long.csv      one row per (sheet, series, quarter)
  fred_monthly.csv    one row per month, 1999-01 onward
  cleaning_log.csv    every transformation, with the number of cells or rows it touched
"""
import csv
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CLEAN = ROOT / "data" / "clean"
CLEAN.mkdir(parents=True, exist_ok=True)

LOG = []


def log(step, source, issue, action, n):
    LOG.append(dict(step=step, source=source, issue=issue, action=action, cells_or_rows=n))


# --------------------------------------------------------------------------------------
# NY Fed workbook
# --------------------------------------------------------------------------------------
# sheet -> (series group name, column names in order, unit)
SHEETS = {
    "Page 3 Data":  ("debt_balance", ["mortgage", "heloc", "auto", "credit_card", "student", "other", "total"], "trillions_usd"),
    "Page 8 Data":  ("auto_orig_by_score", ["lt620", "s620_659", "s660_719", "s720_759", "s760_plus", "_blank", "total"], "billions_usd"),
    "Page 9 Data":  ("auto_orig_score_dist", ["median", "p25", "p10"], "equifax_riskscore"),
    "Page 11 Data": ("balance_by_status_all_debt", ["current", "late30", "late60", "late90", "late120", "sev_derog", "total"], "pct_of_balance"),
    "Page 12 Data": ("pct_balance_90plus", ["mortgage", "heloc", "auto", "credit_card", "student", "other", "all"], "pct"),
    "Page 13 Data": ("flow_into_30plus", ["auto", "credit_card", "mortgage", "heloc", "student", "other", "all"], "pct_annualized"),
    "Page 14 Data": ("flow_into_90plus", ["auto", "credit_card", "mortgage", "heloc", "student", "other", "all"], "pct_annualized"),
    "Page 18 Data": ("third_party_collections", ["pct_consumers_with_collection", "avg_collection_usd"], "mixed"),
    "Page 22 Data": ("auto_orig_by_age", ["a18_29", "a30_39", "a40_49", "a50_59", "a60_69", "a70_plus"], "billions_usd"),
    "Page 26 Data": ("auto_flow_90plus_by_age_4q", ["a18_29", "a30_39", "a40_49", "a50_59", "a60_69", "a70_plus", "all"], "pct_4q_moving_sum"),
}

md = (RAW / "nyfed_hhdc_2026q2_workbook_as_markdown.md").read_text()
sections = {s.split("\n", 1)[0]: s for s in re.split(r"(?m)^## ", md)}

rows = []
for sheet, (group, cols, unit) in SHEETS.items():
    n_data = n_blank = n_comma = n_footer = 0
    for line in sections[sheet].split("\n"):
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        m = re.fullmatch(r"(\d\d):Q([1-4])", cells[0])
        if not m:
            if cells[0].startswith("*") or cells[0].lower().startswith("note"):
                n_footer += 1
            continue
        n_data += 1
        yy, q = int(m.group(1)), int(m.group(2))
        year = 1900 + yy if yy >= 90 else 2000 + yy  # 99:Q2 -> 1999, 00:Q1 -> 2000
        for name, raw in zip(cols, cells[1:1 + len(cols)]):
            if name == "_blank":
                continue
            if raw == "":
                n_blank += 1
                continue
            if "," in raw:
                n_comma += 1
                raw = raw.replace(",", "")
            rows.append(dict(sheet=sheet.replace(" Data", ""), series_group=group, series=name,
                             year=year, quarter=q, value=float(raw), unit=unit))
    log("parse", f"NY Fed {sheet}", "two-digit year labels like 03:Q1 and 99:Q2", "converted to calendar year and quarter", n_data)
    if n_blank:
        log("parse", f"NY Fed {sheet}", "empty cells (series not yet reported)", "left as missing, not zero-filled", n_blank)
    if n_comma:
        log("parse", f"NY Fed {sheet}", "thousands separators in numbers", "removed commas, cast to float", n_comma)
    if n_footer:
        log("parse", f"NY Fed {sheet}", "footnote rows inside the table", "dropped", n_footer)

nyfed = pd.DataFrame(rows)
nyfed["period_end"] = (pd.to_datetime(nyfed["year"].astype(str) + "-" + (nyfed["quarter"] * 3).astype(str).str.zfill(2) + "-01") + pd.offsets.MonthEnd(0)).dt.strftime("%Y-%m-%d")
nyfed.to_csv(CLEAN / "nyfed_long.csv", index=False)

# --------------------------------------------------------------------------------------
# FRED wide CSV
# --------------------------------------------------------------------------------------
fred_raw = pd.read_csv(RAW / "fred_macro_vehicle_raw.csv")
fred_raw = fred_raw.rename(columns={
    "observation_date": "month",
    "CUSR0000SETA02": "cpi_used_vehicles",
    "CUSR0000SETA01": "cpi_new_vehicles",
    "UNRATE": "unemployment_rate",
    "CPIAUCSL": "cpi_all_items",
    "TOTALSA": "vehicle_sales_saar_mil",
    "FEDFUNDS": "fed_funds_rate",
    "UMCSENT": "consumer_sentiment",
    "TERMCBAUTO48NS": "auto_loan_rate_48m_new",
})
n0 = len(fred_raw)
fred = fred_raw[fred_raw["month"] >= "1999-01-01"].copy()
log("filter", "FRED", "series start in 1947; NY Fed panel starts in 1999 (originations) and 2003 (delinquency)",
    "kept 1999-01 onward", n0 - len(fred))
log("parse", "FRED", "mixed frequencies in one wide file: the auto loan rate is quarterly, the rest monthly",
    "kept the quarterly rate only in its reported months, no interpolation",
    int(fred["auto_loan_rate_48m_new"].isna().sum()))
fred.to_csv(CLEAN / "fred_monthly.csv", index=False)

pd.DataFrame(LOG).to_csv(CLEAN / "cleaning_log_step1_parse.csv", index=False)
print("NY Fed rows:", len(nyfed), "| FRED months:", len(fred))
print(pd.DataFrame(LOG).to_string(index=False))
