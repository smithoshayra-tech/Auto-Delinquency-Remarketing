-- Each block: "-- check: <name> | <what it proves>" then a SELECT returning one row:
--   offending_rows (int), detail (text). A check passes when offending_rows = 0.
-- check: no_duplicate_series_quarters | one value per series and quarter
SELECT COUNT(*) AS offending_rows, 'duplicates' AS detail FROM (
  SELECT series_group, series, year, quarter FROM nyfed_long GROUP BY 1,2,3,4 HAVING COUNT(*) > 1);
-- check: quarterly_continuity_auto_delinquency | no missing quarters between 2003Q1 and 2026Q2
SELECT ABS(COUNT(*) - 94) AS offending_rows, 'quarters found=' || COUNT(*) AS detail
FROM nyfed_long WHERE series_group='pct_balance_90plus' AND series='auto';
-- check: debt_composition_sums_to_total | components add to the reported total within 0.05 trillion
SELECT SUM(gap > 0.05) AS offending_rows, 'largest observed gap=' || ROUND(MAX(gap),3) || ' trillion' AS detail FROM (
  SELECT year, quarter,
    ABS(SUM(CASE WHEN series<>'total' THEN value ELSE 0 END) - SUM(CASE WHEN series='total' THEN value ELSE 0 END)) AS gap
  FROM nyfed_long WHERE series_group='debt_balance' GROUP BY year, quarter);
-- check: delinquency_status_sums_to_100 | status shares add to 100 within 0.5 points
SELECT SUM(ABS(s-100) > 0.5) AS offending_rows, 'sums range ' || ROUND(MIN(s),1) || ' to ' || ROUND(MAX(s),1) AS detail FROM (
  SELECT year, quarter, SUM(CASE WHEN series<>'total' THEN value ELSE 0 END) AS s
  FROM nyfed_long WHERE series_group='balance_by_status_all_debt' GROUP BY year, quarter);
-- check: origination_bands_sum_to_total | score bands add to total originations within 0.25 billion
SELECT SUM(gap > 0.25) AS offending_rows, 'largest observed gap=' || ROUND(MAX(gap),2) || ' billion (rounding)' AS detail FROM (
  SELECT year, quarter,
    ABS(SUM(CASE WHEN series<>'total' THEN value ELSE 0 END) - SUM(CASE WHEN series='total' THEN value ELSE 0 END)) AS gap
  FROM nyfed_long WHERE series_group='auto_orig_by_score' GROUP BY year, quarter);
-- check: percent_values_in_range | every percentage series sits between 0 and 100
SELECT COUNT(*) AS offending_rows, 'values outside 0-100' AS detail FROM nyfed_long
WHERE unit IN ('pct','pct_annualized','pct_4q_moving_sum','pct_of_balance') AND (value < 0 OR value > 100);
-- check: early_flow_not_below_serious_flow | new 90+ balances cannot exceed new 30+ balances (auto)
SELECT COUNT(*) AS offending_rows, 'quarters where 90+ flow > 30+ flow' AS detail FROM (
  SELECT a.year, a.quarter FROM nyfed_long a JOIN nyfed_long b
    ON a.year=b.year AND a.quarter=b.quarter
  WHERE a.series_group='flow_into_30plus' AND a.series='auto'
    AND b.series_group='flow_into_90plus' AND b.series='auto' AND b.value > a.value);
-- check: cross_sheet_agreement_flow_vs_age_total | Page 14 auto flow equals Page 26 all-ages total within 0.02 points
SELECT SUM(d > 0.02) AS offending_rows, 'largest observed difference=' || ROUND(MAX(d),3) || ' points over ' || COUNT(*) || ' quarters' AS detail FROM (
  SELECT ABS(a.value - b.value) AS d FROM nyfed_long a JOIN nyfed_long b
    ON a.year=b.year AND a.quarter=b.quarter
  WHERE a.series_group='flow_into_90plus' AND a.series='auto'
    AND b.series_group='auto_flow_90plus_by_age_4q' AND b.series='all');
-- check: fred_no_duplicate_months | month is unique
SELECT COUNT(*) - COUNT(DISTINCT month) AS offending_rows, 'rows=' || COUNT(*) AS detail FROM fred_monthly;
-- check: fred_no_missing_months | 1999-01 to 2026-09 is 333 consecutive months
SELECT ABS(COUNT(*) - 333) AS offending_rows, 'months=' || COUNT(*) AS detail FROM fred_monthly;
-- check: fred_core_series_complete | used and new vehicle CPI, sales, rates have no gaps
SELECT COUNT(*) AS offending_rows, 'rows with a null core series' AS detail FROM fred_monthly
WHERE cpi_used_vehicles IS NULL OR cpi_new_vehicles IS NULL OR vehicle_sales_saar_mil IS NULL
   OR fed_funds_rate IS NULL OR consumer_sentiment IS NULL;
-- check: fred_known_gaps_documented | unemployment and all-items CPI are missing only for 2025-10
SELECT COUNT(*) AS offending_rows, 'unexpected missing months' AS detail FROM fred_monthly
WHERE (unemployment_rate IS NULL OR cpi_all_items IS NULL) AND month <> '2025-10-01';
-- check: fred_latest_month | data run to the latest published month, 2026-09
SELECT CASE WHEN MAX(month)='2026-09-01' THEN 0 ELSE 1 END AS offending_rows, 'latest=' || MAX(month) AS detail FROM fred_monthly;
-- check: used_cpi_extreme_monthly_moves | months where used-vehicle CPI moved more than 6 percent (reviewed, kept)
SELECT 0 AS offending_rows,
  (SELECT COUNT(*) FROM (SELECT month, cpi_used_vehicles / LAG(cpi_used_vehicles) OVER (ORDER BY month) - 1 AS chg FROM fred_monthly) WHERE ABS(chg) > 0.06)
  || ' months moved >6% (2021 reopening and 2009 rebound); kept, not winsorized' AS detail;
-- check: fred_covers_every_nyfed_quarter | each NY Fed quarter since 2003 has at least 2 FRED months
SELECT COUNT(*) AS offending_rows, 'quarters with <2 FRED months' AS detail FROM (
  SELECT n.year, n.quarter, COUNT(f.month) AS m FROM
    (SELECT DISTINCT year, quarter FROM nyfed_long WHERE series_group='pct_balance_90plus') n
  LEFT JOIN fred_monthly f ON CAST(substr(f.month,1,4) AS INT)=n.year AND (CAST(substr(f.month,6,2) AS INT)+2)/3=n.quarter
  GROUP BY n.year, n.quarter HAVING m < 2);
