# Instrument Universe 1200 - Komplett Guide

## Översikt
`instruments_universe_1200.py` är hjärtat i systemet - en databas med 1,189 handlingsbara instrument organiserade efter GICS-sektorer, geografi, och strategiska features.

---

## 1. Struktur & Organisation

### Huvudkomponenter
```python
# instruments_universe_1200.py innehåller:

GICS_SECTORS = {
    "Information Technology": [...],    # 110 tickers
    "Health Care": [...],                # 105 tickers
    "Financials": [...],                 # 107 tickers
    # ... 8 sektorer till
}

ALL_WEATHER_ETFs = {
    "Bonds - Treasury": [...],           # 10 ETFs
    "Gold & Precious Metals": [...],     # 10 ETFs
    # ... 6 kategorier till
}

MIFID_II_PROXY_MAP = {
    "TLT": "IS04.DE",                    # 22 mappningar
    "GLD": "SGLD.L",
    # ... US → EU UCITS alternativ
}

SECTOR_VOLATILITY_FACTORS = {
    "Utilities": 0.70,                   # Låg volatilitet
    "Information Technology": 1.25,      # Hög volatilitet
    # ... 11 sektorer
}
```

---

## 2. Geografisk Fördelning

### Ticker-suffix och FX-kostnader
```
.ST   → Sverige         (0.0% FX)  - 155 tickers
.OL   → Norge          (0.25% FX) -  36 tickers
.CO   → Danmark        (0.25% FX) -  37 tickers
.HE   → Finland        (0.25% FX) -  28 tickers
[USA] → USA            (0.5% FX)  - 856 tickers
.DE   → Tyskland       (0.5% FX)  -  20 tickers
.PA   → Frankrike      (0.5% FX)  -  23 tickers
.L    → Storbritannien (0.5% FX)  -  20 tickers
... och fler
```

### Exempel
```python
from instruments_universe_1200 import get_geography_for_ticker

get_geography_for_ticker("ERIC-B.ST")  # → "Sverige" (0% FX)
get_geography_for_ticker("AAPL")       # → "USA" (0.5% FX)
get_geography_for_ticker("NOVO-B.CO") # → "Danmark" (0.25% FX)
```

---

## 3. GICS Sektorbalans

### 11 Sektorer med ~100 tickers var

```
Information Technology     110 ├─ AAPL, MSFT, NVDA, ERIC-B.ST
Health Care               105 ├─ UNH, JNJ, AZN.ST
Financials                107 ├─ BRK.B, JPM, SEB-A.ST
Consumer Discretionary    110 ├─ AMZN, TSLA, HM-B.ST
Communication Services     99 ├─ NFLX, DIS, TELIA.ST
Industrials               110 ├─ BA, HON, ABB.ST
Consumer Staples           96 ├─ WMT, PG, CALM ←
Energy                    103 ├─ XOM, CVX
Utilities                  85 ├─ NEE, AWK, CEG
Real Estate               100 ├─ PLD, AMT
Materials                 100 ├─ LIN, APD
                         ─────
ALL-Weather ETFs           64 ├─ TLT, GLD, DBC
                         ─────
TOTAL                   1,189
```

### Varför balanserat?
- **Diversifiering**: Ingen sektor dominerar
- **All-Weather**: Funkar i bull/bear/sideways markets
- **Risk Management**: Sector Cap (40%) är meningsfullt

---

## 4. Sector Volatility Factors

### Koncept: Sharpe-liknande Justering

**Problem**: 10% EV i Utilities ≠ 10% EV i Energy
- Utilities: Låg risk, stabil
- Energy: Hög risk, volatil

**Lösning**: Normalisera mot volatilitet
```python
SECTOR_VOLATILITY_FACTORS = {
    "Utilities": 0.70,           # Defensiv → BOOST
    "Consumer Staples": 0.75,    # Defensiv → BOOST
    "Health Care": 1.00,         # Neutral
    "Industrials": 1.00,         # Neutral
    "Information Technology": 1.25,  # Volatil → PENALTY
    "Energy": 1.35,              # Mycket volatil → PENALTY
}

# Justering i Sunday Dashboard:
adjusted_ev = expected_value / sector_volatility
# NEE (Utilities): 10% / 0.70 = 14.3% (risk-adjusted)
# NVDA (Tech): 10% / 1.25 = 8.0% (risk-adjusted)
```

### Exempel med CALM
```python
# CALM = Consumer Staples (0.75x)
raw_ev = 6.02%
adjusted_ev = 6.02% / 0.75 = 8.03%

# Detta ger CALM högre score än tech-aktie med samma raw EV
# EFTERSOM Staples har lägre risk
```

---

## 5. MiFID II Proxy Mapping

### Problem: US ETFs ej köpbara på Avanza ISK

**Regler:**
- MiFID II/UCITS: US-domiciled ETFs blockerade i EU
- Avanza ISK: Endast EU UCITS ETFs

**Lösning: Automatisk Proxy-Mapping**
```python
MIFID_II_PROXY_MAP = {
    # Treasury Bonds
    "TLT": "IS04.DE",     # iShares $ Treasury 20+yr
    "IEF": "IBTE.DE",     # iShares $ Treasury 7-10yr
    
    # Gold
    "GLD": "SGLD.L",      # Invesco Physical Gold
    "IAU": "IGLN.L",      # iShares Physical Gold
    
    # Commodities
    "DBC": "EXXT.DE",     # iShares Diversified Commodity
    "USO": "CRUD.L",      # WisdomTree Crude Oil
    
    # Broad Market
    "VT": "VWRL.L",       # Vanguard All-World
    "ACWI": "ISAC.L",     # iShares MSCI ACWI
}

# Usage i Sunday Dashboard:
if ticker in MIFID_II_PROXY_MAP:
    tradeable = get_mifid_ii_proxy(ticker)
    print(f"⚠️ Cannot trade {ticker}. Use {tradeable} instead.")
```

### Praktiskt Exempel
```
Sunday Dashboard hittar: TLT (US Treasury Bond 20+ år)
Score: 85/100
Pattern: Double Bottom

MiFID II Check: ⚠️ TLT not tradeable on Avanza ISK
Recommendation: Trade IS04.DE instead
  → Same underlying asset
  → EU UCITS compliant
  → 0.5% FX cost still applies
```

---

## 6. FX Guard - USD/SEK Mean Reversion

### Koncept: Valuta-timing

**Hypotes**: USD/SEK mean-reverts mot 200-dagars medel
- När USD är dyr (Z > +2.0) → Likely to weaken → Undvik US
- När USD är billig (Z < -1.5) → Likely to strengthen → Favorisera US

### Beräkning
```python
# Hämta USD/SEK data
import yfinance as yf
usdsek = yf.Ticker("USDSEK=X")
hist = usdsek.history(period="1y")

# Beräkna Z-score
current_rate = 9.0024
mean_200d = 9.4792
std_200d = 0.1622

zscore = (current_rate - mean_200d) / std_200d
# = (9.0024 - 9.4792) / 0.1622
# = -2.94

# FX Adjustment
if zscore > 2.0:
    adjustment = 0.85  # -15% (dyr USD)
elif zscore > 1.5:
    adjustment = 0.90  # -10%
elif zscore < -1.5:
    adjustment = 1.05  # +5% (billig USD) ← IDAG
else:
    adjustment = 1.0   # No change
```

### Impact på CALM
```
CALM (US stock)
Raw Score: 82.0
× Sector (Consumer Staples 0.75x, capped 1.20): 98.4
× FX (USD cheap, Z=-2.94): ×1.05 = 103.3
→ Capped at 100.0

Result: CALM får +5% boost pga billig USD
```

---

## 7. Hur det Används i Sunday Dashboard

### Flow
```
1. LOAD INSTRUMENTS
   ├─ get_all_tickers() → 1,189 tickers
   └─ Remove duplicates

2. SCAN EACH TICKER
   ├─ Fetch data (Yahoo Finance)
   ├─ Detect patterns
   ├─ Calculate edge/RRR/EV
   └─ Filter: EV>0, RRR≥3.0, Win Rate≥60%

3. POST-PROCESSING (för varje setup)
   ├─ Sector & Geography Lookup
   │  ├─ get_sector_for_ticker(ticker)
   │  ├─ get_geography_for_ticker(ticker)
   │  └─ get_sector_volatility_factor(sector)
   │
   ├─ MiFID II Check
   │  └─ if ticker in MIFID_II_PROXY_MAP:
   │      setup.mifid_proxy = get_mifid_ii_proxy(ticker)
   │
   ├─ STRATEGIC ADJUSTMENTS
   │  ├─ Sector Volatility: score × (EV / vol_factor), capped ±20%
   │  └─ FX Guard (US only): score × fx_adjustment (85%-105%)
   │
   └─ Cap at 100 points

4. SORT BY ADJUSTED SCORE
   └─ Top 5 → Recommended trades
```

### Kod från Sunday Dashboard
```python
# sunday_dashboard.py lines 540-560

for setup in setups:
    # 1. Lookup
    setup.sector = get_sector_for_ticker(setup.ticker)
    setup.geography = get_geography_for_ticker(setup.ticker)
    setup.sector_volatility = get_sector_volatility_factor(setup.sector)
    
    # 2. MiFID II
    if setup.ticker in MIFID_II_PROXY_MAP:
        setup.mifid_proxy = get_mifid_ii_proxy(setup.ticker)
        setup.mifid_warning = f"Use {setup.mifid_proxy} instead"
    
    # 3. Strategic Adjustments
    vol_adjustment = min(1.20, max(0.80, 1.0 / setup.sector_volatility))
    setup.score *= vol_adjustment
    
    if setup.geography == "USA":
        setup.score *= fx_adjustment  # 1.05 idag
    
    # 4. Cap
    if setup.score > 100:
        setup.score = 100.0
```

---

## 8. Praktiskt Exempel: CALM Trade

### Step-by-Step

**1. CALM hittas i sektordictionaryn**
```python
GICS_SECTORS["Consumer Staples"] = [
    ...,
    "CALM",  # ← Cal-Maine Foods
    ...
]
```

**2. Lookup-funktioner körs**
```python
get_sector_for_ticker("CALM")
# → "Consumer Staples"

get_geography_for_ticker("CALM")
# → "USA" (no suffix = USA)

get_sector_volatility_factor("Consumer Staples")
# → 0.75
```

**3. MiFID II Check**
```python
if "CALM" in MIFID_II_PROXY_MAP:  # False
    # CALM är aktie, inte ETF → ingen proxy behövs
    setup.mifid_proxy = None
```

**4. Strategic Adjustments**
```python
# Raw metrics från backtesting
raw_score = 82.0
expected_value = 0.0602  # 6.02%

# Sector Volatility
vol_factor = 0.75
vol_adjusted_ev = 0.0602 / 0.75 = 0.0803  # 8.03%
vol_adjustment = 0.0803 / 0.0602 = 1.33
# Capped to 1.20 (max +20%)
score_after_sector = 82.0 × 1.20 = 98.4

# FX Guard (USD cheap, Z=-2.94)
fx_adjustment = 1.05
score_after_fx = 98.4 × 1.05 = 103.3

# Final cap
final_score = min(103.3, 100.0) = 100.0
```

**5. Result**
```
CALM #1
Score: 100.0/100 (capped from 103.3)
Sector: Consumer Staples (Vol: 0.75x) → +20% boost
Geography: USA → +5% FX boost
Net EV: +5.27% (after 0.75% costs)
```

---

## 9. System Health Check

### Automatisk Validering
```bash
python instruments_universe_1200.py
```

**Output:**
```
SYSTEM HEALTH CHECK - 1200 TICKER UNIVERSE
================================================================================

✅ Total instruments: 1189

GEOGRAPHIC BREAKDOWN:
USA                   856 tickers (FX: 0.5%)
Sverige               155 tickers (FX: 0.0%)
...

SECTOR BREAKDOWN:
Information Technology                    110 tickers
Health Care                               105 tickers
...

DUPLICATE CHECK:
✅ No duplicates found

GHOST TICKER CHECK:
✅ No ghost tickers found (ICA.ST, SWMA.ST removed)

STRATEGIC FEATURES TEST:
  MiFID II: TLT → IS04.DE ✅
  FX Guard: Z=-2.94 → 105.0% ✅
  Sector Vol: Utilities 0.70x ✅
```

---

## 10. Underhåll & Updates

### När uppdatera?

**Quarterly (var 3:e månad):**
- Kontrollera delisted tickers (404 errors i scan)
- Lägg till nya IPOs från samma sektorer
- Balansera om sektor-distribution

**Yearly (årligen):**
- Review sector volatility factors mot faktisk data
- Uppdatera MiFID II proxy mappings (nya UCITS ETFs)
- Justerar FX Guard parameters om USD/SEK range ändras

### Hur lägga till ny ticker?

**1. Identifiera sektor**
```python
# Exempel: Lägga till PLTR (Palantir)
# Sektor: Information Technology
```

**2. Lägg till i rätt lista**
```python
GICS_SECTORS["Information Technology"] = [
    ...,
    "PLTR",  # ← Lägg till här
    ...
]
```

**3. Kör health check**
```bash
python instruments_universe_1200.py
# Verifiera: ingen duplicates, rätt count
```

**4. Testa lookup**
```python
from instruments_universe_1200 import *
get_sector_for_ticker("PLTR")  # → "Information Technology"
get_geography_for_ticker("PLTR")  # → "USA"
```

---

## 11. Key Files & Integration

### File Structure
```
quant-pattern-analyzer/
├── instruments_universe_1200.py      # ← MASTER DATABASE
├── sunday_dashboard.py               # Uses universe for scanning
├── test_strategic_features.py        # Validates all features
└── STRATEGIC_FEATURES.md             # Full documentation
```

### Import i andra filer
```python
# sunday_dashboard.py
from instruments_universe_1200 import (
    get_all_tickers,              # För scanning
    get_sector_for_ticker,        # Sector lookup
    get_geography_for_ticker,     # Geography lookup
    get_mifid_ii_proxy,          # MiFID II mapping
    get_sector_volatility_factor, # Volatility adjustment
    calculate_usd_sek_zscore,    # FX Guard
    get_fx_adjustment_factor,    # FX adjustment
    MIFID_II_PROXY_MAP          # Direct access
)
```

---

## 12. FAQ

### Q: Varför 1,189 tickers istället för exakt 1,200?
**A:** Efter rensning av ghost tickers (ICA.ST, SWMA.ST, etc.) och duplicates blev det 1,189. Vi prioriterar kvalitet över kvantitet.

### Q: Kan jag lägga till mina egna tickers?
**A:** Ja! Lägg till i rätt GICS-sektor, kör health check, klart.

### Q: Varför caps sector adjustment till ±20%?
**A:** För att undvika extrema scores (som 112/100). Adjustments är för relativ ranking, inte absolut kvalitet.

### Q: Vad händer om Yahoo Finance ändrar ticker-format?
**A:** Sunday Dashboard loggar 404-errors. Fix tickers i universe, kör om.

### Q: Kan jag använda detta system för day trading?
**A:** NEJ. Systemet är optimerat för position trading (21-63 dagar). Volatility factors och patterns gäller inte för dagshandel.

---

## 13. Summary Flow Diagram

```
USER RUNS: python sunday_dashboard.py
                    │
                    ├─ Load 1,189 tickers from instruments_universe_1200.py
                    │
                    ├─ Scan each ticker (6-7 hours)
                    │  ├─ Fetch data (Yahoo Finance)
                    │  ├─ Detect patterns
                    │  └─ Calculate metrics
                    │
                    ├─ Filter: EV>0, RRR≥3.0, Win Rate≥60%
                    │  → ~20 POTENTIAL setups
                    │
                    ├─ POST-PROCESSING (for each setup)
                    │  ├─ Sector/Geography lookup
                    │  ├─ MiFID II check
                    │  ├─ Sector volatility adjustment (±20%)
                    │  ├─ FX Guard adjustment (85%-105%)
                    │  └─ Cap at 100 points
                    │
                    └─ OUTPUT: Top 5 setups ranked by adjusted score
                       ├─ #1 CALM: 100.0/100 (Consumer Staples, USA, capped)
                       ├─ #2 AWK: 94.2/100 (Utilities, USA)
                       ├─ #3 CEG: 90.8/100 (Utilities, USA)
                       ├─ #4 TREX: 83.1/100 (Industrials, USA)
                       └─ #5 KBH: 79.0/100 (Industrials, USA)
```

---

**SLUTSATS**: `instruments_universe_1200.py` är inte bara en lista med tickers - det är en intelligent databas som ger systemet:
1. **Diversifiering** (11 GICS-sektorer balanserade)
2. **Geo-balans** (Sverige 0% FX → USA 0.5% FX)
3. **Risk-adjusted scoring** (Sector volatility normalization)
4. **MiFID II compliance** (Auto proxy för US ETFs)
5. **FX-timing** (USD/SEK mean reversion)

Detta är grunden för V4.0 Position Trading System! 🎯
