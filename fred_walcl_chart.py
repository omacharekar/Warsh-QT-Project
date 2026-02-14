"""
Download Fed total assets (WALCL) from FRED (2008–present) and save as a line chart PNG.
"""

import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
from fredapi import Fred

# Load API key: env var, then .env next to script, then .env in cwd (read file directly)
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

# Fetch WALCL from FRED: 2008-01-01 to present
fred = Fred(api_key=FRED_API_KEY)
start = "2008-01-01"
series = fred.get_series("WALCL", observation_start=start)

if series is None or series.empty:
    raise RuntimeError("No data returned from FRED for WALCL.")

# Convert to DataFrame for clarity
df = pd.DataFrame(series, columns=["WALCL"])
df.index.name = "Date"
df = df.dropna()

# Plot
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(df.index, df["WALCL"], color="#1f77b4", linewidth=1.5)
ax.set_title("Federal Reserve Total Assets (WALCL)", fontsize=14, fontweight="bold")
ax.set_xlabel("Date")
ax.set_ylabel("Millions of Dollars")
ax.grid(True, alpha=0.3)
ax.ticklabel_format(style="plain", axis="y")
fig.tight_layout()

# Save as PNG
out_path = Path(__file__).resolve().parent / "fed_total_assets_walcl.png"
fig.savefig(out_path, dpi=150, bbox_inches="tight")
plt.close()

print(f"Chart saved to: {out_path}")
