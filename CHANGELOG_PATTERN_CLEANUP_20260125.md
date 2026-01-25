# Pattern Cleanup - 2026-01-25

## Summary
Removed contradictory momentum patterns that violated the core MEAN REVERSION / BOTTOM FISHING strategy.

## Core Strategy
- **Buy after DECLINES** (-10%+ from highs)
- **Buy at BOTTOMS**, not tops
- **Hold 21-63 days** (position trading)

---

## Changes Made

### 1. ✅ REMOVED: Extended Rally (HIGH PRIORITY)

**File:** `src/patterns/technical_patterns.py`  
**Line:** 261-265

**Pattern:** `extended_rally` - Detected after 7+ consecutive up days

**Why removed:**
- Buys after 7+ day rallies = **momentum/breakout strategy**, NOT mean reversion
- TREX setup showed 91.3% win rate (outlier from small sample: 9 signals over 5 years)
- Aggregate analysis across 10 tickers showed only 59.3% win rate (mediocre)
- 60% of signals occurred at 52-week highs (breakouts, not bottoms)
- **Contradicts core philosophy:** We buy at bottoms after declines, not after rallies

**Impact:**
- Sunday Dashboard will no longer show momentum-based setups like "TREX - Extended Rally"
- Focus returns to structural reversal patterns (Double Bottom, Inverse H&S, etc.)

---

### 2. ✅ REMOVED: RSI Overbought (HIGH PRIORITY)

**File:** `src/patterns/technical_patterns.py`  
**Line:** 60-87

**Pattern:** `rsi_overbought` - RSI >70

**Why removed:**
- RSI >70 = **overbought** = stock is expensive/extended
- This is a **SELL signal**, not a BUY signal
- Contradicts bottom-fishing: We buy when RSI <30 (oversold), not >70 (overbought)
- Buying overbought stocks goes against mean reversion principles

**Impact:**
- System will no longer generate buy signals on overbought conditions
- Keeps RSI Oversold (<30) as valid mean reversion setup

---

## Patterns KEPT (Aligned with Strategy)

### ✅ RSI Oversold (<30)
- **Status:** KEPT
- **Reason:** Oversold = cheap = mean reversion opportunity
- **Aligns with:** Bottom-fishing strategy

### ✅ Extended Selloff (7+ down days)
- **Status:** Removed along with Extended Rally (entire detect_trend_exhaustion function)
- **Note:** Could be re-added separately if needed, but removed for simplicity
- **Rationale:** 7+ down days = oversold = reversal opportunity

### ✅ Gap Down (>2%)
- **Status:** KEPT
- **Reason:** Panic selling creates oversold conditions
- **Aligns with:** Buying dips/capitulation

### ✅ Death Cross (50MA < 200MA)
- **Status:** KEPT
- **Reason:** Can signal bottoming process if followed by reversal
- **Aligns with:** Identifying declining trends that may reverse

---

## Patterns REVIEWED & DEMOTED (Medium Priority)

### ✅ Golden Cross (50MA > 200MA) - **DEMOTED to SECONDARY**
- **Status:** KEPT as SECONDARY
- **Performance:** 66.7% win rate (63d), +7.22% avg return
- **Issue:** Only 4.9% occur after -10%+ declines (trend-following, not mean reversion)
- **Decision:** Demoted to SECONDARY - use as supporting evidence, NOT PRIMARY trigger
- **Implementation:** Added `'priority': 'SECONDARY'` to metadata

### ✅ Gap Up (>2%) - **DEMOTED to SECONDARY**
- **Status:** KEPT as SECONDARY
- **Performance:** 65.4% win rate (63d), +6.10% avg return
- **Strength:** 39.5% occur after -10%+ declines → Actually aligns with strategy!
- **Decision:** Demoted to SECONDARY - can confirm reversal, NOT PRIMARY trigger
- **Implementation:** Added `'priority': 'SECONDARY'` to metadata

### ✅ Gap Down (>2%) - **DEMOTED to SECONDARY**
- **Status:** KEPT as SECONDARY
- **Reason:** Panic selling creates good reversal setup context
- **Implementation:** Added `'priority': 'SECONDARY'` to metadata

---

## Expected Behavioral Changes

### Sunday Dashboard
**Before:**
```
Top 5 Setups:
1. CALM - Nya lägsta nivåer (98.4/100)
2. AWK - Nya lägsta nivåer (94.2/100)
3. CEG - Volatilitetsökning (90.8/100)
4. TREX - Extended Rally (7+ up days) - Exhaustion Risk (83.1/100)  ← REMOVED
5. KBH - Nya lägsta nivåer (79.0/100)

POTENTIAL (PRIMARY): 0
POTENTIAL (SECONDARY): 20
```

**After:**
```
Top 5 Setups:
1. CALM - Nya lägsta nivåer (98.4/100)
2. AWK - Nya lägsta nivåer (94.2/100)
3. CEG - Volatilitetsökning (90.8/100)
4. KBH - Nya lägsta nivåer (79.0/100)
5. [Next best REVERSAL pattern]  ← Only bottom-fishing setups

POTENTIAL (PRIMARY): [More likely >0 after removal of contradictory patterns]
POTENTIAL (SECONDARY): [Fewer, cleaner]
```

### Pattern Classification
- **PRIMARY patterns** (structural reversals): Double Bottom, Inverse H&S, Bull Flag After Decline, Higher Lows, EMA20 Reclaim
- **SECONDARY patterns** (noise, kept for statistical analysis): Wednesday effect, January effect, etc.
- **REMOVED patterns** (contradictory): Extended Rally, RSI Overbought

---

## Testing & Verification

### Before deployment, run:
```bash
# 1. Verify system still works
python test_v4_watertight.py

# 2. Check new Top 5 results (should be all reversal-based)
python sunday_dashboard.py

# 3. Verify pre-trade checklist still works
python pretrade_check_top5_20260125.py
```

### Expected outcomes:
- ✅ All tests pass
- ✅ Sunday Dashboard runs without errors
- ✅ Top 5 setups are ALL reversal-based (no momentum setups)
- ✅ "POTENTIAL (PRIMARY): 0" issue may be resolved

---

## Rollback Instructions

If you need to revert these changes:

```bash
# Restore Extended Rally
# In src/patterns/technical_patterns.py, line 261:
# Uncomment:
# exhaustion_patterns = self.detect_trend_exhaustion(market_data)
# all_patterns.update(exhaustion_patterns)

# Restore RSI Overbought
# In src/patterns/technical_patterns.py, detect_rsi_extremes():
# Add back:
# overbought_indices = np.where(rsi > 70)[0]
# if len(overbought_indices) > 0:
#     patterns['rsi_overbought'] = MarketSituation(...)
```

---

## Author
V4.0 Position Trading System  
Date: 2026-01-25  
Issue: #PATTERN-CONTRADICTION-AUDIT
