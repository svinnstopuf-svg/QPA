# Reporting Guide - Veckorapporter & Kvartalsrevisioner

## 📊 Översikt

Version 2.0 inkluderar två kraftfulla rapporteringsmoduler:

1. **Veckorapport** (Delta-analys) - Veckovis jämförelser
2. **Kvartalsrevision** (Pattern audit) - Kvartalsvis systemvalidering

---

## 📅 Veckorapport - Delta-Analys

### Vad Den Gör:

Jämför marknadens temperatur **vecka för vecka**:
- Signal distribution changes (RED/YELLOW/GREEN skiften)
- Confidence changes per instrument
- Nya möjligheter (RED → YELLOW/GREEN transitions)
- Market temperature trends

### Användning:

#### Automatisk från Screener:

```python
from instrument_screener import InstrumentScreener
from instruments_universe import get_all_instruments
from src.reporting import generate_weekly_report

# Kör screening
screener = InstrumentScreener()
instruments = get_all_instruments()
results = screener.screen_instruments(instruments)

# Generera veckorapport
weekly_report = generate_weekly_report(results)
print(weekly_report)

# Spara till fil (valfritt)
with open('weekly_report.txt', 'w', encoding='utf-8') as f:
    f.write(weekly_report)
```

#### Manuell med Specifik Vecka:

```python
from datetime import datetime
from src.reporting import generate_weekly_report

# Specificera veckostart (måndag)
week_start = datetime(2026, 1, 6)  # Monday Jan 6, 2026

report = generate_weekly_report(
    current_results=screening_results,
    current_week=week_start
)
print(report)
```

### Output Exempel:

```
================================================================================
VECKORAPPORT - DELTA-ANALYS
================================================================================
Period: 2026-01-06 till 2026-01-12
Genererad: 2026-01-12 15:30

--------------------------------------------------------------------------------
NUVARANDE MARKNADSSTATUS
--------------------------------------------------------------------------------
Total instrument analyserade: 245
Marknadstemperatur: COLD

Signalfördelning:
  🟢 GREEN  :   1 (  0.4%)
  🟡 YELLOW :  13 (  5.3%)
  🟠 ORANGE :   0 (  0.0%)
  🔴 RED    : 231 ( 94.3%)

Genomsnittlig edge: -0.0234%
Genomsnittlig konfidens: 42.1%

================================================================================
DELTA-ANALYS (Förra veckan → Denna vecka)
================================================================================

🌡️  Temperaturtrend: VÄRMANDE (Förbättring)

--------------------------------------------------------------------------------
SIGNALFÖRDELNING - FÖRÄNDRINGAR
--------------------------------------------------------------------------------
🟢 GREEN  :   0.0% →   0.4% (+0.4%) 📈
🟡 YELLOW :   4.1% →   5.3% (+1.2%) 📈
🟠 ORANGE :   0.0% →   0.0% (+0.0%) ➡️
🔴 RED    :  95.9% →  94.3% (-1.6%) 📉

Edge-förändring: +0.0123% 📈
Konfidens-förändring: +3.2% 📈

--------------------------------------------------------------------------------
NYA MÖJLIGHETER (RED → YELLOW/GREEN): 3 st
--------------------------------------------------------------------------------
  ✨ Zscaler (ZS): RED → GREEN
     Score: +24.7 | Edge: +1.56% | Beslut: ÖKA POSITION

  ✨ Texas Instruments (TXN): RED → YELLOW
     Score: +18.1 | Edge: +2.64% | Beslut: NY MÖJLIGHET

  ✨ Kinder Morgan (KMI): RED → YELLOW
     Score: +13.8 | Edge: +0.80% | Beslut: NY MÖJLIGHET

--------------------------------------------------------------------------------
STÖRSTA KONFIDENSSKIFTEN
--------------------------------------------------------------------------------
  📈 Zscaler (ZS): Konfidens +22.0%
     Signal: RED → GREEN | Beslut: ÖKA POSITION

  📈 Meta (META): Konfidens +8.5%
     Signal: YELLOW → YELLOW | Beslut: BEHÅLL/ÖKA

  📉 Apple (AAPL): Konfidens -12.3%
     Signal: YELLOW → RED | Beslut: MINSKA/STÄNG

================================================================================
```

### Lagring:

Snapshots sparas automatiskt i `weekly_snapshots/`:
```
weekly_snapshots/
├── snapshot_2025_12_30.json
├── snapshot_2026_01_06.json
└── snapshot_2026_01_13.json
```

---

## 🔍 Kvartalsrevision - Pattern Audit

### Vad Den Gör:

För systemarkitekten att köra **var 3:e månad**:
- Identifierar mest lönsamma mönster i realtid
- Detekterar degradation och försämrade patterns
- Validerar Bayesian predictions mot actual outcomes
- Rekommenderar åtgärder (KEEP, ADJUST, MONITOR, REMOVE)

### Användning:

#### Grundläggande:

```python
from src.reporting import generate_quarterly_audit

# Generera kvartal audit (senaste 3 månader)
audit_report = generate_quarterly_audit()
print(audit_report)

# Spara till fil
with open('quarterly_audit.txt', 'w', encoding='utf-8') as f:
    f.write(audit_report)
```

#### Med Specifik Period:

```python
from datetime import datetime
from src.reporting import generate_quarterly_audit

# Specifikt kvartal
quarter_end = datetime(2026, 3, 31)  # Q1 2026

report = generate_quarterly_audit(
    quarter_end=quarter_end,
    lookback_quarters=1  # Analysera 1 kvartal (3 månader)
)
print(report)
```

#### Analysera Flera Kvartal:

```python
# Analysera senaste 6 månaderna (2 kvartal)
report = generate_quarterly_audit(lookback_quarters=2)
print(report)
```

### Output Exempel:

```
================================================================================
KVARTALSREVISION - PATTERN PERFORMANCE & DEGRADATION
================================================================================
Period: 2025-10-01 till 2026-01-01
Genererad: 2026-01-04 14:30
Analyserade patterns: 8

--------------------------------------------------------------------------------
SAMMANFATTNING
--------------------------------------------------------------------------------
Genomsnittlig edge (actual): +0.087%
Genomsnittlig prediction accuracy: 62.3%
Genomsnittlig win rate: 58.7%
Genomsnittlig Sharpe ratio: 0.42
Genomsnittlig degradation rate: -8.3% per kvartal

Rekommendationsfördelning:
  ✅ KEEP: 3 patterns
  🔧 ADJUST: 2 patterns
  👁️ MONITOR: 2 patterns
  ❌ REMOVE: 1 patterns

--------------------------------------------------------------------------------
🏆 TOP 5 MEST LÖNSAMMA PATTERNS
--------------------------------------------------------------------------------
1. November-April (Stark säsong)
   Edge: +0.142% | Accuracy: 68.2% | Win Rate: 64.1%
   Sharpe: 0.58 | Stability: 72.3% | Degradation: -3.2%
   Rekommendation: KEEP

2. Extended Rally (7+ up days)
   Edge: +0.118% | Accuracy: 71.4% | Win Rate: 71.4%
   Sharpe: 0.52 | Stability: 65.8% | Degradation: +2.1%
   Rekommendation: KEEP

3. Volatility over 75th percentile
   Edge: +0.095% | Accuracy: 59.8% | Win Rate: 57.2%
   Sharpe: 0.38 | Stability: 68.1% | Degradation: -5.7%
   Rekommendation: KEEP

4. Sideways Market
   Edge: +0.062% | Accuracy: 58.3% | Win Rate: 55.9%
   Sharpe: 0.31 | Stability: 71.2% | Degradation: -11.2%
   Rekommendation: MONITOR

5. Thursday Effect
   Edge: +0.048% | Accuracy: 52.1% | Win Rate: 52.8%
   Sharpe: 0.22 | Stability: 63.5% | Degradation: -8.9%
   Rekommendation: ADJUST

--------------------------------------------------------------------------------
⚠️  BOTTOM 5 SÄMST PRESTERANDE PATTERNS
--------------------------------------------------------------------------------
1. Extended Selloff (7+ down days)
   Edge: -0.123% | Accuracy: 28.6%
   Degradation: -18.3% | Rekommendation: REMOVE

2. Death Cross (50MA < 200MA)
   Edge: -0.087% | Accuracy: 33.3%
   Degradation: -22.1% | Rekommendation: REMOVE

--------------------------------------------------------------------------------
🚨 DEGRADERANDE PATTERNS (Kräver uppmärksamhet!)
--------------------------------------------------------------------------------
❗ Death Cross (50MA < 200MA)
   Degradation: -22.1% per kvartal
   Edge (predicted): -1.60% → (actual): -0.09%
   Åtgärd: REMOVE

❗ Sideways Market
   Degradation: -11.2% per kvartal
   Edge (predicted): +0.05% → (actual): +0.06%
   Åtgärd: MONITOR

--------------------------------------------------------------------------------
DETALJERADE REKOMMENDATIONER
--------------------------------------------------------------------------------

❌ REMOVE:
  • Extended Selloff (7+ Down Days): Edge -0.12%, Accuracy 28.6%, Degradation -18.3%
  • Death Cross (50Ma < 200Ma): Edge -0.09%, Accuracy 33.3%, Degradation -22.1%

👁️ MONITOR:
  • Sideways Market: Edge +0.06%, Accuracy 58.3%, Degradation -11.2%
  • Thursday Effect: Edge +0.05%, Accuracy 52.1%, Degradation -8.9%

🔧 ADJUST:
  • Thursday Effect: Edge +0.05%, Accuracy 52.1%, Degradation -8.9%
  • Sell In May (Maj Oktober): Edge +0.04%, Accuracy 48.2%, Degradation -6.3%

✅ KEEP:
  • November April (Stark Säsong): Edge +0.14%, Accuracy 68.2%, Degradation -3.2%
  • Extended Rally (7+ Up Days) Exhaustion Risk: Edge +0.12%, Accuracy 71.4%, Degradation +2.1%
  • Volatility Over 75Th Percentile: Edge +0.10%, Accuracy 59.8%, Degradation -5.7%

================================================================================
ÅTGÄRDSPLAN
================================================================================

🚫 TA BORT:
   Dessa patterns presterar dåligt och bör tas bort från modellen

🔧 JUSTERA:
   Dessa patterns har potential men behöver parameterjustering
   Överväg att justera tröskelvärden eller fönsterstorlekar

👁️  ÖVERVAKA:
   Dessa patterns visar varningssignaler - övervaka nästa kvartal

✅ BEHÅLL:
   Dessa patterns presterar väl - fortsätt använda

================================================================================
```

### Lagring:

Reports sparas automatiskt i `quarterly_audits/`:
```
quarterly_audits/
├── audit_2025-10-01_2026-01-01.json
├── audit_2026-01-01_2026-04-01.json
└── audit_2026-04-01_2026-07-01.json
```

---

## 📆 Rekommenderat Schema

### Veckorapporter:
- **Frekvens**: Varje måndag morgon
- **Åtgärd**: Granska nya möjligheter och konfidensskiften
- **Beslut**: Justera positioner baserat på signal-förändringar

### Kvartalsrevisioner:
- **Frekvens**: Var 3:e månad (slutet av kvartalet)
- **Åtgärd**: Validera pattern-performance
- **Beslut**: REMOVE degraderade patterns, ADJUST parametrar, KEEP välfungerande

**Exempel Schema:**
```
Q1 2026: Mars 31  - Kör kvartalsrevision
Q2 2026: Juni 30  - Kör kvartalsrevision
Q3 2026: Sept 30  - Kör kvartalsrevision
Q4 2026: Dec 31   - Kör kvartalsrevision

Varje måndag: Kör veckorapport
```

---

## 🔗 Integration i Workflow

### 1. Komplett Vecko-Workflow:

```python
# weekly_analysis.py
from instrument_screener import InstrumentScreener
from instruments_universe import get_all_instruments
from src.reporting import generate_weekly_report
from datetime import datetime

def run_weekly_analysis():
    """Kör full veckoanalys."""
    print("Startar veckoanalys...")
    
    # 1. Screen instruments
    screener = InstrumentScreener()
    instruments = get_all_instruments()
    results = screener.screen_instruments(instruments)
    
    # 2. Generera veckorapport
    report = generate_weekly_report(results)
    
    # 3. Spara rapport
    today = datetime.now()
    filename = f"reports/weekly_{today.strftime('%Y_%m_%d')}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Rapport sparad: {filename}")
    print("\n" + "="*80)
    print(report)
    
    return results, report

if __name__ == "__main__":
    run_weekly_analysis()
```

### 2. Kvartalsvis Revision:

```python
# quarterly_review.py
from src.reporting import generate_quarterly_audit
from datetime import datetime

def run_quarterly_review():
    """Kör kvartalsrevision."""
    print("Startar kvartalsrevision...")
    
    # Generera audit
    audit = generate_quarterly_audit(lookback_quarters=1)
    
    # Spara
    today = datetime.now()
    filename = f"reports/quarterly_audit_{today.strftime('%Y_Q%q')}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(audit)
    
    print(f"Audit sparad: {filename}")
    print("\n" + "="*80)
    print(audit)
    
    return audit

if __name__ == "__main__":
    run_quarterly_review()
```

---

## 🎯 Praktiska Tips

### För Veckorapporter:
1. **Fokusera på "Nya Möjligheter"** - RED → YELLOW/GREEN är starkast
2. **Bevaka "Konfidensskiften"** - Stora förändringar (>10%) kräver uppmärksamhet
3. **Temperaturtrend** - Använd för makro-allokering (FROZEN = max cash)

### För Kvartalsrevisioner:
1. **REMOVE utan tvekan** - Ta bort degraderade patterns omedelbart
2. **ADJUST försiktigt** - Justera parametrar, testa innan deployment
3. **Dokumentera** - Spara varje revision för framtida jämförelser

### Viktigt:
- ⚠️ **Signal tracking måste köras minst 1 månad** innan första kvartalsrevisionen
- 📊 **Veckorapporter kräver minst 2 veckors data** för delta-analys
- 🔄 **Spara alltid gamla rapporter** - används för trend-analys

---

## 🛠️ Troubleshooting

### Problem: "Ingen tidigare vecka att jämföra med"
**Lösning**: Detta är första körningen - kör igen nästa vecka för delta-analys

### Problem: "No signal data found for this period"
**Lösning**: Signal tracking har inte körts tillräckligt länge. Behöver minst 1 månads data.

### Problem: Konstiga konfidensskiften
**Lösning**: Kontrollera att instrument_screener.py använder samma kategorier mellan körningarna

---

**Version**: 2.0 REPORTING  
**Datum**: 2026-01-04  
**Moduler**: Weekly Report + Quarterly Audit  
**Status**: Production Ready ✅
