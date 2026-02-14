"""
Download multiple FRED series (2000–present), save to Excel (one sheet per series)
and to a combined CSV aligned by date. Prints a summary of date ranges and counts.
"""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from fredapi import Fred

# -----------------------------------------------------------------------------
# 1. Load FRED API key from environment or .env file
# -----------------------------------------------------------------------------
def _read_key_from_env_file(path):
    if not path.exists():
        return None
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except Exception:
        return None
    for line in raw.splitlines():
        line = line.strip().lstrip("\ufeff")
        if not line or line.startswith("#"):
            continue
        if "FRED_API_KEY" in line and "=" in line:
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


FRED_API_KEY = os.getenv("FRED_API_KEY")
if not FRED_API_KEY:
    _script_dir = Path(__file__).resolve().parent
    FRED_API_KEY = _read_key_from_env_file(_script_dir / ".env") or _read_key_from_env_file(Path.cwd() / ".env")
if not FRED_API_KEY:
    load_dotenv(Path(__file__).resolve().parent / ".env")
    FRED_API_KEY = os.getenv("FRED_API_KEY")
if not FRED_API_KEY:
    raise ValueError(
        "FRED_API_KEY not set. Add FRED_API_KEY=your_key to a .env file in this folder, "
        "or set the FRED_API_KEY environment variable. Get a free key at: https://fred.stlouisfed.org/docs/api/api_key.html"
    )

# -----------------------------------------------------------------------------
# 2. Define FRED series to download (code -> short description for reference)
# -----------------------------------------------------------------------------
SERIES_IDS = [
    "WALCL",      # Fed total assets
    "BOGMBASE",   # Monetary base
    "M2SL",       # M2 money supply
    "TOTRESNS",   # Bank reserves
    "RRPONTSYD",  # ON RRP facility
    "WTREGEN",    # Treasury General Account
    "FEDFUNDS",   # Fed funds rate
    "DGS10",      # 10-year Treasury yield
    "DGS2",       # 2-year Treasury yield
    "T10YIE",     # 10-year breakeven inflation
    "SP500",      # S&P 500
    "DTWEXBGS",   # Broad dollar index
    "MORTGAGE30US",  # 30-year mortgage rate
    "BAMLC0A0CM",   # Corporate bond spread
    "VIXCLS",     # VIX volatility
    "NFCI",       # Chicago Fed financial conditions
]

# Start date for all series: January 2000
START_DATE = "2000-01-01"

# -----------------------------------------------------------------------------
# 3. Download each series from FRED
# -----------------------------------------------------------------------------
fred = Fred(api_key=FRED_API_KEY)
series_data = {}

for series_id in SERIES_IDS:
    try:
        s = fred.get_series(series_id, observation_start=START_DATE)
        if s is not None and not s.empty:
            series_data[series_id] = s
        else:
            print(f"  Warning: No data returned for {series_id}, skipping.")
    except Exception as e:
        print(f"  Warning: Failed to fetch {series_id}: {e}")

if not series_data:
    raise RuntimeError("No series could be downloaded. Check API key and series IDs.")

# -----------------------------------------------------------------------------
# 4. Save each series to a separate sheet in fred_data.xlsx
# -----------------------------------------------------------------------------
excel_path = Path(__file__).resolve().parent / "fred_data.xlsx"
with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
    for series_id, ser in series_data.items():
        df = pd.DataFrame(ser).reset_index()
        df.columns = ["date", "value"]
        df.to_excel(writer, sheet_name=series_id[:31], index=False)  # Excel sheet name max 31 chars
print(f"Saved Excel: {excel_path}")

# -----------------------------------------------------------------------------
# 5. Build combined DataFrame aligned by date and save as CSV
# -----------------------------------------------------------------------------
# Outer join on date so we keep all dates from any series
combined = None
for series_id, ser in series_data.items():
    df = ser.to_frame(name=series_id)
    if combined is None:
        combined = df
    else:
        combined = combined.join(df, how="outer")
combined = combined.sort_index()
csv_path = Path(__file__).resolve().parent / "fred_combined.csv"
combined.to_csv(csv_path)
print(f"Saved combined CSV: {csv_path}")

# -----------------------------------------------------------------------------
# 6. Print summary: date range and number of observations per series
# -----------------------------------------------------------------------------
print("\n--- Summary ---")
print(f"{'Series':<14} {'Start':<12} {'End':<12} {'Obs':>8}")
print("-" * 48)
for series_id in SERIES_IDS:
    if series_id not in series_data:
        print(f"{series_id:<14} (no data)")
        continue
    ser = series_data[series_id]
    start = ser.index.min()
    end = ser.index.max()
    n = len(ser)
    print(f"{series_id:<14} {str(start)[:10]:<12} {str(end)[:10]:<12} {n:>8}")
print("-" * 48)
print("Done.")
