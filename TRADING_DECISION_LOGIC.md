# TRADING DECISION LOGIC - Komplett Beslutsflöde

## ÖVERSIKT: Från Data till Köpbeslut

```
Yahoo Finance → Pattern Analysis → Screener V2.2 → Dashboard → Weekly Analyzer → BUY Signal
     ↓               ↓                    ↓              ↓             ↓
  15 års data   Mönsterigenkänning   Scoring 0-100   Daglig JSON   Conviction Score
```

---

## STEG 1: DATAHÄMTNING (data_fetcher.py)

**Källa:** Yahoo Finance API (yfinance)

**Vad hämtas:**
```python
market_data = {
    'timestamps': [],      # Datum för varje dag
    'open_prices': [],     # Öppningspris
    'high_prices': [],     # Högsta pris
    'low_prices': [],      # Lägsta pris
    'close_prices': [],    # Stängningspris
    'volume': []           # Handelsvolym
}
```

**Tidsperiod:** 15 år historisk data (för backtest och pattern recognition)

**Kvalitetskrav:**
- Minst 5 års data (period_years >= 5.0)
- Snittvolym > 50,000 aktier/dag
- Data utan stora luckor

---

## STEG 2: PATTERN ANALYSIS (QuantPatternAnalyzer)

**Algoritm:** Bayes' Theorem + Permutation Testing

### 2A. Mönsterigenkänning
Systemet söker efter **återkommande marknadssituationer**:
- **State Space:** Pris relativ till 200-dagars MA, volym, RSI, volatilitet
- **Forward Returns:** Vad hände 1-10 dagar efter varje mönster?
- **Bayesian Edge:** P(profit|pattern) beräknas med Bayes' Theorem

**Exempel mönster:**
```
Situation: "Pris 2% över 200MA + hög volym + RSI 45-55"
Historik:  Sedd 47 gånger
Resultat:  +0.84% genomsnittlig avkastning (1 dag framåt)
P-värde:   0.03 (statistiskt signifikant)
```

### 2B. Validering
- **Permutation Test:** Jämför verkligt mönster mot 1000 slumpmässiga kombinationer
- **Konfidensintervall:** Bayesian credible intervals (90%)
- **Threshold:** Måste vara bättre än 90% av slumpdata

---

## STEG 3: TRAFFIC LIGHT SYSTEM (4 nivåer)

Aggregerar alla pattern signals till en **trafikljussignal**:

### Signal-nivåer:
```
🟢 GREEN:  Stark köpsignal (3-5% position)
   → Flera patterns med positiv edge
   → Hög confidence (>70%)
   → Korrelation mellan patterns

🟡 YELLOW: Försiktig köpsignal (1-3% position)
   → Vissa patterns positiva
   → Medelhög confidence (40-70%)
   → Risk för falsk signal

🟠 ORANGE: Neutral (0-1% position)
   → Blandade signaler
   → Låg confidence (<40%)

🔴 RED:    Säljsignal / Undvik (0% position)
   → Negativa patterns
   → Hög risk för förlust
```

---

## STEG 4: SCREENER V2.2 - SCORING (0-100 poäng)

**Final Score = 6 komponenter:**

### 1. Traffic Light Signal (30%)
```
GREEN:  30 poäng
YELLOW: 20 poäng
ORANGE: 10 poäng
RED:    0 poäng
```

### 2. Net Edge efter kostnader (25%)
```
Formel: edge_score = min(25, (net_edge / 0.50) * 25)

Exempel:
+0.50% edge → 25 poäng (max)
+0.25% edge → 12.5 poäng
+0.10% edge → 5 poäng
-0.10% edge → -2 poäng (penalty)
```

### 3. V-Kelly Position Size (15%)
```
Volatility-adjusted position sizing
Högre position = lägre volatilitet = bättre

Formel: kelly_score = min(15, (v_kelly / 5.0) * 15)

Exempel:
5% V-Kelly → 15 poäng
2% V-Kelly → 6 poäng
```

### 4. Trend Alignment (15%)
```
Över 200-dagars MA → +15 poäng
Under 200-dagars MA → 0 poäng (BLOCKERAD)
```

### 5. Volatility Breakout (10%)
```
EXTREME breakout → 10 poäng
HIGH breakout    → 8 poäng
MEDIUM breakout  → 5 poäng
LOW breakout     → 2 poäng
```

### 6. Cost Profitability (5%)
```
Net edge > 0 efter courtage → +5 poäng
Net edge < 0                → BLOCKERAD
```

**Exempel-scoring:**
```
Instrument: NOLA-B.ST
1. Traffic: YELLOW       → 20 poäng
2. Net Edge: +1.06%      → 25 poäng (maxat)
3. V-Kelly: 1.5%         → 4.5 poäng
4. Trend: Över 200MA     → 15 poäng
5. Breakout: MEDIUM      → 5 poäng
6. Profitable: Yes       → 5 poäng
-----------------------------------
   TOTAL SCORE:            74.5/100
```

---

## STEG 5: REGIME DETECTION & 1500 SEK FLOOR

### 5A. Marknadsregim
```
Market Signals → Regime Multiplier:

93% RED signals → CRISIS   (0.2x positions)
70% RED signals → STRESSED (0.4x positions)
50% RED signals → CAUTIOUS (0.7x positions)
30% RED signals → HEALTHY  (1.0x positions)
```

### 5B. 1500 SEK Systematic Overlay
```python
if final_allocation > 0 and final_allocation < 1.5%:
    # V-Kelly föreslog t.ex. 0.3%
    final_allocation = 1.5%  # Enforca 1500 SEK floor
    entry_recommendation = "ENTER - 1500 floor"
    
# VARFÖR 1500 SEK?
# Courtage på Avanza Mini: 2 kr round-trip
# 2 kr / 1500 kr = 0.13% (acceptabelt)
# 2 kr / 50 kr = 4.0% (förödande)
```

---

## STEG 6: DASHBOARD KATEGORISERING

**Execution Guard** validerar varje signal:

### INVESTERBARA (Net Edge > 0)
```
Kriteria:
✅ Score > 0
✅ Signal: GREEN eller YELLOW
✅ Net Edge efter execution > 0
✅ Över 200-dagars MA
✅ Entry recommendation: "ENTER"

Exempel:
NOLA-B.ST
  Tech Edge: +1.44%
  Courtage:  -0.38%
  Net Edge:  +1.06% ✅ INVESTABLE
  Position:  1500 SEK (1.5%)
```

### BEVAKNINGSLISTA (Tech Signal men blockerad)
```
Signal är bra MEN:
❌ Net Edge < 0 (courtage äter hela edgen)
❌ Under 200-dagars MA
❌ För låg volym
❌ För hög spread

Exempel:
BND (All-Weather ETF)
  Tech Edge: +0.59%
  Courtage:  -5.50% (EXTREME för utländsk)
  Net Edge:  -4.91% ❌ WATCHLIST
```

---

## STEG 7: WEEKLY CONVICTION SCORING (0-100)

**Aggregerar 30 dagars dashboard-data:**

### Conviction Score = 3 komponenter

#### 1. CONSISTENCY (40%)
```
Formel: (days_investable / 30) * 100 * 0.4

Exempel:
25/30 dagar investable → 83% * 0.4 = 33.2 poäng
10/30 dagar investable → 33% * 0.4 = 13.2 poäng
```

#### 2. QUALITY (30%)
```
Baserat på:
- Genomsnittlig daily score (20%)
- Genomsnittlig net edge (10%)

Formel:
quality = (avg_score/100 * 20) + min(10, avg_net_edge * 10)

Exempel:
avg_score = 74, avg_net_edge = 1.06%
→ (74/100 * 20) + min(10, 1.06*10)
→ 14.8 + 10 = 24.8 poäng
```

#### 3. MOMENTUM (30%)
```
Förbättras signalen eller försämras den?

Score Momentum: (last_score - first_score) / 5
  Range: -15 till +15 poäng

Edge Momentum: (last_edge - first_edge) * 15
  Range: -15 till +15 poäng

Exempel:
Score: 70 → 75 (+5 poäng improvement)
  → +5/5 = +1 poäng momentum
Edge: +0.9% → +1.1% (+0.2% improvement)
  → +0.2*15 = +3 poäng momentum
Total momentum: +4 poäng
```

**Exempel total conviction:**
```
NOLA-B.ST (30 dagar):
1. Consistency: 25/30 days → 33.2 poäng
2. Quality:     avg 74, +1.06% → 24.8 poäng
3. Momentum:    +5 score, +0.2% edge → +4.0 poäng
----------------------------------------
   CONVICTION SCORE:        62.0/100
```

---

## STEG 8: BUY/SELL RECOMMENDATION

### Rekommendationslogik:

```python
if conviction >= 70 and days_investable >= 10 and SNR > 1.0:
    → STRONG BUY
    
elif conviction >= 50 and days_investable >= 5 and net_edge > 0:
    → BUY ✅
    
elif conviction >= 30:
    → WATCH
    
else:
    → AVOID
```

### EXAKT VAD BETYDER "BUY"?

När systemet säger **BUY**, betyder det:

✅ **Matematisk Edge:** Net edge > 0 efter courtage  
✅ **Konsistens:** Minst 5/30 dagar investable (17%)  
✅ **Conviction:** Score ≥ 50/100  
✅ **Trend:** Över 200-dagars moving average  
✅ **Breakout:** Volatility breakout pågår  
✅ **Pattern Validation:** Statistiskt bättre än slump (p < 0.10)

**DET BETYDER INTE:**
- ❌ Garanterad vinst
- ❌ Risk-free trade
- ❌ "Köp allt nu"

**DET BETYDER:**
- ✅ Historiskt positiv edge i denna situation
- ✅ Risk-justerad position (1.5-5% av portfolio)
- ✅ Gynnsam risk/reward ratio
- ✅ Systematisk kant över slumpen

---

## SIGNAL-TO-NOISE RATIO (SNR) - High Confidence Filter

```
SNR = Net Edge / Volatilitet (ATR)

Exempel:
Net Edge: +1.06%
ATR:      1.0% (STABLE volatilitet)
SNR:      1.06/1.0 = 1.06

SNR > 1.0 = HIGH CONFIDENCE ⭐
  → Edge är större än daglig volatilitet
  → "Signalen är starkare än bruset"
```

**Interpretation:**
- **SNR < 0.5:** Edge dränks i brus, undvik
- **SNR 0.5-1.0:** OK edge, normal risk
- **SNR > 1.0:** Stark edge, high confidence ⭐

---

## RISK CONTROLS - Multi-Layer Defense

### Layer 1: Pattern Validation
- Permutation testing (p < 0.10)
- Bayesian confidence intervals
- Minst 5 occurrences per pattern

### Layer 2: Screener Filters
- Traffic Light (GREEN/YELLOW only)
- Trend Filter (200-day MA)
- Cost Filter (net edge > 0)
- Volatility Breakout timing

### Layer 3: Regime Detection
- CRISIS: 0.2x multiplier (max 10% total exposure)
- All-Weather får 1.0x även i CRISIS

### Layer 4: 1500 SEK Floor
- Minimum position för courtage-effektivitet
- 0.13% cost vs gamla 4%

### Layer 5: Weekly Conviction
- Kräver 5+ investable days för BUY
- Kräver 10+ investable days för STRONG BUY
- Momentum tracking (crash protection)

### Layer 6: Stop-Loss Risk (Monte Carlo)
- Simulerar 500 price paths
- Beräknar stop-out probability
- AVOID om risk > 35%

---

## EXEMPEL: NOLA-B.ST → BUY SIGNAL

**Steg-för-steg:**

### 1. Data (Yahoo Finance)
```
Ticker: NOLA-B.ST
Period: 15 år (2011-2026)
Datapoints: 3768
Volym: 85,000 aktier/dag ✅
```

### 2. Pattern Analysis
```
Patterns hittade: 12 st
Bästa pattern: "+1.5% över 200MA, medium vol"
Bayesian Edge: +1.44%
P-value: 0.04 (signifikant) ✅
```

### 3. Traffic Light
```
Signal: YELLOW (flera patterns med positiv edge)
Confidence: MEDIUM (70%)
```

### 4. Screener Score
```
Traffic:   YELLOW → 20 poäng
Net Edge:  +1.06% → 25 poäng
V-Kelly:   1.5%   → 4.5 poäng
Trend:     Above  → 15 poäng
Breakout:  MEDIUM → 5 poäng
Cost:      +1.06% → 5 poäng
-------------------------
TOTAL:              74.5/100
```

### 5. Regime & Floor
```
Market: 93% RED → CRISIS (0.2x)
V-Kelly: 7.5% → 7.5% * 0.2 = 1.5%
Floor: 1.5% ≥ 1.5% ✅ (exakt på floor)
Entry: "ENTER - 1500 floor"
```

### 6. Dashboard
```
INVESTERBARA ✅
  Tech Edge: +1.44%
  Execution Cost: -0.38%
  Net Edge: +1.06%
  Position: 1500 SEK
```

### 7. Weekly Conviction (30 dagar)
```
Days investable: 25/30 (83%)
Consistency:     33.2 poäng
Quality:         24.8 poäng
Momentum:        +4.0 poäng
--------------------------
CONVICTION:      62.0/100
```

### 8. Recommendation
```
conviction = 62.0 ≥ 50 ✅
days_investable = 25 ≥ 5 ✅
net_edge = 1.06% > 0 ✅

→ BUY ✅
```

### 9. Risk Metrics
```
SNR: 1.06 (HIGH CONFIDENCE ⭐)
Stop-Out Risk: 5.8% (10-day Monte Carlo)
Expected Return: +0.05% (10 days)
Worst Case: -5.41%
Best Case: +5.16%
```

---

## SAMMANFATTNING: VEM BESTÄMMER KÖPBESLUTET?

**Inte en enskild signal utan en KONSENSUS av 8 system:**

1. ✅ **Bayesian Pattern:** Edge +1.44% (p=0.04)
2. ✅ **Traffic Light:** YELLOW (köpsignal)
3. ✅ **Screener Score:** 74.5/100
4. ✅ **Trend Filter:** Över 200MA
5. ✅ **Cost Filter:** Net +1.06% efter courtage
6. ✅ **Volatility Breakout:** MEDIUM confidence
7. ✅ **Weekly Conviction:** 62.0/100 (25/30 dagar)
8. ✅ **SNR:** 1.06 (high confidence)

**Alla 8 måste säga JA** för BUY-signal.

Om **någon** säger NEJ → BLOCK eller WATCH

Detta är **casino-matematik**: Vi spelar bara när oddsen är till vår fördel.
