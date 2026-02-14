"""
Read fred_combined.csv and create Fed/M2 analysis charts and statistics table.
Outputs: PNG charts (300 dpi), statistics in model_1a_results.xlsx.
Uses seaborn style, professional colors, clear labels.
"""

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
CSV_PATH = SCRIPT_DIR / "fred_combined.csv"
OUTPUT_DIR = SCRIPT_DIR

# QE/QT periods for shading and stats
QE_PERIODS = [
    ("QE1", "2008-11-01", "2010-03-31"),
    ("QE2", "2010-11-01", "2011-06-30"),
    ("QE3", "2012-09-01", "2014-10-31"),
    ("Pandemic QE", "2020-03-01", "2022-03-31"),
]
QT_PERIODS = [
    ("QT1", "2017-10-01", "2019-09-30"),
    ("QT2", "2022-06-01", "2025-12-31"),
]
ALL_ERAS = QE_PERIODS + QT_PERIODS


def load_monthly_data():
    """Load CSV and resample to monthly; return DataFrame with trillions and multiplier."""
    df = pd.read_csv(CSV_PATH, index_col=0, parse_dates=True)
    df.index = pd.to_datetime(df.index)

    # Keep only needed columns and forward-fill then take month-end
    cols = ["WALCL", "BOGMBASE", "M2SL"]
    df = df[cols].copy()
    df = df.ffill().resample("ME").last()

    # Units: WALCL millions -> trillions (÷1e6), M2SL billions -> trillions (÷1e3), BOGMBASE millions
    df["WALCL_tril"] = df["WALCL"] / 1e6
    df["M2SL_tril"] = df["M2SL"] / 1e3
    # Money multiplier: M2 / monetary base (both FRED series in billions)
    df["money_mult"] = df["M2SL"] / df["BOGMBASE"].replace(0, pd.NA)
    df = df.dropna(subset=["WALCL", "M2SL", "BOGMBASE"])

    return df


# Professional palette: left axis, right axis, main series, reference line
PALETTE = sns.color_palette("colorblind", n_colors=6)


def chart1_twin_axis(df: pd.DataFrame):
    """Twin-axis: WALCL and M2 in trillions, 2008–present, with QE/QT bands."""
    fig, ax1 = plt.subplots(figsize=(12, 6))
    mask = (df.index >= "2008-01-01") & (df.index <= df.index.max())
    x = df.index[mask]
    w = df.loc[mask, "WALCL_tril"]
    m = df.loc[mask, "M2SL_tril"]

    c_left = PALETTE[0]
    c_right = PALETTE[2]

    ax1.set_xlim(x.min(), x.max())
    ax1.set_ylabel("Fed Total Assets (WALCL)\nTrillions USD", color=c_left, fontsize=11, fontweight="medium")
    ax1.plot(x, w, color=c_left, linewidth=2, label="Fed Total Assets (WALCL)")
    ax1.tick_params(axis="y", labelcolor=c_left, labelsize=10)
    ax1.tick_params(axis="x", labelsize=10)

    ax2 = ax1.twinx()
    ax2.set_ylabel("M2 Money Supply (M2SL)\nTrillions USD", color=c_right, fontsize=11, fontweight="medium")
    ax2.plot(x, m, color=c_right, linewidth=2, label="M2 Money Supply (M2SL)")
    ax2.tick_params(axis="y", labelcolor=c_right, labelsize=10)

    # QE bands (muted green)
    for name, start, end in QE_PERIODS:
        ax1.axvspan(
            pd.Timestamp(start), pd.Timestamp(end),
            alpha=0.22, color=PALETTE[1], zorder=0,
        )
    # QT bands (muted orange)
    for name, start, end in QT_PERIODS:
        ax1.axvspan(
            pd.Timestamp(start), pd.Timestamp(end),
            alpha=0.22, color=PALETTE[4], zorder=0,
        )

    ax1.legend(
        [Patch(facecolor=PALETTE[1], alpha=0.45), Patch(facecolor=PALETTE[4], alpha=0.45)],
        ["QE periods", "QT periods"],
        loc="upper left",
        framealpha=0.95,
        fontsize=10,
    )

    ax1.xaxis.set_major_locator(mdates.YearLocator(2))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax1.set_title("Fed Balance Sheet vs M2 Money Supply", fontsize=14, fontweight="bold")
    ax1.set_xlabel("Year", fontsize=11)
    fig.tight_layout()
    return fig


def chart2_money_multiplier(df: pd.DataFrame):
    """Money multiplier M2/BOGMBASE, 2000–present, with pre-2008 average line."""
    fig, ax = plt.subplots(figsize=(12, 6))
    mask = (df.index >= "2000-01-01") & (df.index <= df.index.max())
    x = df.index[mask]
    mult = df.loc[mask, "money_mult"]

    pre2008 = mult[mult.index < "2008-01-01"]
    avg_pre2008 = pre2008.mean()

    ax.plot(x, mult, color=PALETTE[1], linewidth=2, label="Money multiplier (M2 / Monetary base)")
    ax.axhline(avg_pre2008, color=PALETTE[4], linestyle="--", linewidth=1.8, label=f"Pre-2008 average = {avg_pre2008:.2f}")
    ax.set_ylabel("Money Multiplier (M2 / Monetary Base)", fontsize=11, fontweight="medium")
    ax.set_xlabel("Year", fontsize=11, fontweight="medium")
    ax.set_title("The Broken Money Multiplier", fontsize=14, fontweight="bold")
    ax.legend(loc="upper right", fontsize=10)
    ax.tick_params(labelsize=10)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.tight_layout()
    return fig


def chart3_rolling_correlation(df: pd.DataFrame):
    """12-month rolling correlation of MoM changes in WALCL and M2SL, 2008–present."""
    mask = (df.index >= "2008-01-01") & (df.index <= df.index.max())
    sub = df.loc[mask, ["WALCL", "M2SL"]].copy()
    sub["walcl_pct"] = sub["WALCL"].pct_change()
    sub["m2_pct"] = sub["M2SL"].pct_change()
    sub = sub.dropna()
    roll_corr = sub["walcl_pct"].rolling(12).corr(sub["m2_pct"])

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(roll_corr.index, roll_corr, color=PALETTE[3], linewidth=2, label="12-month rolling correlation")
    ax.axhline(0, color="gray", linestyle="-", linewidth=1)
    ax.set_ylabel("Rolling 12-Month Correlation", fontsize=11, fontweight="medium")
    ax.set_xlabel("Year", fontsize=11, fontweight="medium")
    ax.set_title("Rolling 12-Month Correlation: Fed Balance Sheet Changes vs M2 Changes", fontsize=14, fontweight="bold")
    ax.tick_params(labelsize=10)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.tight_layout()
    return fig


def build_statistics_table(df: pd.DataFrame) -> pd.DataFrame:
    """For each era: total balance sheet change, total M2 change, avg money multiplier, correlation."""
    rows = []
    for name, start, end in ALL_ERAS:
        start_ts = pd.Timestamp(start)
        end_ts = pd.Timestamp(end)
        era = df[(df.index >= start_ts) & (df.index <= end_ts)]
        if era.empty:
            rows.append({
                "Era": name,
                "Start": start,
                "End": end,
                "BS Change (tril)": None,
                "M2 Change (tril)": None,
                "Avg Money Mult": None,
                "Correlation (WALCL vs M2)": None,
            })
            continue
        bs_change = era["WALCL_tril"].iloc[-1] - era["WALCL_tril"].iloc[0]
        m2_change = era["M2SL_tril"].iloc[-1] - era["M2SL_tril"].iloc[0]
        avg_mult = era["money_mult"].mean()
        corr = era["WALCL_tril"].corr(era["M2SL_tril"])
        rows.append({
            "Era": name,
            "Start": start,
            "End": end,
            "BS Change (tril)": round(bs_change, 3),
            "M2 Change (tril)": round(m2_change, 3),
            "Avg Money Mult": round(avg_mult, 3),
            "Correlation (WALCL vs M2)": round(corr, 3),
        })
    return pd.DataFrame(rows)


def main():
    sns.set_style("whitegrid")
    sns.set_context("notebook", font_scale=1.05)

    df = load_monthly_data()
    if df.empty:
        raise SystemExit("No monthly data after resampling. Check fred_combined.csv.")

    # 1. Chart 1
    fig1 = chart1_twin_axis(df)
    fig1.savefig(OUTPUT_DIR / "chart1_fed_balance_sheet_vs_m2.png", dpi=300, bbox_inches="tight")
    plt.close(fig1)
    print("Saved: chart1_fed_balance_sheet_vs_m2.png")

    # 2. Chart 2
    fig2 = chart2_money_multiplier(df)
    fig2.savefig(OUTPUT_DIR / "chart2_money_multiplier.png", dpi=300, bbox_inches="tight")
    plt.close(fig2)
    print("Saved: chart2_money_multiplier.png")

    # 3. Chart 3
    fig3 = chart3_rolling_correlation(df)
    fig3.savefig(OUTPUT_DIR / "chart3_rolling_correlation.png", dpi=300, bbox_inches="tight")
    plt.close(fig3)
    print("Saved: chart3_rolling_correlation.png")

    # 4. Statistics table → model_1a_results.xlsx
    stats = build_statistics_table(df)
    excel_path = OUTPUT_DIR / "model_1a_results.xlsx"
    stats.to_excel(excel_path, index=False, sheet_name="Era Statistics")
    print(f"Saved: {excel_path.name}")

    # Print formatted table
    print("\n--- Era statistics ---")
    print(stats.to_string(index=False))


if __name__ == "__main__":
    main()
