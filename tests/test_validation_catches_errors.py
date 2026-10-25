"""The checks are only worth trusting if they fail on bad data. Corrupt a copy of the database in four ways and confirm each is caught."""
import re, shutil, sqlite3, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
tmp = ROOT / "data" / "_test_copy.db"
shutil.copy(ROOT / "data" / "autocredit.db", tmp)
con = sqlite3.connect(tmp)
con.execute("UPDATE nyfed_long SET value = value + 1.0 WHERE series_group='debt_balance' AND series='auto' AND year=2020 AND quarter=2")  # break composition sum
con.execute("UPDATE nyfed_long SET value = 140 WHERE series_group='pct_balance_90plus' AND series='auto' AND year=2015 AND quarter=1")      # impossible percent
con.execute("DELETE FROM nyfed_long WHERE series_group='pct_balance_90plus' AND series='auto' AND year=2012 AND quarter=3")                 # missing quarter
con.execute("DELETE FROM fred_monthly WHERE month='2018-06-01'")                                                                          # missing month
text = (ROOT / "sql" / "02_validation.sql").read_text()
failed = []
for b in re.split(r"(?m)^-- check: ", text)[1:]:
    header, sql = b.split("\n", 1)
    name = header.split("|")[0].strip()
    sql = "\n".join(l for l in sql.split("\n") if not l.startswith("--"))
    off, _ = con.execute(sql).fetchone()
    if off: failed.append(name)
con.close(); tmp.unlink()
expected = {"debt_composition_sums_to_total", "percent_values_in_range", "quarterly_continuity_auto_delinquency", "fred_no_missing_months"}
print("caught:", sorted(failed))
assert expected <= set(failed), f"missed: {expected - set(failed)}"
print("OK: all four injected errors were caught")
