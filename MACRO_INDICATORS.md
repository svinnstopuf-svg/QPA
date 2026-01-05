# 📊 MACRO INDICATORS - Professional Risk Detection

## Översikt

Tre avancerade makro-indikatorer som hjälper dig **se röken innan branden startar**:

1. **Yield Curve Inversion** - Recession warning
2. **Credit Spreads** - Corporate stress detector
3. **Safe Haven Watch** - Capital flight monitor

---

## 1. Yield Curve Inversion (Räntekurvan)

### Vad den mäter
Skillnaden mellan korta och långa räntor:
- **^IRX** (13-week Treasury Bill) = kort ränta
- **^TNX** (10-year Treasury Note) = lång ränta

### Varför det spelar roll
När korta räntor är **högre** än långa räntor (inverterad kurva) är det historiskt ett av de mest tillförlitliga tecknen på kommande recession.

**Normal kurva:**
```
Kort ränta: 3.0%
Lång ränta: 4.5%
Spread: +1.5% ✅ Hälsosamt
```

**Inverterad kurva:**
```
Kort ränta: 4.5%
Lång ränta: 4.0%
Spread: -0.5% 🚨 VARNING!
```

### Risk-nivåer

| Spread | Risk Level | Betydelse |
|--------|------------|-----------|
| +2.0% eller mer | LOW | Normal, hälsosam marknad |
| +0.5% till +2.0% | MEDIUM | Kurvan plattnar ut - bevaka läget |
| 0% till +0.5% | HIGH | Kurvan nästan platt - recession närmar sig |
| Negativ | EXTREME | INVERTERAD - recession mycket trolig |

### Historisk träffsäkerhet
- **1989**: Inversion → Recession 1990-1991
- **2000**: Inversion → Dot-com crash 2001
- **2006**: Inversion → Finanskris 2008
- **2019**: Inversion → COVID-crash 2020

---

## 2. Credit Spreads (Kreditspreadar)

### Vad den mäter
Skillnaden i avkastning mellan säkra statsobligationer och riskfyllda företagsobligationer:
- **TLT** (20+ Year Treasury) = säkra statsobligationer
- **LQD** (Investment Grade Corporate) = företagsobligationer

### Varför det spelar roll
När investerare blir rädda för konkurser flyr de från företagsobligationer till statsobligationer. Detta syns som:
- TLT **stiger** (kapital flödar in)
- LQD **faller** (kapital flödar ut)

### Exempel

**Normal marknad:**
```
TLT: +0.5% (20 dagar)
LQD: +0.8% (20 dagar)
Spread: -0.3% ✅ Företag är starkare
```

**Flight to safety:**
```
TLT: +3.5% (rusar)
LQD: -2.0% (faller)
Spread: +5.5% 🚨 Kapitalflykt!
```

### Stress-nivåer

| Spread | Stress Level | Betydelse |
|--------|--------------|-----------|
| Negativ | LOW | Företag starkare än Treasury - risk-on |
| 0-2% | MEDIUM | Neutral - normal marknad |
| 2-5% | HIGH | Kapitalflykt påbörjad - rädsla för konkurser |
| 5%+ | EXTREME | EXTREM flykt - kreditmarknad i kris |

---

## 3. Safe Haven Watch (Kapitalflykts-monitor)

### Vad den mäter
Hur många av dina 59 All-Weather instruments som är GREEN/YELLOW samtidigt som marknaden (S&P 500) är RED.

### Varför det spelar roll
När 30%+ av safe havens är GREEN medan aktier är RED betyder det att smart money flyr från aktier till säkra tillgångar.

### Safe Haven Styrka

```
Analyserade: 59 All-Weather instruments
GREEN: 15
YELLOW: 12
RED: 32

Safe Haven Styrka: (15+12)/59 = 45.8%
```

### Styrka-nivåer

| Styrka % | Aktivitet | Betydelse |
|----------|-----------|-----------|
| 0-20% | LÅG | Risk-on läge - ingen flykt |
| 20-50% | MÅTTLIG | Viss försiktighet |
| 50-80% | HÖG | Stark flykt till säkerhet |
| 80-100% | EXTREM | TOTAL kapitalflykt pågår |

### Kapitalflykt-detection

**Kriterier:**
- Safe Haven Styrka > 30%
- OCH S&P 500 signal = RED

**När detta händer:**
🚨 **KAPITALFLYKT DETEKTERAD** - Smart money lämnar aktier!

---

## 4. Systemrisk-Poäng (0-100)

Kombinerar alla tre indikatorer i ett enda mått:

### Poäng-sammansättning

| Komponent | Max Poäng |
|-----------|-----------|
| Market Regime (CRISIS/HEALTHY) | 40 |
| Yield Curve Inversion | 30 |
| Credit Spreads | 20 |
| Safe Haven Activity | 10 |
| **TOTALT** | **100** |

### Risk-nivåer

| Poäng | Risk Level | Rekommendation |
|-------|------------|----------------|
| 0-20 | LÅG | Normal trading, full exponering OK |
| 20-40 | MÅTTLIG | Bevaka läget, håll stop-losses |
| 40-60 | FÖRHÖJD | Reducera positioner, öka cash |
| 60-80 | HÖG | Minimal exponering, aktivera All-Weather |
| 80-100 | EXTREM | Recession trolig, endast safe havens |

---

## Användning i Dashboard

När du kör `python daglig_analys.py` visas automatiskt:

```
================================================================================
🛡️ SAFE HAVEN WATCH
================================================================================

📊 Räntekurva (Yield Curve):
   Kort ränta (^IRX): 3.52%
   Lång ränta (^TNX): 4.16%
   Spread: +0.64%
   Kurvan plattnar ut (+0.64%) - bevaka läget

💰 Kreditspreadar (Corporate vs Treasury):
   Treasury (TLT): -0.41%
   Corporate (LQD): +0.04%
   Spread: -0.45%
   Företagsobligationer starkare än Treasury (spread: -0.5%)

🎯 Safe Haven Aktivitet:
   Analyserade: 59
   GREEN: 3 | YELLOW: 8 | RED: 48
   Styrka: 19%
   Låg safe haven-aktivitet (19%) - risk-on läge

   Top Safe Havens:
      • BND: +0.69%
      • TLT: +0.27%
      • AGG: +0.22%

🚨 SYSTEMRISK-POIÄNG: 42/100
   ⚠️ FÖRHÖJD systemrisk - var försiktig
```

---

## Workflow-integration

### Daglig användning
1. Kör `python daglig_analys.py`
2. Kolla **Systemrisk-Poäng**
3. Om >60: Aktivera All-Weather mode
4. Om >80: Endast safe havens

### Exempel-beslut

**Scenario 1: Låg risk (Poäng 25)**
```
Yield Curve: +1.8% (normal)
Credit Spreads: -0.2% (low stress)
Safe Haven: 12% styrka
→ Trade normalt, full exponering OK
```

**Scenario 2: Förhöjd risk (Poäng 55)**
```
Yield Curve: +0.3% (nästan platt)
Credit Spreads: +3.2% (flight to safety)
Safe Haven: 35% styrka
→ Reducera aktier, öka bonds/guld
```

**Scenario 3: Extrem risk (Poäng 85)**
```
Yield Curve: -0.5% (INVERTERAD)
Credit Spreads: +6.8% (EXTREM flykt)
Safe Haven: 72% styrka
→ Endast All-Weather instruments!
```

---

## Filosofi: "See the Smoke Before the Fire"

Traditionella signaler (Traffic Light, patterns) berättar vad som händer **nu**.

Macro indicators berättar vad som kommer hända **senare**:

1. **Yield Curve** inverterar → 6-18 månader senare: Recession
2. **Credit Spreads** vidgas → 2-6 månader senare: Kreditkris
3. **Safe Haven** aktiveras → Redan pågående: Kapitalflykt

**Use case:**
Även om marknaden ser "HEALTHY" ut (50% GREEN signals), om yield curve är inverterad och credit spreads vidgas → **höj din risk-aversity**!

---

## Teknisk Implementation

### Moduler
- `src/analysis/macro_indicators.py` - Core analysis
- `dashboard.py` - Safe Haven Watch sektion
- Automatisk integration i daglig analys

### Dependencies
- Använder `yfinance` för att hämta ^IRX, ^TNX, TLT, LQD data
- Uppdateras live varje gång dashboard körs
- Ingen manual konfiguration behövs

---

**Co-Authored-By: Warp <agent@warp.dev>**
