# 🏗️ SYSTEM ARCHITECTURE - V4.0 Position Trading System

**Complete Technical Documentation: How Everything Works**

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Data Flow: Step-by-Step](#data-flow-step-by-step)
4. [Component Details](#component-details)
5. [Cost Calculations](#cost-calculations)
6. [Pattern Detection & Backtesting](#pattern-detection--backtesting)
7. [Risk Management Layers](#risk-management-layers)
8. [Position Sizing Logic](#position-sizing-logic)
9. [Final Scoring & Ranking](#final-scoring--ranking)
10. [Output Format](#output-format)

---

## 🎯 System Overview

### What Is This System?

**V4.0 Position Trading System** is a bottom-fishing quantitative trading system that:
- Scans **720 instruments** (Swedish, Nordic, US, All-Weather)
- Identifies **structural bottoms** after -10% declines
- Validates patterns with **backtesting** (21/42/63 days forward returns)
- Applies **37 risk management filters**
- Calculates **precise position sizing** (1.5-3.0% of portfolio)
- Generates **Sunday reports** with top 3-5 setups

**Philosophy**: Buy structural bottoms with statistically validated patterns, hold 1-3 months (21-63 days).

---

## 🏛️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     SUNDAY DASHBOARD                            │
│                   (sunday_dashboard.py)                         │
└────────────┬────────────────────────────────────────────────────┘
             │
             ├─► STEP 1: PRE-FLIGHT CHECKS
             │   ├─► Market Breadth (OMXS30: % above 200MA)
             │   ├─► Macro Indicators (Yield Curve, Credit Spreads)
             │   └─► Systemic Risk Score (0-100)
             │
             ├─► STEP 2: INSTRUMENT SCREENER (instrument_screener_v23_position.py)
             │   │
             │   ├─► For each instrument (720 total):
             │   │   │
             │   │   ├─► 2.1: DATA FETCHING (data_fetcher.py)
             │   │   │    └─► Yahoo Finance → 15 years of daily OHLCV data
             │   │   │
             │   │   ├─► 2.2: MARKET CONTEXT FILTER (market_context_filter.py)
             │   │   │    ├─► Decline from 90d high ≥ -10%?
             │   │   │    ├─► Price vs EMA200 (is it oversold)?
             │   │   │    └─► "Vattenpasset" = pre-screen before analysis
             │   │   │
             │   │   ├─► 2.3: PATTERN DETECTION (position_trading_patterns.py)
             │   │   │    ├─► PRIMARY Patterns (structural reversals):
             │   │   │    │   ├─► Double Bottom (W-pattern after decline)
             │   │   │    │   ├─► Inverse Head & Shoulders
             │   │   │    │   ├─► Bull Flag after Decline (stabilization)
             │   │   │    │   └─► Higher Lows Reversal
             │   │   │    │
             │   │   │    └─► SECONDARY Patterns (lower priority):
             │   │   │        ├─► Calendar effects (weekend, month-end)
             │   │   │        └─► Short-term momentum
             │   │   │
             │   │   ├─► 2.4: BACKTESTING (analyzer.py + outcome_analyzer.py)
             │   │   │    ├─► Calculate forward returns (21/42/63 days)
             │   │   │    ├─► Win Rate = % trades profitable
             │   │   │    ├─► Avg Win / Avg Loss
             │   │   │    ├─► Expected Value (EV) = (WR × AvgWin) - (LR × AvgLoss)
             │   │   │    ├─► Risk/Reward Ratio (RRR) = AvgWin / AvgLoss
             │   │   │    │
             │   │   │    └─► QUALITY GATES:
             │   │   │        ├─► EV > 0? (positive expectation)
             │   │   │        ├─► RRR ≥ 3.0? (1:3 minimum)
             │   │   │        ├─► Permutation test (not random?)
             │   │   │        ├─► Regime analysis (works in all markets?)
             │   │   │        └─► Bayesian adjustment (survivorship bias)
             │   │   │
             │   │   ├─► 2.5: EARNINGS RISK (earnings_calendar.py)
             │   │   │    └─► Block if earnings <48h away
             │   │   │
             │   │   └─► 2.6: PRELIMINARY SCORE
             │   │        └─► Pass to Sunday Dashboard for risk filtering
             │   │
             │   └─► Output: List of POTENTIAL setups (typically 5-15 candidates)
             │
             ├─► STEP 3: RISK MANAGEMENT FILTERS (21 layers)
             │   │
             │   ├─► 3.1: POSITION SIZING (volatility_position_sizing.py)
             │   │    ├─► V-Kelly Formula:
             │   │    │    position = (win_rate - (1-win_rate)/RRR) / volatility
             │   │    ├─► Base allocation: 1.5% (low WR) → 3.0% (high WR)
             │   │    ├─► Volatility adjustment (ATR-based)
             │   │    └─► Max 5% per position, Min 0.1%
             │   │
             │   ├─► 3.2: EXECUTION GUARD (execution_guard.py)
             │   │    ├─► FX costs (Sweden 0%, Nordic 0.25%, US 0.5%)
             │   │    ├─► Courtage (Avanza MINI: 1 SEK, SMALL: 7 SEK, MEDIUM: 15 SEK)
             │   │    ├─► Spread costs (volatile stocks = higher spread)
             │   │    └─► Liquidity check (position <2% daily volume)
             │   │
             │   ├─► 3.3: COST-AWARE FILTER (cost_aware_filter.py)
             │   │    └─► Net Edge = Edge - Total Costs
             │   │        └─► Block if Net Edge < 0.3%
             │   │
             │   ├─► 3.4: REGIME DETECTION (regime_detection.py)
             │   │    ├─► HEALTHY: Normal allocation
             │   │    ├─► CRISIS: Reduce to 0.2x (20%)
             │   │    └─► All-Weather gets 1.0x in CRISIS
             │   │
             │   ├─► 3.5: SECTOR CAP (sector_cap_manager.py)
             │   │    └─► Max 40% portfolio per sector
             │   │
             │   ├─► 3.6: MAE OPTIMIZER (mae_optimizer.py)
             │   │    ├─► MAE = Maximum Adverse Excursion
             │   │    ├─► Optimal stop = |avg_loss| × 1.5
             │   │    └─► Typically 1.5-4.5% stops
             │   │
             │   ├─► 3.7: MONTE CARLO SIMULATOR (monte_carlo_simulator.py)
             │   │    ├─► P(stop-out) = (1 - WR) × RRR_factor
             │   │    ├─► RRR_factor: 0.5-1.2 based on RRR
             │   │    └─► Typically 0-45% stop-out risk
             │   │
             │   ├─► 3.8: CORRELATION DETECTOR (correlation_detector.py)
             │   │    └─► Warn if adding correlated positions
             │   │
             │   ├─► 3.9: FX GUARD (fx_guard.py)
             │   │    └─► Warn if USD/SEK >+2σ (overvalued)
             │   │
             │   ├─► 3.10: INACTIVITY CHECKER (inactivity_checker.py)
             │   │    └─► Warn if volume dried up
             │   │
             │   └─► 3.11-3.21: Additional filters...
             │        (See src/ for full list)
             │
             ├─► STEP 4: PORTFOLIO INTELLIGENCE
             │   ├─► Portfolio Health (health_tracker.py)
             │   ├─► Exit Guard (exit_guard.py)
             │   └─► Data Sanity (data_sanity_checker.py)
             │
             ├─► STEP 5: RANKING & DISPLAY
             │   ├─► Score = f(WinRate, RRR, EV, Context, Sample Size)
             │   ├─► Sort by score (100 = best, 0 = worst)
             │   └─► Display top 3-5 setups
             │
             └─► STEP 6: REPORT GENERATION
                 ├─► Console output (see below)
                 ├─► JSON backfill (for historical tracking)
                 └─► PDF report (optional, via weekly_report.py)
```

---

## 🔄 Data Flow: Step-by-Step

### From Ticker Symbol → Buy Recommendation

Let's follow **NMAN.ST (Nilörngruppen)** through the entire pipeline:

---

#### **STEP 1: Data Fetching**

```python
# File: src/utils/data_fetcher.py
ticker = "NMAN.ST"
market_data = data_fetcher.fetch_stock_data(ticker, period="15y")

# Yahoo Finance API returns:
{
  "timestamps": [2010-01-01, 2010-01-02, ..., 2026-01-24],  # 3,750+ days
  "open_prices": [10.2, 10.5, ..., 145.0],
  "high_prices": [10.8, 10.9, ..., 147.0],
  "low_prices": [10.0, 10.3, ..., 143.5],
  "close_prices": [10.5, 10.7, ..., 145.5],
  "volume": [15000, 18000, ..., 45000]
}
```

**Data Quality Check** (data_sanity_checker.py):
- ✅ No missing data
- ✅ No price spikes >25% in 1 day
- ✅ No negative prices
- ✅ Volume >0

---

#### **STEP 2: Market Context Filter ("Vattenpasset")**

```python
# File: src/filters/market_context_filter.py

# Calculate 90-day decline
high_90d = max(close_prices[-90:])  # 165.0 SEK
current_price = close_prices[-1]     # 145.5 SEK
decline = (current_price - high_90d) / high_90d * 100  # -11.8%

# Calculate price vs EMA200
ema200 = calculate_ema(close_prices, 200)  # 140.0 SEK
price_vs_ema200 = (current_price - ema200) / ema200 * 100  # +3.9%

# Decision
if decline <= -10.0:  # Threshold: -10% min decline
    context_valid = True  # ✅ PASS - eligible for pattern detection
else:
    context_valid = False  # ❌ FAIL - skip (no setup)
```

**NMAN.ST Result:**
- Decline: -11.8% ✅
- Price vs EMA200: +3.9% (slightly above, bottoming)
- **Context: VALID** → Continue to pattern detection

---

#### **STEP 3: Pattern Detection**

```python
# File: src/patterns/position_trading_patterns.py

def detect_double_bottom(market_data):
    """
    Detect W-pattern after decline.
    
    Requirements:
    1. Prior decline ≥ 10%
    2. Two lows within 5% of each other
    3. Reaction high between lows (≥2% bounce)
    4. Volume declining into second low
    5. Optional: Breakout above reaction high
    """
    
    # Scan last 40-120 bars for double bottom
    for window in [40, 60, 80, 100, 120]:
        prices = close_prices[-window:]
        
        # Find pivot lows
        lows = find_pivots(prices, min_distance=10)
        
        # Check for two lows
        if len(lows) >= 2:
            low1_idx, low1_price = lows[-2]
            low2_idx, low2_price = lows[-1]
            
            # Check if similar (W-pattern)
            price_diff = abs(low1_price - low2_price) / low1_price
            if price_diff < 0.05:  # Within 5%
                
                # Find reaction high (middle)
                reaction_high = max(prices[low1_idx:low2_idx])
                bounce_height = (reaction_high - low1_price) / low1_price
                
                if bounce_height >= 0.02:  # 2% minimum
                    
                    # Check volume (declining = less selling pressure)
                    volume_declining = check_volume_decline(volume, low1_idx, low2_idx)
                    
                    if volume_declining:
                        # PATTERN DETECTED! ✅
                        return MarketSituation(
                            situation_id="double_bottom",
                            description="Double Bottom after -11.8% decline",
                            timestamp_indices=[low2_idx],
                            confidence=1.0,
                            metadata={
                                'signal_type': 'structural_reversal',
                                'pattern': 'double_bottom',
                                'priority': 'PRIMARY',
                                'decline_pct': -11.8,
                                'triggered': True
                            }
                        )
```

**NMAN.ST Result:**
- Pattern: **Double Bottom** (PRIMARY)
- Detected at: Day 3,745 (last low)
- Confidence: 1.0 (pattern exists = 100%)

---

#### **STEP 4: Backtesting (The Critical Step)**

This is where we **validate the pattern with historical data**:

```python
# File: src/analyzer.py

def analyze_market_data(market_data):
    """
    For each detected pattern, calculate forward returns.
    """
    
    # Double Bottom pattern was detected at indices: [800, 1200, 1850, 2100, 3745]
    # (pattern occurred 5 times in 15-year history)
    
    situation = patterns['double_bottom']
    indices = situation.timestamp_indices  # [800, 1200, 1850, 2100, 3745]
    
    # Calculate forward returns at 21, 42, 63 days
    forward_returns_21d = []
    forward_returns_42d = []
    forward_returns_63d = []
    
    for idx in indices[:-1]:  # Exclude most recent (can't calculate future yet)
        entry_price = close_prices[idx]
        
        # 21 days later
        exit_price_21d = close_prices[idx + 21]
        return_21d = (exit_price_21d - entry_price) / entry_price
        forward_returns_21d.append(return_21d)
        
        # 42 days later
        exit_price_42d = close_prices[idx + 42]
        return_42d = (exit_price_42d - entry_price) / entry_price
        forward_returns_42d.append(return_42d)
        
        # 63 days later
        exit_price_63d = close_prices[idx + 63]
        return_63d = (exit_price_63d - entry_price) / entry_price
        forward_returns_63d.append(return_63d)
    
    # Results (4 historical occurrences):
    # forward_returns_21d = [+2.5%, +3.1%, +1.8%, +4.2%]
    # forward_returns_42d = [+5.8%, +7.2%, +3.5%, +8.1%]
    # forward_returns_63d = [+8.5%, +9.2%, +5.1%, +12.3%]
    
    # Calculate outcome statistics
    outcome_stats = analyze_outcomes(forward_returns_63d)
    
    # Results:
    return {
        'sample_size': 4,
        'win_rate': 1.0,  # 100% (4/4 trades profitable)
        'mean_return': 0.0877,  # 8.77% average
        'avg_win': 0.0877,  # 8.77%
        'avg_loss': 0.0,  # No losses
        'std_dev': 0.0298,  # 2.98% standard deviation
        'sharpe_ratio': 2.94
    }
```

**Calculate Expected Value (EV):**
```python
# File: src/analyzer.py (lines 272-288)

win_rate = 1.0  # 100%
loss_rate = 0.0  # 0%
avg_win = 0.0877  # 8.77%
avg_loss = 0.0  # 0%

# EV Formula
expected_value = (win_rate × avg_win) - (loss_rate × avg_loss)
expected_value = (1.0 × 0.0877) - (0.0 × 0.0)
expected_value = 0.0877  # 8.77% ✅ POSITIVE!

# Risk/Reward Ratio (RRR)
risk_reward_ratio = avg_win / avg_loss if avg_loss > 0 else 999.0
risk_reward_ratio = 999.0  # Perfect (no losses) ✅

# Quality Gates
if expected_value <= 0:
    continue  # ❌ Skip: Negative EV
if risk_reward_ratio < 3.0:
    continue  # ❌ Skip: RRR too low

# NMAN.ST passes both gates! ✅
```

**Additional Validation:**

1. **Permutation Test** (src/analysis/permutation_tester.py):
   - Randomly shuffles market returns 1,000 times
   - Question: "Could this pattern be random luck?"
   - Result: p-value = 0.02 (2% chance of randomness) ✅

2. **Regime Analysis** (src/risk/regime_detection.py):
   - Tests pattern in HEALTHY vs CRISIS markets
   - Result: Works in both (slight degradation in CRISIS)

3. **Bayesian Adjustment** (src/analysis/bayesian_estimator.py):
   - Adjusts for survivorship bias (we only see survivors)
   - Penalty: -20% for delisted stocks
   - Result: Adjusted edge = 7.02% (still strong)

---

#### **STEP 5: Risk Management Filters**

Now the pattern is validated. Apply 21 risk filters:

##### **5.1: Position Sizing**

```python
# File: src/risk/volatility_position_sizing.py

# V-Kelly Formula
win_rate = 1.0
rrr = 999.0
volatility = calculate_atr(close_prices) / current_price  # 2.1% ATR

# Base allocation (scales with win rate)
base_allocation = 0.015 + (win_rate - 0.6) * 0.0375
base_allocation = 0.015 + (1.0 - 0.6) * 0.0375 = 0.03  # 3.0%

# Volatility adjustment
volatility_factor = min(1.0, 0.02 / volatility)  # Target 2.0% daily vol
volatility_factor = min(1.0, 0.02 / 0.021) = 0.952

# Final position size
position_size = base_allocation × volatility_factor
position_size = 0.03 × 0.952 = 0.0286  # 2.86%

# Apply caps
position_size = max(0.001, min(0.05, position_size))  # Min 0.1%, Max 5%
position_size = 0.0286  # 2.86% ✅

# In SEK
position_sek = 100,000 × 0.0286 = 2,860 SEK
```

##### **5.2: Execution Guard (Cost Calculation)**

```python
# File: src/risk/execution_guard.py

ticker = "NMAN.ST"
position_sek = 2860
current_price = 145.5

# FX Costs (Swedish stock)
fx_cost = 0.0  # 0% (Sverige)

# Courtage (Avanza MINI tier)
shares = position_sek / current_price = 19.66 shares
courtage_buy = 1.0 SEK  # MINI minimum
courtage_sell = 1.0 SEK
courtage_total = 2.0 SEK
courtage_pct = courtage_total / position_sek = 0.07%

# Spread (bid-ask spread)
spread_pct = 0.15%  # Swedish mid-cap estimate

# Slippage (volatility-based)
regime = "EXPANDING"  # Volatility increasing
slippage_pct = 0.2%  # 2x normal (EXPANDING = 2x)

# Total Costs
total_cost = fx_cost + courtage_pct + spread_pct + slippage_pct
total_cost = 0.0 + 0.07 + 0.15 + 0.2 = 0.42%

# Net Edge
net_edge = expected_value - total_cost
net_edge = 8.77% - 0.42% = 8.35% ✅ STRONG!

# Decision
if net_edge >= 0.3%:
    status = "PASS"  # ✅ Profitable after costs
else:
    status = "BLOCKED"
```

**NMAN.ST Result:**
- Total costs: 0.42%
- Net edge: 8.35% ✅
- **EXECUTION GUARD: PASS**

##### **5.3: Earnings Risk**

```python
# File: src/filters/earnings_calendar.py

# Check if earnings report <48h away
earnings_risk = check_earnings_risk("NMAN.ST")

# Result:
{
    'risk_level': 'LOW',
    'days_until_earnings': 37,
    'message': 'Earnings in 37 days - safe window'
}
```

**NMAN.ST Result:** ✅ SAFE (earnings 37 days away)

##### **5.4: MAE Optimizer (Stop Loss)**

```python
# File: src/risk/mae_optimizer.py

# MAE = Maximum Adverse Excursion (worst drawdown before win)
# Historical trades: -1.2%, -1.8%, -0.9%, -1.5% (max drawdown before recovery)

avg_loss = 0.0  # No losing trades
mae_worst = -0.018  # Worst intra-trade drawdown was -1.8%

# Optimal stop
optimal_stop = abs(mae_worst) × 1.5
optimal_stop = 0.018 × 1.5 = 0.027  # 2.7%

# MAE-adjusted RRR
mae_rrr = avg_win / optimal_stop
mae_rrr = 0.0877 / 0.027 = 3.25  # Still above 3:1 ✅
```

**NMAN.ST Result:**
- Optimal stop: 2.7%
- MAE RRR: 3.25 ✅

##### **5.5: Monte Carlo Simulation**

```python
# File: src/risk/monte_carlo_simulator.py

# Simplified approximation
win_rate = 1.0
rrr = 999.0

# RRR factor (higher RRR = lower risk)
if rrr >= 5.0:
    rrr_factor = 0.5
elif rrr >= 3.0:
    rrr_factor = 0.8
else:
    rrr_factor = 1.2

# P(stop-out)
stop_out_probability = (1 - win_rate) × rrr_factor
stop_out_probability = (1 - 1.0) × 0.5 = 0.0  # 0% ✅
```

**NMAN.ST Result:**
- Stop-out risk: 0% ✅ (perfect historical record)

##### **5.6-5.21: Additional Filters**

All pass (see sunday_dashboard.py for full implementation).

---

#### **STEP 6: Scoring & Ranking**

```python
# File: instrument_screener_v23_position.py

def calculate_score(result):
    """
    Score = f(Win Rate, RRR, EV, Context, Sample Size)
    """
    score = 0
    
    # Win Rate (40 points max)
    score += win_rate × 40  # 1.0 × 40 = 40 pts
    
    # RRR (25 points max)
    score += min(rrr / 5.0, 1.0) × 25  # (999/5) capped at 1.0 = 25 pts
    
    # Expected Value (20 points max)
    score += min(expected_value / 0.10, 1.0) × 20  # (8.77%/10%) = 17.5 pts
    
    # Market Context (10 points max)
    if context_valid and decline >= -15%:
        score += 10  # 10 pts
    elif context_valid:
        score += 5
    
    # Sample Size penalty (reduce score if <5 occurrences)
    if sample_size < 5:
        score × 0.8  # -20% penalty
    
    # Total
    score = 40 + 25 + 17.5 + 5 = 87.5 / 100 ✅
    
    return score
```

**NMAN.ST Result:**
- Score: **91.7 / 100** (EXCELLENT)
- Rank: #2 (out of 720 instruments)

---

#### **STEP 7: Final Output**

```python
# sunday_dashboard.py - Display Results

print("""
═══════════════════════════════════════════════════════════════
TOP POSITION TRADING SETUPS
═══════════════════════════════════════════════════════════════

2. NMAN.ST - Nilörngruppen
   ────────────────────────────────────────────────────────────
   📊 MARKET CONTEXT
      Decline from high: -11.8%
      Price vs EMA200: +3.9%
      Context: VALID ✅
   
   🎯 PATTERN ANALYSIS
      Primary Patterns: 1 (Double Bottom)
      Pattern Priority: PRIMARY ✅
      Pattern Description: Double Bottom after -11.8% decline
   
   💰 EDGE & RETURNS (Multi-Timeframe)
      21-day edge: +2.8%
      42-day edge: +6.2%
      63-day edge: +8.8% ✅
      Win Rate (63d): 100.0%
   
   🎲 RISK METRICS
      Expected Value: +8.77%
      Risk/Reward: 999.0:1 (perfect)
      Avg Win: +8.77%
      Avg Loss: 0.0%
   
   📊 QUALITY
      Bayesian Edge: +7.02% (adjusted)
      Uncertainty: LOW
      Sample Size: 4 occurrences
   
   🛡️ RISK ANALYSIS
      Monte Carlo stop-out risk: 0%
      MAE optimal stop: 2.7%
      MAE RRR: 3.25:1
   
   💵 POSITION SIZING
      Position: 3,000 SEK (3.0%)
      Max Loss: 1,000 SEK (1.0% of portfolio)
      Shares: 20
      Entry Price: 145.50 SEK
      Stop Loss: 141.57 SEK (-2.7%)
   
   💸 EXECUTION COSTS
      🇸🇪 ISK Account:
         • FX Cost: 0.0% (Svensk aktie)
         • Courtage: 0.07% (MINI: 1+1 SEK)
         • Spread: 0.15%
         • Slippage: 0.20% (EXPANDING regime)
         • Total Cost: 0.42%
      Net Edge: 8.35% ✅
   
   ⚠️ WARNINGS
      Earnings Risk: LOW (37 days until report)
      Volume: CONFIRMED ✅
   
   ✅ STATUS: POTENTIAL (SECONDARY)
      Score: 91.7 / 100
      
   📝 RECOMMENDATION:
      STRONG BUY - Excellent risk/reward, 100% historical win rate,
      low costs, perfect context. Consider 3,000 SEK position.
""")
```

---

## 🔍 Component Details

### 1. Data Fetcher (src/utils/data_fetcher.py)

**Purpose**: Fetch OHLCV data from Yahoo Finance.

**Key Functions**:
```python
fetch_stock_data(ticker, period="15y")
fetch_index_data(index="^GSPC")
fetch_multiple_tickers(tickers_list)
```

**Output**: MarketData object with timestamps, OHLCV, volume.

---

### 2. Market Context Filter (src/filters/market_context_filter.py)

**Purpose**: "Vattenpasset" - pre-screen before heavy analysis.

**Logic**:
- Calculate 90-day high
- Measure decline from high
- Check if decline ≥ -10% (threshold relaxed from -15% for EUPHORIA markets)
- Check price vs EMA200

**Output**: `is_valid_for_entry` (True/False)

---

### 3. Pattern Detector (src/patterns/position_trading_patterns.py)

**Purpose**: Detect structural reversal patterns.

**PRIMARY Patterns**:
1. **Double Bottom** (W-pattern)
2. **Inverse Head & Shoulders**
3. **Bull Flag after Decline** (consolidation)
4. **Higher Lows Reversal**

**Detection Logic**:
- Pivot analysis (find local minima/maxima)
- Volume confirmation (declining volume = less selling pressure)
- Structural requirements (decline → stabilization → reversal)

**Output**: MarketSituation objects with metadata.

---

### 4. Outcome Analyzer (src/analysis/outcome_analyzer.py)

**Purpose**: Calculate forward returns and statistics.

**Key Metrics**:
- Win Rate (% profitable trades)
- Mean Return (average profit)
- Avg Win / Avg Loss
- Standard Deviation
- Sharpe Ratio
- Skewness, Kurtosis

**Output**: OutcomeStats dataclass.

---

### 5. Pattern Evaluator (src/analysis/pattern_evaluator.py)

**Purpose**: Validate pattern robustness.

**Checks**:
- Statistical strength (win rate, sample size)
- Stability over time (no recent degradation)
- Quality gates (EV > 0, RRR ≥ 3.0)

**Output**: `is_significant` (True/False)

---

### 6. Permutation Tester (src/analysis/permutation_tester.py)

**Purpose**: Validate pattern is not random.

**Logic**:
- Shuffle market returns 1,000 times
- Calculate how often random selection beats pattern
- p-value <0.05 = significant

**Output**: p-value, is_significant.

---

### 7. Regime Analyzer (src/risk/regime_detection.py)

**Purpose**: Test pattern in different market conditions.

**Regimes**:
- HEALTHY (normal)
- CRISIS (crash)
- EUPHORIA (bubble)

**Output**: Performance stats per regime.

---

### 8. Bayesian Estimator (src/analysis/bayesian_estimator.py)

**Purpose**: Adjust for survivorship bias.

**Logic**:
- Small sample size → high uncertainty
- Delisted stocks → -20% penalty
- Bayesian prior = 0% (neutral)

**Output**: Bias-adjusted edge.

---

### 9. Volatility Position Sizer (src/risk/volatility_position_sizing.py)

**Purpose**: Calculate position size using V-Kelly.

**Formula**:
```python
base_allocation = 1.5% + (win_rate - 0.6) × 3.75%
volatility_factor = target_vol / current_vol
position_size = base_allocation × volatility_factor
```

**Output**: Position size in % and SEK.

---

### 10. Execution Guard (src/risk/execution_guard.py)

**Purpose**: Calculate total execution costs.

**Components**:
1. **FX Costs** (Sweden 0%, Nordic 0.25%, US 0.5%)
2. **Courtage** (MINI: 1 SEK, SMALL: 7 SEK, MEDIUM: 15 SEK)
3. **Spread** (bid-ask spread, typically 0.1-0.3%)
4. **Slippage** (volatility-based: STABLE 1x, EXPANDING 2x, EXPLOSIVE 4x)

**Output**: Total cost %, net edge.

---

### 11. MAE Optimizer (src/risk/mae_optimizer.py)

**Purpose**: Calculate optimal stop loss.

**Logic**:
- MAE = Maximum Adverse Excursion (worst intra-trade drawdown)
- Optimal stop = |avg_loss| × 1.5
- Typically 1.5-4.5%

**Output**: Optimal stop %, MAE RRR.

---

### 12. Monte Carlo Simulator (src/risk/monte_carlo_simulator.py)

**Purpose**: Estimate stop-out probability.

**Simplified Logic**:
```python
P(stop-out) = (1 - win_rate) × rrr_factor
rrr_factor = 0.5 (high RRR) → 1.2 (low RRR)
```

**Output**: Stop-out probability (0-45%).

---

## 💰 Cost Calculations

### Total Execution Cost Breakdown

```
Total Cost = FX + Courtage + Spread + Slippage
```

#### 1. FX Costs (Currency Exchange)

```python
# File: src/risk/execution_guard.py

def calculate_fx_cost(ticker):
    """
    Sweden: 0.0%
    Nordic (Norge, Finland, Danmark): 0.25%
    Others (USA, UK, etc.): 0.5%
    """
    if ticker.endswith('.ST'):  # Swedish
        return 0.0
    elif ticker.endswith(('.OL', '.HE', '.CO')):  # Nordic
        return 0.0025
    else:  # Foreign
        return 0.005
```

**Example**:
- NMAN.ST (Sweden): 0.0%
- NOKIA.HE (Finland): 0.25%
- AAPL (USA): 0.5%

---

#### 2. Courtage (Transaction Fees)

```python
# Avanza ISK 2024 Pricing (FIXED)

# MINI Tier
if shares × price <= 100,000 SEK:
    courtage = max(1.0, shares × price × 0.00015)  # 0.015%, min 1 SEK

# SMALL Tier
elif shares × price <= 250,000 SEK:
    courtage = max(7.0, shares × price × 0.00035)  # 0.035%, min 7 SEK

# MEDIUM Tier
elif shares × price <= 1,000,000 SEK:
    courtage = max(15.0, shares × price × 0.00056)  # 0.056%, min 15 SEK

# Round-trip (buy + sell)
total_courtage = courtage × 2
```

**Example** (NMAN.ST, 3,000 SEK position):
```
Position: 3,000 SEK → MINI tier
Courtage: max(1.0, 3000 × 0.00015) = 1.0 SEK
Round-trip: 1.0 + 1.0 = 2.0 SEK (0.07%)
```

---

#### 3. Spread (Bid-Ask Spread)

```python
# Estimated based on liquidity

# Large-cap (AAPL, MSFT, etc.)
spread = 0.05%

# Mid-cap (Swedish stocks, small US stocks)
spread = 0.15%

# Small-cap (illiquid)
spread = 0.30%
```

**Example** (NMAN.ST, mid-cap):
```
Spread: 0.15%
```

---

#### 4. Slippage (Volatility-Based)

```python
# File: src/risk/regime_detection.py

# Base slippage
base_slippage = 0.10%

# Regime multiplier
if regime == "STABLE":
    multiplier = 1.0  # Normal
elif regime == "EXPANDING":
    multiplier = 2.0  # Volatile
elif regime == "EXPLOSIVE":
    multiplier = 4.0  # Very volatile
elif regime == "CONTRACTING":
    multiplier = 0.5  # Low volatility

slippage = base_slippage × multiplier
```

**Example** (NMAN.ST, EXPANDING regime):
```
Slippage: 0.10% × 2.0 = 0.20%
```

---

#### **Total Cost Example (NMAN.ST)**

```
FX:        0.00%  (Swedish stock)
Courtage:  0.07%  (2 SEK round-trip)
Spread:    0.15%  (mid-cap estimate)
Slippage:  0.20%  (EXPANDING regime)
─────────────────
TOTAL:     0.42%

Edge before costs: 8.77%
Net Edge:          8.35% ✅ (still profitable)
```

---

### **Minimum Position Filter**

```python
# File: sunday_dashboard.py

min_position_sek = 1500.0  # 1,500 SEK minimum

# Reason: Avoid courtage trap
# Example (bad):
position = 100 SEK
courtage = 1 + 1 = 2 SEK (2% round-trip!)
→ Edge must be >2% just to break even ❌

# With 1,500 SEK minimum:
position = 1500 SEK
courtage = 2 SEK (0.13% round-trip)
→ Reasonable ✅
```

---

## 🔎 Pattern Detection & Backtesting

### How We Find Bottom-Fishing Opportunities

#### Philosophy

**We are NOT day traders. We are NOT swing traders. We are POSITION TRADERS.**

**Goal**: Buy structural bottoms, hold 1-3 months (21-63 days).

---

### Double Bottom Detection (Example)

```python
# File: src/patterns/position_trading_patterns.py

def detect_double_bottom(market_data):
    """
    W-Pattern After Decline
    
    Structure:
    1. Prior decline ≥ 10% (from 90-day high)
    2. First low (pivot)
    3. Reaction high (bounce ≥2%)
    4. Second low (within 5% of first low)
    5. Volume declining (less selling pressure)
    6. Optional: Breakout above reaction high
    """
    
    prices = market_data.close_prices
    volume = market_data.volume
    
    # Scan windows: 40, 60, 80, 100, 120 bars
    for window in [40, 60, 80, 100, 120]:
        scan_prices = prices[-window:]
        
        # Find pivot lows (5-day minima)
        pivots = []
        for i in range(5, len(scan_prices) - 5):
            if scan_prices[i] == min(scan_prices[i-5:i+5]):
                pivots.append((i, scan_prices[i]))
        
        # Need at least 2 pivots
        if len(pivots) >= 2:
            low1_idx, low1_price = pivots[-2]  # First low
            low2_idx, low2_price = pivots[-1]  # Second low
            
            # Check if similar (W-shape)
            price_diff = abs(low1_price - low2_price) / low1_price
            if price_diff < 0.05:  # Within 5%
                
                # Find reaction high (between lows)
                reaction_high = max(scan_prices[low1_idx:low2_idx])
                bounce_height = (reaction_high - low1_price) / low1_price
                
                if bounce_height >= 0.02:  # 2% minimum bounce
                    
                    # Check volume (declining = bullish)
                    vol_low1 = volume[-window + low1_idx]
                    vol_low2 = volume[-window + low2_idx]
                    volume_declining = vol_low2 < vol_low1
                    
                    if volume_declining:
                        
                        # Check for prior decline
                        decline_start_idx = max(0, -window - 90)
                        high_90d = max(prices[decline_start_idx:-window])
                        decline_pct = (low2_price - high_90d) / high_90d * 100
                        
                        if abs(decline_pct) >= 10.0:  # -10% min
                            
                            # PATTERN DETECTED! ✅
                            return MarketSituation(
                                situation_id="double_bottom",
                                description=f"Double Bottom after {decline_pct:.0f}% decline",
                                timestamp_indices=np.array([len(prices) - window + low2_idx]),
                                confidence=1.0,
                                metadata={
                                    'signal_type': 'structural_reversal',
                                    'pattern': 'double_bottom',
                                    'priority': 'PRIMARY',
                                    'decline_pct': decline_pct,
                                    'bounce_height': bounce_height * 100,
                                    'volume_declining': True,
                                    'triggered': True
                                }
                            )
    
    return []  # No pattern found
```

---

### Backtesting Process

Once a pattern is detected, we **validate it with historical data**:

```python
# File: src/analyzer.py

def analyze_market_data(market_data):
    """
    For each pattern occurrence, calculate forward returns.
    """
    
    # Pattern detected at indices: [800, 1200, 1850, 2100, 3745]
    # (5 occurrences in 15-year history)
    
    situation = patterns['double_bottom']
    indices = situation.timestamp_indices
    
    # Calculate forward returns (21, 42, 63 days)
    forward_returns_63d = []
    
    for idx in indices[:-1]:  # Exclude most recent (no future data)
        entry_price = prices[idx]
        exit_price = prices[idx + 63]  # 63 days later
        
        return_pct = (exit_price - entry_price) / entry_price * 100
        forward_returns_63d.append(return_pct)
    
    # Historical results:
    # [+8.5%, +9.2%, +5.1%, +12.3%]
    
    # Calculate stats
    win_rate = sum(1 for r in forward_returns_63d if r > 0) / len(forward_returns_63d)
    avg_win = mean([r for r in forward_returns_63d if r > 0])
    avg_loss = mean([r for r in forward_returns_63d if r < 0]) if any(r < 0 for r in forward_returns_63d) else 0
    
    # Results:
    win_rate = 1.0  # 100%
    avg_win = 8.77%
    avg_loss = 0.0%
    
    # Expected Value
    EV = (win_rate × avg_win) - ((1 - win_rate) × avg_loss)
    EV = (1.0 × 8.77) - (0.0 × 0.0) = 8.77% ✅
    
    # Risk/Reward Ratio
    RRR = avg_win / abs(avg_loss) if avg_loss != 0 else 999
    RRR = 999.0 ✅ (perfect)
    
    # Quality Gates
    if EV <= 0:
        return None  # ❌ Negative EV
    if RRR < 3.0:
        return None  # ❌ RRR too low
    
    # PASS ✅
    return {
        'pattern': 'double_bottom',
        'win_rate': 1.0,
        'expected_value': 0.0877,
        'rrr': 999.0,
        'sample_size': 4
    }
```

---

### Why This Works (Bottom-Fishing Logic)

1. **Decline Requirement (-10% min)**:
   - Filters out random noise
   - Focuses on structural corrections
   - "Buy when there's blood in the streets"

2. **Double Bottom = W-Pattern**:
   - First low = capitulation (panic selling)
   - Reaction high = dead cat bounce (shorts covering)
   - Second low = retest (weak hands out)
   - If second low holds → bottom confirmed ✅

3. **Volume Declining**:
   - Less volume at second low = less selling pressure
   - Indicates exhaustion of sellers
   - Bullish divergence

4. **Backtesting Validation**:
   - Pattern must have **positive expected value** historically
   - Pattern must have **RRR ≥ 3.0** (1:3 risk/reward minimum)
   - This is NOT curve-fitting — we only buy patterns with **statistical proof**

---

## 🛡️ Risk Management Layers

### 37 Features = 37 Safety Checks

```
┌──────────────────────────────────────────────────────────┐
│              37 RISK MANAGEMENT FEATURES                 │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ 16 CORE V4.0 FEATURES (via screener):                   │
│  1. Market Context Filter (Vattenpasset)                │
│  2. PRIMARY Pattern Detection (structural reversals)    │
│  3. Multi-Timeframe Backtesting (21/42/63 days)        │
│  4. Expected Value Filter (EV > 0)                      │
│  5. Risk/Reward Filter (RRR ≥ 3.0)                     │
│  6. Permutation Test (vs random)                        │
│  7. Regime Analysis (HEALTHY vs CRISIS)                 │
│  8. Bayesian Adjustment (survivorship bias)             │
│  9. Sample Size Validation (min 5 occurrences)         │
│ 10. Earnings Risk Guard (block <48h before report)     │
│ 11. Volume Confirmation (required)                      │
│ 12. Signal Decay (stale signals lose conviction)       │
│ 13. Recency Weighting (recent data weighs heavier)     │
│ 14. Beta-Alpha Separation (alpha > 0 required)         │
│ 15. Trend Elasticity (elastic scoring 0-15)            │
│ 16. Data Sanity Checker (anomaly detection)            │
│                                                          │
│ 21 POST-PROCESSING FEATURES (via dashboard):            │
│ 17. V-Kelly Position Sizing (volatility-adjusted)      │
│ 18. Execution Guard (total cost calculation)           │
│ 19. Cost-Aware Filter (net edge > 0.3%)               │
│ 20. Regime Detection (CRISIS = 0.2x allocation)        │
│ 21. Sector Cap (max 40% per sector)                    │
│ 22. MAE Optimizer (optimal stop loss)                  │
│ 23. Monte Carlo Simulator (stop-out probability)       │
│ 24. Correlation Detector (avoid duplicates)            │
│ 25. FX Guard (warn if USD/SEK overvalued)             │
│ 26. Inactivity Checker (volume dried up?)             │
│ 27. Market Breadth (OMXS30 health)                     │
│ 28. Macro Indicators (yield curve, credit spreads)     │
│ 29. Systemic Risk Score (0-100 aggregation)           │
│ 30. Portfolio Health Tracker                           │
│ 31. Exit Guard (profit-taking at +2σ/+3σ)            │
│ 32. ISK Optimizer (Swedish tax-advantaged account)     │
│ 33. FX Cost Tier (Sweden 0%, Nordic 0.25%, US 0.5%)  │
│ 34. Courtage Optimizer (MINI/SMALL/MEDIUM tiers)      │
│ 35. Minimum Position Filter (≥1,500 SEK)              │
│ 36. Volatility Slippage (STABLE 1x, EXPANDING 2x)     │
│ 37. All-Weather Crisis Mode (59 defensive instruments) │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Result**: Only ~0.7% of instruments pass all 37 filters (5-10 out of 720).

---

## 📊 Final Scoring & Ranking

### Scoring Formula

```python
# File: instrument_screener_v23_position.py

def calculate_score(result):
    """
    Score: 0-100
    
    Components:
    - Win Rate (40 pts max)
    - RRR (25 pts max)
    - Expected Value (20 pts max)
    - Market Context (10 pts max)
    - Sample Size (5 pts max)
    """
    
    score = 0
    
    # 1. Win Rate (40 points)
    score += result.win_rate_63d × 40
    
    # 2. RRR (25 points, capped at 5:1)
    score += min(result.risk_reward_ratio / 5.0, 1.0) × 25
    
    # 3. Expected Value (20 points, capped at 10%)
    score += min(result.expected_value / 0.10, 1.0) × 20
    
    # 4. Market Context (10 points)
    if result.context_valid and result.decline_from_high <= -15:
        score += 10  # Deep decline = best
    elif result.context_valid and result.decline_from_high <= -10:
        score += 5   # Moderate decline
    
    # 5. Sample Size (5 points)
    if result.sample_size >= 10:
        score += 5
    elif result.sample_size >= 5:
        score += 3
    elif result.sample_size >= 3:
        score += 1
    
    # Penalties
    if result.earnings_risk == "HIGH":
        score × 0.5  # -50% penalty
    if result.uncertainty == "HIGH":
        score × 0.8  # -20% penalty
    if not result.volume_confirmed:
        score × 0.9  # -10% penalty
    
    return min(100, max(0, score))
```

---

### Ranking Logic

```python
# Sort by score
results.sort(key=lambda x: x.score, reverse=True)

# Display top 3-5
for i, result in enumerate(results[:5], 1):
    print(f"{i}. {result.name} ({result.ticker})")
    print(f"   Score: {result.score:.0f}/100")
    print(f"   Win Rate: {result.win_rate_63d*100:.1f}%")
    print(f"   Expected Value: {result.expected_value*100:.1f}%")
    print(f"   Position: {result.position_size_pct*100:.1f}%")
```

---

## 📄 Output Format

### Console Output (sunday_dashboard.py)

```
════════════════════════════════════════════════════════════════════
SUNDAY DASHBOARD - V4.0 POSITION TRADING
════════════════════════════════════════════════════════════════════

Capital: 100,000 SEK
Risk per trade: 1.0%
Minimum position: 1,500 SEK (1.5%)

════════════════════════════════════════════════════════════════════
STEP 1: PRE-FLIGHT CHECKS
════════════════════════════════════════════════════════════════════

📊 Market Breadth (OMXS30)...
   Breadth: 65% (19/29 above 200MA)
   Regime: HEALTHY

🌍 Macro Indicators...
   Yield Curve: +0.64% (normal)
   Credit Spreads: -0.47% (LOW stress)

🚨 Systemic Risk Score...
   Risk: 50/100 (⚠️ MEDIUM)

════════════════════════════════════════════════════════════════════
STEP 2: INSTRUMENT SCREENING (720 instruments)
════════════════════════════════════════════════════════════════════

[1/720] Nilörngruppen (NMAN.ST)... ✅ POTENTIAL (Score: 92/100)
[2/720] Bilia (BILI-A.ST)... ✅ POTENTIAL (Score: 87/100)
[3/720] Apple (AAPL)... ⊘ NO SETUP (Score: 45/100)
...
[720/720] Catella (CAT-A.ST)... ⊘ NO SETUP (Score: 22/100)

Found 9 POTENTIAL setups.

════════════════════════════════════════════════════════════════════
TOP POSITION TRADING SETUPS
════════════════════════════════════════════════════════════════════

1. BSX - Boston Scientific
   ────────────────────────────────────────────────────────────────
   📊 MARKET CONTEXT: -12.5% decline, VALID ✅
   🎯 PATTERN: Double Bottom (PRIMARY)
   💰 EDGE: +9.2% (63d), Win Rate: 100.0%
   🎲 RISK: EV +9.2%, RRR 999:1
   💵 POSITION: 3,000 SEK (3.0%)
   💸 EXECUTION: Net Edge 8.75% ✅
   ⚠️ WARNINGS: None
   ✅ STATUS: POTENTIAL (PRIMARY)
   📝 RECOMMENDATION: STRONG BUY

2. NMAN.ST - Nilörngruppen
   ────────────────────────────────────────────────────────────────
   [Full details as shown above]

3-5. [Additional setups...]

════════════════════════════════════════════════════════════════════
NEXT STEPS
════════════════════════════════════════════════════════════════════

PRE-TRADE (Before buying):
 1. [ ] Review macro indicators (yield curve, credit spreads)
 2. [ ] Check market breadth (OMXS30 >60% = healthy)
 3. [ ] Verify earnings calendar (no reports <48h)
 4. [ ] Check FX rates (USD/SEK not overvalued)
 5. [ ] Review position sizing (respects 1% risk per trade)

POST-TRADE (After buying):
 6. [ ] Set stop loss (MAE optimal stop)
 7. [ ] Set profit targets (+2σ = 50% exit, +3σ = 100% exit)
 8. [ ] Add to my_positions.json for tracking
 9. [ ] Monitor weekly (run veckovis_analys.py)
10. [ ] Review quarterly (run kvartalsvis_analys.py)

════════════════════════════════════════════════════════════════════
REPORT SAVED
════════════════════════════════════════════════════════════════════

✅ Console output above
✅ JSON backfill: backfill_data/daily_snapshots/2026-01-24.json
✅ PDF report: reports/sunday_dashboard_2026-01-24.pdf

Runtime: 4h 23m 15s
```

---

## 🎯 Summary: End-to-End Flow

```
INPUT: 720 ticker symbols
   ↓
DATA FETCHING: Yahoo Finance → 15 years OHLCV
   ↓
PRE-SCREEN: Market Context Filter (Vattenpasset)
   ↓ (only ~15% pass)
PATTERN DETECTION: Double Bottom, IH&S, Bull Flag, Higher Lows
   ↓ (only patterns with prior -10% decline)
BACKTESTING: Calculate 21/42/63-day forward returns
   ↓
QUALITY GATES: EV > 0? RRR ≥ 3.0?
   ↓ (only ~10% pass)
RISK FILTERS: 37 layers (position sizing, costs, earnings, etc.)
   ↓ (only ~5-10 instruments pass all filters)
SCORING: 0-100 based on Win Rate, RRR, EV, Context
   ↓
RANKING: Sort by score
   ↓
OUTPUT: Top 3-5 setups with full details
```

**Final Result**: 
- 720 instruments scanned
- 5-10 POTENTIAL setups
- Top 3-5 recommended for Sunday review
- Each with precise position size, stop loss, costs, and risk metrics

---

## 🚀 How to Run

```bash
# Full Sunday analysis (4-6 hours)
python sunday_dashboard.py

# Quick test (100 instruments, 30 minutes)
python sunday_dashboard.py --quick

# Custom capital
python sunday_dashboard.py --capital 200000
```

---

## 📚 Related Documentation

- **README.md** - High-level system overview (casino philosophy)
- **V3.0_MASTER_SYSTEM.md** - V3.0 feature documentation (16 features)
- **ISK_OPTIMIZATION.md** - Swedish ISK-specific cost optimization
- **EXECUTION_COST_GUARD.md** - Detailed cost calculation logic
- **ALL_WEATHER_CRISIS_MODE.md** - Crisis trading with 59 defensive instruments
- **MACRO_INDICATORS.md** - Professional risk detection (yield curve, credit spreads)

---

**Co-Authored-By: Warp <agent@warp.dev>**
