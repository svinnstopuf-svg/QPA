# V7.0 Dual-Pipeline Architecture

## Overview

V7.0 introduces **TWO INDEPENDENT PIPELINES** that scan the universe simultaneously:

- **Motor A (Mean Reversion)**: Bottom fishing - buy weakness at support
- **Motor B (Momentum)**: Launchpad trading - buy strength before breakout

## Critical Architectural Insight

Motor A and Motor B have **MUTUALLY EXCLUSIVE** requirements:

| Criterion | Motor A | Motor B |
|-----------|---------|---------|
| Price vs EMA200 | **< EMA200** | **> EMA50 > EMA200** |
| Distance from High | **-15%+ decline** | **>95% of 52w high** |
| Philosophy | Buy fear | Buy greed |
| Pattern | Double Bottom, IH&S | VCP, Cup & Handle |
| Win Rate | 60% (conservative) | 65% (aggressive) |
| Stop Loss | 2-4% (tight MAE) | 8-12% (wide trailing) |

**Result**: Same instrument CANNOT qualify for both simultaneously (except during convergence window).

## Dual-Pipeline Flow

```
UNIVERSE (1200+ tickers)
         |
         +--> MOTOR A PIPELINE
         |    - Scan for price < EMA200, -10% decline
         |    - Pattern detection (mean reversion)
         |    - Statistical validation (Robust Statistics)
         |    - Post-processing (37 Motor A filters)
         |    --> Motor A Results
         |
         +--> MOTOR B PIPELINE
              - Scan for RS≥95, uptrend, VCP
              - Pattern detection (momentum)
              - Statistical validation (Bayesian)
              - Post-processing (37 Motor B filters)
              --> Motor B Results
         
CONVERGENCE CHECK
- If instrument appears in BOTH: 1.2x boost
- Rare! Means Motor A triggered <15d ago, now Motor B active

MERGE & RANK
- Sort by best signal (Motor A rank vs Motor B rank)
- Display top setups from each pipeline
```

## Post-Processing Differences

### Motor A (Mean Reversion) - 37 Features

#### Position Sizing
- **Conservative**: 1.5-2.5% base allocation
- **Sector volatility PENALTY**: Divide by volatility factor (want stable sectors)
- **FX adjustment**: Apply USD/SEK Z-score multiplier

#### Risk Management
- **MAE stops**: Tight 2-4% (mean reversion needs quick exits)
- **Quality filter**: REJECT if Quality Score < 40 (avoid value traps)
- **Macro regime**: Apply Wind Filter multiplier

#### Validation
- **Robust Statistics**: Bayesian with 55% prior (conservative)
- **Timing Score**: RSI(2) hook, volume exhaustion
- **Correlation clustering**: Avoid overexposure

### Motor B (Momentum) - 37 Matching Features

#### Position Sizing
- **Aggressive**: 2-4% base allocation (top RS-Rating = 4%)
- **Sector volatility BONUS**: Multiply by 1.1x for high-vol sectors (momentum loves volatility)
- **NO FX adjustment**: Momentum is momentum regardless of currency

#### Risk Management
- **Trailing stops**: Wide 2.5x ATR (let winners run)
- **Exit strategy**: 2R/3R/5R profit targets
- **Institutional ownership**: REJECT if < 30% (need smart money confirmation)

#### Validation
- **Bayesian Statistics**: 65% prior (momentum historically stronger)
- **Bootstrap resampling**: 1000 simulations
- **Timing Score**: Volume surge (2x+), price acceleration, gap analysis
- **Pattern Detection**: VCP, Cup & Handle, Ascending Triangle
- **Quality Checks**: Earnings growth >15%, liquidity >$10M/day

## Component Mapping

| V6.0 Component | Motor A Usage | Motor B Usage |
|----------------|---------------|---------------|
| PositionTradingScreener | ✅ Primary scanner | ❌ N/A |
| MomentumEngine | ❌ N/A | ✅ Primary scanner |
| Quality Score | ✅ Avoid value traps | ✅ Institutional ownership |
| Timing Score | ✅ RSI hook | ✅ Volume surge |
| MAE Optimizer | ✅ Tight stops | ❌ Uses trailing stops |
| FX Guard | ✅ USD/SEK adjustment | ❌ Not applied |
| Macro Regime | ✅ Defensive halving | ✅ Defensive halving |
| Market Breadth | ✅ Pre-flight check | ✅ Pre-flight check |

## Files

- `sunday_dashboard.py` - **V6.1** (Motor A only, V7.0 bugs fixed)
- `sunday_dashboard_v7_dual.py` - **V7.0** (Complete dual-pipeline)
- `sunday_dashboard_backup_v6.py` - Backup of original V6.0

## Usage

### Run V7.0 Dual-Pipeline

```python
from sunday_dashboard_v7_dual import DualPipelineDashboard

dashboard = DualPipelineDashboard(
    capital=100000.0,
    max_risk_per_trade=0.01,
    min_position_sek=1500.0
)

# Scan full universe (1200+ tickers)
results = dashboard.run(max_setups=10)

# Or custom watchlist
results = dashboard.run(
    tickers=["NVDA", "TSLA", "AAPL", "NOLA-B.ST"],
    max_setups=10
)

print(f"Motor A setups: {results['motor_a_count']}")
print(f"Motor B setups: {results['motor_b_count']}")
print(f"Convergence: {results['convergence_count']}")
```

### Run V6.1 (Motor A Only - Safe)

```python
from sunday_dashboard import SundayDashboard

dashboard = SundayDashboard(
    capital=100000.0,
    max_risk_per_trade=0.01,
    min_position_sek=1500.0
)

results = dashboard.run(max_setups=5)
```

## Testing

```bash
# Test dual-pipeline on small watchlist
python test_dual_pipeline_full.py

# Expected output:
# - Motor A: 0-2 setups (rare in current market)
# - Motor B: 0-3 setups (rare - need RS≥95)
# - Convergence: 0 (very rare)
```

## Migration Path

**Current State**: `sunday_dashboard.py` (V6.1)
- ✅ All V6.0 features work
- ✅ Motor B bugs fixed (disabled)
- ✅ Iron Curtain bugs fixed (disabled)

**Next Step**: Test `sunday_dashboard_v7_dual.py`
- 🧪 Verify Motor A matches V6.1 results
- 🧪 Verify Motor B finds momentum leaders
- 🧪 Test convergence detection

**Final Step**: Replace `sunday_dashboard.py` with V7.0
```bash
cp sunday_dashboard_v7_dual.py sunday_dashboard.py
```

## Known Limitations

1. **Runtime**: Full universe scan takes ~8 hours (Motor A) + ~4 hours (Motor B) = 12 hours
2. **Convergence**: Extremely rare in practice (<1% of setups)
3. **Motor B data requirements**: Needs 2-year history for RS-Rating (some tickers may fail)

## Philosophy

**Motor A**: "Be greedy when others are fearful" (Warren Buffett)
**Motor B**: "The trend is your friend" (Mark Minervini)

Both strategies are valid. Dual-pipeline lets you capture BOTH opportunities.
