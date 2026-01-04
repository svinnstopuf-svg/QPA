# 🎲 Quant Pattern Analyzer - Casino-Style Trading System

## What Does This App Do?

This app finds profitable stock trades by **thinking like a casino**. Casinos don't guess—they calculate odds, manage risk, and only play when they have an edge. This system does the same for stock trading.

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
The app scans 250 stocks/ETFs daily, looking for **chart patterns** that historically predict price moves:
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

**Casino analogy:** Don't play when the dealer is cheating (costs too high) or when the casino is on fire (market crisis).

---

### 6. Profit-Targeting (When To Cash Out)

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

### 7. Monte Carlo Simulation (System Validation)

Quarterly, you run 10,000 simulated futures based on your actual trading stats:
- What's the risk of a 20% drawdown?
- What's the median expected return?
- What's the worst-case scenario (5th percentile)?

**Think of it as:** Stress-testing your entire system. Like a casino running simulations to ensure they won't go bankrupt even in bad scenarios.

---

## The Three Commands You Use

### Daily (2 minutes)
```bash
python daglig_analys.py
```
**Shows:** Buy signals today, top opportunities, market regime
**Action:** Buy if GREEN signals exist in HEALTHY market

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
python daglig_analys.py
```

**Output:**
```
🟢 AAPL - Bullish Flag
   Edge: +0.84%
   V-Kelly Position: 2.5%
   Signal: BUY

🟢 MSFT - Ascending Triangle
   Edge: +1.2%
   V-Kelly Position: 3.0%
   Signal: BUY

MARKET REGIME: HEALTHY
→ 2 buy signals today
```

**You do:** Buy AAPL (2.5% of portfolio) and MSFT (3.0% of portfolio)

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
