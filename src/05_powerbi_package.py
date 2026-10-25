"""Step 5: Power BI-ready star schema (CSV) + DAX measures + external cross-check table."""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "outputs" / "tables"
PB = ROOT / "powerbi"
PB.mkdir(exist_ok=True)
K = json.load(open(ROOT / "outputs" / "key_numbers.json"))

p = pd.read_csv(T / "auto_panel_quarterly.csv", parse_dates=["date"])
p["period_end"] = p["date"].dt.strftime("%Y-%m-%d")
keep = ["period_end", "qlabel", "year", "quarter", "stock90", "flow90", "flow30", "roll_rate_30_to_90", "persistence_index",
        "auto_bal_tn", "seriously_delinquent_bn", "orig_total_bn", "subprime_orig_share_pct", "orig_median_score",
        "cpi_used", "unemployment", "fed_funds", "auto_rate_48m", "pct_with_collection", "avg_collection_usd"]
p[keep].to_csv(PB / "fact_quarterly.csv", index=False)

d = p[["period_end", "qlabel", "year", "quarter"]].copy()
d["era"] = pd.cut(d.year, [2002, 2007, 2012, 2019, 2021, 2100], labels=["2003-2007 pre-crisis", "2008-2012 crisis and recovery", "2013-2019 expansion", "2020-2021 pandemic", "2022 onward"]).astype(str)
d.to_csv(PB / "dim_date.csv", index=False)
pd.read_csv(T / "age_breadth.csv").to_csv(PB / "fact_age_breadth.csv", index=False)
pd.read_csv(T / "vintage_price_ratio.csv").to_csv(PB / "fact_vintage_price.csv", index=False)
pd.read_csv(T / "remarketing_sensitivity.csv").to_csv(PB / "fact_remarketing_sensitivity.csv", index=False)
pd.read_csv(T / "decomposition_windows.csv").to_csv(PB / "fact_decomposition.csv", index=False)
pd.read_csv(T / "forecast_evaluation.csv").to_csv(PB / "fact_forecast_eval.csv", index=False)

dax = """// Measures for the auto-delinquency model. Relationship: dim_date[period_end] 1:* fact_quarterly[period_end]. Mark dim_date as the date table.
Latest Quarter = MAX ( fact_quarterly[period_end] )

Stock 90+ % = CALCULATE ( MAX ( fact_quarterly[stock90] ), fact_quarterly[period_end] = [Latest Quarter] )

Inflow 90+ % = CALCULATE ( MAX ( fact_quarterly[flow90] ), fact_quarterly[period_end] = [Latest Quarter] )

Roll Rate 30 to 90 =
DIVIDE ( SUM ( fact_quarterly[flow90] ), SUM ( fact_quarterly[flow30] ) )   // use on a single quarter; do not sum across quarters

Persistence Years =
DIVIDE ( SUM ( fact_quarterly[stock90] ), SUM ( fact_quarterly[flow90] ) )   // single quarter only

Inflow vs 2019 % =
VAR cur = [Inflow 90+ %]
VAR base = CALCULATE ( AVERAGE ( fact_quarterly[flow90] ), dim_date[year] = 2019 )
RETURN DIVIDE ( cur - base, base )

Seriously Delinquent $B = CALCULATE ( MAX ( fact_quarterly[seriously_delinquent_bn] ), fact_quarterly[period_end] = [Latest Quarter] )

Roll Rate Rank (high = 1) =
RANKX ( ALL ( fact_quarterly[period_end] ), CALCULATE ( [Roll Rate 30 to 90] ), , DESC )

Annual $B Reaching 90+ per Roll Point =   // approximate: annualized 30+ inflow x current balance x 1%
VAR bal = MAX ( fact_quarterly[auto_bal_tn] ) * 1000 * ( 1 - [Stock 90+ %] / 100 )
RETURN SUM ( fact_quarterly[flow30] ) / 100 * bal * 0.01

// Scenario table: fact_remarketing_sensitivity is a parameter grid, not a forecast.
Collateral Value Hit $B = SUM ( fact_remarketing_sensitivity[collateral_value_hit_bn] )
"""
(PB / "measures.dax").write_text(dax)

xc = pd.DataFrame([
    dict(metric="Auto flow into 90+ (annualized %), 2026Q2", our_value=K["flow90_latest"], published_value=3.00, source="NY Fed press release 2026-08-11", url="https://www.newyorkfed.org/newsevents/news/research/2026/20260811"),
    dict(metric="Auto flow into 90+ (annualized %), 2025Q2", our_value=float(p.loc[p.qlabel == "2025Q2", "flow90"].iloc[0]), published_value=2.93, source="NY Fed press release 2026-08-11", url="https://www.newyorkfed.org/newsevents/news/research/2026/20260811"),
    dict(metric="Auto loan balance, $T, 2026Q2", our_value=K["auto_balance_tn_latest"], published_value=1.71, source="NY Fed HHDC landing page", url="https://www.newyorkfed.org/microeconomics/hhdc"),
    dict(metric="Auto originations, $B, 2026Q2", our_value=K["orig_total_bn_latest"], published_value=211, source="NY Fed HHDC 2026Q2 report", url="https://www.newyorkfed.org/medialibrary/interactives/householdcredit/data/pdf/hhdc_2026q2.pdf"),
])
xc["abs_diff"] = (xc.our_value - xc.published_value).abs().round(3)
xc["status"] = ["MATCH" if d < 0.6 else "CHECK" for d in xc.abs_diff]
xc.to_csv(ROOT / "outputs" / "tables" / "external_crosscheck.csv", index=False)
print(xc.to_string(index=False))
