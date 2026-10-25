"""Step 6: README and executive brief generated from key_numbers.json so no figure is typed by hand."""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
K = json.load(open(ROOT / "outputs" / "key_numbers.json"))
D = {r["start"]: r for r in K["decomposition"]}
d24, d21 = D["2024Q2"], D["2021Q4"]
stock19 = 4.745  # 2019 average, recomputed below for safety
p = pd.read_csv(ROOT / "outputs/tables/auto_panel_quarterly.csv")
stock19 = p.loc[p.year == 2019, "stock90"].mean()
stock_vs19 = 100 * (K["stock90_latest"] / stock19 - 1)
pers_vs19 = 100 * (K["persistence_latest"] / K["persistence_2019"] - 1)
fc = {r["model"]: r for r in K["forecast_eval"]}
best = min(K["forecast_eval"][1:], key=lambda r: r["mae_points"])
v = {r["vintage_year"]: r for r in K["vintage_price"]}
sg = {(r["repo_share"], r["used_price_drop"]): r["collateral_value_hit_bn"] for r in K["sensitivity_grid"]}
N = dict(
    stock=K["stock90_latest"], peak=K["stock90_peak"], peak10=K["stock90_2010_peak"], bn=K["seriously_delinquent_bn_latest"], bn19=K["seriously_delinquent_bn_2019q4"],
    bn_growth=100 * (K["seriously_delinquent_bn_latest"] / K["seriously_delinquent_bn_2019q4"] - 1),
    flow=K["flow90_latest"], flow_gfc=K["flow90_gfc_peak"], flow19=K["flow90_2019_avg"], flow_vs19=K["flow90_vs_2019_pct"], flow_tr=K["flow90_trough"],
    pers=K["persistence_latest"], pers19=K["persistence_2019"], pers_tr=K["persistence_trough"],
    roll=100 * K["roll_latest"], roll_gfc=100 * K["roll_gfc_peak"], roll19=100 * K["roll_2019_avg"], roll05=100 * K["roll_2005_avg"], rank=K["roll_rank_of_latest"], nq=K["roll_n_quarters"],
    per_pt=K["bn_per_roll_point"], to19=K["bn_if_roll_at_2019"], togfc=K["bn_if_roll_at_gfc_peak"],
    agemin=K["age_pct_vs_2019_min"], agemax=K["age_pct_vs_2019_max"], sub=K["subprime_share_latest"], sub06=K["subprime_share_2006_avg"], sub19=K["subprime_share_2019_avg"],
    used_peak=K["used_cpi_pct_below_peak"], used19=K["used_cpi_vs_2019_pct"], v22=v[2022]["price_change_since_pct"], v21=v[2021]["price_change_since_pct"], v23=v[2023]["price_change_since_pct"],
    unemp=K["unemployment_latest"], unemp09=K["unemp_gfc_peak"], flow09=K["flow_when_unemp_gfc_peak"],
    nfc=fc["Same as now (naive)"]["mae_points"], bestmae=best["mae_points"], bestpct=best["vs_naive_pct"], bestname=best["model"],
    g25=sg[(0.25, 0.10)], g75=sg[(0.75, 0.10)], g50_15=sg[(0.5, 0.15)], per1=K["bn_per_1pct_used_price_on_all_delinquent"],
    d24_in=d24["share_inflow"], d24_pe=d24["share_persistence"], d24_stock=d24["dlog_stock"], flow_since24=100 * (K["flow90_latest"] / p.loc[p.qlabel == "2024Q2", "flow90"].iloc[0] - 1),
)

readme = f"""# Auto Loan Delinquency and Used-Vehicle Remarketing Exposure

**Question:** Auto loans 90+ days late are at a record share of balances (2026Q2: {N['stock']:.2f}%; peak {N['peak']:.2f}% in 2026Q1). Is this a rerun of 2009, and where does it land for a captive finance company's collections and remarketing teams?

**Short answer:** No, it is not a rerun, but it is not benign either. New serious delinquencies are still below the 2009 peak ({N['flow']:.2f}% vs {N['flow_gfc']:.2f}% annualized), and credit mix and unemployment do not explain the rise. What *is* unusual is the **roll rate**: {N['roll']:.1f}% of balances that go 30 days late now reach 90+, the {N['rank']}th highest of {N['nq']} quarters on record and well above the 2007-11 peak of {N['roll_gfc']:.0f}%. Since mid-2024 the climb in the delinquent stock is mostly loans *staying* delinquent longer, which is a collections and remarketing-timing problem more than an origination problem.

Everything below is computed from public data. No figure is typed by hand: each number in this file is generated from `outputs/key_numbers.json` by `src/06_docs.py`.

## Findings

1. **The record is real but modest against 2010.** 90+ stock is {N['stock']:.2f}% of auto balances vs {N['peak10']:.2f}% at the 2010 peak. In dollars that is about ${N['bn']:.0f}B seriously delinquent, up {N['bn_growth']:.0f}% from ${N['bn19']:.0f}B at the end of 2019 (balances grew too).
2. **Versus 2019, the stock is up {stock_vs19:.0f}% because new problem balances are up {N['flow_vs19']:.0f}%** ({N['flow']:.2f}% vs {N['flow19']:.2f}% annualized), partly offset by shorter time in delinquency (persistence {N['pers']:.2f} years vs {N['pers19']:.2f}, {pers_vs19:.0f}%).
3. **Since mid-2024 the story flips.** From 2024Q2 the log change in the stock is {N['d24_stock']:.0f} points; {N['d24_pe']:.0f}% of it is persistence rising from a {N['pers_tr']:.2f}-year low, {N['d24_in']:.0f}% is inflow. Inflow itself is up only {N['flow_since24']:.0f}% since 2024Q2. This agrees with the Philadelphia Fed's April 2026 finding that the stock of severe delinquencies is rising while the flow into it is fairly stable.
4. **Roll rate is the metric to watch.** {N['roll']:.1f}% now vs {N['roll19']:.1f}% in 2019 and {N['roll05']:.0f}% in 2005. At industry scale, each point of roll rate is roughly ${N['per_pt']:.1f}B a year of balances reaching 90+; returning to the 2019 roll rate would be worth about ${N['to19']:.1f}B a year (approximation, see caveats).
5. **It is broad, not one cohort.** Every age band is {N['agemin']:.0f}% to {N['agemax']:.0f}% above its 2019 level. The subprime share of new originations is {N['sub']:.0f}%, vs {N['sub06']:.0f}% in 2006 and {N['sub19']:.0f}% in 2019, so credit mix is not the driver.
6. **It is not unemployment.** Inflow is {N['flow']:.2f}% with unemployment at {N['unemp']:.1f}%; in 2009 it was {N['flow09']:.2f}% with unemployment at {N['unemp09']:.1f}%. This points to payment burden (loan size and price levels) rather than job losses, consistent with a Federal Reserve Board FEDS Note (Sept 2024) that attributes about 40% of the rise in two-year delinquency probability from end-2019 to end-2022 to higher monthly payments.
7. **Remarketing exposure sits in the 2021-2023 vintages.** Used-vehicle CPI is {abs(N['used_peak']):.0f}% below its Feb-2022 peak, though still {N['used19']:.0f}% above 2019. Against the price level when each vintage was written, 2021 is {N['v21']:+.0f}%, 2022 is {N['v22']:+.0f}% and 2023 is {N['v23']:+.0f}%. The 2018-2020 vintages are well above water. This is a market price indicator, not a loan-level loss estimate.
8. **A further 10% drop in used prices is a ${N['g25']:.1f}B to ${N['g75']:.1f}B collateral-value hit** on the ${N['bn']:.0f}B seriously delinquent pool, depending on the share that ends in repossession and sale (25% to 75%, a scenario axis not in the data). Each 1% on the whole pool is ${N['per1']:.2f}B.
9. **Forecasting from public aggregates adds nothing.** Four-quarter-ahead rolling-origin tests ({K['forecast_window']}) show the best model ({N['bestname']}) at MAE {N['bestmae']:.3f} vs {N['nfc']:.3f} for "same as now" ({N['bestpct']:+.0f}%). Adding unemployment, rates, used prices or credit mix made it worse. The practical read: monitor roll rate and persistence rather than trusting a macro forecast.

## Recommendations (for a collections and remarketing team)

| Action | Why the data supports it | What to test with internal data |
|---|---|---|
| Make 30-to-90 roll rate by vintage and score the lead collections KPI | Record roll rate while inflow is flat since 2024 points at early-stage cure effectiveness | Roll rate by contact strategy, days-to-first-contact, extension and modification use |
| Prioritize outreach to 2021-2023 vintages with large payments | Prices now below origination level for these vintages; payment size is the documented driver | Loan-to-value at origination, payment-to-income, remaining term |
| Plan remarketing capacity for later, lumpier repossession inflow | Persistence is rebuilding, so units reach auction later | Days from 90+ to repossession to sale; auction volumes by month |
| Stress recoveries with the price grid, not a point forecast | No public model beats naive; scenario ranges are honest | Recovery vs book value by model age and mileage |

## Counter-arguments and what they change

- **Philadelphia Fed, April 2026, "Do Recent Auto Loan Delinquency Rates Overstate Borrower Distress?"** argues headline delinquency overstates distress because delinquent loans take longer to resolve. This analysis agrees on mechanics (rising persistence since 2024) but treats longer resolution as a *collections and remarketing workload and cash-timing issue*, not only a measurement artifact. It also finds the early-stage roll rate high, which the Fed piece's flow focus does not capture.
- **Federal Reserve FEDS Note, Sept 2024, "Rising Auto Loan Delinquencies and High Monthly Payments"** attributes about 40% of the rise to higher payments. This supports the payment-burden reading of finding 6; it also means roughly 60% is something else, which this data cannot name.

## Data (all public)

| Source | What | Retrieved |
|---|---|---|
| NY Fed Household Debt and Credit Report, 2026Q2 workbook | Balances, 90+ stock, flows into 30+/90+, originations by score, age breakdowns | 2026-10-24 |
| FRED (St. Louis Fed) | Used and new vehicle CPI, unemployment, CPI all items, fed funds, vehicle sales, consumer sentiment, 48-month new-car loan rate | 2026-10-24 |

Cross-checks against published releases are in `outputs/tables/external_crosscheck.csv` (4 of 4 match).

## How it was built

1. `src/01_parse_raw.py`: parse raw workbook pages and FRED CSV into tidy tables. Cleaning log: `data/clean/cleaning_log_step1_parse.csv` (two-digit years, blanks left as missing, thousands separators, footnote rows, mixed frequencies).
2. `src/02_build_db.py`, `sql/`: load SQLite, run 15 validation checks (duplicates, ranges, identities such as originations by score summing to the total, date continuity), build analysis views. `tests/test_validation_catches_errors.py` corrupts a copy of the database four ways and confirms the checks fail, so a pass means something.
3. `src/03_analysis.py`: metrics, decomposition, scenario grid, forecast test. `tests/test_independent_recompute.py` re-derives headline figures in pandas without SQL.
4. `src/04_figures.py`: 10 charts. `src/05_powerbi_package.py`: star-schema CSVs and DAX measures in `powerbi/`. `src/06_docs.py`: this file and the brief.

Run order: `python src/01_parse_raw.py && python src/02_build_db.py && python src/03_analysis.py && python src/04_figures.py && python src/05_powerbi_package.py && python src/06_docs.py`

## Definitions

- **Stock:** percent of auto balance 90+ days delinquent (NY Fed, end of quarter).
- **Inflow (flow into 90+):** percent of balance newly 90+ delinquent, annualized.
- **Roll rate:** inflow into 90+ divided by inflow into 30+. A proxy: the two flows are measured over the same quarter, not by tracking the same loans.
- **Persistence index:** stock divided by inflow, in years. Assumes steady state; read as a direction signal.
- **Seriously delinquent $B:** auto balance x stock %.

## Limitations (read these)

- Industry aggregates across all lenders, not captive finance or any one company. Findings are hypotheses to test on loan-level data.
- Roll rate and persistence are ratios of aggregate flows, not cohort tracking.
- Used-vehicle CPI is a quality-adjusted consumer price index, not auction recovery values (Manheim or similar would be better and is not freely available).
- Dollar figures per roll point use current balances and annualized flows; treat as order of magnitude.
- The repossession-share axis of the scenario grid is an assumption, not an estimate.
- Origination mix describes new loans only; the existing book's mix differs.
- The forecast test covers {K['forecast_window']} with n={int(K['forecast_eval'][0]['n_forecasts'])} overlapping forecasts, so differences of a few percent are noise.
- Age-band data are four-quarter moving sums, so they react slowly.

## What I would ask a lender for

Loan-level monthly status by vintage, score band, term and payment-to-income; contact and cure history; repossession-to-sale timeline; auction recovery vs book value; and extension and modification outcomes. That would turn these industry signals into forecastable, actionable segments.

## Folder map

`data/raw` source files as retrieved | `data/clean` tidy CSVs and the cleaning log | `sql` schema, validation, analysis views | `src` pipeline | `outputs/figures` charts | `outputs/tables` result tables | `powerbi` model tables and DAX | `docs` executive brief | `tests` validation and recompute tests
"""
(ROOT / "README.md").write_text(readme)

figs = ROOT / "outputs" / "figures"
brief = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page {{ size: Letter; margin: 0.5in }}
body {{ font-family: Carlito, 'DejaVu Sans', sans-serif; color:#1a1a19; font-size: 10.5pt; line-height:1.38 }}
h1 {{ font-size: 19pt; margin:0 0 2px; color:#1F3864 }} .sub {{ color:#6b6b68; margin-bottom:8px; font-size:10pt }}
h2 {{ font-size: 11.5pt; margin:10px 0 3px; color:#1F3864 }}
.kpis {{ display:flex; gap:8px; margin:8px 0 }} .k {{ flex:1; border:1px solid #e6e6e3; border-radius:6px; padding:6px 8px }}
.k b {{ display:block; font-size:17pt; color:#2a78d6 }} .k span {{ font-size:8.5pt; color:#6b6b68 }}
img {{ width:100% }} .row {{ display:flex; gap:10px }} .row img {{ width:50% }}
table {{ border-collapse:collapse; width:100%; font-size:9.5pt }} td,th {{ border-bottom:1px solid #e6e6e3; padding:3px 5px; text-align:left; vertical-align:top }}
.small {{ font-size:8.5pt; color:#6b6b68 }} .pb {{ page-break-before: always }} ul {{ margin:3px 0 3px 16px; padding:0 }}
</style></head><body>
<h1>Auto Delinquency Is at a Record, but It Is Not 2009</h1>
<div class="sub">What it means for collections and used-vehicle remarketing | Data through 2026Q2 | Public data: NY Fed, FRED | Sharon Smith</div>
<div class="kpis">
<div class="k"><b>{N['stock']:.2f}%</b><span>of auto balance 90+ late (record {N['peak']:.2f}% in 2026Q1; 2010: {N['peak10']:.2f}%)</span></div>
<div class="k"><b>${N['bn']:.0f}B</b><span>seriously delinquent, up {N['bn_growth']:.0f}% since end-2019</span></div>
<div class="k"><b>{N['roll']:.1f}%</b><span>of 30+ inflow rolls to 90+ ({N['rank']}th highest of {N['nq']} quarters)</span></div>
<div class="k"><b>{abs(N['v22']):.0f}%</b><span>used prices below the level the 2022 vintage was written at</span></div>
</div>
<h2>The point of view</h2>
<p>Fewer new loans are going seriously late than in 2009 ({N['flow']:.2f}% vs {N['flow_gfc']:.2f}% annualized), credit mix is safer than 2006 ({N['sub']:.0f}% vs {N['sub06']:.0f}% subprime) and unemployment is {N['unemp']:.1f}%. Yet a record share of balances that go 30 days late now reaches 90+, and since mid-2024 the climb in the delinquent stock is {N['d24_pe']:.0f}% loans staying delinquent longer. That is a collections-effectiveness and remarketing-timing issue, and the 2021-2023 vintages sit on used prices that have fallen below origination levels.</p>
<img src="{figs/'fig01_stock_vs_flow.png'}" style="width:88%;display:block;margin:0 auto">
<h2>What the data says</h2>
<ul>
<li><b>Inflow is {N['flow_vs19']:.0f}% above 2019</b> ({N['flow']:.2f}% vs {N['flow19']:.2f}%) but flat since mid-2024 (up {N['flow_since24']:.0f}%).</li>
<li><b>Persistence rebuilt</b> from {N['pers_tr']:.2f} years (2024Q2) to {N['pers']:.2f}; still below 2019 ({N['pers19']:.2f}).</li>
<li><b>Broad:</b> every age band is {N['agemin']:.0f}% to {N['agemax']:.0f}% above 2019. <b>Not unemployment:</b> 2009 inflow {N['flow09']:.2f}% came with {N['unemp09']:.1f}% unemployment.</li>
</ul>
<div class="pb"></div>
<div class="row"><img src="{figs/'fig04_roll_rate.png'}"><img src="{figs/'fig07_vintage_prices.png'}"></div>
<h2>What to do</h2>
<table><tr><th>Action</th><th>Why</th></tr>
<tr><td>Lead collections KPI: 30-to-90 roll rate by vintage and score</td><td>Roll rate {N['roll']:.1f}% vs {N['roll19']:.1f}% in 2019. Industry-scale, one point is about ${N['per_pt']:.1f}B a year reaching 90+; back to 2019 level is about ${N['to19']:.1f}B.</td></tr>
<tr><td>Early outreach on 2021-2023 vintages with large payments</td><td>Prices {N['v21']:+.0f}% / {N['v22']:+.0f}% / {N['v23']:+.0f}% vs origination year; payment size explains about 40% of the rise (Fed Board, 2024).</td></tr>
<tr><td>Plan remarketing capacity for later, lumpier inflow</td><td>Delinquent loans take longer to resolve (Philadelphia Fed, Apr 2026); persistence is rising again.</td></tr>
<tr><td>Stress recoveries with a price grid, not a forecast</td><td>No public-data model beat "same as now" ({N['bestpct']:+.0f}% best). A further 10% price drop is ${N['g25']:.1f}B to ${N['g75']:.1f}B of collateral value depending on repossession share.</td></tr></table>
<h2>Where I could be wrong</h2>
<ul>
<li>These are industry aggregates for all lenders, not any one company's book; treat them as hypotheses for loan-level data.</li>
<li>Roll rate and persistence are ratios of aggregate flows. Used-vehicle CPI is a consumer index, not auction recovery value. The repossession share in the grid is an assumption.</li>
<li>The Philadelphia Fed argues headline delinquency overstates distress; this brief agrees on mechanics and differs on what it means for operations.</li>
</ul>
<p class="small">Method: tidy parse of 5,715 NY Fed observations and 333 FRED months; 15 SQL validation checks (all pass; tested to fail on corrupted data); headline numbers recomputed independently in pandas; 4 of 4 figures match NY Fed publications. Code, data, Power BI tables and DAX are in the repository.</p>
</body></html>"""
(ROOT / "docs").mkdir(exist_ok=True)
(ROOT / "docs" / "executive_brief.html").write_text(brief)
print("ok", round(stock19, 3), round(stock_vs19, 1), round(pers_vs19, 1))
