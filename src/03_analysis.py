"""Step 3: analysis. Reads the SQLite database, computes every number used in the write-up, and saves it to
outputs/key_numbers.json so nothing in the README, brief or dashboard is typed by hand.

Outputs:
  outputs/key_numbers.json
  outputs/tables/*.csv  (additional)
"""
import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
con = sqlite3.connect(ROOT / "data" / "autocredit.db")

panel = pd.read_sql("SELECT * FROM v_auto_panel_wow ORDER BY year, quarter", con)
panel["qlabel"] = panel["year"].astype(str) + "Q" + panel["quarter"].astype(str)
panel["date"] = pd.to_datetime(panel["period_end"])
panel = panel.set_index("date")
K = {}  # key numbers

last = panel.iloc[-1]
K["latest_quarter"] = last["qlabel"]

# ---------------------------------------------------------------------------------------------
# 1. Headline levels
# ---------------------------------------------------------------------------------------------
K["stock90_latest"] = float(last.stock90)
K["stock90_peak"] = float(panel.stock90.max())
K["stock90_peak_quarter"] = panel.stock90.idxmax().strftime("%Y-Q") + str(panel.stock90.idxmax().quarter)
K["stock90_2010_peak"] = float(panel.loc["2009":"2012", "stock90"].max())
K["flow90_latest"] = float(last.flow90)
K["flow90_gfc_peak"] = float(panel.loc["2007":"2011", "flow90"].max())
K["flow90_gfc_peak_quarter"] = panel.loc["2007":"2011", "flow90"].idxmax().strftime("%Y-%m")
K["flow90_2019_avg"] = float(panel.loc["2019", "flow90"].mean())
K["flow90_trough"] = float(panel.loc["2020":, "flow90"].min())
K["flow90_trough_quarter"] = panel.loc["2020":, "flow90"].idxmin().strftime("%Y-%m")
K["flow90_vs_2019_pct"] = float(100 * (last.flow90 / K["flow90_2019_avg"] - 1))
K["flow90_vs_trough_pct"] = float(100 * (last.flow90 / K["flow90_trough"] - 1))
K["unemployment_latest"] = float(last.unemployment)
K["seriously_delinquent_bn_latest"] = float(last.seriously_delinquent_bn)
K["seriously_delinquent_bn_2019q4"] = float(panel.loc["2019-12-31", "seriously_delinquent_bn"])
K["auto_balance_tn_latest"] = float(last.auto_bal_tn)
K["auto_balance_tn_2019q4"] = float(panel.loc["2019-12-31", "auto_bal_tn"])

# ---------------------------------------------------------------------------------------------
# 2. Stock = inflow x persistence: log decomposition over several start windows
# ---------------------------------------------------------------------------------------------
decomp = []
for start in ["2021-12-31", "2022-12-31", "2023-12-31", "2024-06-30", "2025-06-30"]:
    a, b = panel.loc[start], panel.iloc[-1]
    d_stock = np.log(b.stock90 / a.stock90)
    d_flow = np.log(b.flow90 / a.flow90)
    d_pers = np.log(b.persistence_index / a.persistence_index)
    decomp.append(dict(start=a.qlabel, stock_start=a.stock90, stock_end=b.stock90, flow_start=a.flow90, flow_end=b.flow90,
                       persistence_start=a.persistence_index, persistence_end=b.persistence_index,
                       dlog_stock=100 * d_stock, share_inflow=100 * d_flow / d_stock, share_persistence=100 * d_pers / d_stock))
decomp = pd.DataFrame(decomp)
decomp.to_csv(OUT / "tables" / "decomposition_windows.csv", index=False)
K["decomposition"] = decomp.round(2).to_dict("records")
K["persistence_latest"] = float(last.persistence_index)
K["persistence_2019"] = float(panel.loc["2019", "persistence_index"].mean())
K["persistence_pre_gfc_2005_2007"] = float(panel.loc["2005":"2007", "persistence_index"].mean())
K["persistence_2024q2"] = float(panel.loc["2024-06-30", "persistence_index"])
K["persistence_trough"] = float(panel.loc["2022":, "persistence_index"].min())
K["persistence_trough_quarter"] = panel.loc["2022":, "persistence_index"].idxmin().strftime("%Y-%m")
K["persistence_2021q4"] = float(panel.loc["2021-12-31", "persistence_index"])
K["stock_if_2019_persistence"] = float(last.flow90 * K["persistence_2019"])

# ---------------------------------------------------------------------------------------------
# 3. Early-stage roll rate (30+ to 90+)
# ---------------------------------------------------------------------------------------------
K["roll_latest"] = float(last.roll_rate_30_to_90)
K["roll_max"] = float(panel.roll_rate_30_to_90.max())
K["roll_max_quarter"] = panel.roll_rate_30_to_90.idxmax().strftime("%Y-%m")
K["roll_rank_of_latest"] = int(last.roll_rate_rank_high)
K["roll_n_quarters"] = int(panel.roll_rate_30_to_90.notna().sum())
K["roll_gfc_peak"] = float(panel.loc["2007":"2011", "roll_rate_30_to_90"].max())
K["roll_2005_avg"] = float(panel.loc["2005", "roll_rate_30_to_90"].mean())
K["roll_2019_avg"] = float(panel.loc["2019", "roll_rate_30_to_90"].mean())
K["flow30_latest"] = float(last.flow30)
K["flow30_gfc_peak"] = float(panel.loc["2007":"2011", "flow30"].max())
K["flow30_2019_avg"] = float(panel.loc["2019", "flow30"].mean())
# What one point of roll rate is worth, in balances (industry level; current balances approx = auto balance x (1 - stock90/100))
current_bal_bn = last.auto_bal_tn * 1000 * (1 - last.stock90 / 100)
K["current_balance_bn_approx"] = float(current_bal_bn)
K["bn_per_roll_point"] = float(last.flow30 / 100 * current_bal_bn * 0.01)  # one point (0.01) of roll rate
K["bn_if_roll_at_gfc_peak"] = float((last.roll_rate_30_to_90 - K["roll_gfc_peak"]) * last.flow30 / 100 * current_bal_bn)
K["bn_if_roll_at_2019"] = float((last.roll_rate_30_to_90 - K["roll_2019_avg"]) * last.flow30 / 100 * current_bal_bn)

# ---------------------------------------------------------------------------------------------
# 4. Breadth by age and origination mix
# ---------------------------------------------------------------------------------------------
age = pd.read_sql("SELECT * FROM v_age_breadth", con)
age = age[age.age_band != "all"]
age.to_csv(OUT / "tables" / "age_breadth.csv", index=False)
K["age_pct_vs_2019_min"] = float(age.pct_vs_2019.min())
K["age_pct_vs_2019_max"] = float(age.pct_vs_2019.max())
K["age_all_pct_vs_2019"] = float(pd.read_sql("SELECT pct_vs_2019 FROM v_age_breadth WHERE age_band='all'", con).iloc[0, 0])
K["age_pct_vs_trough_min"] = float(age.pct_vs_trough.min())
K["age_pct_vs_trough_max"] = float(age.pct_vs_trough.max())
K["subprime_share_latest"] = float(last.subprime_orig_share_pct)
K["subprime_share_2006_avg"] = float(panel.loc["2006", "subprime_orig_share_pct"].mean())
K["subprime_share_min"] = float(panel.subprime_orig_share_pct.min())
K["subprime_share_min_quarter"] = panel.subprime_orig_share_pct.idxmin().strftime("%Y-%m")
K["subprime_share_2019_avg"] = float(panel.loc["2019", "subprime_orig_share_pct"].mean())
K["orig_median_score_latest"] = float(last.orig_median_score)
K["orig_total_bn_latest"] = float(last.orig_total_bn)
K["orig_total_bn_2019_avg_quarter"] = float(panel.loc["2019", "orig_total_bn"].mean())

# ---------------------------------------------------------------------------------------------
# 5. Used-vehicle prices and remarketing sensitivity
# ---------------------------------------------------------------------------------------------
fred = pd.read_sql("SELECT * FROM fred_monthly", con, parse_dates=["month"]).set_index("month")
used = fred.cpi_used_vehicles
K["used_cpi_peak"] = float(used.max())
K["used_cpi_peak_month"] = used.idxmax().strftime("%Y-%m")
K["used_cpi_latest"] = float(used.iloc[-1])
K["used_cpi_latest_month"] = used.index[-1].strftime("%Y-%m")
K["used_cpi_pct_below_peak"] = float(100 * (used.iloc[-1] / used.max() - 1))
K["used_cpi_2019_avg"] = float(used.loc["2019"].mean())
K["used_cpi_vs_2019_pct"] = float(100 * (used.iloc[-1] / used.loc["2019"].mean() - 1))
K["new_cpi_vs_2019_pct"] = float(100 * (fred.cpi_new_vehicles.iloc[-1] / fred.cpi_new_vehicles.loc["2019"].mean() - 1))
K["all_items_cpi_vs_2019_pct"] = float(100 * (fred.cpi_all_items.dropna().iloc[-1] / fred.cpi_all_items.loc["2019"].mean() - 1))
K["fed_funds_latest"] = float(fred.fed_funds_rate.iloc[-1])
K["auto_rate_latest"] = float(fred.auto_loan_rate_48m_new.dropna().iloc[-1])
K["auto_rate_latest_month"] = fred.auto_loan_rate_48m_new.dropna().index[-1].strftime("%Y-%m")
K["auto_rate_2019_avg"] = float(fred.auto_loan_rate_48m_new.loc["2019"].dropna().mean())

vint = pd.read_sql("SELECT * FROM v_vintage_price_ratio", con)
vint.to_csv(OUT / "tables" / "vintage_price_ratio.csv", index=False)
K["vintage_price"] = vint.round(1).to_dict("records")

# Remarketing sensitivity: seriously delinquent balance x share of those balances that end in repossession and sale x used-price move.
# The repossession share is NOT in the public data; it is a scenario axis, not an estimate.
sd = float(last.seriously_delinquent_bn)
grid = []
for repo in [0.25, 0.50, 0.75]:
    for drop in [0.05, 0.10, 0.15]:
        grid.append(dict(repo_share=repo, used_price_drop=drop, collateral_value_hit_bn=sd * repo * drop))
grid = pd.DataFrame(grid)
grid.to_csv(OUT / "tables" / "remarketing_sensitivity.csv", index=False)
K["bn_per_1pct_used_price_on_all_delinquent"] = sd * 0.01
K["sensitivity_grid"] = grid.round(2).to_dict("records")
K["used_price_drop_since_peak_pct"] = K["used_cpi_pct_below_peak"]

# ---------------------------------------------------------------------------------------------
# 6. Does unemployment explain it?
# ---------------------------------------------------------------------------------------------
pre = panel.loc["2003":"2019"].dropna(subset=["unemployment"])
post = panel.loc["2022":].dropna(subset=["unemployment"])
K["corr_flow_unemp_2003_2019"] = float(pre.flow90.corr(pre.unemployment))
K["corr_stock_unemp_2003_2019"] = float(pre.stock90.corr(pre.unemployment))
K["corr_flow_unemp_2022_now"] = float(post.flow90.corr(post.unemployment))
K["unemp_2022_avg"] = float(panel.loc["2022", "unemployment"].mean())
K["unemp_gfc_peak"] = float(panel.loc["2008":"2011", "unemployment"].max())
K["flow_when_unemp_gfc_peak"] = float(panel.loc[panel.loc["2008":"2011", "unemployment"].idxmax(), "flow90"])

# ---------------------------------------------------------------------------------------------
# 7. Forecast test: can public aggregates beat 'same as now' four quarters ahead?
# ---------------------------------------------------------------------------------------------
X = panel.copy()
X["d_unemp4"] = X.unemployment.diff(4)
X["d_ff4"] = X.fed_funds.diff(4)
X["used_chg8"] = X.cpi_used.pct_change(8) * 100
X["y"] = X.flow90.shift(-4)
need = ["y", "flow90", "flow30", "unemployment", "d_unemp4", "d_ff4", "used_chg8", "subprime_orig_share_pct"]
D = X.dropna(subset=need)
sets = {
    "Same as now (naive)": None,
    "Ridge: inflow only": ["flow90"],
    "Ridge: + early-stage inflow": ["flow90", "flow30"],
    "Ridge: + unemployment, rates": ["flow90", "flow30", "unemployment", "d_unemp4", "d_ff4"],
    "Ridge: + used prices, mix": ["flow90", "flow30", "unemployment", "d_unemp4", "d_ff4", "used_chg8", "subprime_orig_share_pct"],
}
test_idx = [i for i in range(len(D)) if D.index[i] >= pd.Timestamp("2013-12-31")]
fc = []
for name, cols in sets.items():
    errs = []
    for i in test_idx:
        tr = D.iloc[: i - 3]  # only forecast targets already observed at the forecast origin
        te = D.iloc[[i]]
        if cols is None:
            p = float(te.flow90.iloc[0])
        else:
            m = make_pipeline(StandardScaler(), Ridge(alpha=1.0)).fit(tr[cols], tr.y)
            p = float(m.predict(te[cols])[0])
        errs.append(abs(p - float(te.y.iloc[0])))
    fc.append(dict(model=name, mae_points=float(np.mean(errs)), n_forecasts=len(errs)))
fc = pd.DataFrame(fc)
base = fc.loc[0, "mae_points"]
fc["vs_naive_pct"] = 100 * (fc.mae_points / base - 1)
fc.to_csv(OUT / "tables" / "forecast_evaluation.csv", index=False)
K["forecast_eval"] = fc.round(3).to_dict("records")
K["forecast_window"] = f"origins {D.index[test_idx[0]].strftime('%Y-%m')} to {D.index[test_idx[-1]].strftime('%Y-%m')}"

# ---------------------------------------------------------------------------------------------
# 8. Collections-reporting caveat
# ---------------------------------------------------------------------------------------------
K["pct_with_collection_latest"] = float(last.pct_with_collection)
K["pct_with_collection_peak"] = float(panel.pct_with_collection.max())
K["pct_with_collection_peak_quarter"] = panel.pct_with_collection.idxmax().strftime("%Y-%m")
K["avg_collection_usd_latest"] = float(last.avg_collection_usd)

# save the panel for the dashboard and Power BI
panel.reset_index().to_csv(OUT / "tables" / "auto_panel_quarterly.csv", index=False)
json.dump(K, open(OUT / "key_numbers.json", "w"), indent=2, default=float)
for k, v in K.items():
    if not isinstance(v, (list, dict)):
        print(f"{k:42s} {round(v, 3) if isinstance(v, float) else v}")
print(decomp.round(2).to_string(index=False))
print(fc.round(3).to_string(index=False))
print(age.to_string(index=False))
print(vint.to_string(index=False))
