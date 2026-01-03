# Quant Pattern Analyzer - Version 2.0
## Skalad, Dynamisk och Riskkontrollerad

---

## 📊 Översikt

Version 2.0 transformerar appen från ett enkelt analysverktyg till ett fullskaligt instrument-screening-system som kan analysera **111 Avanza-kompatibla instrument** simultant och ge dig konkreta investeringsrekommendationer baserade på statistisk analys och riskkontroll.

### 🎯 Huvudmål
- **Skala upp**: Från enskild analys till massanalys av hela portföljen
- **Dynamisk allokering**: Graderade position sizes (inte binärt ja/nej)
- **Riskkontroll**: Max 30-50% exponering i svaga marknader
- **Praktiskt**: Avanza-vänliga instrument, konkreta SEK-belopp

---

## ✅ Implementerade Funktioner

### 1. 4-Nivå Traffic Light System
**Stark förbättring från binärt RED/GREEN**

```
🟢 GREEN  (Stark positiv)    → 3-5% allokering per instrument
🟡 YELLOW (Måttlig positiv)  → 1-3% allokering per instrument  
🟠 ORANGE (Neutral/observant) → 0-1% allokering per instrument
🔴 RED    (Stark negativ)     → 0% allokering
```

**Logik:**
- GREEN: green_score ≥ 4 + handelsbara mönster + hög Bayesian certainty
- YELLOW: green_score ≥ 3 + handelsbara mönster
- ORANGE: green_score ≥ 2 ELLER blandade signaler
- RED: red_score ≥ 2 eller otillräckliga positiva signaler

### 2. Bayesian Edge-kvalitetsbedömning
**Säkerställer att edges är robusta**

Ny metod `_evaluate_edge_quality()` som utvärderar:
- `high_certainty`: True när stabilitet > 70% + ≥ 2 handelsbara mönster
- `avg_edge`: Genomsnittlig edge för handelsbara mönster
- `certainty_score`: Samlad säkerhetspoäng (0-1)

Detta används för att skilja på GREEN (hög certainty) vs YELLOW (viss osäkerhet).

### 3. Dynamisk Proportionell Allokering
**Praktiska riktlinjer istället för teoretisk Kelly**

**Exempel** - 100,000 SEK portfölj:
```
GREEN-instrument:  3,000-5,000 SEK per position (3-5%)
YELLOW-instrument: 1,000-3,000 SEK per position (1-3%)
ORANGE-instrument: 0-1,000 SEK per position (0-1%)
RED-instrument:    0 SEK (stå utanför)
```

**Max total exponering**: Automatisk beräkning säkerställer 30-50% max i svaga marknader.

### 4. Sektor/Kategori-analys med Outlier-detektion
**Identifierar okorrelerade möjligheter**

**12 kategorier:**
- index_global (5)
- index_regional (11)
- stock_swedish_large (19)
- stock_swedish_mid (5)
- stock_us_tech (15)
- stock_us_defensive (13)
- stock_us_finance (10)
- stock_us_industrial (8)
- stock_us_energy (4)
- stock_european (6)
- etf_broad (6)
- etf_sector (9)

**Outlier-detektion:**
När en sektor är >70% RED men ett instrument visar GREEN/YELLOW/ORANGE → flaggas som potentiell okorrelerad möjlighet.

### 5. Massivt Utökat Instrumentuniversum
**111 Avanza-kompatibla instrument**

**Fördelning:**
- **Index**: 16 globala och regionala index
- **Svenska aktier**: 24 storbolag + medelstora
- **Amerikanska aktier**: 50+ aktier över 6 sektorer
- **Europeiska aktier**: 6 (via ADRs)
- **ETF:er**: 15 breda + sektor-ETF:er

**Kvalitetskriterier:**
- ✅ Minst 5 års historik
- ✅ Snittvolym > 50,000/dag
- ✅ Handelsbart via Avanza
- ✅ Tillgänglig via Yahoo Finance

### 6. Dashboard-stil Visualisering
**GREEN-signaler först, bättre översikt**

**Ny layout:**
1. **Signalöversikt** - Snabb status på marknaden
2. **GREEN/YELLOW/ORANGE först** - Investeringsmöjligheter högst upp
3. **Sektor-gruppering** - Se hela sektorer på en gång
4. **Outlier-alert** - Okorrelerade möjligheter markerade
5. **Portföljrekommendation** - Konkret exponering och cash reserve

---

## 🚀 Användning

### Snabbstart

**Kör full analys** (111 instrument):
```bash
python instrument_screener.py
```

**Snabb test** (10 instrument):
```bash
python test_screener_v2.py
```

**Visa instrumentuniversum**:
```bash
python instruments_universe.py
```

### Exempel Output

```
================================================================================
📊 INSTRUMENT SCREENER - VERSION 2.0 (4-NIVÅ SYSTEM)
================================================================================

🚦 SIGNAÖVERSIKT:
  🟢 GREEN  (Stark positiv):     8 instrument
  🟡 YELLOW (Måttlig positiv):   15 instrument
  🟠 ORANGE (Neutral/bevaka):    22 instrument
  🔴 RED    (Stark negativ):     66 instrument

Analyserade: 111 instrument

--------------------------------------------------------------------------------
👉 INVESTERINGSMÖJLIGHETER (GREEN/YELLOW/ORANGE FÖRST)
--------------------------------------------------------------------------------

Rank  Instrument                     Signal     Edge     Score  Allokering
--------------------------------------------------------------------------------
1     Apple                          GREEN      +0.96%   58.2   3-5%
2     Microsoft                      YELLOW     +0.89%   51.5   1-3%
3     Nvidia                         YELLOW     +0.85%   49.8   1-3%
4     JPMorgan                       ORANGE     +0.45%   38.2   0-1%
...
```

### Tolka Resultaten

**SIGNAL** = Din handlingsvägledning
- 🟢 = Investera aktivt
- 🟡 = Var försiktig, små positioner
- 🟠 = Bevaka eller mikro-positioner
- 🔴 = Stå utanför

**SCORE** = Ranking (0-100)
- Kombinerar Traffic Light, Edge, Stabilitet, Patterns
- Högre = bättre kandidat när signal förbättras

**EDGE** = Statistisk fördel
- Informativt - visar historisk edge
- Signal avgör om du agerar på den

**ALLOKERING** = Konkret position size
- Baserad direkt på signal
- Exempel vid 100k portfölj visas i guide

---

## 📁 Filstruktur

```
quant-pattern-analyzer/
├── src/
│   ├── decision/
│   │   └── traffic_light.py          ⭐ 4-nivå system + Bayesian
│   └── ...
├── instrument_screener.py             ⭐ Huvudscreener (V2.0)
├── instruments_universe.py            ⭐ 111 instruments
├── test_screener_v2.py               ⭐ Snabb testning
├── VERSION_2.0_FEATURES.md           📄 Feature-dokumentation
├── README_V2.md                      📄 Denna fil
└── main.py                           Original single-instrument
```

---

## ⚙️ Teknisk Implementation

### Nya/Uppdaterade Komponenter

**TrafficLightEvaluator** (`src/decision/traffic_light.py`):
```python
# Nya metoder
_evaluate_edge_quality()      # Bayesian kvalitetsbedömning
_get_orange_reasoning()       # ORANGE-specifikt resonemang
_get_orange_action()          # ORANGE action guide

# Uppdaterade
evaluate()                    # 4-nivå logik
_build_result()              # Hanterar ORANGE
_get_requirements_for_change() # ORANGE transitions
```

**InstrumentScreener** (`instrument_screener.py`):
```python
# Uppdaterade metoder
_calculate_overall_score()    # ORANGE scoring
_analyze_instrument()         # 4-nivå allokering
_signal_to_text()            # Inkluderar ORANGE

# Nya funktioner
format_screener_report()      # Dashboard-stil
  ├── Signalöversikt först
  ├── GREEN-prioriterad sortering
  ├── Sektor-analys med outliers
  └── 4-nivå portföljrekommendation
```

**InstrumentUniverse** (`instruments_universe.py`):
```python
# Nya funktioner
get_all_instruments()         # Alla 111 instrument
get_instruments_by_category() # Filtrera per kategori
get_instrument_count()        # Antal instrument
get_category_counts()         # Fördelning per kategori
```

### Score-beräkning

```python
Overall Score (0-100) = 
    Traffic Light: 30 poäng (GREEN=30, YELLOW=20, ORANGE=10, RED=0)
  + Edge: 30 poäng (normaliserad mot 0.50% edge)
  + Stabilitet: 20 poäng
  + Tradeable patterns: 20 poäng
  + Kategori-bonus/malus: ±10%
```

---

## ⏳ Kommande Funktioner (Version 2.1)

### 1. Fundamentaldata Integration
**Status**: Ej implementerat

Planerad funktionalitet:
- Hämta P/E, P/B, utdelning, market cap från Yahoo Finance
- Integrera i scoring-algoritm
- Filter: P/E < 25, utdelning > 2%, etc.

### 2. Historisk Signal-tracking
**Status**: Ej implementerat

Planerad funktionalitet:
- Logga alla signals och outcomes
- Performance-tracking över tid
- Validering av edge-estimat
- "Hur bra var våra signaler?" rapport

---

## 🎯 Performance

**Test med 10 instrument**: ~45 sekunder  
**Test med 111 instrument**: ~8-10 minuter (beräknat)

**Minnesanvändning**: ~200-300 MB  
**CPU**: Single-threaded (kan paralleliseras i framtiden)

---

## 💡 Användningsexempel

### Scenario 1: Hitta Investeringsmöjligheter

```bash
python instrument_screener.py
```

**Resultat**:
- 8 GREEN-signaler → Investera 3-5% per instrument
- 15 YELLOW-signaler → Försiktig 1-3% per instrument
- 22 ORANGE-signaler → Bevaka eller mikro-positioner
- 66 RED-signaler → Stå utanför

**Action** med 100,000 SEK:
- Välj topp 5 GREEN → 4,000 SEK per instrument = 20,000 SEK
- Välj topp 5 YELLOW → 2,000 SEK per instrument = 10,000 SEK
- Total exponering: 30,000 SEK (30%)
- Cash reserve: 70,000 SEK (70%)

### Scenario 2: Sektor-analys

Scrollen ned till "SEKTOR/KATEGORI-ANALYS" för att se:
- Vilka sektorer är starka (många GREEN/YELLOW)
- Vilka sektorer är svaga (mest RED)
- Outliers: Enskilda möjligheter i svaga sektorer

### Scenario 3: Löpande Monitorering

Kör screener varje vecka för att:
- Se signal-förändringar
- Justera positioner baserat på nya signals
- Identifiera nya GREEN-möjligheter
- Exit RED-positioner

---

## 🔧 Konfiguration

### Anpassa Filterkriterier

I `instrument_screener.py`:
```python
screener = InstrumentScreener(
    min_data_years=5.0,      # Minst 5 års historik
    min_avg_volume=50000,    # Min snittvolym/dag
    max_beta=1.5             # Max volatilitet
)
```

### Lägg Till/Ta Bort Instrument

I `instruments_universe.py`, redigera listorna:
```python
SWEDISH_LARGE_CAP = [
    ("VOLV-B.ST", "Volvo B", "stock_swedish_large"),
    # Lägg till fler här...
]
```

---

## 📊 Statistik

### Version 2.0 Metrics
- ✅ 111 analyserbara instrument
- ✅ 12 distinkta kategorier
- ✅ 4-nivå signal-system
- ✅ Bayesian kvalitetskontroll
- ✅ Sektor-analys med outlier-detektion
- ✅ Dashboard-visualisering
- ⏳ Fundamentaldata (kommande)
- ⏳ Historisk tracking (kommande)

---

## 🚨 Viktiga Påminnelser

1. **Detta är inte investeringsrådgivning** - Statistiskt filter-verktyg
2. **Kombinera med egen due diligence** - Researcha företag innan investering
3. **Respektera din risktolerans** - Använd inte mer än du har råd att förlora
4. **Diversifiera** - Sprid över flera instrument och sektorer
5. **Max exponering** - Håll 30-50% i svaga marknader, max 70-80% i starka
6. **Rebalansera regelbundet** - Kör screener veckovis/månadsvis

---

## 📝 Changelog

### Version 2.0 (2026-01-03)
- ➕ 4-nivå Traffic Light (GREEN/YELLOW/ORANGE/RED)
- ➕ Bayesian edge-kvalitetsbedömning
- ➕ Dynamisk proportionell allokering (3-5%, 1-3%, 0-1%, 0%)
- ➕ Sektor/kategori-analys med outlier-detektion
- ➕ Utökat till 111 Avanza-kompatibla instrument
- ➕ Dashboard-stil visualisering
- 🔧 Förbättrad rapportering
- 🔧 Bättre signal-transitions

### Version 1.0 (2025-12-XX)
- ✅ Traffic Light beslutsstöd (3-nivå)
- ✅ Pattern-baserad analys
- ✅ Kelly criterion
- ✅ Bayesian osäkerhet
- ✅ Instrument screener (17 instrument)

---

## 📞 Support & Contribution

Detta är ett personligt kvantanalys-projekt. För frågor eller förbättringsförslag, se GitHub repository.

---

**Version**: 2.0  
**Datum**: 2026-01-03  
**Status**: Production Ready (Core Features)  
**Nästa Release**: 2.1 (Fundamentaldata + Historisk tracking)
