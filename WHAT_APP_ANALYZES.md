# Vad Appen Analyserar & Beslutsunderlag

## 🎯 Kort Svar
Appen analyserar **historiska prismönster** i marknadsdata och använder **Bayesiansk statistik** för att bedöma sannolikheten att dessa mönster fortsätter ge positiv avkastning. Den baserar sina beslut på **kvantitativ edge**, **statistisk stabilitet** och **riskjusterad position sizing**.

---

## 📊 Detaljerad Förklaring

### 1. **Rådata Som Analyseras** 📈

#### A. Prisdata (från Yahoo Finance):
- **Close Price**: Stängningskurs varje dag
- **Open Price**: Öppningskurs
- **High/Low**: Högsta/lägsta pris under dagen
- **Volume**: Handelsvolym
- **Returns**: Daglig procentuell förändring

#### B. Tidsperiod:
- **15 års historik** (2011-2026)
- **~3,773 datapunkter** per instrument (för S&P 500)
- Använder "walk-forward" metodik för backtesting

---

### 2. **Mönster Som Identifieras** 🔍

Appen letar efter **8 typer av mönster** baserade på:

#### **A. Volatilitetsmönster:**
- **Hög volatilitet** (>75:e percentilen)
  - När är marknaden mer oförutsägbar?
  - Edge: +0.08%/dag
  - Används för att justera position sizing

#### **B. Trendmönster:**
- **Sideways Market** (<10% förändring över 50 dagar)
  - Identifierar "range-bound" marknader
  - Edge: +0.05%/dag
  - P(edge > 0): 99.9%

- **Death Cross** (50MA < 200MA)
  - Bearish signal när kort MA korsar under lång MA
  - Edge: -1.60%/dag (!)
  - P(edge > 0): 6.6% (stark negativ)

- **Golden Cross** (50MA > 200MA)
  - Bullish signal när kort MA korsar över lång MA
  - Motsatsen till Death Cross

#### **C. Momentum-mönster:**
- **Extended Rally** (7+ upp-dagar i rad)
  - "Exhaustion risk" - kan vända snart
  - Edge: +0.40%/dag (men med risk)
  - P(edge > 0): 100%

- **Extended Selloff** (7+ ned-dagar i rad)
  - "Bounce risk" - kan studsa upp
  - Edge: -0.82%/dag
  - P(edge > 0): 1.7%

#### **D. Kalendereffekter:**
- **November-April** (Stark säsong)
  - Historiskt starkare period
  - Edge: +0.06%/dag
  - P(edge > 0): 97.9%

- **Sell in May** (Maj-Oktober)
  - Traditionellt svagare period
  - Edge: +0.05%/dag
  - P(edge > 0): 97.8%

- **Veckodagseffekter** (Thursday, Friday, etc.)
  - Vissa dagar har historiskt bättre avkastning
  - Edge: +0.05%/dag
  - P(edge > 0): 90.9%

#### **E. Tekniska Indikatorer:**
- **RSI** (Relative Strength Index)
  - RSI < 30: Översåld (bounce risk)
  - RSI > 70: Överköpt (pullback risk)

- **Volume Spikes**
  - Volym >2x genomsnitt
  - Indikerar stark aktivitet/intresse

---

### 3. **Bayesiansk Edge-analys** 🎲

För varje mönster beräknas:

#### **A. Point Estimate (Förväntat Edge):**
```
Edge = Genomsnittlig daglig avkastning när mönster är aktivt - Transaktionskostnader
```

**Exempel:**
- November-April mönster: Edge = +0.06%/dag
- Death Cross: Edge = -1.60%/dag

#### **B. Sannolikhet (Bayesian Confidence):**
```
P(edge > 0) = Sannolikhet att edge faktiskt är positiv
P(edge > 0.10%) = Sannolikhet att edge är >0.10% (efter kostnader)
```

**Exempel:**
- Sideways Market: P(edge > 0) = 99.9% (mycket säker)
- Death Cross: P(edge > 0) = 6.6% (nästan säkert negativ)

#### **C. Stabilitet:**
```
Stabilitet = Hur konsekvent mönstret fungerar över tid
Degeneration = Om mönstret försvagas (viktas ned då)
```

**Status:**
- ✅ **Healthy**: >80% stabilitet
- ⚠️ **Weakening**: 70-80% stabilitet
- 🔴 **Unstable**: <70% stabilitet
- ⚫ **Inactive**: >30% degeneration (ignoreras)

---

### 4. **Traffic Light Decision System** 🚦

Appen kombinerar alla mönster till **EN signal**:

#### **🟢 GREEN (Stark Positiv):**
**Krav (alla måste uppfyllas):**
1. Green Score ≥ 4/5:
   - Marknadsbias ≠ Bearish
   - Minst 1 friskt mönster med edge ≥ 0.10%
   - Inga kraftigt negativa mönster (<-0.10%)
   - Stabilitet >60% för huvudmönstren
   - Konfidens ≠ LÅG

2. **Minst 1 handelsbart mönster** (edge ≥ 0.10%)

3. **Hög Bayesian certainty** (låg osäkerhet)

**Action:**
- 🎯 **Allokera 3-5% per instrument**
- Aggressiv investering
- Öka risknivå

---

#### **🟡 YELLOW (Måttlig Positiv):**
**Krav:**
1. Green Score ≥ 3/5
2. Minst 1 handelsbart mönster (edge ≥ 0.10%)
3. Viss osäkerhet accepteras

**Action:**
- 🎯 **Allokera 1-3% per instrument**
- Försiktig investering
- Måttlig risknivå

---

#### **🟠 ORANGE (Neutral/Observant):**
**Krav:**
1. Green Score ≥ 2/5, ELLER
2. Blandade signaler (red_score = 1, green_score ≥ 1)

**Action:**
- 🎯 **Allokera 0-1% per instrument**
- Extremt försiktig
- Minimal exponering

---

#### **🔴 RED (Stark Negativ):**
**Krav:**
1. Red Score ≥ 2/3:
   - Marknadsbias = Bearish
   - Många mönster med negativ edge
   - Låg konfidens

ELLER

2. Green Score < 2 (otillräckliga positiva signaler)

**Action:**
- 🎯 **Allokera 0%**
- INGEN ny investering
- Skydda kapital
- Vänta på bättre läge

---

### 5. **Score-beräkning (Screener)** 📊

När appen jämför flera instrument (instrument_screener.py):

```python
Overall Score (0-100) = 
    Traffic Light Signal: 30 poäng
        GREEN = 30 poäng
        YELLOW = 20 poäng
        ORANGE = 10 poäng
        RED = 0 poäng
        
  + Edge: 30 poäng (normaliserad till 0.50% edge)
        +0.50% edge eller mer = 30 poäng
        +0.25% edge = 15 poäng
        0% edge = 0 poäng
        
  + Stability: 20 poäng
        100% stabilitet = 20 poäng
        80% stabilitet = 16 poäng
        
  + Tradeable Patterns: 20 poäng
        5+ patterns med edge ≥ 0.10% = 20 poäng
        3 patterns = 12 poäng
        1 pattern = 4 poäng
        
  + Category Bonus/Malus: ±10%
        Outlier i negativ sektor = +10%
        Negativ i positiv sektor = -10%
```

**Exempel (Zscaler - Score 94.7):**
- Signal: GREEN = 30 poäng
- Edge: +1.56% = 30 poäng (mycket hög)
- Stability: ~85% = 17 poäng
- Tradeable: 4 patterns = 16 poäng
- Category: Tech outlier = +1.7 poäng
- **Total: 94.7/100**

---

### 6. **Kelly Criterion (Position Sizing)** 💰

Används för att beräkna optimal position size:

```python
Kelly Fraction = (Win Rate × Avg Win - Lose Rate × Avg Loss) / Avg Win

Adjusted Kelly = Kelly × Safety Factor (typiskt 25-50%)
```

**Exempel:**
- Win Rate: 55%
- Avg Win: +2%
- Lose Rate: 45%
- Avg Loss: -1.5%
- Kelly = (0.55 × 2 - 0.45 × 1.5) / 2 = 0.2125 = **21.25%**
- Adjusted (25%): **5.3%** per position

---

### 7. **Renaissance-Filter** 🏆

**Krav för att mönster ska handlas:**

```python
1. Edge ≥ 0.10% efter transaktionskostnader
2. P(edge > 0) > 50% (Bayesian confidence)
3. Minst 50 förekomster (statistisk signifikans)
4. Stabilitet > 60%
5. Ingen kraftig degeneration (< -30%)
```

**Endast mönster som passerar detta filter används i beslut!**

---

### 8. **Fundamentaldata (NY i V2.0)** 📋

**Ytterligare filter för kvalitet:**

```python
Quality Score (0-100) baserat på:
- P/E < 15: +20 poäng
- P/B < 1.5: +15 poäng
- Dividend Yield > 3%: +15 poäng
- Profit Margin > 15%: +20 poäng
- ROE > 15%: +15 poäng
- Revenue Growth > 10%: +15 poäng
```

**Används för:**
- Filtrera bort "dåliga" företag även med bra tekniska signaler
- Kombinera kvant + fundamental analys

---

## 🎯 Sammanfattning: Vad Appen GÖR

### **Input:**
1. 15 års prisdata från Yahoo Finance
2. 250 Avanza-kompatibla instrument
3. Fundamentaldata (P/E, dividend, etc.)

### **Analys:**
1. Identifierar 8 typer av mönster
2. Beräknar Bayesian edge för varje mönster
3. Utvärderar stabilitet och degeneration
4. Filtrerar med Renaissance-criteria
5. Kombinerar fundamentals

### **Output:**
1. **Traffic Light Signal** (GREEN/YELLOW/ORANGE/RED)
2. **Overall Score** (0-100)
3. **Edge Estimate** (+X.XX%)
4. **Position Size Recommendation** (0-5%)
5. **Konkreta Actions** (investera, vänta, pausa)

---

## ⚠️ Viktiga Begränsningar

### **Vad Appen INTE gör:**
❌ **Förutsäga framtiden** - Den säger bara "historiskt har detta mönster fungerat X% av gångerna"
❌ **Garantera vinst** - Edge = sannolikhet, inte säkerhet
❌ **Tidsbestämma exakt** - Säger inte "köp exakt nu kl 14:23"
❌ **Stock picking** - Säger inte "köp AAPL istället för MSFT"
❌ **Fundamentalanalys** (i V1.0) - Bryr sig inte om företagets produkter/ledning

### **Vad Appen VÄL gör:**
✅ **Risk Management** - Säger hur aggressiv du bör vara
✅ **Edge Identification** - Hittar statistiska fördelar
✅ **Position Sizing** - Beräknar optimal allokering
✅ **Signal Aggregation** - Kombinerar många svaga signaler
✅ **Uncertainty Quantification** - Mäter hur säker signalen är

---

## 🔬 Renaissance Technologies Principles

Appen följer samma filosofi som Renaissance:

1. **"We don't predict, we measure probabilities"**
   - Edge är sannolikhet, inte förutsägelse

2. **"Many weak signals beat few strong ones"**
   - 8 mönster kombineras, inget är perfekt ensamt

3. **"Statistical significance over narrative"**
   - Bryr sig inte om "varför", bara "vad fungerar"

4. **"Control risk, not returns"**
   - Focus på position sizing och capital preservation

5. **"Degeneration is real"**
   - Mönster försvinner över tid → måste övervakas

---

## 📚 För Vidare Läsning

Se dessa filer för tekniska detaljer:
- `src/patterns/detector.py` - Mönsterigenkänning
- `src/patterns/technical_patterns.py` - Tekniska indikatorer
- `src/decision/traffic_light.py` - Beslutssystem
- `src/analysis/bayesian.py` - Bayesiansk analys
- `src/utils/fundamental_data.py` - Fundamentaldata

---

**Version**: 2.0 EXPANDED  
**Datum**: 2026-01-03  
**Instrument Analyzed**: 250  
**Analysis Method**: Bayesian Pattern Recognition + Renaissance Filtering
