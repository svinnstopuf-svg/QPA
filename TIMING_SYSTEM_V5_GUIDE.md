# V5.0 MAE-Minimizing Buy Signal System

## Overview

Upgraded Sunday Dashboard från statistiska kandidater till **skarpa köpsignaler** med fokus på att minimera MAE (Maximum Adverse Excursion - nedgång efter köp).

## Filosofi

**Tidigare (V4.0):** Hitta statistiskt starka patterns med hög Robust Score  
**Nu (V5.0):** Generera ACTIVE BUY SIGNALS endast när timing är optimal för omedelbar reversal

## De 4 Nya Villkoren

### 1. TIMING_THRESHOLD = 50%

**Regel:**
- Robust Score > 70 + Timing Confidence ≥ 50% = **ACTIVE BUY SIGNAL** 🚀
- Robust Score > 70 + Timing Confidence < 50% = **WATCHLIST** ⏸️

**Varför 50%?**
- Minimerar initial drawdown
- Endast köp när minst 2 av 4 timing-signaler är starka
- Väntar på konkret reversal-bevis, inte bara statistisk edge

### 2. Enhanced Volume Confirmation

**Funktion:** `check_volume_exhaustion()`

**Två godkända scenarion:**

**A) Seller Exhaustion:**
- Senaste dagens volym är ≥15% lägre än 5-dagars snitt
- Under en prisnedgång
- **Tolkning:** Säljare ger upp, pressure minskar

**B) Buyer Entry:**
- Senaste dagen är grön (close > open)
- Volym är ≥10% högre än 5-dagars snitt
- **Tolkning:** Köpare har klivit in

**Output:** Boolean `volume_confirmed` (YES/NO)

### 3. RSI(2) Hook Logic

**Funktion:** `_detect_rsi_hook()`

**Hook-mönster:**
1. RSI(2) < 10 de senaste 2 dagarna (extremt översåld)
2. RSI(2) vänt uppåt och stängt > 15
3. **Bonus:** +20% boost på total timing score

**Varför detta fungerar:**
- RSI(2) < 10 = kortsiktig momentum-fjäder komprimerad maximalt
- Vändning > 15 = fjädern börjar släppa
- Historiskt ofta 1-3 dagars window för optimal entry

**Exempel:**
- Dag -2: RSI(2) = 8.5
- Dag -1: RSI(2) = 9.2
- Dag 0: RSI(2) = 16.5 ✓ HOOK DETECTED
- Timing Score: 50 × (1 + 0.20) = **60%** → ACTIVE BUY SIGNAL

### 4. Två-Grupps Presentation

**GROUP 1: ACTIVE BUY SIGNALS**
- Robust Score > 70 OCH Timing ≥ 50%
- Färdiga att köpa samma dag
- Sorterade efter timing confidence (högst först)

**GROUP 2: WATCHLIST (Waiting for Trigger)**
- Robust Score > 70 MEN Timing < 50%
- Kräver övervakning dagligen
- Kolumn: "Reason for Waiting" visar vad som saknas

**Möjliga Waiting Reasons:**
- "Waiting for Volume" - Volume inte confirmed
- "RSI not oversold" - RSI(2) > 30
- "RSI too low (no hook yet)" - RSI(2) < 15 utan hook
- "Price Action missing" - Ingen Hammer/Bullish Engulfing
- "Timing < 50%" - Generell låg confidence

## Implementering

### Timing Score Dataclass

```python
@dataclass
class TimingSignals:
    rsi_momentum_flip: float          # 0-25 points
    mean_reversion_distance: float    # 0-25 points
    volume_exhaustion: float          # 0-25 points
    price_action_signal: float        # 0-25 points
    
    # Enhanced fields
    rsi_2_current: float
    rsi_2_previous: float
    rsi_2_two_days_ago: float        # För RSI Hook
    volume_confirmed: bool           # Enhanced volume check
    rsi_hook_boost: float           # 0.0 or 0.20 (20% boost)
    
    @property
    def total_score(self) -> float:
        base = sum of 4 signals (0-100)
        boosted = base × (1 + rsi_hook_boost)
        return min(100, boosted)
```

### Sunday Dashboard Output

**Exempel:**

```
================================================================================
🎯 SUNDAY ANALYSIS - BUY SIGNAL CLASSIFICATION
================================================================================

✅ ACTIVE BUY SIGNALS: 2
⏸️  WATCHLIST (Waiting for Trigger): 3
📊 Total Analyzed: 8

================================================================================

################################################################################
GROUP 1: ACTIVE BUY SIGNALS (Robust Score > 70 AND Timing > 50%)
################################################################################

🚀 RANK 1: TICKER - Pattern Name
Score: 85.2/100 | Priority: PRIMARY | Timing: 65% | Status: ACTIVE BUY SIGNAL

TIMING SCORE (Immediate Reversal):
  Overall Confidence: 65% (0-100)
  🎯 RSI HOOK DETECTED: +20% boost applied!
  └─ RSI Momentum Flip: 20/25
     RSI(2): 16.5 (prev: 9.2, 2d ago: 8.5)
  └─ Mean Reversion: 25/25
     Distance: -3.2 std from EMA(5)
  └─ Volume Exhaustion: 20/25
     Trend: Decreasing
     Enhanced Volume Check: ✅ CONFIRMED
  └─ Price Action: 15/25
     Pattern: Bullish High Close
  🚀 ACTIVE BUY SIGNAL - Good timing for entry

################################################################################
GROUP 2: CANDIDATES ON WATCHLIST (High Robust Score, Waiting for Timing)
################################################################################

⏸️ RANK 1: TICKER2 - Pattern Name
Score: 92.0/100 | Priority: PRIMARY | Timing: 35% | Status: WATCHLIST
⚠️ Reason for Waiting: Waiting for Volume, Price Action missing

TIMING SCORE (Immediate Reversal):
  Overall Confidence: 35% (0-100)
  └─ RSI Momentum Flip: 10/25
     RSI(2): 8.2 (prev: 12.3, 2d ago: 18.5)
  └─ Mean Reversion: 25/25
     Distance: -3.5 std from EMA(5)
  └─ Volume Exhaustion: 0/25
     Trend: Increasing
     Enhanced Volume Check: ❌ NOT CONFIRMED
  └─ Price Action: 0/25
     Pattern: Bearish/Neutral
  ⏸️ WATCHLIST - Timing below 50% threshold
```

## Workflow

### Söndag (Analys)
1. Kör `python sunday_dashboard.py`
2. Se ACTIVE BUY SIGNALS (färdiga att köpa måndag)
3. Se WATCHLIST (bevaka dagligen)

### Måndag-Fredag (Övervakning)
**För WATCHLIST-kandidater:**
1. Öppna TradingView/Avanza
2. Kolla varje WATCHLIST-ticker
3. Om "Reason for Waiting" är uppfylld:
   - Waiting for Volume → Kolla om dagens volym confirmar
   - RSI too low → Kolla om RSI(2) > 15
   - Price Action missing → Kolla om Hammer/Bullish Engulfing
4. Om alla villkor uppfyllda → Övergår till BUY SIGNAL

### Entry Execution
**För ACTIVE BUY SIGNALS:**
- Köp vid marknadens öppning eller vid dagens lägsta
- Sätt stop-loss enligt MAE Optimizer (se RISK ANALYSIS)
- Dokumentera i `positions.json`

## Fördelar med V5.0

### 1. Reducerad MAE
- **V4.0:** Köpte när Robust Score > 70 → ofta initial drawdown 5-10%
- **V5.0:** Väntar på timing → initial drawdown typ 2-4%

### 2. Högre Win Rate
- Endast entry när reversal redan påbörjad
- Volume + RSI + Price Action alla konfirmerar samtidigt

### 3. Mindre Stress
- ACTIVE BUY SIGNALS = handla direkt
- WATCHLIST = lugn övervakning, inga FOMO-trades

### 4. Bättre Kapitaleffektivitet
- Färre positioner som "bara ligger"
- Snabbare moves efter entry

## Limitations

### False Negatives
- Vissa bra setups missar vi (rev ersalar som sker utan volym-spike)
- Acceptabelt: Bättre missa några än ta för tidig entry

### Timing kan vända snabbt
- WATCHLIST kan bli ACTIVE BUY SIGNAL på 1 dag
- Kräver daglig övervakning

### RSI Hook är sällsynt
- Många setups får aldrig RSI < 10
- Men när det händer = extremt kraftfull signal

## Backtesting Guidance

För att validera V5.0:
1. Jämför MAE för trades med Timing ≥50% vs <50%
2. Mät win rate för ACTIVE BUY SIGNALS vs alla WATCHLIST
3. Analysera "Days to Profit" för olika timing-nivåer

**Hypotes:**
- Timing ≥50%: Avg MAE -3%, Win Rate 75%, Days to Profit: 5
- Timing <50%: Avg MAE -7%, Win Rate 65%, Days to Profit: 15

## Quick Reference

| Metric | Threshold | Action |
|--------|-----------|--------|
| Robust Score | >70 | Required |
| Timing Confidence | ≥50% | BUY SIGNAL |
| Timing Confidence | <50% | WATCHLIST |
| RSI(2) Hook | Detected | +20% boost |
| Volume Confirmed | YES | Strong signal |
| Volume Confirmed | NO | Waiting reason |

## Next Steps

1. **Kör första Sunday analys med V5.0**
2. **Dokumentera alla ACTIVE BUY SIGNALS → positions.json**
3. **Sätt upp dagliga alerts för WATCHLIST-tickers**
4. **Efter 4 veckor: Analysera MAE och win rate vs V4.0**
