# 🛡️ EXECUTION COST GUARD - Minimera Dolda Kostnader

## Filosofi
**"Don't let execution costs eat your edge"**

Professional traders vet: Det räcker inte att hitta edge - du måste behålla den efter exekvering.

Hidden costs (dolda kostnader) kan äta upp din teoretiska edge:
- 🔄 **Slippage** - Priset rör sig medan du köper
- 💱 **FX Risk** - Valutaförlust vid USD-toppen
- 💰 **Courtage** - Minimiavgifter äter små positioner
- 📊 **Spread** - Bid-ask skillnad

## Features

### 1. 🛡️ FX Shield (Valuta-Risk)
**Problem:** Du köper en US-aktie när USD/SEK är vid toppen → vinsten äts av valutaförlust.

**Lösning:** 
- Hämtar USD/SEK data från Yahoo Finance
- Beräknar 20-dagars SMA och standardavvikelse
- Varnar om USD är >+2σ (övervärderad)

**Exempel:**
```
FX Risk: ⚠️ USD DYR (+2.3σ) - överväg SEK-säkrat alternativ
```

**Lägen:**
- **>+3σ:** 🚨 EXTREME - vänta på bättre FX-läge!
- **>+2σ:** ⚠️ HIGH - överväg SEK-säkrat alternativ
- **>+1σ:** MEDIUM - FX-risk finns
- **<-2σ:** ✅ LOW - bra FX-läge! (USD billig)
- **Normal:** USD neutral

### 2. 💰 Avanza Fee Calculator
**Problem:** Små positioner äts av minimicourtage (39 SEK för Avanza Small).

**Lösning:**
- Beräknar courtage baserat på kontotyp
- Beräknar spread-kostnad per instrumenttyp
- Jämför total kostnad mot net edge
- Varnar om kostnader >30% av edge

**Account Types:**
| Account Type | Courtage | Min Courtage |
|--------------|----------|--------------|
| START        | 0.25%    | 1 SEK        |
| SMALL        | 0.15%    | 39 SEK       |
| MEDIUM       | 0.10%    | 69 SEK       |

**Spread Estimates:**
| Instrument Type    | Spread |
|-------------------|--------|
| Large Cap US      | 0.05%  |
| Small Cap US      | 0.15%  |
| Swedish Stocks    | 0.10%  |
| Liquid ETFs       | 0.05%  |
| Sector ETFs       | 0.10%  |
| Commodity ETFs    | 0.20%  |
| Inverse ETFs      | 0.25%  |

**Exempel:**
```python
Position: 2,500 SEK (2.5%)
Net Edge: +1.5%

Courtage: 39 SEK (3.12%)
Spread: 0.15%
Total Cost (round-trip): 3.42%

Cost/Edge Ratio: 228% 🚨
→ Kostnader äter hela edgen!
```

### 3. 📊 Liquidity & Spread Guard
**Problem:** Du köper en illiquid aktie → slippage äter vinsten.

**Lösning:**
- Hämtar genomsnittlig daglig volym (1 månad)
- Beräknar din position som % av volymen
- Varnar om position >2% av volymen
- Uppskattar slippage

**Slippage Estimates:**
| Position vs Volume | Slippage | Risk        |
|-------------------|----------|-------------|
| >5%               | 1.0%     | 🚨 EXTREME  |
| 2-5%              | 0.5%     | ⚠️ HIGH     |
| 1-2%              | 0.2%     | MEDIUM      |
| <1%               | 0.05%    | ✅ LOW      |

### 4. 🎯 Avanza Product Mapper
**Problem:** Du köper fel produkt-typ → onödiga avgifter.

**Lösning:**
- Rekommenderar mest effektiva produkten
- Varnar för inverse/leveraged ETFs (daily reset)
- Prioriterar XACT/iShares framför dyra certifikat

**Exempel:**
```
✅ US stocks with good FX: Köp direkt
⚠️ US stocks with high FX: Överväg SEK-säkrat certifikat
⚠️ Inverse ETFs: Daily reset - endast kortsiktig hedging!
💡 Commodities: XACT eller iShares ETF (lägre avgifter)
🟢 Swedish stocks: Inga FX-risker
```

## Integration

### I Dashboard (Automatiskt)
Execution Guard körs automatiskt för varje köpsignal:

```
1. AAPL (Apple Inc.)
   Signal: GREEN
   Net Edge: +1.5%
   Position: 2.5%
   
   🛡️ EXECUTION GUARD: 🔴 HIGH
      • 🚨 HÖGA KOSTNADER: 3.42% äter 228% av edgen!
      • Total kostnad: 3.47%
      • Rekommendation: Överväg större position eller vänta
```

### Manuell Användning
```python
from src.risk.execution_guard import ExecutionGuard, AvanzaAccountType

# Initialize
guard = ExecutionGuard(
    account_type=AvanzaAccountType.SMALL,
    portfolio_value_sek=100000
)

# Analyze
result = guard.analyze(
    ticker="NVDA",
    category="stock_us_tech",
    position_size_pct=2.5,
    net_edge_pct=1.5
)

# Check warnings
if result.execution_risk_level in ["HIGH", "EXTREME"]:
    print("⚠️ WARNING:")
    for warning in result.warnings:
        print(f"  - {warning}")
```

## Configuration

### Justera för Din Portfolio
I `dashboard.py`, ändra:

```python
execution_guard = ExecutionGuard(
    account_type=AvanzaAccountType.SMALL,  # START/SMALL/MEDIUM
    portfolio_value_sek=100000  # Din portfolio-storlek
)
```

### Account Types
- **START:** Nybörjare, 0.25% courtage (min 1 SEK)
- **SMALL:** Standard, 0.15% courtage (min 39 SEK)
- **MEDIUM:** Större konto, 0.10% courtage (min 69 SEK)

## How It Works

### Complete Analysis Flow
```
Input:
  - Ticker (NVDA)
  - Category (stock_us_tech)
  - Position Size (2.5%)
  - Net Edge (1.5%)

Analysis:
  1. FX Risk Analysis
     ├─ Fetch USD/SEK data
     ├─ Calculate 20-day SMA + σ
     └─ Determine sigma level

  2. Fee Analysis
     ├─ Calculate courtage (account type)
     ├─ Estimate spread (instrument type)
     ├─ Total cost (round-trip)
     └─ Cost/Edge ratio

  3. Liquidity Analysis
     ├─ Fetch average volume
     ├─ Calculate position vs volume
     └─ Estimate slippage

  4. Aggregate Results
     ├─ Collect warnings
     ├─ Determine execution risk level
     └─ Generate Avanza recommendation

Output:
  - ExecutionGuardResult
    ├─ FX Risk (σ level, message)
    ├─ Fee Analysis (cost %, ratio)
    ├─ Liquidity (slippage %, message)
    ├─ Total Execution Cost %
    ├─ Execution Risk Level (LOW/MEDIUM/HIGH/EXTREME)
    ├─ Warnings []
    └─ Avanza Recommendation
```

## Risk Levels

### LOW (🟢)
- USD neutral
- Kostnader <15% av edge
- God likviditet
- **Action:** Köp med förtroende

### MEDIUM (🟡)
- USD något dyr ELLER
- Kostnader 15-30% av edge ELLER
- Måttlig likviditet
- **Action:** Granska innan köp

### HIGH (🔴)
- USD dyr (+2σ) ELLER
- Kostnader 30-50% av edge ELLER
- Låg likviditet (>2% volym)
- **Action:** Överväg alternativ

### EXTREME (🚨)
- USD extremt dyr (+3σ) OCH/ELLER
- Kostnader >50% av edge OCH/ELLER
- Mycket låg likviditet (>5% volym)
- **Action:** VÄNTA

## Examples

### Exempel 1: Good Execution (LOW Risk)
```
Ticker: AAPL
Position: 5.0% (5,000 SEK)
Net Edge: +2.5%

FX Risk: USD neutral (-0.2σ)
Fees: ✅ Låga kostnader: 0.51% (20% av edge)
Liquidity: ✅ God likviditet (0.01% av volym)

Total Execution Cost: 0.56%
Execution Risk: LOW

✅ Köp med förtroende!
```

### Exempel 2: FX Risk (HIGH)
```
Ticker: NVDA
Position: 3.0%
Net Edge: +1.8%

FX Risk: ⚠️ USD DYR (+2.3σ) - överväg SEK-säkrat alternativ
Fees: Kostnader OK: 1.2% (67% av edge)
Liquidity: ✅ God likviditet

Total Execution Cost: 2.45% (inkl FX premium)
Execution Risk: HIGH

⚠️ Vänta på bättre FX-läge eller köp SEK-säkrat certifikat
```

### Exempel 3: Fee Problem (HIGH)
```
Ticker: XLU
Position: 1.5% (1,500 SEK)
Net Edge: +0.8%

FX Risk: USD neutral
Fees: 🚨 HÖGA KOSTNADER: 5.2% äter 650% av edgen!
Liquidity: ✅ God likviditet

Total Execution Cost: 5.25%
Execution Risk: HIGH

🚨 För liten position - courtage äter edgen!
→ Öka position till minst 3% eller skippa
```

### Exempel 4: Liquidity Problem (HIGH)
```
Ticker: VIXY (Volatility ETF)
Position: 2.0%
Net Edge: +3.5%

FX Risk: USD neutral
Fees: Kostnader OK: 0.6%
Liquidity: ⚠️ LÅG LIKVIDITET: Position är 3.2% av volymen

Total Execution Cost: 1.6% (inkl slippage 0.5%)
Execution Risk: HIGH

⚠️ Illiquid instrument - risk för slippage
→ Dela upp order eller minska storlek
```

## Files

- `src/risk/execution_guard.py` - Main module
- `dashboard.py` - Dashboard integration
- `EXECUTION_COST_GUARD.md` - This documentation

## Testing

```bash
# Test module directly
python src/risk/execution_guard.py

# Test in dashboard
python daglig_analys.py
```

## Best Practices

### 1. Small Positions
**Problem:** Minimicourtage äter små positioner.

**Solutions:**
- Öka position size till minst 3-5%
- Skippa signalen om edge är för liten
- Använd ISK-konto (lägre courtage)

### 2. USD Topping
**Problem:** Köper US-aktier vid USD-toppen.

**Solutions:**
- Vänta tills USD/SEK normaliseras
- Köp SEK-säkrat certifikat
- Fokusera på svenska alternativ

### 3. Illiquid Instruments
**Problem:** Stora positioner i illiquida aktier.

**Solutions:**
- Dela upp order över flera dagar
- Använd limit orders
- Minska position size
- Skippa illiquida instruments

### 4. Inverse ETFs
**Problem:** Daily reset äter värde över tid.

**Solutions:**
- Endast för kortsiktig hedging (<1 vecka)
- Stäng position snabbt
- Använd ej för långsiktig short

## Future Enhancements

- [ ] Real-time spread data (istället för estimates)
- [ ] Intraday volatility (bästa tid att köpa)
- [ ] Order splitting recommendations
- [ ] Tax efficiency (ISK vs AF)
- [ ] Multiple currency pairs (EUR/SEK)
- [ ] Historical slippage tracking

## Summary

Execution Guard är din "cost watchdog":
- 🛡️ **FX Shield:** Varna för USD-toppen
- 💰 **Fee Calculator:** Minimera courtage-förluster
- 📊 **Liquidity Guard:** Undvik slippage
- 🎯 **Product Mapper:** Välj rätt produkt

**Result:** Mer av din teoretiska edge landar faktiskt på kontot! 💰
