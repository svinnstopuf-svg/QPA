# Version 2.1 - Advanced Risk Controls

**Datum**: 2026-01-04  
**Status**: Production Ready  
**Nytt**: 4 Avancerade Riskkontroller

---

## 🎯 Översikt

Version 2.1 adderar sofistikerade riskkontroller som gör systemet marknadsneutralt och adaptivt:

1. **V-Kelly Position Sizing** - ATR-justerad risk parity
2. **Trend Filter** - 200-day MA confirmation (förhindra "fallande kniv")
3. **Regime Detection** - Market Stress Index (korrelationskontroll)
4. **Integration** - Alla tre arbetar tillsammans automatiskt

---

## 1. 🎲 Volatilitetsjusterad Position Sizing (V-Kelly)

### Problem:
1% i en stabil räntefond (BND) ≠ 1% i en volatil aktie (SBB)

### Lösning:
Justera positionsstorlek med Average True Range (ATR) för **Risk Parity**.

### Hur Det Fungerar:

```python
Target Risk per Position = 1% portfolio volatility

Position Size = Target Risk / ATR%

Exempel:
- BND: ATR 0.5% → Position = 1.0% / 0.5% = 2.0%
- SBB: ATR 3.0% → Position = 1.0% / 3.0% = 0.33%

Båda bidrar samma risk till portföljen!
```

### Användning:

```python
from src.risk import VolatilityPositionSizer

sizer = VolatilityPositionSizer(
    target_volatility=1.0,  # 1% risk per position
    max_position=0.05,  # Max 5%
    min_position=0.001  # Min 0.1%
)

# Justera position
position = sizer.adjust_position_size(
    base_allocation=3.0,  # Traffic light rekommendation
    atr_percent=2.5,  # ATR = 2.5% av pris
    signal_strength="GREEN"
)

print(f"Base: {position.base_allocation}%")
print(f"Adjusted: {position.volatility_adjusted}%")
print(f"Risk Units: {position.risk_units}")
print(f"Recommendation: {position.recommendation}")
```

### Output:
```
Base: 3.0%
Adjusted: 1.2%  # Reducerat pga hög volatilitet
Risk Units: 0.030  # Normaliserad risk
Recommendation: REDUCED
```

### Volatility Categories:
- **Low (<1% ATR)**: FULL position allowed
- **Medium (1-2% ATR)**: FULL if GREEN, REDUCED if YELLOW
- **High (2-3% ATR)**: REDUCED always
- **Very High (>3% ATR)**: MINIMAL position

---

## 2. 📊 Trend Filter (Multi-Timeframe Confirmation)

### Problem:
Ett mönster kan se GREEN ut kortsiktigt men aktien är i långsiktig nedtrend.
→ "Catching a falling knife"

### Lösning:
Investera bara i GREEN/YELLOW om pris > 200-dagars MA.

### Hur Det Fungerar:

```
Price vs 200-day MA:

🚀 STRONG_UPTREND: Price >10% above MA → Full positions OK
📈 UPTREND: Price >0% above MA → Positions allowed
📉 DOWNTREND: Price <0% below MA → BLOCK GREEN/YELLOW signals
⚠️ STRONG_DOWNTREND: Price >10% below MA → Strong BLOCK
```

### Användning:

```python
from src.risk import TrendFilter

filter = TrendFilter(
    ma_period=200,
    strong_trend_threshold=10.0,
    allow_slight_below=False  # Strikt över MA
)

# Analysera trend
analysis = filter.analyze_trend(
    prices=price_array,
    current_signal="GREEN"
)

print(f"Distance from MA: {analysis.distance_from_ma:.1f}%")
print(f"Regime: {analysis.regime}")
print(f"Allow Long: {analysis.allow_long}")
print(f"Recommendation: {analysis.recommendation}")
```

### Output Exempel:

**Fall 1: Positiv Trend**
```
Distance from MA: +5.2%
Regime: UPTREND
Allow Long: True
Recommendation: FULL POSITION - Uptrend + GREEN signal
```

**Fall 2: Negativ Trend (OVERRIDE)**
```
Distance from MA: -8.3%
Regime: DOWNTREND
Allow Long: False
Recommendation: OVERRIDE - Below 200 MA (-8.3%) - Fallande kniv!
```

### Automatisk Signal Override:
```python
# Filter kan automatiskt ändra signaler
filtered_signals = filter.filter_signals(
    signals={'AAPL': 'GREEN', 'SBB': 'YELLOW'},
    prices={'AAPL': price_data_aapl, 'SBB': price_data_sbb}
)

# Om SBB under 200 MA:
# filtered_signals['SBB'] = 'RED'  # Overrided!
```

---

## 3. 🚨 Regime Detection (Market Stress Index)

### Problem:
När >80% av alla instrument är RED, fungerar inte teknisk analys.
Korrelation → 1 (allt faller tillsammans).

### Lösning:
Market Stress Index justerar exponering automatiskt baserat på marknadens "väder".

### Regimes:

| Regime | GREEN+YELLOW | Stress | Max Exposure | Position Multiplier |
|--------|--------------|--------|--------------|---------------------|
| 🚀 **EUPHORIA** | >70% | <30 | 80% | 1.0x |
| ✅ **HEALTHY** | 50-70% | 30-50 | 60% | 1.0x |
| ⚠️ **CAUTIOUS** | 30-50% | 50-70 | 40% | 0.7x |
| 😰 **STRESSED** | 10-30% | 70-90 | 20% | 0.4x |
| 🚨 **CRISIS** | <10% | >90 | 10% | 0.2x |

### Användning:

```python
from src.risk import RegimeDetector

detector = RegimeDetector()

# Detect regime från signal distribution
signal_dist = {
    'GREEN': 1,
    'YELLOW': 13,
    'ORANGE': 0,
    'RED': 231
}

regime = detector.detect_regime(signal_dist)

print(f"Regime: {regime.regime}")
print(f"Stress Index: {regime.stress_index:.1f}/100")
print(f"RED %: {regime.red_pct:.1f}%")
print(f"Recommended Exposure: {regime.recommended_exposure:.0f}%")
print(f"Position Multiplier: {regime.position_size_multiplier}x")
```

### Output (Nuvarande Marknad):
```
Regime: CRISIS
Stress Index: 94.3/100
RED %: 94.3%
Recommended Exposure: 10%
Position Multiplier: 0.2x

Recommendation: KRIS - Nästan ingen exponering! Korrelation = 1
```

### Automatisk Positionsjustering:

```python
# Base positions från traffic light
base_positions = {
    'ZS': 5.0,  # GREEN signal
    'TXN': 3.0,  # YELLOW signal
    'META': 2.0  # YELLOW signal
}

# Justera för regime
adjusted = detector.adjust_positions_for_regime(
    base_positions=base_positions,
    regime=regime
)

# Med CRISIS regime (0.2x multiplier):
# adjusted = {'ZS': 1.0%, 'TXN': 0.6%, 'META': 0.4%}
```

### Trading Halt:

```python
should_halt, reason = detector.should_halt_trading(regime)

if should_halt:
    print(f"⛔ {reason}")
    # HALT TRADING - Stress index 94% (94% RED signals).
    # Correlation → 1, technical analysis unreliable.
```

---

## 4. 🔄 Integration - Allt Tillsammans

### Workflow:

```
1. Traffic Light Signal → Base allocation (3-5%, 1-3%, etc)
2. Trend Filter → Override if below 200 MA
3. V-Kelly → Adjust for volatility (ATR)
4. Regime Detection → Scale down in crisis
5. Final Position → Actual allocation
```

### Exempel:

**Scenario: Zscaler (ZS) med GREEN signal**

```python
# Step 1: Traffic Light
signal = "GREEN"
base_allocation = 4.0  # 3-5% range

# Step 2: Trend Filter
price_distance_from_200ma = +12.3%  # Above MA
trend_allow = True  # ✅ Allowed

# Step 3: V-Kelly
atr_percent = 2.8  # High volatility
vol_adjusted = 1.07%  # Reduced due to ATR

# Step 4: Regime Detection
market_regime = "CRISIS"
regime_multiplier = 0.2x
final_position = 1.07% * 0.2 = 0.21%

# Final Allocation
print(f"Base: 4.0% → Final: 0.21%")
print("Rationale:")
print("  - GREEN signal OK")
print("  - Above 200 MA ✅")
print("  - High vol → reduced to 1.07%")
print("  - CRISIS regime → scaled to 0.21%")
```

**Scenario: Apple (AAPL) med YELLOW signal, below 200 MA**

```python
# Step 1: Traffic Light
signal = "YELLOW"
base_allocation = 2.0  # 1-3% range

# Step 2: Trend Filter
price_distance_from_200ma = -5.2%  # Below MA
trend_allow = False  # ❌ BLOCKED

# Result: Position = 0%
print("Signal overridden to RED - below 200 MA")
print("Skipping V-Kelly and Regime steps")
print("Final: 0% (blocked by trend filter)")
```

---

## 📊 Complete Integration Example:

```python
from src.risk import (
    VolatilityPositionSizer,
    TrendFilter,
    RegimeDetector
)

# Initialize
vol_sizer = VolatilityPositionSizer(target_volatility=1.0)
trend_filter = TrendFilter(ma_period=200)
regime_detector = RegimeDetector()

# Market regime (do once for all instruments)
signal_dist = {'GREEN': 1, 'YELLOW': 13, 'RED': 231}
regime = regime_detector.detect_regime(signal_dist)

# For each instrument
def calculate_final_position(
    ticker, base_allocation, signal,
    prices, high, low, close
):
    # Step 1: Trend filter
    trend = trend_filter.analyze_trend(prices, signal)
    if not trend.allow_long:
        return 0.0, "Blocked by trend filter"
    
    # Step 2: Volatility adjustment
    atr_pct = vol_sizer.calculate_atr_percent(high, low, close)
    vol_pos = vol_sizer.adjust_position_size(base_allocation, atr_pct, signal)
    
    # Step 3: Regime adjustment
    regime_adjusted = vol_pos.volatility_adjusted * regime.position_size_multiplier
    
    return regime_adjusted, f"Trend✅ Vol:{atr_pct:.1f}% Regime:{regime.regime.value}"

# Usage
final_pos, rationale = calculate_final_position(
    'ZS', 4.0, 'GREEN',
    price_array, high_array, low_array, close_array
)

print(f"Final Position: {final_pos:.2f}%")
print(f"Rationale: {rationale}")
```

---

## 📈 Förväntade Resultat

### Före V2.1 (Scenario: CRISIS Market):
```
Zscaler GREEN: 4.0% allocation
→ Risk: 4.0% * 2.8% ATR = 0.112% portfolio risk
→ Total for 14 positions: ~1.5% portfolio risk
```

### Efter V2.1 (Scenario: CRISIS Market):
```
Zscaler GREEN: 0.21% allocation
→ Risk: 0.21% * 2.8% ATR = 0.006% portfolio risk
→ Total for 14 positions: ~0.08% portfolio risk
→ 95% reduction in risk during crisis!
```

### Key Benefits:
1. **Risk Parity**: Equal risk contribution across positions
2. **Trend Protection**: No catching falling knives
3. **Regime Adaptation**: Automatic exposure reduction in crisis
4. **Correlation Control**: Recognizes when diversification fails

---

## 🚀 Snabbstart V2.1

### Installation:
```bash
# Inget nytt att installera - alla moduler färdiga
```

### Basic Usage:
```python
from src.risk import (
    VolatilityPositionSizer,
    TrendFilter,
    RegimeDetector,
    format_regime_report
)

# Detect market regime
detector = RegimeDetector()
regime = detector.detect_regime(signal_distribution)
print(format_regime_report(regime))

# Check if halt needed
should_halt, reason = detector.should_halt_trading(regime)
if should_halt:
    print(f"⛔ {reason}")
    exit()

# Apply all filters
# (see Complete Integration Example above)
```

---

## 📚 Dokumentation

**Nya filer:**
- `src/risk/volatility_position_sizing.py` - V-Kelly implementation
- `src/risk/trend_filter.py` - 200-day MA filter
- `src/risk/regime_detection.py` - Market stress index
- `src/risk/__init__.py` - Module exports

**Guides:**
- `VERSION_2.1_FEATURES.md` - Denna fil
- `WHAT_APP_ANALYZES.md` - Uppdaterad med nya riskkontroller

---

## ⚠️ Viktiga Restriktioner

### 1. Data Requirements:
- **ATR**: Behöver high/low/close data (inte bara close)
- **200 MA**: Behöver minst 200 dagars historik
- **Regime**: Behöver signal distribution från screening

### 2. När Använda:
- ✅ **V-Kelly**: Alltid (standardiserar risk)
- ✅ **Trend Filter**: För aktier och ETF:er
- ⚠️ **Trend Filter**: Undvik för bonds (de följer inte trends)
- ✅ **Regime**: Alltid (portföljnivå)

### 3. Tuning:
```python
# Conservative (risk-averse)
vol_sizer = VolatilityPositionSizer(target_volatility=0.5)  # Lower risk
trend_filter = TrendFilter(allow_slight_below=False)  # Strict

# Aggressive (risk-seeking)
vol_sizer = VolatilityPositionSizer(target_volatility=1.5)  # Higher risk
trend_filter = TrendFilter(allow_slight_below=True)  # Lenient
```

---

## 🎯 Version Summary

**V2.0 → V2.1 Förbättringar:**

| Feature | V2.0 | V2.1 |
|---------|------|------|
| Position Sizing | Fixed % from signal | ATR-adjusted (Risk Parity) |
| Trend Awareness | None | 200-day MA filter |
| Regime Adaptation | Manual | Automatic stress index |
| Crisis Protection | None | 95% risk reduction |
| Catching Falling Knives | Possible | Prevented |
| Correlation Awareness | None | Entropy-based estimate |

**Status**: Production Ready 🚀  
**Datum**: 2026-01-04  
**Version**: 2.1 ADVANCED RISK CONTROLS
