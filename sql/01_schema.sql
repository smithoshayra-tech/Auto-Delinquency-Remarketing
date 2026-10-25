-- Tidy tables loaded from data/clean. Raw files are never edited.
DROP TABLE IF EXISTS nyfed_long;
CREATE TABLE nyfed_long (
    sheet        TEXT NOT NULL,      -- workbook page, e.g. 'Page 14'
    series_group TEXT NOT NULL,      -- e.g. 'flow_into_90plus'
    series       TEXT NOT NULL,      -- e.g. 'auto'
    year         INTEGER NOT NULL,
    quarter      INTEGER NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    value        REAL NOT NULL,
    unit         TEXT NOT NULL,
    period_end   TEXT NOT NULL,
    UNIQUE (series_group, series, year, quarter)
);

DROP TABLE IF EXISTS fred_monthly;
CREATE TABLE fred_monthly (
    month TEXT PRIMARY KEY,          -- first day of month, ISO
    cpi_used_vehicles REAL,
    cpi_new_vehicles REAL,
    unemployment_rate REAL,
    cpi_all_items REAL,
    vehicle_sales_saar_mil REAL,
    fed_funds_rate REAL,
    consumer_sentiment REAL,
    auto_loan_rate_48m_new REAL
);
