# ISK-Optimering för Quant Pattern Analyzer

**För svenska investerare med Investeringssparkonto (ISK)**

---

## Översikt

ISK-optimering hjälper dig minimera "dolda kostnader" som äter upp din teoretiska edge. Systemet består av tre huvudkomponenter som analyserar ISK-specifika kostnader:

### 1. FX-Växlingsvakt
Detekterar utländska aktier och beräknar valutaväxlingskostnader.

**Kostnad**: 0.5% (0.25% vid köp + 0.25% vid sälj)

**Varning**: Om din edge < 1.0% efter FX-växling flaggas transaktionen som marginell.

### 2. Tracking Error Filter
Rangordnar instrument efter innehavskostnad och produkthälsa.

**Product Health Score** (0-100):
- **100**: Fysiskt backade ETF:er (t.ex. WisdomTree Physical Gold)
- **95**: Svenska aktier
- **85**: Utländska aktier
- **60**: Open-end certifikat
- **40**: Bull/Bear utan hävstång
- **20**: Bull/Bear med hävstång (X2, X3, X5, X10)

**Urholkningsvarning**: Bull/Bear-produkter med daglig ombalansering varnas för innehavsperioder >3-4 dagar.

### 3. Courtage-trappan
Analyserar positionsstorlek mot Avanza courtagemodell.

**Courtageklasser**:
| Klass  | Procentsats | Min  | Max  |
|--------|-------------|------|------|
| START  | 0.25%       | 39kr | 99kr |
| MINI   | 0.19%       | 39kr | 89kr |
| SMALL  | 0.15%       | 39kr | 79kr |
| MEDIUM | 0.10%       | 39kr | 69kr |
| LARGE  | 0.07%       | 29kr | 49kr |

**Spärr**: Om courtaget >0.5% av positionen flaggas transaktionen som ineffektiv.

---

## Användning

### Grundläggande användning

```python
from src.risk.isk_optimizer import ISKOptimizer, CourtageTier

# Skapa optimizer med din courtageklass
optimizer = ISKOptimizer(
    courtage_tier=CourtageTier.MINI,  # Din Avanza-klass
    portfolio_size=100000,              # Total portföljstorlek i SEK
    min_edge_threshold=0.010             # Minsta acceptabla edge (1.0%)
)

# Analysera en transaktion
result = optimizer.optimize(
    ticker="ERO.TO",                    # Ticker-symbol
    expected_edge=0.008,                # Förväntad edge (0.8%)
    position_size_sek=5000,             # Positionsstorlek i SEK
    holding_period_days=5,              # Förväntad innehavstid
    product_name="Ero Copper Corp"      # Produktnamn (valfritt)
)

# Visa resultat
from src.risk.isk_optimizer import format_isk_report
print(format_isk_report(result))
```

### Integration med ExecutionGuard

ISK-optimering är automatiskt integrerad i ExecutionGuard:

```python
from src.risk.execution_guard import ExecutionGuard, CourtageTier

guard = ExecutionGuard(
    use_isk_optimizer=True,               # Aktivera ISK-optimering
    isk_courtage_tier=CourtageTier.MINI,  # Din courtageklass
    portfolio_value_sek=100000
)

result = guard.analyze(
    ticker="ERO.TO",
    category="stock",
    position_size_pct=5.0,
    net_edge_pct=0.8,
    product_name="Ero Copper Corp",
    holding_period_days=5
)

# ISK-analys finns i result.isk_analysis
if result.isk_analysis:
    print(f"Net edge efter ISK: {result.isk_analysis.net_edge_after_isk:.2%}")
    print(f"Rekommendation: {result.isk_analysis.recommendation}")
```

---

## Tre Vanliga ISK-Fällor

### 1. 🚫 FX-FÄLLAN

**Problem**: Köpa utländska aktier när edge < 1.0%

**Exempel**: ERO.TO (kanadensisk aktie)
- Edge före ISK: 0.8%
- FX-kostnad: 0.5%
- Courtage: 1.56%
- **Net edge: -1.26%** ❌

**Lösning**:
- Sök svenska alternativ
- Öka edge till >1.5% innan du handlar utländskt
- Vänta på bättre FX-läge om USD/SEK är dyr (>+2σ)

### 2. 🚫 COURTAGE-FÄLLAN

**Problem**: För små positioner där minimicourtage äter >0.5%

**Exempel**: 2000 SEK position (MINI-klass)
- Edge före ISK: 1.2%
- FX-kostnad: 0.5%
- Courtage: 39 SEK × 2 = 78 SEK (3.9%)
- **Net edge: -3.2%** ❌

**Lösning**:
- Öka position till minst 7800 SEK för MINI-klass
- Eller avstå från transaktionen

**Brytpunkter per courtageklass**:
- MINI (39 SEK min): 7800 SEK minimiposition
- SMALL (39 SEK min): 7800 SEK minimiposition
- MEDIUM (39 SEK min): 7800 SEK minimiposition
- LARGE (29 SEK min): 5800 SEK minimiposition

### 3. 🚫 URHOLKNINGSFÄLLAN

**Problem**: Bull/Bear-produkter med daglig ombalansering

**Exempel**: Bull Guld X2 (10 dagar innehavstid)
- Edge före ISK: 1.5%
- Innehavskostnad: 2.0%/år × (10/365) = 0.055%
- Courtage: 0.78%
- Urholkning i sidledes marknad: ~0.1-0.3%/dag
- **Net edge: 0.72%** 🟡

**Lösning**:
- Bull/Bear endast för korta trades (<3 dagar)
- Byt till fysiskt backade ETF:er för längre positioner
- Exempel: GZUR (WisdomTree Physical Gold) istället för Bull Guld X2

---

## Rekommendationer

### ✅ Bästa Praxis för ISK

1. **Prioritera svenska aktier**
   - Inga FX-kostnader
   - Product Health Score: 95/100
   - Exempel: NOVO-B.ST, ERIC-B.ST, VOLV-B.ST

2. **Rätt positionsstorlek**
   - MINI/SMALL/MEDIUM: ≥7800 SEK
   - LARGE: ≥5800 SEK
   - Courtage ska vara <0.5% av positionen

3. **Välj rätt produkttyp**
   - **Långsiktig (>1 vecka)**: Fysiskt backade ETF:er eller aktier
   - **Kortsiktig (<3 dagar)**: Bull/Bear acceptabelt
   - **Undvik**: Open-end certifikat med höga avgifter

4. **FX-medveten handel**
   - Kontrollera USD/SEK innan US-handel (FX Shield i ExecutionGuard)
   - Om USD >+2σ: vänta eller sök SEK-säkrat alternativ
   - Edge efter FX ska vara >1.0%

5. **Hållbar edge**
   - Net edge efter alla ISK-kostnader >1.0%
   - Annars är strategin inte hållbar långsiktigt

---

## Testscenarier

Kör `test_isk_optimizer.py` för att se alla tre ISK-fällorna i aktion:

```bash
python test_isk_optimizer.py
```

**Scenarion**:
1. ERO.TO (kanadensisk) → FX-fällan
2. Liten position (2000 SEK) → Courtage-fällan
3. Bull Guld X2 (10 dagar) → Urholkningsfällan
4. NOVO-B.ST (svensk) → Optimalt för ISK ✅

---

## Renaissance-Principer

ISK-optimering följer Renaissance Technologies principer:

> **"Varje baspunkt räknas. Döda dolda kostnader."**

- **Var brutal mot kostnader**: En edge på 0.8% är värdelös om 0.5% försvinner i FX-växling
- **Aggregera små fördelar**: ISK-optimering ger dig 3-4 extra "sparat" misstag per år
- **Ärlig osäkerhet**: Om edge efter ISK <1.0%, säg det rakt ut - trade inte

---

## Implementation Details

### Kostnadsberäkning

**Total ISK-kostnad**:
```
Total ISK Cost = FX-kostnad + Courtage (roundtrip) + Innehavskostnad

FX-kostnad = 0.5% (om utländsk)
Courtage = (39 SEK / position_size_sek) × 2
Innehavskostnad = (yearly_rate / 365) × holding_days
```

**Net Edge**:
```
Net Edge = Expected Edge - Total ISK Cost
```

### Produktklassificering

Baserad på ticker-suffix och produktnamn:

**Suffixer**:
- `.ST`, `.OL`, `.HE`, `.CO` → Svenska/Nordiska (ingen FX)
- `.TO`, `.V` → Kanadensiska (FX 0.5%)
- `.US`, ingen suffix → Amerikanska (FX 0.5%)
- `.L`, `.PA`, `.DE` → Europeiska (FX 0.5%)

**Produkttyper** (heuristik):
- Innehåller "Physical", "WisdomTree", "GZUR" → Fysiskt backad ETF
- Innehåller "Bull X2", "Bear X5" → Hävstångsprodukt
- Innehåller "Certifikat", "Mini", "Turbo" → Certifikat

---

## Framtida Förbättringar

1. **Databas för produkter**
   - Automatisk produktklassificering
   - Realtids-avgifter från Avanza API

2. **Dynamiska FX-kostnader**
   - Hämta aktuella FX-spreads
   - Optimera för bästa växlingstidpunkt

3. **Skattschablonberäkning**
   - Beräkna ISK-skatt (0.875% på kapitalbas)
   - Jämför ISK vs Aktie- och fondkonto

4. **Alternativrekommendationer**
   - Automatiskt föreslå svenska alternativ
   - Jämför flera produkter för samma underliggande

---

## Support

För frågor eller problem:
- Se `test_isk_optimizer.py` för exempel
- Läs `src/risk/isk_optimizer.py` för implementation
- Kolla `EXECUTION_COST_GUARD.md` för övergripande kostnadsstrategi

---

**Skapad**: 2026-01-06  
**Version**: 1.0  
**Författare**: Quant Pattern Analyzer Team
