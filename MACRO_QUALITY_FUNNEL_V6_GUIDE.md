# V6.0 Macro + Quality Funnel System

## Overview

Sunday Dashboard uppgraderad från "Hitta mönster" till **"Trade smart companies in good markets"**.

Systemet fungerar nu som en **tratt med 3 filter**:
1. **Macro Filter (The 'Wind')**: Bestämmer OM vi handlar (full size vs half size)
2. **Quality Filter (The 'Company')**: Bestämmer VAD vi handlar (bara profitabla bolag)
3. **Timing + Robust Filter**: Bestämmer NÄR vi handlar (immediate reversal probability)

## Filosofi

**V5.0 Problem:**
- Köpte statistiskt starka patterns...
- ...i dåliga bolag (value traps, skuldsatta, unprofitable)
- ...när marknaden kollapsade (S&P < EMA200, räntor skenade)

**V6.0 Lösning:**
- **Macro regime** halverar position sizes vid marknads-stress
- **Quality score** filtrerar bort trash-bolag innan vi ens tittar på pattern
- **Multi-Factor Rank** kombinerar statistik (Robust) + fundamenta (Quality)

## Modul 1: Global Macro Regime (The 'Wind' Filter)

### Data Sources
Hämtar 3 index varje söndag:
1. **S&P 500 (^GSPC)**: Global risk sentiment
2. **US 10Y Yield (^TNX)**: Ränte-stress
3. **USD/SEK (USDSEK=X)**: Valutapositionering

### Regime Logic

**DEFENSIVE Regime triggers om:**
- S&P 500 < 200-day EMA, ELLER
- US 10Y Yield stiger >30 basis points på 3 veckor

**AGGRESSIVE Regime annars**

### Position Size Effect

| Regime | Multiplier | Action |
|--------|-----------|--------|
| AGGRESSIVE | 1.0x (100%) | Normal position sizing |
| DEFENSIVE | 0.5x (50%) | Halve all positions |

**Exempel:**
- Base allocation: 3% (3,000 SEK på 100k portfolio)
- AGGRESSIVE: 3,000 SEK position
- DEFENSIVE: 1,500 SEK position (halved)

### Display Output

```
🌐 Macro Regime Analysis (The 'Wind' Filter)...
   Regime: DEFENSIVE
   Position Size Multiplier: 50%

   S&P 500:
      Current: 5,850.45
      200-day EMA: 5,920.30
      ⚠️ -1.18% vs EMA

   US 10Y Yield:
      Current: 4.45%
      3-week change: +35 bps
      Trend: Rising

   ⚠️ DEFENSIVE MODE ACTIVATED:
      • S&P 500 below 200-day EMA
      • 10Y yield rising sharply (+35 bps)
   → All position sizes will be HALVED (50%)
```

## Modul 2: Factor Quality Score (The 'Company' Filter)

### Scoring Components

**1. Profitability (0-40 points)**
- Metric: ROE (Return on Equity)
- Target: >15%
- Full points: ROE ≥15%
- Scales linearly: 10% ROE = 26.7 points

**2. Solvency (0-40 points)**
- Metric: Debt/Equity ratio
- Target: <1.0
- Full points: D/E <1.0
- Penalty for high debt: D/E=2.0 → 20pts, D/E≥4.0 → 0pts

**3. Value (0-20 points)**
- Metric: P/E vs Sector Average
- Target: Below sector average
- Max points: 50% discount to sector = 20pts
- Penalty for premium: 2x sector P/E = 0pts

**Total: 0-100 points**

### Quality Categories

| Score | Category | Interpretation |
|-------|----------|---------------|
| 80-100 | HIGH QUALITY ✅ | Strong profitability, low debt, fair value |
| 40-79 | ACCEPTABLE ⚠️ | Passable fundamentals, tradeable |
| 0-39 | HIGH RISK/TRASH 🚨 | Avoid - likely value trap |

### Value Trap Detection

**Warning triggered if:**
- Quality Score < 40 (trash company)
- AND P/E < Sector Average (appears "cheap")

**Interpretation:** Cheap for a reason - avoid!

### Sector P/E Benchmarks

| Sector | Avg P/E |
|--------|---------|
| Technology | 25.0 |
| Healthcare | 20.0 |
| Financial Services | 12.0 |
| Consumer Cyclical | 18.0 |
| Consumer Defensive | 20.0 |
| Industrials | 18.0 |
| Energy | 15.0 |
| Basic Materials | 16.0 |
| Communication Services | 20.0 |
| Utilities | 18.0 |
| Real Estate | 22.0 |

### Display Output

```
🏭 Quality Score Analysis (The 'Company' Filter)...
   ✅ CALM: HIGH QUALITY (Q:85)
   ✅ KBH: HIGH QUALITY (Q:82)
   🚨 TICKER3: HIGH RISK/TRASH (Q:32) - VALUE TRAP!

COMPANY QUALITY (V6.0 - The 'Company' Filter):
  Quality Score: ✅ HIGH QUALITY (85/100)
  Company: Cal-Maine Foods Inc.
  ROE: 22.3% (Score: 40/40)
  Debt/Equity: 0.15 (Score: 40/40)
  P/E: 12.5 vs Sector 20.0 (-38%, Score: 15/20)
```

## Modul 3: Multi-Factor Rank

### Calculation

Combines statistical edge (Robust Score) with fundamental quality:

```python
Multi-Factor Rank = (Robust Score × 0.60) + (Quality Score × 0.40)
```

**Rationale:**
- 60% weight on pattern strength (proven edge)
- 40% weight on company quality (risk mitigation)

### Sorting Priority

Setups now ranked by:
1. **Signal Status** (ACTIVE BUY vs WATCHLIST)
2. **Quality Score** (companies that make money first)
3. **Timing Confidence** (immediate reversal probability)
4. **Robust Score** (statistical edge)
5. **Multi-Factor Rank** (combined metric)

### Example Rankings

**Before V6.0 (Robust only):**
1. TICKER1: Robust 95, Quality 25 → Ranked #1 (bad company, strong pattern)
2. TICKER2: Robust 80, Quality 90 → Ranked #2 (great company, good pattern)

**After V6.0 (Multi-Factor):**
1. TICKER2: Multi-Factor 84 (80×0.6 + 90×0.4) → Ranked #1 ✅
2. TICKER1: Multi-Factor 67 (95×0.6 + 25×0.4) → Ranked #2 (filtered out if Q<40)

## Complete Workflow

### Sunday Analysis

```powershell
python sunday_dashboard.py
```

**Step 1: PRE-FLIGHT (Macro Filter)**
1. Analyze S&P 500 vs 200-day EMA
2. Check US 10Y yield trend (3-week)
3. Determine regime: AGGRESSIVE or DEFENSIVE
4. Set position size multiplier (100% or 50%)

**Step 2: SCREENING**
1. Scan 1000+ instruments for patterns
2. Filter to Robust Score > 70

**Step 3: POST-PROCESSING**
1. **Quality Filter**: Analyze ROE, Debt/Equity, P/E for each setup
2. **Timing Filter**: Calculate timing confidence (RSI, volume, price action)
3. **Multi-Factor Rank**: Combine Robust + Quality scores
4. **Position Sizing**: Apply regime multiplier (macro adjustment)

**Step 4: CLASSIFICATION**
- **ACTIVE BUY SIGNALS**: Quality ≥40, Timing ≥50%
- **WATCHLIST**: Quality ≥40, Timing <50%
- **FILTERED OUT**: Quality <40 (trash companies)

### Output Format

```
🎯 SUNDAY ANALYSIS - BUY SIGNAL CLASSIFICATION
================================================================================

✅ ACTIVE BUY SIGNALS: 3
⏸️  WATCHLIST (Waiting for Trigger): 5
📊 Total Analyzed: 12
🚨 Filtered (Quality < 40): 4

################################################################################
GROUP 1: ACTIVE BUY SIGNALS (Robust Score > 70 AND Timing > 50%)
################################################################################

🚀 RANK 1: CALM - Nya lägsta nivåer (252 perioder)
Score: 96.7/100 | Priority: PRIMARY | Timing: 65% | Status: ACTIVE BUY SIGNAL
Quality: 85/100 | Multi-Factor Rank: 88.5/100 | Macro: 🟡 DEFENSIVE

COMPANY QUALITY (V6.0 - The 'Company' Filter):
  Quality Score: ✅ HIGH QUALITY (85/100)
  Company: Cal-Maine Foods Inc.
  ROE: 22.3% (Score: 40/40)
  Debt/Equity: 0.15 (Score: 40/40)
  P/E: 12.5 vs Sector 20.0 (-38%, Score: 15/20)

POSITION SIZING:
  Position: 1,500 SEK (1.50%)
  🌐 Macro Adjustment: Position HALVED due to DEFENSIVE regime (50%)
  Expected Profit: +173 SEK
```

## Decision Tree

```
START: New Low pattern detected
  │
  ├─ Robust Score > 70? 
  │   ├─ NO → REJECT (weak pattern)
  │   └─ YES → Continue
  │
  ├─ Quality Score ≥ 40?
  │   ├─ NO → REJECT (trash company / value trap)
  │   └─ YES → Continue
  │
  ├─ Timing Confidence ≥ 50%?
  │   ├─ NO → WATCHLIST (wait for better timing)
  │   └─ YES → ACTIVE BUY SIGNAL
  │
  ├─ Macro Regime?
  │   ├─ DEFENSIVE → Position size × 0.5
  │   └─ AGGRESSIVE → Position size × 1.0
  │
  └─ EXECUTE TRADE
```

## Risk Mitigation Benefits

### 1. Avoid Value Traps
**Problem:** Pattern shows +30% edge, but company is unprofitable with 3.0 D/E
**Solution:** Quality Score = 20/100 → FILTERED OUT before entry

### 2. Reduce Drawdown in Bear Markets
**Problem:** Great patterns collapse when S&P breaks below 200-day EMA
**Solution:** DEFENSIVE regime → Halve position sizes automatically

### 3. Prioritize Quality Companies
**Problem:** Equal weight to trash (Q:30) and quality (Q:90) if same Robust Score
**Solution:** Multi-Factor Rank → Quality companies ranked first

## Backtesting Validation

**Recommended Tests:**

1. **Macro Regime Effectiveness**
   - Compare MAE during AGGRESSIVE vs DEFENSIVE periods
   - Hypothesis: Smaller MAE in DEFENSIVE (due to halved positions)

2. **Quality Score Correlation**
   - Win rate for Q≥80 vs Q<40
   - Hypothesis: High quality = higher win rate, lower volatility

3. **Multi-Factor vs Robust-Only**
   - Sharpe ratio using Multi-Factor Rank vs Robust Score alone
   - Hypothesis: Multi-Factor → better risk-adjusted returns

## Quick Reference

### Macro Regime
- **Triggers**: S&P < EMA200 OR Yield +30bps
- **Effect**: Position × 0.5
- **Check**: Sunday PRE-FLIGHT

### Quality Score
- **Components**: ROE (40pts) + Debt (40pts) + P/E (20pts)
- **Threshold**: ≥40 to trade
- **Warning**: <40 + cheap P/E = VALUE TRAP

### Multi-Factor Rank
- **Formula**: Robust×0.6 + Quality×0.4
- **Purpose**: Balance edge + safety
- **Sorting**: Quality → Timing → Robust

## Limitations

1. **Fundamental Data Lag**
   - yfinance data may be outdated
   - Quality score based on last reported quarter

2. **Macro Whipsaws**
   - S&P can cross 200-day EMA frequently
   - May cause position sizing to flip-flop

3. **Quality Doesn't Guarantee Performance**
   - High quality ≠ guaranteed win
   - Pattern must still work (Robust Score)

## Next Steps

1. **Run first V6.0 Sunday Dashboard**
2. **Document filtered setups** (Quality <40) for learning
3. **Track DEFENSIVE regime periods** vs actual market performance
4. **After 8 weeks:** Compare V6.0 (Macro+Quality) vs V5.0 (Timing only)

**Goal:** Only trade patterns in profitable companies when markets cooperate! 🎯
