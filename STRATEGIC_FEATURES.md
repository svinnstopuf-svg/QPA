# Strategic Features - V4.0 Position Trading System

## Overview
These features optimize the system for real-world Avanza ISK trading with intelligent risk management.

---

## 1. MiFID II Proxy Mapping 🇪🇺

### Problem
US-domiciled ETFs (TLT, GLD, DBC, etc.) **cannot be purchased** on Avanza ISK due to MiFID II/UCITS regulations.

### Solution
Automatic proxy mapping to EU UCITS equivalents.

### Usage
```python
from instruments_universe_1200 import get_mifid_ii_proxy

# System detects buy signal on TLT
us_ticker = "TLT"
eu_proxy = get_mifid_ii_proxy(us_ticker)
print(f"Trade {eu_proxy} instead")  # Output: Trade IS04.DE instead
```

### Complete Mapping Table

| US ETF | EU UCITS Proxy | Description |
|--------|----------------|-------------|
| **Treasury Bonds** |
| TLT | IS04.DE | iShares $ Treasury Bond 20+yr |
| IEF | IBTE.DE | iShares $ Treasury Bond 7-10yr |
| SHY | IBTS.DE | iShares $ Treasury Bond 1-3yr |
| **Corporate/High Yield** |
| LQD | IUAA.L | iShares $ Corp Bond |
| HYG | IHYG.L | iShares $ High Yield Corp Bond |
| AGG | EUNA.DE | iShares Core € Govt Bond |
| **Gold & Precious Metals** |
| GLD | SGLD.L | Invesco Physical Gold ETC |
| IAU | IGLN.L | iShares Physical Gold ETC |
| GDX | JGLD.L | VanEck Gold Miners |
| SLV | ISLN.L | iShares Physical Silver ETC |
| **Commodities** |
| DBC | EXXT.DE | iShares Diversified Commodity |
| USO | CRUD.L | WisdomTree WTI Crude Oil |
| UNG | NGAS.L | WisdomTree Natural Gas |
| **Broad Market** |
| VT | VWRL.L | Vanguard FTSE All-World |
| ACWI | ISAC.L | iShares MSCI ACWI |
| VWO | VFEM.L | Vanguard FTSE Emerging Markets |
| EEM | EIMI.L | iShares Core MSCI EM IMI |

### Integration
Dashboard automatically suggests EU proxy when US ETF triggers buy signal.

---

## 2. FX Guard - USD/SEK Mean Reversion 💱

### Problem
When USD/SEK is at extreme levels (e.g., 11.50), buying US stocks risks currency reversal eating your alpha.

### Solution
Z-score detection against 200-day USD/SEK mean with automatic score adjustment.

### Logic

| USD/SEK Z-Score | Interpretation | Score Adjustment | Action |
|-----------------|----------------|------------------|--------|
| **Z > +2.0** | Extreme expensive | **-15%** | ⚠️ Avoid US positions |
| **Z > +1.5** | Expensive | **-10%** | ⚡ Reduce US exposure |
| **-1.5 < Z < +1.5** | Fair value | **0%** | ✅ Normal trading |
| **Z < -1.5** | Cheap USD | **+5%** | 🎯 Opportunity for US |

### Example Calculation
```python
from instruments_universe_1200 import calculate_usd_sek_zscore, get_fx_adjustment_factor

# Current market data
current_rate = 11.50  # USD/SEK today
mean_200d = 10.50     # 200-day average
std_200d = 0.40       # 200-day std dev

# Calculate Z-score
zscore = calculate_usd_sek_zscore(current_rate, mean_200d, std_200d)
# Output: +2.50 (extreme expensive)

# Get score adjustment
adjustment = get_fx_adjustment_factor(zscore)
# Output: 0.85 (-15% penalty)

# Apply to US ticker score
us_score = 85  # Original score for AAPL setup
adjusted_score = us_score * adjustment
# Output: 72.25 (penalized due to extreme USD)
```

### Real-World Scenario
**January 2026**: USD/SEK = 11.50 (Z = +2.5)
- System finds Double Bottom in AAPL (EV = 12%, RRR = 4.0)
- Original score: 85/100
- **FX Guard triggers**: Score reduced to 72/100 (-15%)
- Warning: "USD extremely expensive vs SEK. Currency reversal risk."

**Result**: Position size reduced or skipped in favor of Swedish tickers (0% FX cost).

---

## 3. Sector Volatility Adjustment 📊

### Problem
A "Double Bottom" in NEE (Utility, β=0.70) requires **different risk management** than NVDA (Tech, β=1.25).

Raw EV comparison is misleading without volatility normalization.

### Solution
Beta-adjusted scoring that normalizes returns against sector volatility.

### Sector Volatility Factors

| Sector | Factor | Interpretation |
|--------|--------|----------------|
| **Utilities** | 0.70x | Very low volatility (defensive) |
| **Consumer Staples** | 0.75x | Low volatility (defensive) |
| **Health Care** | 1.00x | Medium volatility (neutral) |
| **Industrials** | 1.00x | Medium volatility (neutral) |
| **Communication Services** | 1.05x | Average volatility |
| **Real Estate** | 1.05x | Average volatility |
| **Consumer Discretionary** | 1.10x | Above-average volatility |
| **Financials** | 1.15x | Above-average volatility |
| **Materials** | 1.20x | High volatility (cyclical) |
| **Information Technology** | 1.25x | High volatility |
| **Energy** | 1.35x | Very high volatility |

### Usage Example
```python
from instruments_universe_1200 import get_sector_for_ticker, get_sector_volatility_factor

# Ticker 1: NEE (Utility)
sector_nee = get_sector_for_ticker("NEE")  # "Utilities"
vol_factor_nee = get_sector_volatility_factor(sector_nee)  # 0.70x

# Ticker 2: NVDA (Tech)
sector_nvda = get_sector_for_ticker("NVDA")  # "Information Technology"
vol_factor_nvda = get_sector_volatility_factor(sector_nvda)  # 1.25x

# Both have same raw EV: 10%
raw_ev = 10.0

# Volatility-adjusted EV (Sharpe-like)
adj_ev_nee = raw_ev / vol_factor_nee   # 10 / 0.70 = 14.3% (better risk-adjusted)
adj_ev_nvda = raw_ev / vol_factor_nvda # 10 / 1.25 = 8.0% (worse risk-adjusted)

print(f"NEE adjusted EV: {adj_ev_nee:.1f}%")
print(f"NVDA adjusted EV: {adj_ev_nvda:.1f}%")
```

### Real-World Impact

**Scenario**: Sunday Dashboard finds 2 setups with identical raw metrics:

| Ticker | Sector | EV | RRR | Raw Score |
|--------|--------|-----|-----|-----------|
| NEE | Utilities | 10% | 4.0 | 80 |
| NVDA | Tech | 10% | 4.0 | 80 |

**After Volatility Adjustment**:

| Ticker | Vol Factor | Adj EV | Adj Score | Ranking |
|--------|-----------|--------|-----------|---------|
| NEE | 0.70x | 14.3% | **92** | 🥇 #1 |
| NVDA | 1.25x | 8.0% | **72** | #2 |

**Result**: NEE ranked higher due to superior risk-adjusted returns.

---

## Integration with Scoring System

### Current Score Formula (V4.0)
```python
score = (EV * 30) + (RRR * 15) + (sample_size_factor * 10) + ...
```

### Enhanced Score Formula (with Strategic Features)
```python
# 1. Base score (unchanged)
base_score = (EV * 30) + (RRR * 15) + (sample_size_factor * 10) + ...

# 2. Sector volatility adjustment
sector = get_sector_for_ticker(ticker)
vol_factor = get_sector_volatility_factor(sector)
adjusted_ev = EV / vol_factor
vol_adjusted_score = base_score * (adjusted_ev / EV)  # Normalize

# 3. FX Guard adjustment (if US ticker)
if is_us_ticker(ticker):
    fx_factor = get_fx_adjustment_factor(usd_sek_zscore)
    final_score = vol_adjusted_score * fx_factor
else:
    final_score = vol_adjusted_score

# 4. MiFID II proxy (for display)
if ticker in MIFID_II_PROXY_MAP:
    tradeable_ticker = get_mifid_ii_proxy(ticker)
    show_warning = True
```

---

## Testing

Run system health check to verify all features:
```bash
python instruments_universe_1200.py
```

Expected output:
```
STRATEGIC FEATURES TEST
================================================================================

1. MiFID II Proxy Mapping:
   TLT → IS04.DE (proxy found)
   GLD → SGLD.L (proxy found)
   DBC → EXXT.DE (proxy found)
   VT → VWRL.L (proxy found)

2. Sector Volatility Factors (Beta Adjustment):
   Utilities                 0.70x
   Consumer Staples          0.75x
   Information Technology    1.25x
   Energy                    1.35x

3. FX Guard (USD/SEK Mean Reversion):
   USD/SEK=11.50 (Z=+2.50): 85.00% score → Extreme expensive
   USD/SEK=11.00 (Z=+1.67): 90.00% score → Expensive
   USD/SEK=10.50 (Z=+0.00): 100.00% score → Fair value
   USD/SEK=10.00 (Z=-1.67): 105.00% score → Cheap
```

---

## Next Steps

1. **Integrate into `sunday_dashboard.py`**:
   - Import functions from `instruments_universe_1200.py`
   - Apply FX adjustment to US tickers
   - Apply sector volatility normalization
   - Display MiFID II proxy warnings

2. **Fetch USD/SEK Data**:
   - Add `USDSEK=X` to Yahoo Finance fetch
   - Calculate 200-day rolling mean/std
   - Pass to FX Guard functions

3. **Dashboard Display Enhancements**:
   ```
   Ticker: AAPL
   Sector: Information Technology (Vol: 1.25x)
   FX Warning: USD extremely expensive (Z=+2.5) - Score reduced 15%
   Raw Score: 85 → Adjusted Score: 61
   ```

4. **Weekly Decision Maker Integration**:
   - Auto-suggest EU proxy when US ETF triggers
   - Flag extreme FX scenarios in email report
   - Sort by volatility-adjusted EV instead of raw EV
