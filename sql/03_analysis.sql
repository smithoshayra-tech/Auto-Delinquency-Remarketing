-- Analysis layer. Everything below is derived from the two loaded tables with plain SQL.

-- Quarterly FRED averages aligned to NY Fed quarters. Quarters with a missing month average the months that exist.
DROP VIEW IF EXISTS v_fred_q;
CREATE VIEW v_fred_q AS
SELECT CAST(substr(month,1,4) AS INT) AS year,
       (CAST(substr(month,6,2) AS INT)+2)/3 AS quarter,
       COUNT(*)                         AS months_in_quarter,
       AVG(cpi_used_vehicles)           AS cpi_used,
       AVG(cpi_new_vehicles)            AS cpi_new,
       AVG(unemployment_rate)           AS unemployment,
       AVG(fed_funds_rate)              AS fed_funds,
       AVG(consumer_sentiment)          AS sentiment,
       AVG(vehicle_sales_saar_mil)      AS vehicle_sales,
       AVG(auto_loan_rate_48m_new)      AS auto_rate_48m
FROM fred_monthly GROUP BY 1, 2;

-- One row per quarter with the auto-credit series side by side.
DROP VIEW IF EXISTS v_auto_panel;
CREATE VIEW v_auto_panel AS
WITH p AS (
  SELECT year, quarter, period_end,
    MAX(CASE WHEN series_group='pct_balance_90plus'  AND series='auto' THEN value END) AS stock90,
    MAX(CASE WHEN series_group='flow_into_90plus'    AND series='auto' THEN value END) AS flow90,
    MAX(CASE WHEN series_group='flow_into_30plus'    AND series='auto' THEN value END) AS flow30,
    MAX(CASE WHEN series_group='debt_balance'        AND series='auto' THEN value END) AS auto_bal_tn,
    MAX(CASE WHEN series_group='auto_orig_by_score'  AND series='total' THEN value END) AS orig_total_bn,
    MAX(CASE WHEN series_group='auto_orig_by_score'  AND series='lt620' THEN value END) AS orig_lt620_bn,
    MAX(CASE WHEN series_group='auto_orig_by_score'  AND series='s620_659' THEN value END) AS orig_620_659_bn,
    MAX(CASE WHEN series_group='auto_orig_score_dist' AND series='median' THEN value END) AS orig_median_score,
    MAX(CASE WHEN series_group='third_party_collections' AND series='pct_consumers_with_collection' THEN value END) AS pct_with_collection,
    MAX(CASE WHEN series_group='third_party_collections' AND series='avg_collection_usd' THEN value END) AS avg_collection_usd
  FROM nyfed_long GROUP BY year, quarter, period_end)
SELECT p.*,
  ROUND(p.flow90 / p.flow30, 4)                              AS roll_rate_30_to_90,   -- share of new 30+ balances that reach 90+
  ROUND(p.stock90 / p.flow90, 3)                             AS persistence_index,    -- stock / annual inflow, in years
  ROUND(100.0 * (p.orig_lt620_bn + p.orig_620_659_bn) / p.orig_total_bn, 2) AS subprime_orig_share_pct,
  ROUND(p.auto_bal_tn * 1000 * p.stock90 / 100, 1)           AS seriously_delinquent_bn,
  f.cpi_used, f.cpi_new, f.unemployment, f.fed_funds, f.sentiment, f.vehicle_sales, f.auto_rate_48m,
  f.months_in_quarter
FROM p LEFT JOIN v_fred_q f ON f.year = p.year AND f.quarter = p.quarter
WHERE p.stock90 IS NOT NULL;

-- Four-quarter changes and rank statistics.
DROP VIEW IF EXISTS v_auto_panel_wow;
CREATE VIEW v_auto_panel_wow AS
SELECT *,
  stock90 - LAG(stock90, 4) OVER w                           AS stock90_chg_4q,
  flow90  - LAG(flow90, 4)  OVER w                           AS flow90_chg_4q,
  ROUND(100.0 * (cpi_used / LAG(cpi_used, 4) OVER w - 1), 2) AS used_cpi_yoy_pct,
  RANK() OVER (ORDER BY roll_rate_30_to_90 DESC)             AS roll_rate_rank_high,
  RANK() OVER (ORDER BY stock90 DESC)                        AS stock90_rank_high
FROM v_auto_panel WINDOW w AS (ORDER BY year, quarter);

-- Log decomposition of the change in the delinquent stock: ln(stock) = ln(inflow) + ln(persistence).
-- Windows are chosen in the Python step and passed in as parameters; this view gives every start quarter vs the latest.
DROP VIEW IF EXISTS v_decomp_to_latest;
CREATE VIEW v_decomp_to_latest AS
WITH latest AS (SELECT * FROM v_auto_panel ORDER BY year DESC, quarter DESC LIMIT 1)
SELECT a.year || 'Q' || a.quarter AS start_quarter,
       ROUND(100*(LN(l.stock90) - LN(a.stock90)), 1)                              AS dlog_stock_pct,
       ROUND(100*(LN(l.flow90) - LN(a.flow90)), 1)                                AS dlog_inflow_pct,
       ROUND(100*((LN(l.stock90/l.flow90)) - LN(a.stock90/a.flow90)), 1)          AS dlog_persistence_pct,
       ROUND(100.0*(LN(l.flow90) - LN(a.flow90)) / (LN(l.stock90) - LN(a.stock90)), 0)         AS share_from_inflow_pct,
       ROUND(100.0*((LN(l.stock90/l.flow90)) - LN(a.stock90/a.flow90)) / (LN(l.stock90) - LN(a.stock90)), 0) AS share_from_persistence_pct
FROM v_auto_panel a, latest l WHERE a.year >= 2019;

-- Age breadth: flow into 90+ for each age band, latest vs 2019 average and vs the 2021Q4 trough.
DROP VIEW IF EXISTS v_age_breadth;
CREATE VIEW v_age_breadth AS
WITH base AS (
  SELECT series AS age_band,
    AVG(CASE WHEN year = 2019 THEN value END) AS avg_2019,
    MAX(CASE WHEN year = 2021 AND quarter = 4 THEN value END) AS trough_2021q4,
    MAX(CASE WHEN year = 2026 AND quarter = 2 THEN value END) AS latest
  FROM nyfed_long WHERE series_group='auto_flow_90plus_by_age_4q' GROUP BY series)
SELECT age_band, ROUND(avg_2019,2) AS avg_2019, ROUND(trough_2021q4,2) AS trough_2021q4, ROUND(latest,2) AS latest,
       ROUND(100*(latest/avg_2019-1),1) AS pct_vs_2019, ROUND(100*(latest/trough_2021q4-1),1) AS pct_vs_trough
FROM base;

-- Price-since-origination ratio: used-vehicle CPI now vs average during the quarter a vintage was written.
-- This is a price-level indicator for the market, not a loan-level loss estimate.
DROP VIEW IF EXISTS v_vintage_price_ratio;
CREATE VIEW v_vintage_price_ratio AS
WITH latest AS (SELECT cpi_used AS now_cpi FROM v_auto_panel ORDER BY year DESC, quarter DESC LIMIT 1),
vint AS (SELECT p.year, AVG(p.cpi_used) AS cpi_at_orig, SUM(p.orig_total_bn) AS orig_bn, AVG(p.orig_median_score) AS median_score
         FROM v_auto_panel p WHERE p.year BETWEEN 2018 AND 2026 GROUP BY p.year)
SELECT v.year AS vintage_year, ROUND(v.orig_bn,0) AS originations_bn, ROUND(v.cpi_at_orig,1) AS used_cpi_at_origination,
       ROUND(l.now_cpi,1) AS used_cpi_now, ROUND(100*(l.now_cpi / v.cpi_at_orig - 1),1) AS price_change_since_pct
FROM vint v, latest l;
