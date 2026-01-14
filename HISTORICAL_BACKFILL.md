# 🎯 HISTORICAL BACKFILL SIMULATION
Point-in-Time Analysis Engine för Kvantitativ Trading

## Översikt

Historical Backfill Simulation låter dig köra komplett dashboard-analys för historiska perioder med **Point-in-Time constraints** - systemet använder endast data som var tillgänglig vid varje specifik analysdatum.

Detta ger dig möjlighet att:
- **Testa strategier** på historisk data utan look-ahead bias
- **Bygga consistency scores** baserat på daglig screening över längre perioder
- **Validera systemets prestanda** över olika marknadsregimer
- **Generera kompletta veckorapporter** med HIGH data quality

## Arkitektur

### Time-Slice Engine
```
Historical Period (T-N till T-0)
    ↓
Split into Trading Days (skip weekends)
    ↓
För varje dag T:
    ├─ Load instruments (800 tickers)
    ├─ Screen med data endast fram till T
    ├─ Run Execution Guard (cost analysis)
    ├─ Categorize: Investable vs Watchlist
    └─ Save actionable_YYYY-MM-DD.json
    ↓
Aggregate Results
    ↓
Generate Weekly Decision Report
```

### Point-in-Time Constraints
- **15 år historik**: Varje screening använder 15 års data fram till analysdagen
- **No look-ahead bias**: Framtida data är aldrig synlig
- **Synthetic Consistency**: Bygger consistency scores från daglig screening
- **Cost-Adjusted**: Alla signaler körs genom Execution Guard

## Installation

Systemet är redan integrerat i din befintliga codebase. Inga extra dependencies krävs.

## Usage

### 1. Kör Backfill Simulation

```bash
# Senaste veckan (7 handelsdagar)
python historical_backfill.py --period "senaste veckan"

# Senaste månaden (30 handelsdagar)
python historical_backfill.py --period "senaste månaden"

# Specifikt antal dagar
python historical_backfill.py --days 14

# Med custom portföljstorlek
python historical_backfill.py --days 7 --portfolio 200000
```

### 2. Kör Veckoanalys på Backfilled Data

```bash
python veckovis_analys.py --backfill
```

Detta kommer att:
- Läsa alla `actionable_YYYY-MM-DD.json` filer från `reports/backfill/`
- Beräkna Conviction Scores med full consistency tracking
- Generera rapport med **"BACKFILLED DATA QUALITY: HIGH"** stämpel

## Output

### Backfill Directory Structure
```
reports/backfill/
├── actionable_2026-01-06.json
├── actionable_2026-01-07.json
├── actionable_2026-01-08.json
├── actionable_2026-01-09.json
├── actionable_2026-01-10.json
├── backfill_summary.json
└── weekly_decision_2026-01-13.md
```

### Daily Actionable Files
Format: `actionable_YYYY-MM-DD.json`

```json
{
  "date": "2026-01-10",
  "regime": "🔴 CRISIS",
  "regime_multiplier": 0.2,
  "investable": [
    {
      "ticker": "ELUX-B.ST",
      "name": "Swedish - ELUX-B.ST",
      "signal": "YELLOW",
      "score": 65.2,
      "technical_edge": 0.81,
      "net_edge_after_execution": 0.31,
      "position": 0.05,
      "execution_risk": "MEDIUM"
    }
  ],
  "watchlist": [...],
  "market_stats": {
    "total_analyzed": 800,
    "green_signals": 5,
    "yellow_signals": 39,
    "red_signals": 756
  }
}
```

### Backfill Summary
Format: `backfill_summary.json`

```json
{
  "period": {
    "start_date": "2026-01-06",
    "end_date": "2026-01-10",
    "total_days": 5
  },
  "signals": {
    "total_investable": 12,
    "total_watchlist": 145,
    "avg_investable_per_day": 2.4,
    "avg_watchlist_per_day": 29.0
  },
  "regime_distribution": {
    "🔴 CRISIS": 5
  },
  "data_quality": "HIGH (Backfilled Point-in-Time Analysis)"
}
```

## Weekly Report Förbättringar

### Normal Mode (Låg data quality)
```
⚠️ DATA QUALITY WARNING:
- Endast 2 dagars data analyserad
- Consistency Score (40% av vägning) är statistiskt missvisande
- Rekommendation: Kör dashboard dagligen för mer robust analys
```

### Backfill Mode (Hög data quality)
```
✅ BACKFILLED DATA QUALITY: HIGH
- Point-in-Time Analysis: 7 handelsdagar
- Synthetic Consistency: Baserad på daglig screening
- Cost-Adjusted: Alla signaler körda genom Execution Guard
```

## Användningsfall

### 1. Initial Setup
Om du precis börjat använda systemet och vill ha en full veckas data:
```bash
python historical_backfill.py --period "senaste veckan"
python veckovis_analys.py --backfill
```

### 2. Monthly Review
Analysera en hel månad för att identifiera patterns:
```bash
python historical_backfill.py --period "senaste månaden"
python veckovis_analys.py --backfill
```

### 3. Strategy Validation
Testa om din strategi hade fungerat under en specifik period:
```bash
python historical_backfill.py --days 30
python veckovis_analys.py --backfill
```

### 4. Regime Analysis
Kör backfill över flera månader för att se hur systemet presterar i olika regimer:
```bash
python historical_backfill.py --days 90
python veckovis_analys.py --backfill
```

## Prestanda

### Tid per Dag
- **~10-15 sekunder** per handelsdag (beroende på din dator)
- **1 vecka (7 dagar)**: ~2 minuter
- **1 månad (30 dagar)**: ~8 minuter
- **1 kvartal (90 dagar)**: ~25 minuter

### Memory Usage
- **Peak memory**: ~2-3 GB (beroende på antal instruments)
- **Disk space**: ~100 KB per dag (JSON files)

## Begränsningar

### Data Availability
- Kräver historisk data från `yfinance`
- Vissa delisted instruments kan sakna data för äldre perioder
- Helger och marknadsavslutningar skippas automatiskt

### Point-in-Time Constraints
- Använder endast 15 års historik fram till varje analysdag
- Future data är ALDRIG synlig (no look-ahead bias)
- Execution costs beräknas med dagens courtage-struktur (Avanza Mini)

### Computational Cost
- Kör full screening för varje dag (800 instruments × N dagar)
- Större perioder (>90 dagar) kan ta lång tid
- Rekommenderas att köra över natten för perioder >1 månad

## Troubleshooting

### Problem: "InstrumentScreenerV22 does not support analysis_date"
**Lösning**: Screener måste stödja `analysis_date` parameter. Kontrollera att du har uppdaterad version av `instrument_screener_v22.py`.

### Problem: "No data available för vissa instruments"
**Lösning**: Vissa delisted eller nya instruments kan sakna historisk data. Systemet skippar dessa automatiskt.

### Problem: "Backfill tar för lång tid"
**Lösning**: 
- Reducera antal dagar: `--days 7` istället för `--days 30`
- Kör över natten för längre perioder
- Överväg att cacha results mellan körningar

## Advanced Usage

### Custom Portfolio Size
```bash
python historical_backfill.py --days 7 --portfolio 200000
```

Detta kommer att:
- Ändra Execution Guard breakeven-beräkningar
- Påverka vilka instruments som blir "investable"
- Ge dig ett beslutsunderlag för en 200k SEK portfölj

### Parse Custom Period Strings
Systemet stödjer naturliga språk-uttryck:
- "senaste veckan" → 7 dagar
- "senaste 2 veckorna" → 14 dagar
- "senaste månaden" → 30 dagar
- "senaste 3 månaderna" → 90 dagar

## Integration med Befintliga System

### Dashboard Workflow
```bash
# Normal: Kör dagligen
python dashboard.py

# Backfill: Fyll i historik
python historical_backfill.py --days 7
```

### Weekly Analysis Workflow
```bash
# Normal: Använd live data
python veckovis_analys.py

# Backfill: Använd historisk data
python veckovis_analys.py --backfill
```

## Best Practices

### 1. Initial Setup
Första gången du använder systemet:
```bash
# Generera en full veckas historik
python historical_backfill.py --period "senaste veckan"

# Kör veckoanalys
python veckovis_analys.py --backfill

# Från och med nu: kör dashboard dagligen
python dashboard.py
```

### 2. Gap Filling
Om du missat några dagar:
```bash
# Fyll i gaps med backfill
python historical_backfill.py --days 5

# Kör normal veckoanalys (kombinerar backfill + live data om båda finns)
python veckovis_analys.py
```

### 3. Monthly Reviews
En gång per månad:
```bash
# Generera månadsdata
python historical_backfill.py --period "senaste månaden"

# Analysera
python veckovis_analys.py --backfill
```

## Theoretical Foundation

### Synthetic Consistency
Backfill systemet bygger **Synthetic Consistency Scores** genom att:
1. Köra daglig screening över N dagar
2. Tracka varje instruments score över tid
3. Beräkna consistency som `days_investable / total_days`

Detta ger en **statistiskt robust** consistency measure jämfört med endast 1-2 dagars data.

### Cost-Adjusted Reality
Varje signal körs genom **Execution Guard** för att säkerställa:
- Courtage-kostnader är medräknade
- FX-kostnader för utländska instruments
- Spread-estimat baserat på volym
- Net edge efter ALLA kostnader

Detta ger en **realistisk** bild av vilka signaler som faktiskt var investable.

### Point-in-Time Integrity
Systemet använder endast data tillgänglig vid analysdagen:
- **No future information**: Framtida priser/volymer är aldrig synliga
- **Historical consistency**: Samma logik som live dashboard
- **Regime accuracy**: Market regime beräknas korrekt för varje dag

## Future Enhancements

### Planerade Features
- [ ] **Parallel processing**: Kör flera dagar samtidigt
- [ ] **Caching**: Spara screenings mellan körningar
- [ ] **Incremental backfill**: Uppdatera endast nya dagar
- [ ] **Backtesting mode**: Simulera faktiska trades och avkastning
- [ ] **Regime transition analysis**: Identifiera regime-shifts i historisk data

### Community Contributions
Om du vill bidra till Historical Backfill systemet:
1. Fork repot
2. Implementera din feature
3. Skapa en pull request
4. Inkludera tests och dokumentation

## Support

### Frågor?
- Läs WEEKLY_ANALYZER.md för veckoanalys-detaljer
- Läs EXECUTION_GUARD.md för cost-analysis
- Kontakta systemarkitekten för advanced support

### Bug Reports
Om du hittar en bug:
1. Dokumentera reproduktionsstegen
2. Inkludera error messages
3. Bifoga relevanta log files
4. Skapa en issue i repot

## Licens

Detta system är en del av Quant Pattern Analyzer trading system.
© 2026 All rights reserved.

---

**Built with ❤️  for kvantitativa traders som värdesätter Point-in-Time accuracy.**
