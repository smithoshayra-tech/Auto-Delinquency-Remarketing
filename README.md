# Auto Loan Delinquency and Used-Vehicle Remarketing Exposure

**Question:** Auto loans 90+ days late are at a record share of balances (2026Q2: 5.49%; peak 5.60% in 2026Q1). Is this a rerun of 2009, and where does it land for a captive finance company's collections and remarketing teams?

**Short answer:** No, it is not a rerun, but it is not benign either. New serious delinquencies are still below the 2009 peak (3.00% vs 3.48% annualized), and credit mix and unemployment do not explain the rise. What *is* unusual is the **roll rate**: 38.1% of balances that go 30 days late now reach 90+, the 4th highest of 94 quarters on record and well above the 2007-11 peak of 32%. Since mid-2024 the climb in the delinquent stock is mostly loans *staying* delinquent longer, which is a collections and remarketing-timing problem more than an origination problem.

Everything below is computed from public data. No figure is typed by hand: each number in this file is generated from `outputs/key_numbers.json` by `src/06_docs.py`.

## Findings

1. **The record is real but modest against 2010.** 90+ stock is 5.49% of auto balances vs 5.27% at the 2010 peak. In dollars that is about $94B seriously delinquent, up 43% from $66B at the end of 2019 (balances grew too).
2. **Versus 2019, the stock is up 16% because new problem balances are up 28%** (3.00% vs 2.35% annualized), partly offset by shorter time in delinquency (persistence 1.83 years vs 2.02, -9%).
3. **Since mid-2024 the story flips.** From 2024Q2 the log change in the stock is 21 points; 81% of it is persistence rising from a 1.54-year low, 19% is inflow. Inflow itself is up only 4% since 2024Q2. This agrees with the Philadelphia Fed's April 2026 finding that the stock of severe delinquencies is rising while the flow into it is fairly stable.
4. **Roll rate is the metric to watch.** 38.1% now vs 33.7% in 2019 and 24% in 2005. At industry scale, each point of roll rate is roughly $1.3B a year of balances reaching 90+; returning to the 2019 roll rate would be worth about $5.6B a year (approximation, see caveats).
5. **It is broad, not one cohort.** Every age band is 21% to 33% above its 2019 level. The subprime share of new originations is 29%, vs 44% in 2006 and 32% in 2019, so credit mix is not the driver.
6. **It is not unemployment.** Inflow is 3.00% with unemployment at 4.3%; in 2009 it was 3.24% with unemployment at 9.9%. This points to payment burden (loan size and price levels) rather than job losses, consistent with a Federal Reserve Board FEDS Note (Sept 2024) that attributes about 40% of the rise in two-year delinquency probability from end-2019 to end-2022 to higher monthly payments.
7. **Remarketing exposure sits in the 2021-2023 vintages.** Used-vehicle CPI is 16% below its Feb-2022 peak, though still 30% above 2019. Against the price level when each vintage was written, 2021 is -2%, 2022 is -13% and 2023 is -6%. The 2018-2020 vintages are well above water. This is a market price indicator, not a loan-level loss estimate.
8. **A further 10% drop in used prices is a $2.4B to $7.0B collateral-value hit** on the $94B seriously delinquent pool, depending on the share that ends in repossession and sale (25% to 75%, a scenario axis not in the data). Each 1% on the whole pool is $0.94B.
9. **Forecasting from public aggregates adds nothing.** Four-quarter-ahead rolling-origin tests (origins 2013-12 to 2025-06) show the best model (Ridge: inflow only) at MAE 0.241 vs 0.249 for "same as now" (-3%). Adding unemployment, rates, used prices or credit mix made it worse. The practical read: monitor roll rate and persistence rather than trusting a macro forecast.

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
- The forecast test covers origins 2013-12 to 2025-06 with n=47 overlapping forecasts, so differences of a few percent are noise.
- Age-band data are four-quarter moving sums, so they react slowly.

## What I would ask a lender for

Loan-level monthly status by vintage, score band, term and payment-to-income; contact and cure history; repossession-to-sale timeline; auction recovery vs book value; and extension and modification outcomes. That would turn these industry signals into forecastable, actionable segments.

## Folder map

`data/raw` source files as retrieved | `data/clean` tidy CSVs and the cleaning log | `sql` schema, validation, analysis views | `src` pipeline | `outputs/figures` charts | `outputs/tables` result tables | `powerbi` model tables and DAX | `docs` executive brief | `tests` validation and recompute tests
