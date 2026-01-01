# Renaissance-Level Statistical Features

This document describes all advanced features implemented in the Quant Pattern Analyzer, inspired by Renaissance Technologies' approach to quantitative trading.

## 7-Step Value Extraction Framework

### ✅ Step 1: Lowered Thresholds for Broader Pattern Discovery
**Status**: Complete

**Implementation**:
- `min_occurrences`: 30 → 15 (allows patterns with fewer observations)
- `min_confidence`: 0.70 → 0.55 (casts wider net)
- Data period: 2y → 15y (ensures long-term reliability)

**Philosophy**: Renaissance finds value by combining 10-20 weak signals. We need to detect more pattern candidates, even if individually weak.

**Location**: `main.py` lines 115-118

---

### ✅ Step 2: Regime-Filtered Trading Strategies
**Status**: Complete

**Implementation**:
- `TradingStrategyGenerator` class filters patterns by regime performance
- Only trades patterns when in favorable market regime
- Requires minimum 0.10% edge after 0.02% transaction costs
- Shows which regime to trade in: `high_vol`, `low_vol`, `uptrend`, `downtrend`, etc.

**Example Output**:
```
HANDELBARA STRATEGIER (Renaissance-filtrerade)
1. November-April (Stark säsong)
   Max edge: 0.16% i high_vol (138 obs)
   Handla endast när: high_vol edge >= 0.16%
```

**Philosophy**: Patterns don't work all the time. Only trade when conditions are right.

**Location**: `src/trading/strategy_generator.py` (212 lines)

---

### ✅ Step 3: Multi-Pattern Combination with Correlation Penalty
**Status**: Complete

**Implementation**:
- `PatternCombiner` class aggregates multiple pattern signals
- Weighted average based on pattern quality (observations × confidence)
- Automatic 50% correlation penalty (avoids double-counting)
- Regime-specific activation (only active patterns contribute)
- Confidence scaling: Strong (>3 patterns), Moderate (2-3), Weak (1)

**Example Output**:
```
KOMBINERAD STRATEGI (Multi-Pattern Aggregation)
Antal kombinerade mönster: 1
Aggregerad edge: 0.09%
Korrelationsstraff: -0.0%
⚠️ WEAK: 0.09% aggregate edge - Monitor only
```

**Philosophy**: Renaissance combines weak signals into strong portfolio. Correlation kills diversification.

**Location**: `src/trading/pattern_combiner.py` (230 lines)

---

### ✅ Step 4: Walk-Forward Backtesting Engine
**Status**: Complete

**Implementation**:
- `Backtester` class with realistic costs: 0.02% transaction + 0.01% slippage
- Walk-forward validation: 70% in-sample (training) / 30% out-of-sample (testing)
- Metrics: Sharpe ratio, max drawdown, win rate, profit factor, annual return
- Ratings: EXCELLENT (Sharpe≥2.0), GOOD (≥1.0), MODERATE (≥0.5), POOR (<0.5)
- Warns if out-of-sample Sharpe < 50% of in-sample (overfitting detection)

**Example Output**:
```
BACKTEST RESULTAT (Walk-Forward Validation)
November-April (Stark säsong)
📊 IN-SAMPLE (70% av data - träning)
  Sharpe ratio: 0.46 (POOR)
  
📊 OUT-OF-SAMPLE (30% av data - validering)
  Sharpe ratio: 0.08 (POOR)
  
⚠️ VARNING: Out-of-sample mycket sämre än in-sample - risk för överanpassning!
```

**Philosophy**: Jim Simons: "Test everything on out-of-sample data. If it doesn't work there, it won't work in production."

**Location**: `src/trading/backtester.py` (257 lines)

---

### ⏭️ Step 5: Intraday Data Support
**Status**: Skipped - requires paid data

**Reason**: yfinance API only provides 7 days of intraday data (5min/15min/1h bars). For 15 years of intraday data, you need paid APIs:
- IEX Cloud ($9-79/month)
- Polygon.io ($29-249/month)
- Alpha Vantage ($49.99+/month)

**Future Implementation**: Add support for these APIs when budget allows.

---

### ✅ Step 6: Macro Data Integration
**Status**: Complete

**Implementation**:
- `MacroDataIntegrator` fetches VIX (fear gauge) and 10-year treasury yields
- Classifies macro environment:
  - VIX level: low (<15), normal (15-20), high (20-30), extreme (>30)
  - Interest rate trend: falling, stable, rising
  - Sector leadership: growth, value, defensive, cyclical
  - Risk appetite: risk-on vs risk-off
- Filters patterns by macro regime (e.g., high VIX → only mean reversion)

**Philosophy**: Patterns work differently in different macro regimes. Don't trade momentum in a crisis.

**Location**: `src/data/macro_data.py` (222 lines)

---

### ✅ Step 7: Portfolio Optimization with Kelly Criterion
**Status**: Complete

**Implementation**:
- `PortfolioOptimizer` calculates optimal position size using Kelly Criterion
- Formula: `f* = (p*b - q) / b` where p=win rate, b=payoff ratio
- Recommends fractional Kelly: Full (1.0x), Half (0.5x), Quarter (0.25x)
- Max position size: 25% per pattern (never risk too much on one signal)
- Min edge required: 0.1% (filters unprofitable patterns)

**Example Output**:
```
PORTFOLIO OPTIMIZATION (Kelly Criterion)
Total Capital: $100,000
Max Position: 25.0%
Kelly Fraction: 50.0% (safer than full Kelly)

1. November-April (Stark säsong)
   Expected edge: +0.06%
   Win rate: 55.0%
   Full Kelly: 2.1%
   ✅ Recommendation: QUARTER KELLY
   Position size: 0.5% = $526

⚠️ Renaissance principle: NEVER use full Kelly. Use 0.25-0.5x Kelly.
⚠️ This protects against estimation errors and black swan events.
```

**Philosophy**: Kelly tells you *how much* to bet. But never bet the full Kelly - it's too aggressive and assumes perfect parameter estimation. Renaissance uses ~0.25x Kelly.

**Location**: `src/trading/portfolio_optimizer.py` (227 lines)

---

## Original 7 Statistical Rigor Features

### 1. Long Historical Data (8-10 years minimum)
- Calendar patterns require 8+ years
- Weekday patterns require 8+ years (10+ cycles through regimes)
- Current implementation: 15 years of daily data

### 2. Baseline Comparison
- Shows pattern mean vs market mean vs edge
- Edge = pattern performance minus market baseline
- Displayed in all pattern reports

### 3. Continuous Degradation Scale
- 4 levels: Friskt (0-10%), Försvagande (10-20%), Instabilt (20-30%), Inaktivt (>30%)
- Based on recent performance vs historical average
- Avoids binary "good/bad" classification

### 4. Softened Predictive Language
- "Historiskt har sannolikheten varit X%" instead of "Reversering trolig"
- Avoids false confidence
- Emphasizes uncertainty

### 5. Permutation Testing (Shuffle Test)
- Validates pattern against 1000 random day assignments
- P-value shows if pattern is better than random
- If p-value > 0.05, pattern might be spurious

### 6. Regime-Dependent Analysis
- Splits performance by:
  - Trend: uptrend, neutral, downtrend (50-day MA)
  - Volatility: high, normal, low (20-day rolling std)
- Shows which regime pattern works best in

### 7. Signal Aggregation with Correlation Awareness
- Combines multiple active signals
- Applies 50% penalty if signals are correlated
- Prevents double-counting related patterns

---

## File Structure

```
src/
├── analysis/
│   ├── permutation_tester.py       # Shuffle testing
│   ├── regime_analyzer.py          # Trend/vol regime classification
│   └── signal_aggregator.py        # Multi-signal combination
├── trading/
│   ├── strategy_generator.py       # Regime-filtered strategies
│   ├── pattern_combiner.py         # Multi-pattern aggregation
│   ├── backtester.py               # Walk-forward backtesting
│   └── portfolio_optimizer.py      # Kelly Criterion sizing
├── data/
│   └── macro_data.py               # VIX, rates, sector rotation
└── analyzer.py                      # Orchestrates all features
```

---

## Running the Full Analysis

```bash
python main.py
```

Select market (S&P 500, OMX, etc.) and the analyzer will:
1. Fetch 15 years of data
2. Identify patterns (lowered thresholds)
3. Filter by regime
4. Combine patterns (correlation-aware)
5. Backtest with walk-forward validation
6. Calculate optimal position sizes (Kelly)
7. Display everything in Renaissance-style report

---

## Key Principles (Jim Simons / Renaissance Technologies)

1. **Test on out-of-sample data**: In-sample performance means nothing
2. **Account for all costs**: Transaction costs, slippage, market impact
3. **Never use full Kelly**: Always use fractional (0.25-0.5x)
4. **Combine weak signals**: 10-20 weak patterns > 1 strong pattern
5. **Correlation kills**: Diversification only works with independent signals
6. **Regime matters**: Trade patterns only when conditions are right
7. **Long history required**: 8-10+ years to avoid regime bias
8. **Permutation test**: If it doesn't beat random, don't trade it

---

## Next Steps (Future Enhancements)

1. **Intraday data**: Add support for IEX Cloud / Polygon.io APIs
2. **Machine learning**: Use ML to identify non-linear pattern combinations
3. **Execution modeling**: Model realistic execution with order book depth
4. **Risk budgeting**: Allocate risk instead of capital (volatility parity)
5. **Real-time alerts**: Push notifications when tradeable patterns activate
6. **Multi-asset**: Extend to forex, crypto, commodities
7. **Factor analysis**: Decompose returns into Fama-French factors

---

## Credits

Inspired by:
- Jim Simons & Renaissance Technologies
- "The Man Who Solved the Market" by Gregory Zuckerman
- Edward Thorp's Kelly Criterion work
- Modern statistical arbitrage research

Built with: Python, NumPy, Pandas, yfinance

Co-Authored-By: Warp AI Agent
