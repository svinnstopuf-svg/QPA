# Pattern Cleanup - Final Summary (2026-01-25)

## ✅ Implementation: Option A (Pragmatic)

### Changes Made

**1. REMOVED (High Priority)**
- ❌ **Extended Rally** - Contradicts bottom-fishing (momentum, not reversal)
- ❌ **RSI Overbought** - Buying expensive stocks (overbought ≠ oversold)

**2. DEMOTED TO SECONDARY (Medium Priority)**
- ⬇️ **Golden Cross** - Trend-following (only 4.9% after declines) but works (67% WR, +7.2%)
- ⬇️ **Gap Up** - Momentum signal but 39.5% after declines, works (65% WR, +6.1%)
- ⬇️ **Gap Down** - Panic selling context (already marked SECONDARY)

**3. KEPT AS-IS**
- ✅ **RSI Oversold** - Perfect reversal setup
- ✅ **Death Cross** - Can signal bottoming process
- ✅ All PRIMARY patterns (Double Bottom, Inverse H&S, etc.)

---

## File Changes

### `src/patterns/technical_patterns.py`

**Lines 61-87:** Removed RSI Overbought detection
```python
# BEFORE:
overbought_indices = np.where(rsi > 70)[0]
patterns['rsi_overbought'] = MarketSituation(...)

# AFTER:
# RSI Overbought REMOVED - use for sell signals, not buy signals
```

**Lines 261-265:** Removed Extended Rally/Selloff detection
```python
# BEFORE:
exhaustion_patterns = self.detect_trend_exhaustion(market_data)
all_patterns.update(exhaustion_patterns)

# AFTER:
# Trend exhaustion - REMOVED: Extended Rally contradicts mean reversion strategy
# exhaustion_patterns = self.detect_trend_exhaustion(market_data)
# all_patterns.update(exhaustion_patterns)
```

**Lines 129-134, 221-243:** Added SECONDARY priority to Golden Cross, Gap Up, Gap Down
```python
metadata={
    'signal_type': 'technical',
    'priority': 'SECONDARY'  # ← ADDED
}
```

---

## Expected Behavior Changes

### Pattern Classification
```
PRIMARY (Structural Reversals):
  - Double Bottom
  - Inverse Head & Shoulders
  - Bull Flag After Decline
  - Higher Lows Reversal
  - EMA20 Reclaim
  - Nya lägsta nivåer (252 perioder)

SECONDARY (Supporting Evidence):
  - Golden Cross ← DEMOTED
  - Gap Up ← DEMOTED
  - Gap Down ← DEMOTED
  - RSI Oversold
  - Death Cross
  - Calendar effects (Wednesday, January, etc.)

REMOVED (Contradictory):
  - Extended Rally ✗
  - RSI Overbought ✗
```

### Sunday Dashboard Impact

**Before:**
```
POTENTIAL (PRIMARY): 0
POTENTIAL (SECONDARY): 20
Top 5: CALM, AWK, CEG, TREX (Extended Rally), KBH
```

**After:**
```
POTENTIAL (PRIMARY): [Likely >0 with cleaner filters]
POTENTIAL (SECONDARY): [Fewer, higher quality]
Top 5: CALM, AWK, CEG, KBH, [Next best REVERSAL setup]
       ↑ All reversal-based, no momentum setups
```

---

## Empirical Results (Supporting Data)

### Extended Rally Analysis
- **TREX:** 75% WR (not 91.3% - small sample artifact)
- **Aggregate (10 tickers):** 59.3% WR, +7.14% avg (mediocre)
- **60% at 52-week highs** = breakout, not reversal
- **Verdict:** REMOVE ✗

### Golden Cross Analysis
- **Win Rate (63d):** 66.7% ✅
- **Avg Return (63d):** +7.22% ✅
- **After declines:** Only 4.9% ❌
- **Verdict:** DEMOTE to SECONDARY ⬇️

### Gap Up Analysis
- **Win Rate (63d):** 65.4% ✅
- **Avg Return (63d):** +6.10% ✅
- **After declines:** 39.5% ✅
- **Verdict:** DEMOTE to SECONDARY ⬇️ (but useful!)

---

## Rationale: Why Option A (Pragmatic)?

**Why not Option B (Remove Golden Cross)?**
- Golden Cross works (67% WR, +7.2% return)
- Small sample (31 signals) - not harmful as SECONDARY
- Can boost confidence on existing positions

**Why not Option C (Remove Both)?**
- Gap Up actually useful (39.5% after declines!)
- Both patterns have >65% win rate for position trading
- As SECONDARY, they support but don't drive decisions

**Option A Benefits:**
- **Strict on PRIMARY** (only reversal patterns)
- **Flexible on SECONDARY** (supporting evidence allowed)
- **Data-driven** (kept patterns that actually work)
- **Practical** (uses all available edge, not dogmatic)

---

## Critical Fix: Sunday Dashboard Filtering

**Issue Found:** Death Cross was still appearing in Top 5 despite SECONDARY tag.

**Root Cause:** sunday_dashboard.py line 771 sorted ALL patterns by score without filtering SECONDARY.

**Solution:** Added PRIMARY-only filtering in `_post_process_setups()`:
```python
# Line 773-802: Filter PRIMARY vs SECONDARY
primary_only = []
secondary_only = []

for setup in processed:
    is_primary = any(keyword in setup.best_pattern_name.lower() for keyword in [
        'lägsta nivåer', 'double bottom', 'inverse', 'bull flag', 'higher lows',
        'ema20 reclaim', 'volatilitetökning'
    ])
    
    if is_primary:
        primary_only.append(setup)
    else:
        secondary_only.append(setup)

# Return PRIMARY first, then SECONDARY
return primary_only + secondary_only
```

Also fixed priority display (line 868-876) to show actual priority, not hardcoded "PRIMARY".

## Testing Checklist

Before deploying to production:

```bash
# 1. Verify pattern priorities
python verify_pattern_priorities.py

# 2. Run Sunday Dashboard (should exclude Death Cross from Top 5)
python sunday_dashboard.py

# 3. Verify pre-trade checklist on new Top 5
python pretrade_check_top5_20260125.py

# 4. Verify system integrity
python test_v4_watertight.py
```

**Expected outcomes:**
- ✅ All patterns have correct priority tags
- ✅ No "Extended Rally" setups in Top 5
- ✅ No "Death Cross" as PRIMARY in Top 5
- ✅ All Top 5 are PRIMARY reversal patterns only
- ✅ POTENTIAL (PRIMARY) > 0 (cleaner filtering)

---

## Philosophy

**Core Strategy (Unchanged):**
- Buy after DECLINES (-10%+ from highs)
- Buy at BOTTOMS, not tops
- Hold 21-63 days (position trading)

**Pattern Hierarchy (Refined):**
- **PRIMARY:** Must be structural reversal at bottom
- **SECONDARY:** Can support but never drive entry alone
- **REMOVED:** Contradicts core strategy (momentum, overbought)

**Implementation Principle:**
> "Be strict on PRIMARY entries (only reversals), but pragmatic on SECONDARY evidence (use what works)."

---

## Rollback (If Needed)

To revert Option A:

```python
# Restore Extended Rally (line 261)
exhaustion_patterns = self.detect_trend_exhaustion(market_data)
all_patterns.update(exhaustion_patterns)

# Restore RSI Overbought (line 72-90)
overbought_indices = np.where(rsi > 70)[0]
if len(overbought_indices) > 0:
    patterns['rsi_overbought'] = MarketSituation(...)

# Remove SECONDARY tags from Golden Cross, Gap Up, Gap Down
# (Delete 'priority': 'SECONDARY' from metadata)
```

---

## Author
V4.0 Position Trading System  
Date: 2026-01-25  
Implementation: Option A (Pragmatic)  
Status: ✅ Complete
