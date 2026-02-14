"""
Event study of the Warsh Shock on January 30, 2026.
Downloads daily data via yfinance, computes abnormal returns and CAR,
produces 2x3 grid of normalized price charts and summary table.
Outputs: warsh_shock_event_study.png, warsh_shock_results.xlsx.
"""

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf
from scipy import stats as scipy_stats

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR

# Date ranges
START_DATE = "2025-10-01"
END_DATE = "2026-02-14"
EVENT_DATE = pd.Timestamp("2026-01-30")
EST_END = pd.Timestamp("2026-01-27")  # last day of estimation window
EVENT_START = pd.Timestamp("2026-01-28")  # first day of event window

# Assets: (ticker, display name)
ASSETS = [
    ("GC=F", "Gold Futures"),
    ("SI=F", "Silver Futures"),
    ("DX-Y.NYB", "Dollar Index"),
    ("^TNX", "10Y Treasury Yield"),
    ("^GSPC", "S&P 500"),
    ("^VIX", "VIX"),
]


def download_data():
    """Download daily close prices for all assets."""
    tickers = [a[0] for a in ASSETS]
    df = yf.download(
        tickers,
        start=START_DATE,
        end=END_DATE,
        progress=False,
        group_by="ticker",
        auto_adjust=True,
        threads=False,
    )
    df.index = pd.to_datetime(df.index).tz_localize(None)
    # Single ticker: columns are Open, High, Low, Close, Adj Close, Volume
    if len(tickers) == 1:
        close_col = "Adj Close" if "Adj Close" in df.columns else "Close"
        out = df[[close_col]].copy()
        out.columns = [tickers[0]]
        return out.dropna(how="all")
    # MultiIndex: with group_by='ticker' columns are (Ticker, Type) e.g. (GC=F, Close)
    if isinstance(df.columns, pd.MultiIndex):
        level1 = df.columns.get_level_values(1)
        if "Adj Close" in level1:
            out = df.xs("Adj Close", axis=1, level=1).copy()
        else:
            out = df.xs("Close", axis=1, level=1).copy()
        out = out.reindex(columns=tickers)
    else:
        out = df.copy()
    return out.dropna(how="all")


def compute_returns(prices: pd.DataFrame):
    """Daily log returns (so CAR = sum of AR in log space)."""
    return np.log(prices / prices.shift(1))


def run_event_study(prices: pd.DataFrame, returns: pd.DataFrame):
    """
    For each asset: estimation-window stats, abnormal returns, CAR, t-stats.
    Returns dict of DataFrames and series keyed by ticker.
    """
    results = {}
    for ticker, name in ASSETS:
        if ticker not in returns.columns:
            continue
        ret = returns[ticker].dropna()
        est_mask = (ret.index >= START_DATE) & (ret.index <= EST_END)
        event_mask = (ret.index >= EVENT_START) & (ret.index <= END_DATE)
        est_ret = ret[est_mask].dropna()
        event_ret = ret[event_mask]

        mu = est_ret.mean()
        sigma = est_ret.std()
        if sigma == 0 or np.isnan(sigma):
            sigma = np.nan
        n_est = len(est_ret)

        # Abnormal return = actual - expected (expected = avg from estimation)
        ar = event_ret - mu
        car = ar.cumsum()
        # t-stat for AR: (AR - 0) / (sigma_AR); sigma_AR ≈ sigma * sqrt(1 + 1/n_est) for event window
        se_ar = sigma * np.sqrt(1 + 1 / n_est) if n_est and sigma and not np.isnan(sigma) else np.nan
        t_stat = (ar / se_ar) if se_ar and not np.isnan(se_ar) else pd.Series(index=ar.index, dtype=float)

        # 1-day AR on event date (Jan 30)
        ar_1d = ar.loc[EVENT_DATE] if EVENT_DATE in ar.index else np.nan
        t_1d = t_stat.loc[EVENT_DATE] if EVENT_DATE in t_stat.index else np.nan

        # 5-day CAR: event date + 4 trading days after (or available)
        event_dates = ar.index.sort_values()
        idx_event = event_dates.get_loc(EVENT_DATE) if EVENT_DATE in event_dates else 0
        window_5d = event_dates[idx_event : idx_event + 5]
        car_5d = car.loc[window_5d].iloc[-1] if len(window_5d) else np.nan

        # Full event window CAR
        car_full = car.iloc[-1] if len(car) else np.nan

        # t-stat for CAR: use last day's cumulative; se(CAR) = sigma * sqrt(L * (1 + L/n_est))
        L = len(ar)
        se_car = sigma * np.sqrt(L * (1 + L / n_est)) if n_est and L and sigma and not np.isnan(sigma) else np.nan
        t_car = (car_full / se_car) if se_car and not np.isnan(se_car) else np.nan

        results[ticker] = {
            "name": name,
            "mu": mu,
            "sigma": sigma,
            "n_est": n_est,
            "ar": ar,
            "car": car,
            "t_stat": t_stat,
            "ar_1d": ar_1d,
            "car_5d": car_5d,
            "car_full": car_full,
            "t_1d": t_1d,
            "t_car": t_car,
            "prices": prices[ticker].reindex(returns.index).ffill().dropna(),
        }
    return results


def significance_marker(p):
    """Return *, **, or '' based on p-value."""
    if np.isnan(p):
        return ""
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return ""


def make_summary_table(results: dict) -> pd.DataFrame:
    """Build summary table: Asset, 1-day AR, 5-day CAR, full CAR, t-stat, sig."""
    rows = []
    for ticker, name in ASSETS:
        if ticker not in results:
            continue
        r = results[ticker]
        p_1d = 2 * (1 - scipy_stats.t.cdf(abs(r["t_1d"]), r["n_est"] - 1)) if not np.isnan(r["t_1d"]) else np.nan
        p_car = 2 * (1 - scipy_stats.t.cdf(abs(r["t_car"]), r["n_est"] - 1)) if not np.isnan(r["t_car"]) else np.nan
        sig_1d = significance_marker(p_1d)
        sig_car = significance_marker(p_car)
        rows.append({
            "Asset": r["name"],
            "1-day AR (%)": r["ar_1d"] * 100 if not np.isnan(r["ar_1d"]) else np.nan,
            "5-day CAR (%)": r["car_5d"] * 100 if not np.isnan(r["car_5d"]) else np.nan,
            "Full CAR (%)": r["car_full"] * 100 if not np.isnan(r["car_full"]) else np.nan,
            "t-stat (1-day)": r["t_1d"],
            "t-stat (CAR)": r["t_car"],
            "Sig (1-day)": sig_1d,
            "Sig (CAR)": sig_car,
        })
    return pd.DataFrame(rows)


def plot_grid(results: dict):
    """2x3 grid: price normalized to 100 on Jan 27, red dashed line on Jan 30."""
    fig, axes = plt.subplots(2, 3, figsize=(16, 10), constrained_layout=True)
    axes = axes.flatten()
    norm_date = pd.Timestamp("2026-01-27")

    for i, (ticker, name) in enumerate(ASSETS):
        if ticker not in results:
            axes[i].set_visible(False)
            continue
        r = results[ticker]
        prices = r["prices"]
        if prices.empty:
            axes[i].set_visible(False)
            continue
        # Normalize to 100 on last trading day on or before norm_date
        norm_idx = prices.index[prices.index <= norm_date]
        if len(norm_idx) == 0:
            base = prices.iloc[0]
        else:
            base = prices.loc[norm_idx.max()]
        series = (prices / base * 100).sort_index()
        ax = axes[i]
        ax.plot(series.index, series.values, color="steelblue", linewidth=2)
        ax.axvline(EVENT_DATE, color="red", linestyle="--", linewidth=1.5, zorder=5)
        car_pct = r["car_full"] * 100
        car_str = f"{car_pct:+.2f}%" if not np.isnan(car_pct) else "N/A"
        ax.set_title(f"{name}\nTotal CAR = {car_str}", fontsize=11, fontweight="medium")
        ax.set_ylabel("Price (norm. to 100)")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")
        ax.grid(True, alpha=0.3)
        ax.set_xlim(series.index.min(), series.index.max())

    for j in range(len(ASSETS), len(axes)):
        axes[j].set_visible(False)

    fig.suptitle("Warsh Shock Event Study — Prices Normalized to 100 on Jan 27, 2026", fontsize=14, fontweight="bold", y=1.02)
    return fig


def main():
    print("Downloading data...")
    prices = download_data()
    # Keep only requested tickers that we got
    tickers_in_data = [a[0] for a in ASSETS if a[0] in prices.columns]
    prices = prices[[c for c in prices.columns if c in tickers_in_data]]

    returns = compute_returns(prices)
    print("Running event study...")
    results = run_event_study(prices, returns)

    # Summary table
    summary = make_summary_table(results)
    print("\n" + "=" * 80)
    print("Warsh Shock Event Study — Summary Table")
    print("Event date: January 30, 2026  |  Estimation: Oct 1, 2025 – Jan 27, 2026  |  Event window: Jan 28 – Feb 14, 2026")
    print("=" * 80)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)
    pd.set_option("display.float_format", lambda x: f"{x:.4f}" if abs(x) < 1e3 else f"{x:.2f}")
    print(summary.to_string(index=False))
    print("\n* p<0.05, ** p<0.01")

    # Charts
    fig = plot_grid(results)
    chart_path = OUTPUT_DIR / "warsh_shock_event_study.png"
    fig.savefig(chart_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"\nCharts saved to {chart_path}")

    # Excel: summary + optional sheets (AR/CAR by asset)
    excel_path = OUTPUT_DIR / "warsh_shock_results.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as w:
        summary.to_excel(w, sheet_name="Summary", index=False)
        for ticker in results:
            r = results[ticker]
            df_ar = pd.DataFrame({"Date": r["ar"].index, "AR": r["ar"].values, "CAR": r["car"].values})
            df_ar.to_excel(w, sheet_name=r["name"][:31], index=False)
    print(f"Results saved to {excel_path}")


if __name__ == "__main__":
    main()
