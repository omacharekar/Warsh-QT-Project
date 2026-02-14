"""
Reserve Drain (Plumbing) Model: project bank reserves forward 24 months
under four scenarios (Warsh Hawk, Moderate, Duration Shift, Crisis Reversal).
Uses fred_combined.csv for historical data and starting conditions.
Outputs: PNG charts (300 dpi), model_2a_results.xlsx summary table.
"""

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
# ---------------------------------------------------------------------------
# PATHS AND CONSTANTS
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
CSV_PATH = SCRIPT_DIR / "fred_combined.csv"
OUTPUT_DIR = SCRIPT_DIR

# Starting conditions (February 2026) – populated from CSV
CURRENCY_GROWTH_BN = 5.5   # $ billion per month (trend)
OTHER_DRAINS_BN = 2.0     # $ billion per month (misc liabilities)

# Scenario runoffs (QT) in $ billion per month: positive = balance sheet shrinks
QT_HAWK_BN = 95.0         # A: $60B Treas + $35B MBS
QT_MODERATE_BN = 40.0     # B: $25B Treas + $15B MBS
QT_DURATION_BN = 0.0      # C: $0 net QT (roll into bills)
QE_CRISIS_BN = -75.0      # D: resume QE (negative = adds reserves)

# TGA sine wave: mean $650B, amplitude $100B, period 6 months
TGA_MEAN_BN = 650.0
TGA_AMPLITUDE_BN = 100.0
TGA_PERIOD_MONTHS = 6.0

# Reserve threshold levels (for charts and summary), in billions
THRESH_ABUNDANT_BN = 3000.0   # $3.0T
THRESH_AMPLE_BN = 2500.0      # $2.5T
THRESH_CAUTION_BN = 2000.0    # $2.0T
THRESH_CRISIS_BN = 1400.0     # 2019 crisis level

# Scenario D: trigger in month 6 of Scenario A when reserves approach $2.0T
CRISIS_TRIGGER_MONTH = 6

PROJECTION_MONTHS = 24
START_DATE = pd.Timestamp("2026-02-01")   # February 2026
REPO_CRISIS_DATE = pd.Timestamp("2019-09-01")  # Sep 2019 repo crisis


def load_starting_conditions():
    """
    Load fred_combined.csv and extract latest values for TOTRESNS, RRPONTSYD, WTREGEN.
    TOTRESNS is monthly and in billions; RRPONTSYD and WTREGEN may be in millions on FRED.
    Returns dict with reserves_bn, rrp_bn, tga_bn (all in billions).
    """
    df = pd.read_csv(CSV_PATH, index_col=0, parse_dates=True)
    df.index = pd.to_datetime(df.index)

    # Reserves: use last monthly observation (TOTRESNS > 100 indicates billions scale)
    res_series = df["TOTRESNS"].dropna()
    monthly_res = res_series[res_series > 100]
    if monthly_res.empty:
        monthly_res = res_series
    reserves_bn = float(monthly_res.iloc[-1])

    # ON RRP: latest value; FRED RRPONTSYD can be in millions for large values
    rrp = df["RRPONTSYD"].dropna()
    rrp_last = float(rrp.iloc[-1])
    rrp_bn = rrp_last / 1000.0 if rrp_last > 1000 else rrp_last

    # TGA (WTREGEN): FRED in millions -> convert to billions
    tga = df["WTREGEN"].dropna()
    tga_last = float(tga.iloc[-1])
    tga_bn = tga_last / 1000.0 if tga_last > 100 else tga_last

    return {
        "reserves_bn": reserves_bn,
        "rrp_bn": rrp_bn,
        "tga_bn": tga_bn,
    }


def tga_path_bn(month_index, tga_start_bn):
    """
    TGA in billions: sine wave around $650B mean, $100B amplitude, 6-month period.
    month_index 0 = first projection month (Feb 2026).
    """
    t = month_index
    return TGA_MEAN_BN + TGA_AMPLITUDE_BN * np.sin(2 * np.pi * t / TGA_PERIOD_MONTHS)


def run_scenario(qt_bn_per_month, start, currency_bn, other_bn, rrp_near_zero=True,
                 crisis_reversal_after_month=None, qe_bn_per_month=None):
    """
    Run the reserve drain equation forward for 24 months.

    Core equation (monthly):
      new_reserves = old_reserves - QT_runoff + delta_RRP - delta_TGA - currency_growth - other

    Parameters
    ----------
    qt_bn_per_month : float
        QT runoff in $B/month (positive = shrink). Use negative for QE.
    start : dict
        Starting conditions: reserves_bn, rrp_bn, tga_bn.
    currency_bn : float
        Currency growth drain per month ($B).
    other_bn : float
        Other drains per month ($B).
    rrp_near_zero : bool
        If True, ON RRP stays at 0 (buffer exhausted); delta_RRP = 0 after initial drawdown.
    crisis_reversal_after_month : int or None
        If set (e.g. 6), from that month onward use QE instead of QT.
    qe_bn_per_month : float or None
        When crisis_reversal_after_month is set, this is the QE add per month (e.g. -75 -> +75 to reserves).

    Returns
    -------
    dict with keys: reserves_bn (list), rrp_bn, tga_bn (lists), currency_cum_bn, other_cum_bn
    for decomposition chart; and tga_series (list) for TGA path.
    """
    reserves = [start["reserves_bn"]]
    rrp = [start["rrp_bn"]]
    tga_series = [start["tga_bn"]]
    # Build full TGA path (sine) for all 24 months
    for m in range(1, PROJECTION_MONTHS + 1):
        tga_series.append(tga_path_bn(m, start["tga_bn"]))

    for m in range(1, PROJECTION_MONTHS + 1):
        # Effective QT this month (switch to QE if crisis reversal)
        if crisis_reversal_after_month is not None and m >= crisis_reversal_after_month and qe_bn_per_month is not None:
            effective_qt = qe_bn_per_month  # e.g. -75 -> adds 75 to reserves
        else:
            effective_qt = qt_bn_per_month

        # delta_RRP: ON RRP stays near zero; first month can drain remaining RRP into reserves (RRP down -> reserves up)
        if rrp_near_zero:
            if m == 1 and rrp[-1] > 0:
                delta_rrp = -rrp[-1]  # drawdown RRP to zero (adds to reserves)
            else:
                delta_rrp = 0.0
        else:
            delta_rrp = 0.0

        rrp_next = 0.0 if rrp_near_zero else rrp[-1]
        rrp.append(rrp_next)

        # delta_TGA: change in TGA (TGA up -> reserves down)
        tga_prev = tga_series[m - 1]
        tga_curr = tga_series[m]
        delta_tga = tga_curr - tga_prev

        # Core equation (all in billions)
        new_res = reserves[-1] - effective_qt + delta_rrp - delta_tga - currency_bn - other_bn
        reserves.append(max(0.0, new_res))

    # Cumulative currency and other for decomposition (cumulative drain over time)
    currency_cum = [currency_bn * (m + 1) for m in range(PROJECTION_MONTHS + 1)]
    other_cum = [other_bn * (m + 1) for m in range(PROJECTION_MONTHS + 1)]

    return {
        "reserves_bn": reserves,
        "rrp_bn": rrp,
        "tga_bn": tga_series,
        "currency_cum_bn": currency_cum,
        "other_cum_bn": other_cum,
    }


def build_all_scenarios(start):
    """Build 24-month paths for scenarios A, B, C, and D."""
    # A: Warsh Hawk $95B/mo
    A = run_scenario(QT_HAWK_BN, start, CURRENCY_GROWTH_BN, OTHER_DRAINS_BN,
                     rrp_near_zero=True)

    # B: Moderate $40B/mo
    B = run_scenario(QT_MODERATE_BN, start, CURRENCY_GROWTH_BN, OTHER_DRAINS_BN,
                     rrp_near_zero=True)

    # C: Duration shift $0 QT
    C = run_scenario(QT_DURATION_BN, start, CURRENCY_GROWTH_BN, OTHER_DRAINS_BN,
                     rrp_near_zero=True)

    # D: Crisis reversal: same as A for first 6 months, then -$75B/mo (QE)
    D = run_scenario(
        QT_HAWK_BN, start, CURRENCY_GROWTH_BN, OTHER_DRAINS_BN,
        rrp_near_zero=True,
        crisis_reversal_after_month=CRISIS_TRIGGER_MONTH,
        qe_bn_per_month=QE_CRISIS_BN,
    )

    return {"A": A, "B": B, "C": C, "D": D}


def months_until(reserves_bn_list, threshold_bn):
    """Return first 0-based month index where reserves <= threshold, else None."""
    for i, r in enumerate(reserves_bn_list):
        if r <= threshold_bn:
            return i
    return None


def summary_table(scenarios, start_bn):
    """Compute summary stats for each scenario for table and Excel."""
    rows = []
    for name, label in [("A", "Warsh Hawk"), ("B", "Moderate"), ("C", "Duration Shift"), ("D", "Crisis Reversal")]:
        r = scenarios[name]["reserves_bn"]
        m_25 = months_until(r, THRESH_AMPLE_BN)
        m_20 = months_until(r, THRESH_CAUTION_BN)
        r_12 = r[12] if len(r) > 12 else None
        r_24 = r[24] if len(r) > 24 else None
        # Total balance sheet reduction over 24 months: start - end reserves (simplified; full BS = reserves + RRP + TGA + currency + other)
        total_bs_reduction_bn = start_bn - r[24] if len(r) > 24 else None
        rows.append({
            "Scenario": label,
            "Months until $2.5T (ample)": m_25 if m_25 is not None else "—",
            "Months until $2.0T (caution)": m_20 if m_20 is not None else "—",
            "Reserves at 12 mo ($B)": round(r_12, 1) if r_12 is not None else "—",
            "Reserves at 24 mo ($B)": round(r_24, 1) if r_24 is not None else "—",
            "Total BS reduction 24mo ($B)": round(total_bs_reduction_bn, 1) if total_bs_reduction_bn is not None else "—",
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# CHARTS
# ---------------------------------------------------------------------------
def chart1_main_projection(scenarios, start_date):
    """
    Line chart: projected reserves (trillions) over 24 months for all 4 scenarios.
    Horizontal dashed lines at 3.0T (Abundant), 2.5T (Ample), 2.0T (Caution), 1.4T (2019 Crisis).
    Background zones between thresholds. 14x8 in, 300 dpi.
    """
    sns.set_theme(style="whitegrid", font_scale=1.1)
    fig, ax = plt.subplots(figsize=(14, 8))

    months = np.arange(PROJECTION_MONTHS + 1)
    dates = pd.date_range(start=start_date, periods=PROJECTION_MONTHS + 1, freq="ME")

    # Thresholds in trillions for plotting
    thresh_tril = [THRESH_ABUNDANT_BN / 1000, THRESH_AMPLE_BN / 1000, THRESH_CAUTION_BN / 1000, THRESH_CRISIS_BN / 1000]
    labels = ["Abundant", "Ample", "Caution", "2019 Crisis Level"]
    colors = ["green", "blue", "orange", "red"]
    for i, (t, lab, c) in enumerate(zip(thresh_tril, labels, colors)):
        ax.axhline(y=t, color=c, linestyle="--", linewidth=1.5, alpha=0.9, label=lab)

    # Background zones (filled between thresholds)
    ax.axhspan(THRESH_CRISIS_BN / 1000, THRESH_CAUTION_BN / 1000, alpha=0.15, color="red")
    ax.axhspan(THRESH_CAUTION_BN / 1000, THRESH_AMPLE_BN / 1000, alpha=0.15, color="orange")
    ax.axhspan(THRESH_AMPLE_BN / 1000, THRESH_ABUNDANT_BN / 1000, alpha=0.15, color="blue")
    ax.axhspan(THRESH_ABUNDANT_BN / 1000, 5, alpha=0.1, color="green")

    palette = sns.color_palette("colorblind", n_colors=4)
    scenario_labels = ["A: Warsh Hawk", "B: Moderate", "C: Duration Shift", "D: Crisis Reversal"]
    for (key, lab), color in zip([("A", scenario_labels[0]), ("B", scenario_labels[1]), ("C", scenario_labels[2]), ("D", scenario_labels[3])], palette):
        r = np.array(scenarios[key]["reserves_bn"]) / 1000.0  # to trillions
        ax.plot(dates, r, color=color, linewidth=2.5, label=lab)

    ax.set_xlim(dates[0], dates[-1])
    ax.set_ylim(0, max(4.0, max(r for s in scenarios.values() for r in s["reserves_bn"]) / 1000.0 * 1.05))
    ax.set_ylabel("Bank Reserves (Trillions USD)", fontsize=12, fontweight="medium")
    ax.set_xlabel("Date", fontsize=12, fontweight="medium")
    ax.set_title("Projected Bank Reserves Under Warsh Scenarios", fontsize=14, fontweight="bold")
    ax.legend(loc="best", frameon=True, fontsize=10)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=25)
    fig.tight_layout()
    out_path = OUTPUT_DIR / "reserve_drain_main.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


def chart2_decomposition(scenario_a, start_date):
    """
    Stacked area chart for Scenario A (Warsh Hawk): reserves, ON RRP, TGA, currency, other.
    """
    sns.set_theme(style="whitegrid", font_scale=1.05)
    fig, ax = plt.subplots(figsize=(12, 6))

    months = np.arange(PROJECTION_MONTHS + 1)
    dates = pd.date_range(start=start_date, periods=PROJECTION_MONTHS + 1, freq="ME")

    # For stacked area we need components that sum to total balance sheet (or show liabilities).
    # Fed liabilities (simplified): Reserves + ON RRP + TGA + Currency + Other.
    reserves = np.array(scenario_a["reserves_bn"])
    rrp = np.array(scenario_a["rrp_bn"])
    tga = np.array(scenario_a["tga_bn"])
    # Currency and other: model as cumulative drain from initial level; for stacking we show level at each month.
    # "Currency" and "other" in the equation are flows; for stock we need cumulative or assume a base.
    # Simplification: show reserves, RRP, TGA as stocks; then currency growth and other as cumulative amounts "drained" (so they're not part of Fed BS liability stock). For a liability decomposition we want: Reserves, ON RRP, TGA, and "Other liabilities" (currency + other). So stack: Reserves, RRP, TGA, and a "Currency + Other" that grows. We don't have a level for currency/other—we have flows. So assume initial "other" base from identity: BS = Reserves + RRP + TGA + Currency + Other. We don't have total BS. So just stack the five series we have: use reserves, RRP, TGA, and for "currency" and "other" use cumulative drain as a proxy for the growing part (so the stack shows how reserves shrink and the "drain" categories grow in a cumulative sense). That would double-count. Simpler: stacked area of reserves, ON RRP, TGA (all in billions). Then add two more series: "Currency (cumulative growth)" and "Other (cumulative)" as the amount that has been drained out of reserves into those. So the total stacked = reserves + RRP + TGA + cum_currency + cum_other, which would be constant if we started from a total. Actually the identity is: each month reserves change by -QT + delta_RRP - delta_TGA - currency - other. So the "stock" of currency and other grows by currency_bn and other_bn per month. So at month t: currency_stock = currency_0 + t * 5.5, other_stock = other_0 + t * 2. We don't have currency_0. So for a clean chart, stack only the Fed balance sheet liability components we model: Reserves, ON RRP, TGA. And optionally show "Currency drain" and "Other drain" as separate (non-stacked) cumulative lines, or stack them with an assumed starting level. User asked: "stacked area chart of how each liability component evolves: reserves, ON RRP, TGA, currency, other." So we need all five. For currency and other, the model only has flows. So we'll show reserves, RRP, TGA as levels; currency and other as cumulative flows from 0 (so at month t: 5.5*t and 2*t). Then the "total" would not be constant—it's not a full identity, but it shows the evolution of each component. I'll do: stack reserves, RRP, TGA, currency_cum, other_cum (so 5 layers). Currency cum = 5.5 * (0,1,...,24), other_cum = 2 * (0,1,...,24). So the bottom is reserves, then RRP, then TGA, then currency_cum, then other_cum. That way reserves are the main shrinking part and the "drains" grow. Good.
    currency_cum = np.array(scenario_a["currency_cum_bn"])
    other_cum = np.array(scenario_a["other_cum_bn"])

    # Stack order (bottom to top): reserves, ON RRP, TGA, currency_cum, other_cum
    palette = sns.color_palette("colorblind", n_colors=5)
    ax.fill_between(dates, 0, reserves / 1000, label="Reserves", color=palette[0], alpha=0.85)
    ax.fill_between(dates, reserves / 1000, (reserves + rrp) / 1000, label="ON RRP", color=palette[1], alpha=0.85)
    ax.fill_between(dates, (reserves + rrp) / 1000, (reserves + rrp + tga) / 1000, label="TGA", color=palette[2], alpha=0.85)
    ax.fill_between(dates, (reserves + rrp + tga) / 1000,
                    (reserves + rrp + tga + currency_cum) / 1000, label="Currency (cum. growth)", color=palette[3], alpha=0.85)
    ax.fill_between(dates, (reserves + rrp + tga + currency_cum) / 1000,
                    (reserves + rrp + tga + currency_cum + other_cum) / 1000, label="Other (cum. drains)", color=palette[4], alpha=0.85)

    ax.set_ylabel("Fed Liability Components (Trillions USD)", fontsize=11, fontweight="medium")
    ax.set_xlabel("Date", fontsize=11, fontweight="medium")
    ax.set_title("Fed Liability Decomposition: Warsh Hawk Scenario", fontsize=13, fontweight="bold")
    ax.legend(loc="upper right", frameon=True, fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=25)
    fig.tight_layout()
    out_path = OUTPUT_DIR / "reserve_drain_decomposition.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


def chart3_historical_and_projected(historical_reserves_bn, scenarios, start_date, repo_crisis_date):
    """
    Plot actual TOTRESNS from 2017 to present, then extend with projected paths.
    Mark Sep 2019 repo crisis. Show where each scenario sits relative to historical low.
    """
    sns.set_theme(style="whitegrid", font_scale=1.05)
    fig, ax = plt.subplots(figsize=(14, 7))

    # Historical: from 2017 to latest
    hist = historical_reserves_bn
    hist = hist[hist.index >= "2017-01-01"]
    hist_tril = hist / 1000.0
    ax.plot(hist_tril.index, hist_tril.values, color="black", linewidth=2, label="Actual reserves (TOTRESNS)")

    # Projected paths
    dates_proj = pd.date_range(start=start_date, periods=PROJECTION_MONTHS + 1, freq="ME")
    palette = sns.color_palette("colorblind", n_colors=4)
    for (key, lab), color in zip([
        ("A", "A: Warsh Hawk"), ("B", "B: Moderate"), ("C", "C: Duration Shift"), ("D", "D: Crisis Reversal")
    ], palette):
        r = np.array(scenarios[key]["reserves_bn"]) / 1000.0
        ax.plot(dates_proj, r, color=color, linewidth=2, label=lab)

    # Sep 2019 crisis level and marker
    ax.axhline(y=THRESH_CRISIS_BN / 1000, color="red", linestyle=":", linewidth=1.5, alpha=0.8, label="2019 crisis level (~$1.4T)")
    # Mark the repo crisis point (Sep 2019) on the historical line
    sep2019 = hist_tril[hist_tril.index.to_period("M") == repo_crisis_date.to_period("M")]
    if not sep2019.empty:
        t = sep2019.index[0]
        ax.scatter([t], [sep2019.iloc[0]], color="red", s=80, zorder=5, marker="o", edgecolors="darkred", linewidths=2, label="Sep 2019 repo crisis")

    ax.set_ylabel("Bank Reserves (Trillions USD)", fontsize=11, fontweight="medium")
    ax.set_xlabel("Date", fontsize=11, fontweight="medium")
    ax.set_title("Historical and Projected Bank Reserves (2017–Present + 24mo)", fontsize=13, fontweight="bold")
    ax.legend(loc="best", frameon=True, fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.xticks(rotation=25)
    fig.tight_layout()
    out_path = OUTPUT_DIR / "reserve_drain_historical_projected.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


def get_historical_reserves():
    """Load TOTRESNS from CSV and return monthly series in billions (2017–present)."""
    df = pd.read_csv(CSV_PATH, index_col=0, parse_dates=True)
    df.index = pd.to_datetime(df.index)
    res = df["TOTRESNS"].dropna()
    # Monthly observations are large (billions); daily noise is small. Keep monthly scale.
    monthly = res[res > 100].copy()
    monthly = monthly[~monthly.index.duplicated(keep="last")]
    monthly = monthly.resample("ME").last().ffill()
    if monthly.empty:
        monthly = res.resample("ME").last().ffill()
    return monthly


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    print("Reserve Drain (Plumbing) Model – 24-month projection")
    print("=" * 50)

    # 1. Starting conditions from fred_combined.csv
    start = load_starting_conditions()
    print(f"Starting conditions (Feb 2026): Reserves = {start['reserves_bn']:.1f} $B, "
          f"ON RRP = {start['rrp_bn']:.2f} $B, TGA = {start['tga_bn']:.1f} $B")
    print(f"Currency growth = ${CURRENCY_GROWTH_BN}B/mo, Other drains = ${OTHER_DRAINS_BN}B/mo")
    print()

    # 2. Run all four scenarios
    scenarios = build_all_scenarios(start)
    print("Scenarios: A (Hawk $95B/mo), B (Moderate $40B/mo), C ($0 QT), D (Crisis reversal at mo 6)")

    # 3. Summary table
    summary = summary_table(scenarios, start["reserves_bn"])
    print("\nSummary Table:")
    print(summary.to_string(index=False))
    out_xlsx = OUTPUT_DIR / "model_2a_results.xlsx"
    summary.to_excel(out_xlsx, index=False, sheet_name="Summary")
    print(f"\nSaved: {out_xlsx}")

    # 4. Charts
    chart1_main_projection(scenarios, START_DATE)
    chart2_decomposition(scenarios["A"], START_DATE)
    historical_reserves = get_historical_reserves()
    chart3_historical_and_projected(historical_reserves, scenarios, START_DATE, REPO_CRISIS_DATE)

    print("\nDone.")


if __name__ == "__main__":
    main()
