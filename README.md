# 🎲 Quant Pattern Analyzer - Casino-Style Trading System

## What Does This App Do?

This app finds profitable stock trades by **thinking like a casino**. Casinos don't guess—they calculate odds, manage risk, minimize costs, and only play when they have an edge. This system does the same for stock trading.

**Latest additions:**
- 🎯 **800-Ticker Universe** - Expanded from 250 to 800 instruments (Sweden, Nordic neighbors, US, All-Weather)
- 💰 **Fixed ISK Courtage** - Correct Avanza costs (MINI: 1 SEK, SMALL: 7 SEK, MEDIUM: 15 SEK)
- 📊 **Minimum Position Filter** - Blocks trades <50 SEK where courtage makes them unprofitable
- 🚀 **INVESTERBARA vs BEVAKNINGSLISTA** - Clear separation between profitable and blocked signals
- 🇸🇪 **ISK Optimization** - Swedish ISK-specific cost protection (FX, courtage, product health)
- 🛡️ **Execution Cost Guard** - Prevents trades where fees/slippage eat your edge
- 🌪️ **All-Weather Crisis Mode** - 59 defensive instruments for market crashes
- 📊 **Macro Indicators** - Professional risk detection (yield curve, credit spreads, safe haven watch)

---

## The Problem It Solves

**Traditional trading issues:**
- "This stock looks good, should I buy?" (pure guessing)
- "I'm up 10%, should I sell?" (emotional decisions)
- "How much should I invest?" (random position sizing)

**This app answers:**
1. **Should I buy?** (Only when math says odds are in your favor)
2. **How much should I buy?** (Position size based on volatility and edge)
3. **When should I sell?** (Statistical exits, not emotions)

---

## How It Works (Simple Explanation)

### 1. Pattern Detection (Finding Opportunities)
The app scans **800 stocks/ETFs** daily (expanded from 250), looking for **chart patterns** that historically predict price moves:
- Bullish flags (continuation patterns)
- Head & shoulders (reversal patterns)
- Triangles (breakout patterns)
- Double bottoms (reversal patterns)

**Think of it as:** Reading the same "tells" in the market that casinos read in poker players.

---

### 2. Edge Calculation (Are The Odds Good?)
For every pattern found, the app calculates:
- **Win rate:** How often does this pattern win? (e.g., 55% of the time)
- **Win/loss ratio:** When it wins, how much? When it loses, how much? (e.g., +2.5% vs -1.2%)
- **Predicted edge:** Expected profit per trade after accounting for wins AND losses

**Example:**
```
Pattern: Bullish Flag on AAPL
Win rate: 55%
Avg win: +2.5%
Avg loss: -1.2%
Expected edge: +0.84% per trade
```

**Casino analogy:** The house edge in blackjack is ~0.5%. This pattern has +0.84% edge—better than the casino!

---

### 3. Traffic Light System (Simple Buy/Sell Signals)

Every stock gets a color based on its edge:

🟢 **GREEN** - Strong positive edge → BUY
🟡 **YELLOW** - Weak positive edge → MAYBE (watch closely)
🟠 **ORANGE** - Weak negative edge → DON'T BUY
🔴 **RED** - Strong negative edge → SELL (if you own it)

**Think of it as:** A simple "go/no-go" decision system. If it's not GREEN in a healthy market, don't play.

---

### 4. Position Sizing (How Much To Bet)

The app uses **V-Kelly formula** (volatility-adjusted Kelly Criterion) to calculate position size:
- **Higher edge** = larger position
- **Higher volatility** = smaller position (more risk)
- **Lower confidence** = smaller position (less certain)

**Example:**
```
AAPL: 
- Edge: +0.84%
- Volatility: 1.5% (calm)
- Position size: 2.5% of portfolio

NVDA:
- Edge: +1.2%
- Volatility: 3.0% (wild)
- Position size: 1.8% of portfolio (lower due to volatility)
```

**Casino analogy:** Bet more when you have an edge AND the table is predictable. Bet less when the game is chaotic.

---

### 5. Risk Filters (Don't Play Rigged Games)

Before buying, the app checks multiple filters:

**A) Trend Filter**
- Don't buy long if the trend is down (fighting the current)
- Aligns trades with market momentum

**B) Volatility Breakout Filter**
- Detects if volatility is expanding (opportunity) or contracting (risk)
- Adjusts position size based on 4 regimes: STABLE / EXPANDING / EXPLOSIVE / CONTRACTING

**C) Cost-Aware Filter**
- Calculates if your edge is STILL positive after spreads and fees
- Example: +0.5% edge - 0.3% costs = +0.2% net edge (still profitable)

**D) Market Regime Detection**
- Is the overall market HEALTHY or in CRISIS?
- In CRISIS: reduces all positions or exits entirely

**E) Execution Cost Guard** 🆕
- **FX Shield:** Warns if USD/SEK is >+2σ (overvalued) - don't buy at currency top
- **Fee Calculator:** Warns if courtage + spreads >30% of your edge
- **Liquidity Guard:** Warns if your position >2% of daily volume (slippage risk)
- **Product Mapper:** Recommends best Avanza product (avoid daily reset ETFs, prefer low-fee options)
- **Example:** Even if screener says BUY, Execution Guard blocks if fees eat the edge

**F) ISK Optimization** 🇸🇪 (For Swedish Investors)
- **FX-Växlingsvakt:** 3-tier FX costs: Sverige 0%, Norden 0.25%, Övriga 0.5%
- **Tracking Error Filter:** Product health scoring (0-100) - warns for Bull/Bear daily reset >3 days
- **Courtage-trappan (FIXED):** Correct Avanza costs - MINI: 1 SEK min, SMALL: 7 SEK, MEDIUM: 15 SEK
- **Minimum Position:** Blocks positions <50 SEK where courtage would eat >4% of capital
- **Example:** 10 SEK position with 1 SEK courtage = 20% round-trip cost → 🔴 BLOCKERAD

**Casino analogy:** Don't play when the dealer is cheating (costs too high), when the casino is on fire (market crisis), or when the exchange rate is terrible (FX risk).

---

### 6. All-Weather Crisis Mode 🆕

When markets crash (CRISIS regime), most trading stops—but **59 defensive instruments** get **full allocation** (1.0x multiplier vs 0.2x for normal stocks):

**Categories:**
- **Inverse ETFs:** SH, PSQ, DOG, SQQQ, SPXS (profit from market declines)
- **Precious Metals:** GLD, IAU, SLV (safe havens)
- **Bonds:** TLT, IEF, BIL, AGG (flight to safety)
- **Defensive Sectors:** XLU, XLP, XLV (utilities, staples, healthcare)
- **Volatility:** VIXY, VIXM (VIX products)
- **Commodities:** USO, UNG, DBA (real assets)

**Philosophy:** "When the casino is on fire, switch to the fireproof table."

**Example:**
```
Market: CRISIS (90% RED signals)
Regular stocks: 0.2x allocation (minimal)
All-Weather (XLU, TLT, GLD): 1.0x allocation (full)

→ Dashboard prioritizes All-Weather signals first
→ Shows Avanza alternatives (e.g., XACT Bear for SH)
```

---

### 7. Macro Indicators (Professional Risk Detection) 🆕

The system monitors **systemic risk** using three professional indicators:

**A) Yield Curve Inversion**
- Compares ^IRX (13-week T-bill) vs ^TNX (10-year T-note)
- **Inverted curve** (short > long rates) predicts recession
- Historical accuracy: 1989, 2000, 2006, 2019 recessions

**B) Credit Spreads**
- Compares LQD (corporate bonds) vs TLT (treasury bonds)
- **Widening spreads** = capital flight from corporate to safe assets
- Detects credit stress before equity crashes

**C) Safe Haven Watch**
- Monitors all 59 All-Weather instruments
- **>30% GREEN while S&P RED** = capital flight to safety
- Early warning system for market crashes

**Systemic Risk Score:** Combines all three into 0-100 score
- **0-30:** LOW risk
- **31-60:** MEDIUM risk
- **61-80:** HIGH risk
- **81-100:** EXTREME risk

**Philosophy:** "See the smoke before the fire starts."

**Example:**
```
📊 Yield Curve: +0.64% (normal)
💰 Credit Spreads: -0.47% (LOW stress)
🛡️ Safe Haven Activity: 3% (LOW)
🚨 SYSTEMRISK: 50/100 (⚠️ FÖRHÖJD systemrisk)
```

---

### 8. Profit-Targeting (When To Cash Out)

Once you own a stock, the app monitors when to sell using **sigma levels**:

- **+2σ (2 standard deviations):** Price is statistically high → Sell 50%
- **+3σ (3 standard deviations):** Price is VERY statistically high → Sell 100%

**Example:**
```
You bought AAPL at $150
Mean price (20 days): $155
Standard deviation: $5

+2σ level: $165 → If price hits this, sell 50%
+3σ level: $170 → If price hits this, sell remaining 50%

Current price: $168 → You're at +2.6σ → SELL 50% NOW
```

**Casino analogy:** When you're up BIG at the poker table, the odds say "cash out before variance brings you back down."

---

### 9. Monte Carlo Simulation (System Validation)

Quarterly, you run 10,000 simulated futures based on your actual trading stats:
- What's the risk of a 20% drawdown?
- What's the median expected return?
- What's the worst-case scenario (5th percentile)?

**Think of it as:** Stress-testing your entire system. Like a casino running simulations to ensure they won't go bankrupt even in bad scenarios.

---

## The Three Commands You Use

### Daily (2 minutes)
```bash
python dashboard.py
```
**Shows:** 
- **🚀 INVESTERBARA:** Signals with positive net edge after ALL costs (courtage, FX, spread)
- **📋 BEVAKNINGSLISTA:** Technical signals blocked by costs (monitor for better entry)
- Market regime, All-Weather opportunities, systemic risk

**Action:** Buy only from INVESTERBARA list - these are mathematically profitable after fees

---

### Weekly (15 minutes, every Sunday)
```bash
python veckovis_analys.py
```
**Shows:** 
- What changed since last week (new GREEN, new RED)
- Exit checks for your positions (profit-targeting)

**Action:** 
- Buy new GREEN signals
- Sell RED signals
- Take profits at +2σ / +3σ

---

### Quarterly (30 minutes, 4 times per year)
```bash
python kvartalsvis_analys.py
```
**Shows:**
- Which patterns worked over 3 months
- Which patterns stopped working
- System risk validation (Monte Carlo)

**Action:**
- Adjust which patterns to trust
- Adjust position sizing (Kelly fraction)

---

## Real-World Example

**Monday morning:**
```bash
python dashboard.py
```

**Output:**
```
✅ 2 INVESTERBARA | 📋 3 PÅ BEVAKNING

🚀 INVESTERBARA (Matematiskt lönsamma efter alla avgifter)

1. MSFT (Microsoft)
   Signal: GREEN
   Teknisk Edge: +1.20%
   Position: 3.0%
   🛡️ EXECUTION GUARD: 🟢 LOW
      • Total kostnad: 0.62%
      • Net Edge efter execution: +0.58%
      🇸🇪 ISK: Utländsk aktie | Net edge: 0.58%
   Entry: ENTER

2. BILI-A.ST (Bilia)
   Signal: GREEN
   Teknisk Edge: +2.50%
   Position: 1.2%
   🛡️ EXECUTION GUARD: 🟢 LOW
      • Total kostnad: 0.38%
      • Net Edge efter execution: +2.12%
      🇸🇪 ISK: Svensk aktie | Net edge: 2.12%
   Entry: ENTER

📋 BEVAKNINGSLISTA (Teknisk signal men blockerad av kostnader)

• AAPL       | GREEN  | Teknisk: +0.8% | ⚠️ FX-VARNING: Edge efter valutaväxling (0.30%) för låg
• NVDA       | YELLOW | Teknisk: +0.5% | Position för liten (10 SEK) - courtage 20%
• TGT        | YELLOW | Teknisk: +1.2% | ⚠️ FX + courtage äter 0.9% av 1.2% edge

MARKET REGIME: HEALTHY
🛡️ Safe Haven Activity: 5% (LOW)
🚨 Systemrisk: 35/100 (LOW)
```

**You do:** Buy ONLY from INVESTERBARA (MSFT 3.0%, BILI-A.ST 1.2%). Ignore BEVAKNINGSLISTA.

---

**Sunday:**
```bash
python veckovis_analys.py
```

**Output:**
```
WEEKLY REPORT:
- AAPL turned RED → SELL
- NVDA new GREEN → BUY

EXIT CHECKS:
🟡 MSFT: $445 (+5.8%) → +2.1σ → SELL 50%
🟢 GOOGL: $155 (+2.0%) → +0.7σ → HOLD
```

**You do:**
- Sell AAPL (turned RED)
- Sell 50% of MSFT (hit +2σ)
- Buy NVDA (new GREEN)
- Hold GOOGL

---

**March (quarterly):**
```bash
python kvartalsvis_analys.py
```

**Output:**
```
PATTERN PERFORMANCE (last 3 months):
✅ Bullish Flags: 62% win rate
✅ Triangles: 58% win rate
❌ Head & Shoulders: 42% win rate (DEGRADED)

RECOMMENDATION:
- Continue trading Flags and Triangles
- Stop trading Head & Shoulders
- Run Monte Carlo to validate system risk
```

**You do:**
- Adjust pattern selection
- Run Monte Carlo
- If risk is acceptable, continue trading

---

## What Makes This Different From Guessing?

| **Guessing** | **This App** |
|--------------|--------------|  
| "This stock looks good" | "This pattern has 55% win rate, +0.84% edge" |
| "I'll invest $1000" | "V-Kelly says 2.5% position based on volatility and edge" |
| "I'm up 10%, should I sell?" | "+2σ hit, statistics say sell 50%" |
| "I lost money, bad luck?" | "Monte Carlo shows this is within normal variance" |
| Trading on emotions | Trading on mathematics |

---

## The Casino Philosophy

**Casinos don't:**
- Play games where they have no edge
- Bet their entire bankroll on one game
- Make emotional decisions
- Ignore their own rules

**This app doesn't either:**
- Only trades when edge is positive (GREEN signals)
- Sizes positions based on edge and volatility (V-Kelly)
- Uses statistical exits (sigma levels)
- Validates system quarterly (Monte Carlo)

---

## Technical Stack (For Developers)

**Language:** Python  
**Data Source:** Yahoo Finance (yfinance)  
**Pattern Detection:** Custom algorithms for 15+ chart patterns  
**Statistics:** Bayesian inference, Kelly Criterion, Monte Carlo simulation  
**Position Sizing:** Volatility-adjusted Kelly (V-Kelly)  
**Risk Management:** Multi-layer filters (trend, volatility, cost, regime)

---

## Files You Need To Know

**Daily use:**
- `daglig_analys.py` - Find buy signals
- `my_positions.json` - Track what you own (manual entry)

**Weekly use:**
- `veckovis_analys.py` - Delta analysis + exit checks

**Quarterly use:**
- `kvartalsvis_analys.py` - System validation

**Documentation:**
- `ENKEL_GUIDE.md` - Quick start
- `VERSION_2.2_FEATURES.md` - Technical details
- `POSITION_TRACKING.md` - How to track positions
- `ISK_OPTIMIZATION.md` - ISK-specific cost optimization (Swedish investors) 🆕 🇸🇪
- `EXECUTION_COST_GUARD.md` - Minimize hidden costs (FX, fees, spreads, liquidity) 🆕
- `ALL_WEATHER_CRISIS_MODE.md` - 59 defensive instruments for crashes 🆕
- `MACRO_INDICATORS.md` - Professional risk detection 🆕

---

## Installation

### Requirements
- Python 3.8 or later
- pip

### Install Dependencies
```bash
pip install -r requirements.txt
```

**Note:** The app automatically fetches real market data from Yahoo Finance. No API key required.

---

## ISK Optimization (For Swedish Investors) 🇸🇪

If you trade on an **Investeringssparkonto (ISK)** through Avanza, the system protects you from three common ISK traps:

### 1. 🚫 FX-FÄLLAN (Currency Exchange Trap)
**Problem:** Buying foreign stocks when edge < 1.0%  
**Cost:** 0.5% FX roundtrip (0.25% buy + 0.25% sell)  
**Example:**
```
ERO.TO (Canadian mining stock)
Edge before ISK: 0.8%
FX cost: 0.5%
Courtage: 1.56%
Net edge: -1.26% ❌
Recommendation: 🔴 AVSTÅ
```

### 2. 🚫 COURTAGE-FÄLLAN (Minimum Fee Trap) - FIXED ✅
**Problem:** Small positions where minimum courtage eats the edge
**Correct Costs (2024):**
- MINI: 1 SEK min
- SMALL: 7 SEK min  
- MEDIUM: 15 SEK min
**Automatic Protection:** System blocks positions <50 SEK (courtage >4% round-trip)
**Example:**
```
CRISIS regime: V-Kelly says 10 SEK position
Courtage: 1 SEK × 2 = 2 SEK roundtrip (20%)
Edge: 0.8%
Net edge: -19.2% ❌
→ Automatically BLOCKED by minimum position filter
```

### 3. 🚫 URHOLKNINGSFÄLLAN (Daily Reset Trap)
**Problem:** Bull/Bear products with daily rebalancing held >3 days  
**Cost:** ~0.1-0.3% daily decay in sideways markets  
**Example:**
```
Bull Guld X2 (10 days holding)
Product Health: 20/100
Daily reset warning: ⚠️ Urholkningsrisk
Recommendation: Switch to physical ETF (GZUR)
```

### ISK Best Practices
✅ **Swedish stocks** (0% FX costs - prioritize these!)  
✅ **Nordic neighbors** (Norge/Finland/Danmark: 0.25% FX cost vs 0.5% for USA)
✅ **Positions ≥50 SEK** (automatic minimum - system protects you)
✅ **MINI courtage** (1 SEK min) - efficient for positions >100 SEK
✅ **Physical ETFs** for long-term (low holding costs)  
✅ **Only trade INVESTERBARA** - ignore BEVAKNINGSLISTA (costs too high)

**See `ISK_OPTIMIZATION.md` for full details.**

---

## Summary

**What it does:** Finds profitable trades using math, not emotions  
**How it works:** Detects patterns → Calculates edge → Filters risk → Sizes positions → Exits statistically  
**Why it works:** Same philosophy casinos use (play with an edge, manage risk, ignore emotions)  
**How you use it:** 3 simple commands (daily, weekly, quarterly)  

**The goal:** Trade like a casino, not like a gambler.

---

## Important Disclaimers

- **This is NOT investment advice**: The tool provides statistical analysis, not recommendations
- **Historical data guarantees nothing**: Patterns that worked historically can stop working at any time
- **Trading involves risk**: You can lose money. Only trade with capital you can afford to lose
- **Data quality is critical**: Incorrect or incomplete data produces misleading results

---

## Use Cases

**This tool is suitable for:**
- Quantitative analysts seeking statistical patterns
- Researchers studying market structure
- Educational purposes to understand market behavior
- Systematic traders who value mathematical edges

**This tool is NOT suitable for:**
- Direct investment decisions without deeper analysis
- Real-time trading without extensive validation
- Users without understanding of statistical analysis
- Emotional or impulsive trading decisions

---

**Co-Authored-By: Warp <agent@warp.dev>**
