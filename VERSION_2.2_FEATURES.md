# Version 2.2 - Casino-Style Risk Improvements

**Datum:** 2025-01-XX  
**Status:** ✅ Complete (4/4 features)  
**Theme:** "Kasinot vet exakt vad de kan förlora"

---

## 🎰 Overview

Version 2.2 lägger till fyra "kasino-inspirerade" förbättringar som förstärker risk management och edge-awareness:

1. ✅ **Volatility Breakout Filter** - Endast in när oddsen är tydliga
2. ✅ **Profit-Targeting med Sigmas** - Matematisk exit-disciplin
3. ✅ **Monte Carlo Simulation** - Validera risk och Kelly-faktor
4. ✅ **Cost-Aware Edge Filter** - Räkna med driftskostnader

Dessa features följer kasinots princip: **"Trade inte om oddsen är mot dig efter costs."**

---

## 1. Volatility Breakout Filter ✅

**Modul:** `src/entry/volatility_breakout.py`

### Problem
Ett kasino tjänar pengar när oddsen är tydliga. Inom trading är oddsen oftast som bäst när marknaden går från "stilla" till "explosiv". Men många signaler kommer när volatiliteten är låg och vag - vilket leder till whipsaws.

### Lösning
Lägg till ett filter som känner av ATR-expansion. Om du får en GREEN-signal, men aktien knappt rör sig (låg volym och låg ATR-förändring), väntar du. Du vill bara gå in när volatiliteten börjar öka i signalens riktning.

### Implementation

```python
from src.entry.volatility_breakout import VolatilityBreakoutFilter

# Initialize filter
breakout_filter = VolatilityBreakoutFilter(
    atr_lookback=14,
    expansion_threshold=0.05,  # 5% ATR increase
    explosive_threshold=0.20,   # 20% ATR increase
    volume_multiplier=1.2       # 1.2x average volume
)

# Analyze breakout potential
analysis = breakout_filter.analyze_breakout(
    ticker="AAPL",
    prices=price_data,
    volumes=volume_data
)

print(f"Regime: {analysis.breakout_regime.value}")
print(f"Entry Confidence: {analysis.entry_confidence.value}")
print(f"Recommendation: {analysis.recommendation}")
```

### Regimes

| Regime | ATR Change | Volume | Action |
|--------|-----------|---------|---------|
| **CONTRACTING** | Decreasing | Any | ❌ BLOCK - Whipsaw risk |
| **STABLE** | -5% to +5% | Normal | ⚠️ CAUTIOUS - Wait for catalyst |
| **EXPANDING** | +5% to +20% | >1.2x avg | ✅ ENTER - Good entry timing |
| **EXPLOSIVE** | >+20% | >1.2x avg | 🚀 AGGRESSIVE - Strong momentum |

### Why This Works
1. **Whipsaw Prevention:** Låg volatilitet = osäker riktning → vänta
2. **Momentum Confirmation:** ATR-expansion + volym = kraft bakom rörelsen
3. **Timing Edge:** In när oddsen är bäst, inte när marknaden sover

### Example Output
```
================================================================================
VOLATILITY BREAKOUT ANALYSIS - AAPL
================================================================================

📊 VOLATILITY METRICS
--------------------------------------------------------------------------------
Current ATR: 2.45
Previous ATR: 2.10
ATR Change: +16.67%

Volume (5d avg): 85.2M
Today's Volume: 102.4M
Volume Ratio: 1.20x

🎯 BREAKOUT ASSESSMENT
--------------------------------------------------------------------------------
Regime: EXPANDING
Entry Confidence: HIGH
Recommendation: ✅ STRONG ENTRY - Expanding volatility + volume confirmation

⚡ ENTRY TIMING
--------------------------------------------------------------------------------
✅ ATR expanding (>5%)
✅ Volume confirmation (>1.2x)
✅ Regime supports entry

Signal: ENTER POSITION
```

---

## 2. Profit-Targeting med Standardavvikelser ✅

**Modul:** `src/exit/profit_targeting.py`

### Problem
Många gör felet att de säljer för tidigt eller för sent. Ett kasino vet exakt när spelet är slut.

### Lösning
Istället för att bara sälja när signalen blir RED, använd Standardavvikelser (Sigmas) för att skala ut vinst. Om en aktie rör sig +2 eller +3 standardavvikelser från sitt medelvärde på kort tid, är sannolikheten för en rekyl extremt hög.

### Implementation

```python
from src.exit.profit_targeting import ProfitTargetingSystem

# Initialize system
system = ProfitTargetingSystem(
    lookback_period=20,   # 20-day mean/std calculation
    sigma_2_exit=0.5,     # Exit 50% at +2σ
    sigma_3_exit=1.0      # Exit 100% at +3σ
)

# Calculate profit targets
target = system.calculate_profit_targets(prices)

print(f"Mean Price: {target.mean_price:.2f}")
print(f"+2σ Target: {target.sigma_2_level:.2f} (50% exit)")
print(f"+3σ Target: {target.sigma_3_level:.2f} (100% exit)")

# Check exit signal
current_price = prices.iloc[-1]
exit_rec = system.check_exit_signal(current_price, target)
print(exit_rec.message)
```

### Exit Strategy

| Sigma Level | Action | Reasoning |
|------------|--------|-----------|
| **+2σ** | Exit 50% | Statistiskt osannolikt att fortsätta (>95% av rörelser inom ±2σ) |
| **+3σ** | Exit 100% | Extremt osannolikt - ta hem allt |

### Why This Works
1. **Mathematical Foundation:** 95% av prisrörelser inom ±2σ i normalfördelning
2. **Mean Reversion:** Extrema rörelser tenderar att revertera
3. **Take Profit When Odds Turn:** Vid +2σ är oddsen mot fortsatt uppgång
4. **Psychological Discipline:** Eliminerar "ska jag sälja nu?"-tvivel

### Example
```
Aktie: 100 kr (mean), std dev = 5 kr

+2σ Level = 110 kr → Sälj 50%
+3σ Level = 115 kr → Sälj 100%

Vid 110 kr:
- Tar hem 50% av vinsten (+10%)
- Låter resten löpa för att fånga +15% eller mer
```

### Integration with Screener
- **Screener:** Ger GREEN signal → Köp
- **Profit-Targeting:** Säger när du ska sälja (statistiskt)
- **Traffic Light RED:** Alternativ exit trigger

**Note:** Detta är en TRADING-strategi, inte screening. Används när du är i en position.

---

## 3. Monte Carlo Simulation ✅

**Modul:** `src/analysis/monte_carlo.py`

### Problem
"Hur stor är risken att jag förlorar 20% av mitt kapital trots att jag har en edge?"

### Lösning
Detta är den ultimata uppgraderingen för din kvartalsvisa genomgång. Mata in din historiska Win-Rate och genomsnittliga vinst/förlust i en Monte Carlo-simulator. Den kör 10,000 simuleringar av din framtid.

### Implementation

```python
from src.analysis.monte_carlo import MonteCarloSimulator, TradingStats

# Define historical statistics
stats = TradingStats(
    win_rate=0.55,        # 55% win rate
    avg_win=2.5,          # Average win: +2.5%
    avg_loss=-1.2,        # Average loss: -1.2%
    num_trades=50,        # 50 trades per period
    kelly_fraction=0.25   # Using 1/4 Kelly
)

# Run simulation
sim = MonteCarloSimulator(
    initial_capital=100000,
    time_periods=252  # 1 year
)

result = sim.run_simulation(stats, num_simulations=10000)

# Print report
print(format_simulation_report(result, stats))

# Generate recommendations
recommendations = sim.generate_recommendations(result, current_kelly_fraction=0.25)
print(recommendations)

# Plot results
sim.plot_simulation_results(result, output_path="monte_carlo_results.png")
```

### Output Metrics

| Metric | Description |
|--------|-------------|
| **Median Return** | Median outcome across 10,000 simulations |
| **5th Percentile** | "Bad year" scenario (5% chance of worse) |
| **95th Percentile** | "Good year" scenario |
| **Worst Drawdown** | Worst observed drawdown across all simulations |
| **Prob(DD > 20%)** | Probability of 20%+ drawdown |
| **Prob(DD > 30%)** | Probability of 30%+ drawdown |
| **Prob(Ruin)** | Probability of >50% loss |

### Why This Works
1. **Risk Quantification:** Exakt sannolikhet för olika drawdowns
2. **Kelly Validation:** Vet om din Kelly-faktor är för aggressiv
3. **Psychological Preparation:** "Förlustsviter är statistiskt förväntade" → lugn
4. **Data-Driven Decisions:** Justera positionsstorlek baserat på simulerad risk

### Example Output
```
================================================================================
MONTE CARLO SIMULATION REPORT
================================================================================

📈 INPUT STATISTICS
--------------------------------------------------------------------------------
Win Rate: 55.0%
Avg Win: +2.50%
Avg Loss: -1.20%
Trades per Period: 50
Kelly Fraction: 0.25

🎲 SIMULATION RESULTS
--------------------------------------------------------------------------------
Median Return: +18.5%
5th Percentile: -5.2%
95th Percentile: +45.8%

Worst Drawdown: 22.3%
Prob(DD > 20%): 15.4%
Prob(DD > 30%): 3.2%
Prob(Ruin): 0.05%

================================================================================
```

### Recommendations Logic

| Prob(DD > 20%) | Action |
|---------------|--------|
| **>30%** | ⚠️ Reduce Kelly (0.25 → 0.18) |
| **15-30%** | ✅ Keep current Kelly |
| **<15%** | 📈 Can increase Kelly (0.25 → 0.30) |

---

## 4. Cost-Aware Edge Filter ✅

**Modul:** `src/risk/cost_aware_filter.py`

### Problem
Din app kan visa att ett mönster i en småbolagsaktie har en edge på 0.8%, men om courtage + spread = 1.0%, så är det en förlustaffär trots att den ser "grön" ut.

### Lösning
Din app bör automatiskt dra av courtage och beräknad spread från den historiska edgen. Kasinot räknar alltid med sina driftskostnader.

### Implementation

```python
from src.risk.cost_aware_filter import CostAwareFilter

# Initialize filter (Avanza Zero = 0 courtage)
cost_filter = CostAwareFilter(
    courtage_per_trade=0.0,      # SEK per trade
    min_courtage=0.0,
    fx_conversion_cost=0.0025    # 0.25% for USD/SEK
)

# Analyze single instrument
analysis = cost_filter.analyze_edge_after_costs(
    predicted_edge=0.8,        # 0.8% predicted edge
    ticker="SBB-B.ST",
    category="small_cap",
    position_size=10000,       # 10k SEK position
    is_foreign=False
)

print(f"Predicted Edge: {analysis.predicted_edge:.2f}%")
print(f"Trading Costs: {analysis.trading_costs.total_pct:.2f}%")
print(f"Net Edge: {analysis.net_edge:+.2f}%")
print(f"Profitable: {analysis.profitable}")
print(f"Recommendation: {analysis.recommendation}")

# Batch analyze multiple instruments
instruments_data = {
    "SBB-B.ST": {"predicted_edge": 0.8, "category": "small_cap", "position_size": 10000},
    "AAPL": {"predicted_edge": 1.2, "category": "large_cap", "position_size": 10000, "is_foreign": True}
}

analyses = cost_filter.batch_analyze_costs(instruments_data)
profitable_only = cost_filter.filter_profitable_only(analyses)

print(format_cost_report(analyses))
```

### Cost Estimates by Instrument Type

| Instrument Type | Spread Estimate | Total Cost (round-trip) |
|----------------|----------------|------------------------|
| **Large Cap** | 0.15% | ~0.30% |
| **Small Cap** | 1.00% | ~2.00% |
| **Index ETF** | 0.10% | ~0.20% |
| **Sector ETF** | 0.20% | ~0.40% |
| **International** | 0.30% + 0.5% FX | ~1.10% |

### Why This Works
1. **Reality Check:** Edge måste överstiga kostnader för att vara lönsam
2. **Prevents False Positives:** Blockerar "gröna" signaler med negativ net edge
3. **Instrument-Aware:** Större spread för småbolag → högre bar för entry
4. **Casino Mindset:** Räkna alltid med driftskostnader

### Example Output
```
================================================================================
COST-AWARE EDGE FILTER
================================================================================

✅ PROFITABLE AFTER COSTS: 8
--------------------------------------------------------------------------------
Ticker     Edge       Costs      Net Edge     Status    
--------------------------------------------------------------------------------
AAPL          1.50%     0.40%      +1.10% ✅
MSFT          1.20%     0.35%      +0.85% ✅
GOOGL         0.90%     0.40%      +0.50% ✅

❌ BLOCKED (Negative Net Edge): 3
--------------------------------------------------------------------------------
Ticker     Edge       Costs      Net Edge     Status    
--------------------------------------------------------------------------------
SBB-B.ST      0.80%     2.00%      -1.20% ❌
XXX.ST        0.60%     2.00%      -1.40% ❌

================================================================================
SAMMANFATTNING
Total: 11 | Profitable: 8 | Blocked: 3
Avg Net Edge (profitable): +0.82%
================================================================================
```

### Integration Example
```python
# Step 1: Screener ger signal
signal = "GREEN"
predicted_edge = 0.8  # %

# Step 2: Check cost-adjusted edge
analysis = cost_filter.analyze_edge_after_costs(
    predicted_edge=predicted_edge,
    ticker="SBB-B.ST",
    category="small_cap"
)

# Step 3: Only enter if net edge > 0
if analysis.profitable:
    print(f"✅ Enter position - Net edge: {analysis.net_edge:+.2f}%")
else:
    print(f"❌ Block trade - Net edge: {analysis.net_edge:+.2f}%")
```

---

## 🎯 Integration Guide

### Full V2.2 Workflow

```python
# 1. Screen for signals (V2.0 + V2.1)
from instrument_screener import screen_instruments
signals = screen_instruments(250)  # Your universe

# 2. Apply Volatility Breakout Filter (V2.2.1)
from src.entry.volatility_breakout import VolatilityBreakoutFilter
breakout_filter = VolatilityBreakoutFilter()

for signal in signals['GREEN']:
    breakout = breakout_filter.analyze_breakout(signal['ticker'], prices, volumes)
    
    if breakout.entry_confidence in ['HIGH', 'EXTREME']:
        # 3. Apply Cost-Aware Filter (V2.2.4)
        from src.risk.cost_aware_filter import CostAwareFilter
        cost_filter = CostAwareFilter()
        
        analysis = cost_filter.analyze_edge_after_costs(
            predicted_edge=signal['edge'],
            ticker=signal['ticker'],
            category=signal['category']
        )
        
        if analysis.profitable:
            print(f"✅ {signal['ticker']}: Enter position")
            print(f"   Net Edge: {analysis.net_edge:+.2f}%")
            print(f"   Breakout: {breakout.breakout_regime.value}")

# 4. During Trade: Monitor Profit Targets (V2.2.2)
from src.exit.profit_targeting import ProfitTargetingSystem
exit_system = ProfitTargetingSystem()

target = exit_system.calculate_profit_targets(prices)
exit_rec = exit_system.check_exit_signal(current_price, target)
print(exit_rec.message)

# 5. Quarterly: Run Monte Carlo (V2.2.3)
from src.analysis.monte_carlo import MonteCarloSimulator, TradingStats

stats = TradingStats(win_rate=0.55, avg_win=2.5, avg_loss=-1.2, num_trades=50)
sim = MonteCarloSimulator()
result = sim.run_simulation(stats, num_simulations=10000)
print(sim.generate_recommendations(result, current_kelly_fraction=0.25))
```

---

## 📊 Feature Comparison

| Feature | V2.0 | V2.1 | V2.2 |
|---------|------|------|------|
| Traffic Light | ✅ | ✅ | ✅ |
| Bayesian Edge | ✅ | ✅ | ✅ |
| V-Kelly Sizing | ❌ | ✅ | ✅ |
| Trend Filter | ❌ | ✅ | ✅ |
| Regime Detection | ❌ | ✅ | ✅ |
| **Volatility Breakout** | ❌ | ❌ | ✅ |
| **Profit Targeting** | ❌ | ❌ | ✅ |
| **Monte Carlo** | ❌ | ❌ | ✅ |
| **Cost-Aware Filter** | ❌ | ❌ | ✅ |

---

## 🧪 Testing

Each module includes comprehensive testing:

```bash
# Test volatility breakout filter
python -m pytest tests/test_volatility_breakout.py

# Test profit targeting
python src/exit/profit_targeting.py

# Test Monte Carlo
python src/analysis/monte_carlo.py

# Test cost-aware filter
python src/risk/cost_aware_filter.py
```

---

## 📚 Documentation Files

- `VERSION_2.0_COMPLETE.md` - Traffic Light, Bayesian, 250 instruments
- `VERSION_2.1_FEATURES.md` - V-Kelly, Trend Filter, Regime Detection
- **`VERSION_2.2_FEATURES.md`** - Casino-Style Risk Improvements (this file)
- `REPORTING_GUIDE.md` - Weekly/Quarterly reporting
- `WHAT_APP_ANALYZES.md` - Complete system overview

---

## 🎓 Key Takeaways

### Casino Principles Applied to Trading

1. **Volatility Breakout:** Trade när oddsen är tydliga, inte i vag marknad
2. **Profit Targeting:** Ta hem vinst vid statistiskt extrema nivåer (+2σ, +3σ)
3. **Monte Carlo:** Kvantifiera risk och validera Kelly-faktor  
4. **Cost-Aware:** Räkna alltid med driftskostnader före entry

### When to Use Each Tool

| Tool | Timing | Purpose |
|------|--------|---------|
| **Volatility Breakout** | Pre-entry | Filter ut whipsaws, vänta på ATR-expansion |
| **Cost-Aware Filter** | Pre-entry | Verifiera att net edge > 0 efter kostnader |
| **Profit Targeting** | During trade | Skala ut vid +2σ, +3σ för mathematisk exit |
| **Monte Carlo** | Quarterly | Validera Kelly-faktor, förstå drawdown risk |

---

## 🚀 Next Steps

Version 2.2 kompletterar risk management-stacken:

```
V2.0: Foundation (Traffic Light, Bayesian, 250 instruments)
V2.1: Risk Controls (V-Kelly, Trend, Regime)
V2.2: Casino-Style Refinements (Entry timing, Exit discipline, Cost awareness, Risk validation)
```

**The System is Now Complete.**

Nästa utveckling kan vara:
- Machine learning för pattern detection
- Options strategies integration
- Real-time alerting system
- Portfolio optimization across correlated positions

Men kärnan är klar: **Edge + Risk Management + Cost Awareness = Kasinots metod.**

---

**Co-Authored-By: Warp <agent@warp.dev>**
