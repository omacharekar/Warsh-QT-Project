# Analyzing the Impact of Quantitative Tightening on Money Supply & Financial Markets

**A Student's Guide to Building a Multi-Model Analytical Framework**

---

## Table of Contents

1. [Why This Project, Why Now](#1-why-this-project-why-now)
2. [The Problem Statement](#2-the-problem-statement)
3. [Key Concepts](#3-key-concepts-you-need-to-understand-first)
4. [Data Sources](#4-free-data-sources-your-toolkit)
5. [Models to Build](#5-models-to-build-phased-approach)
6. [Tools & Learning Resources](#6-suggested-tools--learning-resources)
7. [Weekly Project Plan](#7-weekly-project-plan)
8. [How We'll Work Together](#8-how-well-work-together)
9. [Glossary](#9-glossary-of-key-terms)

---

## 1. Why This Project, Why Now

On January 30, 2026, President Trump nominated **Kevin Warsh** as the next Federal Reserve Chair, succeeding Jerome Powell (whose term expires May 2026). Warsh is a known critic of the Fed's bloated balance sheet and has long advocated for aggressively shrinking it. The Fed's balance sheet currently stands at **~$6.6 trillion**, down from a peak of ~$9 trillion, but still astronomically high compared to the ~$800 billion it held before the 2008 financial crisis.

The market reaction — dubbed the **"Warsh Shock"** — was immediate:

- **Gold** plunged ~15% from record highs near $5,600/oz within 48 hours
- **Silver** suffered a flash crash from ~$120 to below $85
- **US Dollar** strengthened sharply as the "debasement trade" reversed
- **Long-term Treasury yields** rose on expectations of balance sheet runoff
- **Equities** initially wobbled but stabilized as rate-cut expectations held

This creates a *perfect real-world laboratory* for studying the transmission mechanisms of monetary policy.

---

## 2. The Problem Statement

**Core Question:** *How does the Federal Reserve's balance sheet size and composition — particularly Quantitative Tightening (QT) — transmit through the financial system to affect money supply, interest rates, asset prices, currency values, and commodity markets?*

**Sub-questions to investigate:**

1. What is the mechanical relationship between the Fed's balance sheet and bank reserves / money supply (M1, M2)?
2. How does QT affect short-term funding markets (repo rates, fed funds)?
3. What is the transmission from QT → Treasury yields → mortgage rates → equity valuations?
4. Why did the "Warsh Shock" hit gold/silver so hard, and what does that tell us about the dollar-debasement narrative?
5. Under different QT pace scenarios, what happens to financial conditions?
6. Are there historical parallels (2017–2019 QT, Volcker era) we can use for calibration?

---

## 3. Key Concepts You Need to Understand First

Before building models, spend time deeply understanding each of these building blocks. Think of them as layers of an onion — each layer wraps around the previous one.

### Layer 1: The Fed's Balance Sheet (Foundation)

| Component | What It Is | Why It Matters |
|-----------|------------|----------------|
| **Assets: Treasury Securities** | UST bonds the Fed bought via QE (~$4.2T) | Removing these = private market must absorb the supply |
| **Assets: MBS** | Mortgage-backed securities (~$2.2T) | Affects mortgage rates directly when sold/run off |
| **Liabilities: Bank Reserves** | Cash that commercial banks hold at the Fed | The "fuel" for lending; QT drains this |
| **Liabilities: Reverse Repo (RRP)** | Overnight lending facility | Acts as a liquidity buffer; absorbs/releases cash |
| **Liabilities: Treasury General Account (TGA)** | The government's checking account at the Fed | When Treasury spends, reserves go UP; when it collects taxes, reserves go DOWN |

**Key insight:** QT doesn't destroy money directly — it drains *reserves* from the banking system, which *constrains* the system's ability to create money through lending.

### Layer 2: Money Supply Mechanics

- **Monetary Base (M0)** = Currency in circulation + Bank reserves
- **M1** = Currency + Demand deposits + Other checkable deposits
- **M2** = M1 + Savings deposits + Small time deposits + Retail money market funds
- **Money Multiplier** = M2 / Monetary Base (how much "real economy money" each dollar of base money creates)

QT shrinks the monetary base. Whether M2 contracts depends on whether banks were actually using those reserves to lend (the multiplier effect).

### Layer 3: Interest Rate Transmission

```
Fed Balance Sheet Shrinks
       ↓
Bank Reserves Decline
       ↓
Short-term funding costs rise (fed funds, repo rates)
       ↓
Treasury yields rise (more supply for private market to absorb)
       ↓
Mortgage rates rise    Corporate borrowing costs rise    Dollar strengthens
       ↓                        ↓                              ↓
Housing slows          Equity valuations compress        Gold/commodities fall
```

### Layer 4: The "Warsh Trilemma"

Kevin Warsh faces three choices, and he can only pick one:

1. **Shrink the balance sheet aggressively** → Accepts higher long-term yields → Hurts housing, increases government interest expense
2. **Maintain holdings at lower yields** → Perpetuates the "monetary dominance" he has criticized his entire career
3. **Roll maturing securities into shorter duration** → Kicks the can down the road, converts Fed portfolio into floating-rate liability

Your models should test the market implications of each path.

---

## 4. Free Data Sources (Your Toolkit)

### Primary Source: FRED (Federal Reserve Economic Data)

**Website:** https://fred.stlouisfed.org

FRED is your single most important resource. It's free, comprehensive, and downloadable as CSV. Here are the exact series you need:

| Data Series | FRED Code | Frequency |
|-------------|-----------|-----------|
| Fed Total Assets | `WALCL` | Weekly |
| Fed Treasury Holdings | `TREAST` | Weekly |
| Fed MBS Holdings | `WSHOMCB` | Weekly |
| Monetary Base | `BOGMBASE` | Monthly |
| M1 Money Supply | `M1SL` | Monthly |
| M2 Money Supply | `M2SL` | Monthly |
| Real M2 Money Stock | `M2REAL` | Monthly |
| Money Velocity (M2) | `M2V` | Quarterly |
| Bank Reserves | `TOTRESNS` | Monthly |
| Reverse Repo (ON RRP) | `RRPONTSYD` | Daily |
| Treasury General Account | `WTREGEN` | Weekly |
| Federal Funds Rate (Effective) | `FEDFUNDS` | Monthly |
| 2-Year Treasury Yield | `DGS2` | Daily |
| 10-Year Treasury Yield | `DGS10` | Daily |
| 30-Year Treasury Yield | `DGS30` | Daily |
| 10Y-2Y Spread (Yield Curve) | `T10Y2Y` | Daily |
| 30-Year Mortgage Rate | `MORTGAGE30US` | Weekly |
| S&P 500 | `SP500` | Daily |
| US Dollar Index (Broad) | `DTWEXBGS` | Daily |
| CPI (All Urban) | `CPIAUCSL` | Monthly |
| Core PCE | `PCEPILFE` | Monthly |
| Real GDP | `GDPC1` | Quarterly |
| Breakeven Inflation (5Y) | `T5YIE` | Daily |
| Breakeven Inflation (10Y) | `T10YIE` | Daily |
| Bank Credit (All Commercial Banks) | `TOTBKCR` | Weekly |
| Consumer Credit | `TOTALSL` | Monthly |
| ICE BofA Corporate Bond Spread | `BAMLC0A0CM` | Daily |
| CBOE Volatility Index (VIX) | `VIXCLS` | Daily |

**How to download:** Go to any series page → Click "Download" → Select CSV → Choose date range.

**Pro tip:** Use the [FRED API](https://fred.stlouisfed.org/docs/api/) (free key) to pull data directly into Python.

### Additional Free Sources

| Source | URL | What You Get |
|--------|-----|--------------|
| **Fed H.4.1 Release** | federalreserve.gov/releases/h41/ | Weekly balance sheet breakdown |
| **Fed H.6 Release** | federalreserve.gov/releases/h6/ | Money stock measures |
| **Treasury.gov** | fiscaldata.treasury.gov | Debt outstanding, auction data, TGA balance |
| **Yahoo Finance** | finance.yahoo.com | Gold (GC=F), Silver (SI=F), DXY, equity indices |
| **CBOE** | cboe.com | VIX data |
| **BIS Statistics** | bis.org/statistics | Global credit, cross-border flows |
| **IMF Data** | data.imf.org | International comparisons, reserves |
| **World Gold Council** | gold.org/goldhub | Gold demand/supply data, central bank buying |
| **CME FedWatch** | cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html | Market-implied rate probabilities |
| **NY Fed** | newyorkfed.org/markets | Open market operations, repo data |

---

## 5. Models to Build (Phased Approach)

### Phase 1: Descriptive & Historical Analysis (Weeks 1–2)

**Goal:** Understand what happened historically during QE/QT cycles.

| Model | Description |
|-------|-------------|
| **1A: Balance Sheet ↔ Money Supply** | Plot WALCL, BOGMBASE, M1SL, M2SL from 2008; rolling correlations; investigate post-2020 correlation breakdown |
| **1B: QT Episode Comparison** | Compare QT 2017–2019 vs. 2022–2025: pace, reserves, repo stress, equity drawdowns, yield curve |
| **1C: "Warsh Shock" Event Study** | Daily data Jan 27 – Feb 7, 2026; abnormal returns vs. 60-day averages for Gold, Silver, DXY, 10Y, S&P 500, VIX |

**Tools:** Python (pandas, matplotlib) or Excel.

---

### Phase 2: Transmission Mechanism Models (Weeks 3–5)

**Goal:** Quantify how QT transmits through the system.

| Model | Description |
|-------|-------------|
| **2A: Reserve Drain (Plumbing)** | Mechanical model: Change in Reserves = - QT Runoff + ΔRRP + ΔTGA + other. Scenario paces: aggressive ($60B/mo UST + $35B MBS), moderate ($25B UST), cautious (roll to shorter duration), status quo |
| **2B: IS-LM Framework** | QT shifts LM left; model equilibrium under Warsh scenarios |
| **2C: Term Premium / Duration Supply** | Preferred-habitat style: more duration supply → higher term premium. Calibrate ~3–8 bp per $100B; apply to scenarios |

---

### Phase 3: Multi-Asset Impact Models (Weeks 5–7)

**Goal:** Model how QT flows through to different asset classes.

| Model | Description |
|-------|-------------|
| **3A: Financial Conditions Index** | FCI = weighted (Fed Funds, 10Y, corp spread, S&P, DXY, mortgage rate); compare to FRED `NFCI` |
| **3B: Gold/Silver ↔ Real Rates** | Regression: Gold = f(real rate, DXY, VIX); real rate = DGS10 − T10YIE |
| **3C: Equity Valuation** | P = E/(r−g); sensitivity of S&P P/E to 10Y (e.g. 2–3x per 100 bp) |
| **3D: Dollar Strength** | DXY ≈ f(US-foreign rate differential, relative QT/QE, risk appetite) |

---

### Phase 4: Scenario Analysis & Stress Testing (Weeks 7–9)

**Goal:** Unified scenario framework.

**Scenario Dashboard Parameters:**

| Parameter | Scenario A: Warsh Hawk | Scenario B: Moderate | Scenario C: Status Quo | Scenario D: Crisis Reversal |
|-----------|------------------------|----------------------|------------------------|-----------------------------|
| Monthly QT (Treasuries) | $60B | $25B | $0 (buy bills) | −$50B (QE) |
| Monthly QT (MBS) | $35B | $15B | $0 | −$25B |
| Fed Funds (end 2026) | 4.00% | 3.75% | 4.25% | 3.00% |
| Balance Sheet (end 2026) | $5.5T | $6.2T | $6.8T | $7.5T |

**For each scenario, project:** M2 path, reserve adequacy (danger zone &lt;$2.5T), 10Y yield, 30Y mortgage rate, S&P fair value, gold range, DXY range, FCI.

**Stress Test:** At what QT pace do reserves hit danger levels (e.g. 2019-style ~$1.5T)? How fast?

---

### Phase 5: Advanced Models (Weeks 9–12, Optional)

| Model | Description |
|-------|-------------|
| **5A: VAR** | Variables: Fed Assets, M2, Fed Funds, 10Y, S&P 500, Gold, DXY; impulse response functions via `statsmodels` |
| **5B: Regime-Switching** | Markov regime: "risk-on QE" vs. "risk-off QT"; transition probabilities |
| **5C: Monte Carlo** | Distributions for QT pace, GDP, inflation; 10k runs → confidence intervals for 10Y, etc. |

---

## 6. Suggested Tools & Learning Resources

### Programming (All Free)

| Tool | Purpose | Install |
|------|---------|--------|
| **Python** | Primary analysis | python.org |
| **Jupyter** | Interactive analysis | jupyter.org or Google Colab |
| **pandas** | Data manipulation | `pip install pandas` |
| **matplotlib / seaborn** | Visualization | `pip install matplotlib seaborn` |
| **statsmodels** | Regression, VAR, time series | `pip install statsmodels` |
| **fredapi** | FRED data in Python | `pip install fredapi` |
| **yfinance** | Yahoo Finance data | `pip install yfinance` |
| **numpy / scipy** | Numerical computing, Monte Carlo | `pip install numpy scipy` |

### Learning Resources

| Resource | What You'll Learn |
|----------|-------------------|
| Khan Academy: Macroeconomics | Money supply, Fed operations, IS-LM |
| MIT OpenCourseWare 14.02 | Intermediate Macroeconomics |
| Yale: Financial Markets (Shiller), Coursera | Market fundamentals, behavioral finance |
| [Fed Education](https://www.federalreserve.gov/education.htm) | How the Fed works |
| [NY Fed: Open Market Operations](https://www.newyorkfed.org/markets/desk-operations) | How QT is executed |
| Brookings Hutchins Center | Plain-English Fed explainers |
| FRED Blog | Data analysis tutorials |
| Perry Mehrling: Economics of Money and Banking, Coursera | Monetary plumbing |

### Key Papers (Google Scholar, SSRN, Fed sites)

- Bernanke (2020) — "The New Tools of Monetary Policy"
- Greenwood, Hanson, Stein (2015) — "A Comparative-Advantage Approach to Government Debt Maturity"
- Krishnamurthy & Vissing-Jorgensen (2011) — "The Effects of Quantitative Easing on Interest Rates"
- Duffie & Krishnamurthy (2016) — "Passthrough Efficiency in the Fed's New Monetary Policy Setting"
- Adrian, Crump, Moench — NY Fed term premium model (newyorkfed.org)

---

## 7. Weekly Project Plan

| Week | Focus | Deliverable |
|------|-------|-------------|
| 1 | Concept study; set up Python/Jupyter | Notes on QE/QT, balance sheet, money multiplier |
| 2 | FRED data; Model 1A + 1C | Historical charts + Warsh Shock event study table |
| 3 | Model 1B + 2A | QT episode comparison + reserve projection |
| 4 | Model 2B + 2C | IS-LM diagram + term premium estimate |
| 5 | Model 3A + 3B | FCI regression + projected gold range |
| 6 | Model 3C + 3D | S&P fair value table + DXY projection |
| 7 | Scenario Dashboard (Phase 4) | Unified scenario comparison table |
| 8 | Stress testing | Stress test report |
| 9–10 | VAR or Monte Carlo | Impulse responses or outcome distributions |
| 11–12 | Write-up, presentation | Final report with models, scenarios, conclusions |

---

## 8. How We'll Work Together

1. **Each week**, bring questions on concepts, data, or code.
2. **Support available:** Python code, debugging, interpretation, theory, and review.
3. **Start small** — get Model 1A solid before adding complexity.
4. **Document everything** — use a Jupyter notebook to tell the story.
5. **Challenge assumptions** — good models state what they *don’t* capture.

### Immediate First Steps

- [ ] Get a free [FRED API key](https://fred.stlouisfed.org/docs/api/)
- [ ] Install Python + Jupyter (or use [Google Colab](https://colab.research.google.com))
- [ ] Read Brookings "Hutchins Center Explains" on QE and the balance sheet
- [ ] Read the NY Fed page on open market operations
- [ ] Download first dataset: **WALCL** (Fed total assets) from 2008 to present
- [ ] Return and build Model 1A

---

## 9. Glossary of Key Terms

| Term | Definition |
|------|------------|
| **QE (Quantitative Easing)** | Fed buys bonds → injects reserves → expands balance sheet |
| **QT (Quantitative Tightening)** | Fed lets bonds mature or sells → drains reserves → shrinks balance sheet |
| **Reserves** | Cash banks hold at the Fed; QT drains these |
| **Repo Market** | Short-term lending against Treasury collateral; sensitive to reserve levels |
| **Term Premium** | Extra yield for holding long-term bonds; QT tends to increase it |
| **Fed Put** | Belief the Fed will support markets in stress; Warsh may weaken it |
| **Debasement Trade** | Buying gold/crypto/hard assets on fear of money printing |
| **Real Rate** | Nominal rate minus inflation |
| **Duration Risk** | Bond price sensitivity to rates; QT pushes more duration to private sector |
| **Financial Conditions** | How easy/tight it is to borrow and take risk |
| **Ample Reserves** | Framework where the Fed keeps reserves high so it doesn’t manage daily liquidity |
| **Neutral Rate (r\*)** | Rate that neither stimulates nor restrains the economy (~3% in many projections) |

---

*This README is the project charter. Refine it as you learn and as new data arrives. The project is live: every FOMC meeting, Warsh speech, and market move is another data point for your models.*

*Let's get started.*
