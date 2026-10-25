"""Step 4: static figures (PNG, 200 dpi) from the analysis tables. Insight titles, direct labels, one axis per chart.
Palette (validated for light surface): blue #2a78d6, orange #eb6834, aqua #1baf7a (aqua used only with direct labels)."""
import json
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "outputs" / "tables"
FIG = ROOT / "outputs" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
K = json.load(open(ROOT / "outputs" / "key_numbers.json"))
P = pd.read_csv(T / "auto_panel_quarterly.csv", parse_dates=["date"]).set_index("date")

BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID, SURF = "#1a1a19", "#6b6b68", "#e6e6e3", "#fcfcfb"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.facecolor": SURF, "figure.facecolor": SURF,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.axisbelow": True, "text.color": INK,
})
SRC = "Source: NY Fed Household Debt and Credit Report (2026 Q2), FRED. Analysis: S. Smith."


def frame(title, sub=None, w=9.5, h=5.2):
    fig, ax = plt.subplots(figsize=(w, h))
    lines = textwrap.wrap(title, 68)
    fig.text(0.09, 0.96, "\n".join(lines), fontsize=13.5, fontweight="bold", ha="left", va="top", linespacing=1.25)
    sub_y = 0.96 - 0.058 * len(lines) - 0.01
    if sub:
        sub = "\n".join(textwrap.wrap(sub, 105))
        fig.text(0.09, sub_y, sub, fontsize=9.5, color=MUTED, ha="left", va="top")
        sub_y -= 0.045 * (sub.count("\n") + 1)
    fig.subplots_adjust(top=sub_y - 0.03, bottom=0.17, left=0.09, right=0.95)
    fig.text(0.09, 0.025, SRC, fontsize=7.5, color=MUTED, ha="left")
    return fig, ax


def save(fig, name):
    fig.savefig(FIG / name, dpi=200)
    plt.close(fig)


# 1. stock vs inflow, two stacked panels (not dual axis)
fig, axs = plt.subplots(2, 1, figsize=(9.5, 6.4), sharex=True)
fig.subplots_adjust(top=0.83, bottom=0.1, left=0.09, right=0.95, hspace=0.18)
fig.text(0.09, 0.97, "The share of auto balances 90+ days late is at a record,\nbut the rate of new serious delinquencies is still below 2009", fontsize=13.5, fontweight="bold", va="top", linespacing=1.25)
fig.text(0.09, 0.885, "Top: stock (% of balance seriously delinquent). Bottom: annualized flow of balances newly 90+ late.", fontsize=9.5, color=MUTED, va="top")
axs[0].plot(P.index, P.stock90, color=BLUE, lw=2)
axs[0].set_ylabel("% of auto balance 90+")
axs[0].annotate(f"{K['stock90_peak']:.2f}% ({K['stock90_peak_quarter'][:4]}Q1)\nrecord", (P.stock90.idxmax(), P.stock90.max()), xytext=(-70, -4), textcoords="offset points", fontsize=9, color=INK, ha="right",
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
axs[0].annotate(f"{K['stock90_2010_peak']:.2f}% in 2010", (P.loc["2009":"2012", "stock90"].idxmax(), K["stock90_2010_peak"]), xytext=(8, 8), textcoords="offset points", fontsize=9)
axs[1].plot(P.index, P.flow90, color=ORANGE, lw=2)
axs[1].set_ylabel("% annualized")
g = P.loc["2007":"2011", "flow90"].idxmax()
axs[1].annotate(f"GFC peak {K['flow90_gfc_peak']:.2f}%", (g, K["flow90_gfc_peak"]), xytext=(8, 2), textcoords="offset points", fontsize=9)
axs[1].annotate(f"{K['flow90_latest']:.2f}% now\n+{K['flow90_vs_2019_pct']:.0f}% vs 2019", (P.index[-1], K["flow90_latest"]), xytext=(-14, -52), textcoords="offset points", fontsize=9, ha="right", arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
t = P.loc["2020":, "flow90"].idxmin()
axs[1].annotate(f"{K['flow90_trough']:.2f}% trough", (t, K["flow90_trough"]), xytext=(46, -4), textcoords="offset points", fontsize=9, ha="left", va="center", arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
fig.text(0.09, 0.015, SRC, fontsize=7.5, color=MUTED)
save(fig, "fig01_stock_vs_flow.png")

# 2. decomposition vs 2019 (levels) and recent windows
d = pd.read_csv(T / "decomposition_windows.csv")
d["inflow_pts"] = d.dlog_stock * d.share_inflow / 100
d["persist_pts"] = d.dlog_stock * d.share_persistence / 100
fig, ax = frame("Since mid-2024 the climb is mostly loans staying bad longer; before that it was more new problems",
                "Change in log stock of 90+ balances to 2026Q2, split into inflow and persistence (points of log change x100)", h=5.0)
x = np.arange(len(d))
w = 0.36
ax.bar(x - w / 2, d.inflow_pts, w, color=ORANGE, label="New 90+ inflow")
ax.bar(x + w / 2, d.persist_pts, w, color=BLUE, label="Persistence (time in 90+)")
for i, r in d.iterrows():
    ax.text(i - w / 2, r.inflow_pts + (1.5 if r.inflow_pts >= 0 else -4), f"{r.inflow_pts:.0f}", ha="center", fontsize=9)
    ax.text(i + w / 2, r.persist_pts + (1.5 if r.persist_pts >= 0 else -4), f"{r.persist_pts:.0f}", ha="center", fontsize=9)
ax.set_xticks(x)
ax.set_xticklabels([f"from {s}" for s in d.start])
ax.axhline(0, color=MUTED, lw=0.8)
ax.legend(frameon=False, loc="upper right")
ax.set_ylabel("log points x100")
save(fig, "fig02_decomposition.png")

# 3. persistence
fig, ax = frame("Time spent in serious delinquency fell to a 2024 low, then rebuilt", "Persistence index = stock of 90+ balance divided by annualized inflow (years). Steady-state approximation.")
s = P.persistence_index.dropna()
ax.plot(s.index, s, color=BLUE, lw=2)
ax.axhline(K["persistence_2019"], color=MUTED, ls=(0, (4, 3)), lw=1)
ax.text(s.index[2], K["persistence_2019"] + 0.04, f"2019 average {K['persistence_2019']:.2f}", fontsize=9, color=MUTED)
ax.annotate(f"{K['persistence_latest']:.2f} now", (s.index[-1], s.iloc[-1]), xytext=(-6, 8), textcoords="offset points", fontsize=9, ha="right")
ax.annotate(f"{K['persistence_trough']:.2f} (2024Q2)", (pd.Timestamp("2024-06-30"), K["persistence_trough"]), xytext=(-8, -16), textcoords="offset points", fontsize=9, ha="right")
ax.set_ylabel("years")
save(fig, "fig03_persistence.png")

# 4. roll rate
fig, ax = frame("Nearly 4 in 10 balances that go 30 days late now reach 90+, among the highest in 94 quarters",
                "Roll rate = annualized flow into 90+ divided by flow into 30+ (auto). Proxy for how far early-stage collections fall short.")
r = P.roll_rate_30_to_90.dropna() * 100
ax.plot(r.index, r, color=BLUE, lw=2)
ax.axhline(K["roll_gfc_peak"] * 100, color=MUTED, ls=(0, (4, 3)), lw=1)
ax.text(r.index[1], K["roll_gfc_peak"] * 100 + 0.8, f"2007-11 peak {K['roll_gfc_peak']*100:.0f}%", fontsize=9, color=MUTED)
ax.annotate(f"{K['roll_latest']*100:.1f}% now\n(rank {K['roll_rank_of_latest']} of {K['roll_n_quarters']})", (r.index[-1], r.iloc[-1]), xytext=(-40, -130), textcoords="offset points", fontsize=9, ha="right", arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
ax.set_ylabel("% of 30+ inflow that reaches 90+")
save(fig, "fig04_roll_rate.png")

# 5. age breadth
a = pd.read_csv(T / "age_breadth.csv")
lab = {"a18_29": "18-29", "a30_39": "30-39", "a40_49": "40-49", "a50_59": "50-59", "a60_69": "60-69", "a70_plus": "70+"}
a["lab"] = a.age_band.map(lab)
fig, ax = frame("It is not one cohort: every age band is 21% to 33% above its 2019 level",
                "New 90+ auto balance (4-quarter moving sum), 2026Q2 vs 2019 average", h=4.6)
ax.barh(a.lab[::-1], a.pct_vs_2019[::-1], color=BLUE, height=0.55)
for i, v in enumerate(a.pct_vs_2019[::-1]):
    ax.text(v + 0.5, i, f"+{v:.0f}%", va="center", fontsize=9)
ax.axvline(K["age_all_pct_vs_2019"], color=MUTED, ls=(0, (4, 3)), lw=1)
ax.text(K["age_all_pct_vs_2019"] + 0.4, -0.65, f"all ages +{K['age_all_pct_vs_2019']:.0f}%", fontsize=9, color=MUTED)
ax.set_xlim(0, 40)
ax.grid(axis="y", visible=False)
ax.set_xlabel("% above 2019 average")
save(fig, "fig05_age_breadth.png")

# 6. subprime mix
fig, ax = frame("Credit mix does not explain it: subprime share of new auto loans is well below 2006",
                "Share of auto originations to borrowers scoring under 660", h=4.8)
m = P.subprime_orig_share_pct.dropna()
ax.plot(m.index, m, color=BLUE, lw=2)
ax.annotate(f"{K['subprime_share_2006_avg']:.0f}% (2006 avg)", (pd.Timestamp("2006-06-30"), K["subprime_share_2006_avg"]), xytext=(8, 4), textcoords="offset points", fontsize=9)
ax.annotate(f"{K['subprime_share_latest']:.0f}% now", (m.index[-1], m.iloc[-1]), xytext=(-8, 10), textcoords="offset points", fontsize=9, ha="right")
ax.set_ylabel("% of originations")
save(fig, "fig06_subprime_mix.png")

# 7. vintage price ratio
v = pd.read_csv(T / "vintage_price_ratio.csv")
fig, ax = frame("Used prices now sit below the level at which the 2021-2023 vintages were written",
                "Used-vehicle CPI today vs its average in each origination year. Market price indicator, not a loan-level loss estimate.", h=4.8)
col = [ORANGE if x < 0 else BLUE for x in v.price_change_since_pct]
ax.bar(v.vintage_year.astype(str), v.price_change_since_pct, color=col, width=0.62)
for i, val in enumerate(v.price_change_since_pct):
    ax.text(i, val + (1.2 if val >= 0 else -3.2), f"{val:+.0f}%" if abs(val) >= 0.5 else "0%", ha="center", fontsize=9)
ax.axhline(0, color=MUTED, lw=0.8)
ax.set_ylim(-18, 35)
ax.set_ylabel("% change since vintage year")
ax.text(0.99, 0.04, "orange = prices below origination level", transform=ax.transAxes, ha="right", fontsize=8.5, color=MUTED)
save(fig, "fig07_vintage_prices.png")

# 8. sensitivity heatmap
g = pd.read_csv(T / "remarketing_sensitivity.csv")
piv = g.pivot(index="repo_share", columns="used_price_drop", values="collateral_value_hit_bn").sort_index(ascending=False)
fig, ax = frame("A further 10% fall in used prices costs \\$2B to \\$7B of collateral value across scenarios",
                f"Scenario grid, not a forecast: \\${K['seriously_delinquent_bn_latest']:.0f}B seriously delinquent balance x share ending in repossession x used-price drop", h=4.6)
ax.grid(False)
im = ax.imshow(piv.values, cmap=matplotlib.colors.LinearSegmentedColormap.from_list("b", ["#e8f0fb", BLUE]), aspect="auto")
ax.set_xticks(range(3)); ax.set_xticklabels([f"-{int(c*100)}%" for c in piv.columns])
ax.set_yticks(range(3)); ax.set_yticklabels([f"{int(i*100)}%" for i in piv.index])
for i in range(3):
    for j in range(3):
        ax.text(j, i, f"\\${piv.values[i, j]:.1f}B", ha="center", va="center", fontsize=11, color="white" if piv.values[i, j] > 9 else INK)
ax.set_xlabel("Further drop in used-vehicle prices", labelpad=8)
ax.set_ylabel("Share of 90+ balance repossessed and sold")
for s_ in ax.spines.values():
    s_.set_visible(False)
save(fig, "fig08_remarketing_sensitivity.png")

# 9. forecast evaluation
f = pd.read_csv(T / "forecast_evaluation.csv")
fig, ax = frame("Public aggregates do not beat 'same as now' for forecasting new 90+ inflow",
                f"Mean absolute error, 4 quarters ahead, rolling origin, {K['forecast_window']} (n={int(f.n_forecasts[0])})", h=4.8)
cols = [MUTED if i == 0 else BLUE for i in range(len(f))]
ax.barh(f.model[::-1], f.mae_points[::-1], color=cols[::-1], height=0.55)
for i, (val, pct) in enumerate(zip(f.mae_points[::-1], f.vs_naive_pct[::-1])):
    ax.text(val + 0.006, i, f"{val:.2f} ({pct:+.0f}%)" if pct != 0 else f"{val:.2f} baseline", va="center", fontsize=9)
ax.set_xlim(0, 0.55)
ax.grid(axis="y", visible=False)
ax.set_xlabel("MAE, percentage points of annualized inflow")
fig.subplots_adjust(left=0.30)
save(fig, "fig09_forecast_eval.png")

# 10. decoupling from unemployment
fig, ax = frame("New 90+ inflow is near its 2009 level with unemployment less than half as high",
                "Annualized new 90+ inflow vs unemployment rate, quarterly, 2003 to 2026Q2", h=5.2)
a1 = P.loc["2003":"2019"].dropna(subset=["unemployment"])
a2 = P.loc["2020":"2021"].dropna(subset=["unemployment"])
a3 = P.loc["2022":].dropna(subset=["unemployment"])
ax.scatter(a1.unemployment, a1.flow90, s=26, color=BLUE, label="2003-2019", edgecolor=SURF, linewidth=0.6)
ax.scatter(a2.unemployment, a2.flow90, s=26, color=MUTED, label="2020-2021", edgecolor=SURF, linewidth=0.6)
ax.scatter(a3.unemployment, a3.flow90, s=34, color=ORANGE, label="2022 to 2026Q2", edgecolor=SURF, linewidth=0.6)
ax.annotate("2009: unemployment 9.9%", (K["unemp_gfc_peak"], K["flow_when_unemp_gfc_peak"]), xytext=(10, 22), textcoords="offset points", fontsize=9, ha="left", arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
ax.annotate("2026Q2: 4.3%", (K["unemployment_latest"], K["flow90_latest"]), xytext=(28, 14), textcoords="offset points", fontsize=9, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
ax.set_xlabel("Unemployment rate (%)"); ax.set_ylabel("New 90+ inflow, % annualized")
ax.legend(frameon=False, loc="lower right")
save(fig, "fig10_unemployment_decoupling.png")
print(sorted(p.name for p in FIG.glob("*.png")))
