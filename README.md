# Quant Pattern Analyzer

Ett statistiskt observationsinstrument för finansiella marknader, inspirerat av Jim Simons och Renaissance Technologies tillvägagångssätt.

## Filosofi

Detta verktyg är byggt kring följande grundprinciper:

- **Mätbara variabler**: Arbetar uteslutande med historisk data och kvantifierbara marknadsegenskaper
- **Sannolikheter, inte förutsägelser**: Uttrycker resultat som historiska tendenser, aldrig som absoluta påståenden
- **Ingen tolkning**: Ignorerar narrativ, bolagsnamn och subjektiva bedömningar
- **Statistisk robusthet**: Kräver tillräcklig data och stabilitet över tid

## Vad verktyget gör

Verktyget utför följande steg:

1. **Identifierar marknadssituationer (X)** baserat på:
   - Prisrörelser
   - Volatilitet
   - Volym
   - Tid och kalendereffekter
   - Relationer mellan tillgångar

2. **Analyserar historiska utfall (Y)** för varje situation:
   - Fördelning av framtida avkastning
   - Statistiska mått (mean, median, standardavvikelse)
   - Vinst/förlust-frekvens
   - Maximal historisk drawdown

3. **Utvärderar mönstrens robusthet**:
   - Tillräckligt antal observationer
   - Stabilitet över olika tidsperioder
   - Skydd mot överanpassning

4. **Kommunicerar insikter** på ett användarvänligt sätt:
   - Enkelt, neutralt språk
   - Historiska tendenser utan garantier
   - Tydlig osäkerhetskommunikation

## Installation

### Krav

- Python 3.8 eller senare
- pip

### Installera beroenden

```bash
pip install -r requirements.txt
```

## Användning

### Grundläggande exempel

```python
from src import QuantPatternAnalyzer, MarketData
import numpy as np

# Skapa eller ladda marknadsdata
market_data = MarketData(
    timestamps=your_timestamps,
    open_prices=your_open_prices,
    high_prices=your_high_prices,
    low_prices=your_low_prices,
    close_prices=your_close_prices,
    volume=your_volume
)

# Initiera analysverktyget
analyzer = QuantPatternAnalyzer(
    min_occurrences=30,
    min_confidence=0.70,
    forward_periods=1
)

# Kör analys
results = analyzer.analyze_market_data(market_data)

# Generera rapport
report = analyzer.generate_report(results)
print(report)
```

### Kör exempelskriptet

```bash
python main.py
```

Detta kör en demonstration med simulerad data och visar hur verktyget fungerar.

## Projektstruktur

```
quant-pattern-analyzer/
├── src/
│   ├── core/                 # Kärnlogik för mönsterutvärdering
│   │   └── pattern_evaluator.py
│   ├── patterns/             # Mönsterigenkänning (X-variabler)
│   │   └── detector.py
│   ├── analysis/             # Utfallsanalys (Y-variabler)
│   │   └── outcome_analyzer.py
│   ├── utils/                # Databehandling och verktyg
│   │   └── market_data.py
│   ├── communication/        # Användarvänlig formattering
│   │   └── formatter.py
│   └── analyzer.py           # Huvudapplikation
├── tests/                    # Enhetstester
├── config/                   # Konfigurationsfiler
├── data/                     # Datalagringsplats
├── main.py                   # Exempelskript
├── requirements.txt          # Python-beroenden
└── README.md                 # Denna fil
```

## Konfiguration

Redigera `config/config.yaml` för att anpassa:

- Minsta antal observationer för mönstervalidering
- Konfidenströsklar
- Parametrar för olika mönsterdetektorer
- Output-formattering

## Viktiga begränsningar

- **Detta är INTE en investeringsrådgivare**: Verktyget ger inga köp- eller säljrekommendationer
- **Historisk data garanterar inget**: Mönster som fungerat historiskt kan upphöra när som helst
- **Svaga individuella mönster**: Varje mönster är svagt isolerat; värdet ligger i aggregation
- **Datakvalitet är kritisk**: Felaktig eller bristfällig data ger missvisande resultat

## Användningsfall

Detta verktyg är lämpligt för:

- Forskare som undersöker marknadsstruktur
- Kvantitativa analytiker som söker statistiska mönster
- Utbildningssyfte för att förstå marknadsbeteende
- Backtesting av marknadsregimer

Det är INTE lämpligt för:

- Direkta investeringsbeslut utan djupare analys
- Realtidshandel utan omfattande validering
- Användning av personer utan förståelse för statistisk analys

## Teknisk information

### Beroenden

- **NumPy**: Numeriska beräkningar och array-hantering
- **Pandas**: Tidsserieanalys och rullande beräkningar
- **SciPy**: Statistiska funktioner och hypotestestning

### Python-version

Kräver Python 3.8 eller senare för dataclass och typing-stöd.

## Licens

Detta projekt är skapat för utbildnings- och forskningssyfte.

## Bidrag

Detta är ett utbildningsprojekt. För frågor eller diskussioner, vänligen kontakta projektägaren.

## Ansvarsfriskrivning

DETTA VERKTYG TILLHANDAHÅLLS "SOM DET ÄR" UTAN GARANTIER AV NÅGOT SLAG.

Användning av detta verktyg för faktiska investeringsbeslut sker på egen risk. Utvecklaren tar inget ansvar för ekonomiska förluster som kan uppstå från användning av detta verktyg.

Historisk avkastning är ingen garanti för framtida resultat.
