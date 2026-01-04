# Quick Start - Instrument Screener V2.2

## 🎰 Casino-Style Risk Improvements

Version 2.2 integrerar **alla** risk management features i ett unified workflow.

---

## Snabbstart (Enklaste sättet)

Kör hela analysen med ett kommando:

```bash
python run_screener_v22.py
```

Detta kör:
1. ✅ Pattern analysis på alla 250 instruments
2. ✅ Traffic Light evaluation (4-tier system)
3. ✅ V-Kelly position sizing (ATR-adjusted)
4. ✅ Trend filter (200-day MA)
5. ✅ Regime detection (market stress)
6. ✅ **Volatility Breakout Filter** (V2.2)
7. ✅ **Cost-Aware Edge Filter** (V2.2)
8. ✅ Final recommendations med entry timing

Output:
- Console report med top opportunities
- `screener_v22_results.txt` - Full report
- `screener_v22_detailed.csv` - Detaljerad data (optional)

---

## Manuell Körning (Mer Kontroll)

```python
from instrument_screener_v22 import InstrumentScreenerV22, format_v22_report
from instruments_universe import get_instruments_universe

# 1. Initialize screener
screener = InstrumentScreenerV22(
    min_data_years=5.0,
    min_avg_volume=50000,
    enable_v22_filters=True  # V2.2 features
)

# 2. Get instruments
instruments = get_instruments_universe()  # 250 instruments

# 3. Run analysis
results = screener.screen_instruments(instruments)

# 4. Display report
print(format_v22_report(results))

# 5. Access individual results
for r in results[:5]:  # Top 5
    print(f"{r.name}: {r.entry_recommendation}")
    print(f"  Net Edge: {r.net_edge_after_costs:.2f}%")
    print(f"  Final Allocation: {r.final_allocation:.2f}%")
    print(f"  Volatility Regime: {r.volatility_regime}")
```

---

## Output Förklaring

### Entry Recommendations

| Recommendation | Betydelse | Action |
|---------------|-----------|--------|
| **ENTER - Strong entry conditions** | Alla filters godkända | Köp enligt final_allocation |
| **CAUTIOUS - Medium breakout** | Okej men inte optimal timing | Mindre position eller vänta |
| **WAIT - Low breakout confidence** | Signal ok men volatility låg | Vänta på ATR-expansion |
| **BLOCK - Below 200-day MA** | Under trend | Hoppa över |
| **BLOCK - Negative net edge** | Kostnader > edge | Hoppa över |

### Signal Distribution

- **GREEN**: Stark positiv signal (3-5% base allocation)
- **YELLOW**: Måttlig positiv (1-3% base allocation)  
- **ORANGE**: Neutral (0-1% base allocation)
- **RED**: Negativ (0% allocation)

### Key Metrics

```
Net Edge = Predicted Edge - Trading Costs
Final Allocation = V-Kelly Position × Regime Multiplier × Breakout Adjustment
```

---

## Exempel: Tolka Ett Resultat

```
Rank 1: Zscaler Inc
Signal: GREEN
Net Edge: +0.85%  (efter costs)
Final Allocation: 2.1%  (after all filters)
Volatility Regime: EXPANDING
Entry: ENTER - Strong entry conditions
```

**Tolkning:**
- ✅ GREEN signal → stark positiv momentum
- ✅ Net edge +0.85% → profitabel efter costs
- ✅ EXPANDING volatility → bra entry timing
- ✅ Alla filters godkända → köp 2.1% av portfolio

---

## Jämförelse: V2.0 vs V2.1 vs V2.2

### V2.0 (Original)
```python
# Endast traffic light
if signal == GREEN:
    buy 3-5%
```

### V2.1 (Risk Controls)
```python
# + V-Kelly, Trend, Regime
if signal == GREEN and above_200ma:
    buy v_kelly_position * regime_multiplier
```

### V2.2 (Casino-Style)
```python
# + Volatility Breakout, Cost Filter
if signal == GREEN and above_200ma and net_edge > 0 and high_breakout:
    buy v_kelly_position * regime_multiplier
else:
    wait or block
```

**Resultat:** Färre trades, men mycket högre quality.

---

## Disable V2.2 Filters (Fallback)

Om du vill köra utan V2.2 features:

```python
screener = InstrumentScreenerV22(
    enable_v22_filters=False  # Only V2.0 + V2.1
)
```

Detta skippar:
- Volatility Breakout Filter
- Cost-Aware Edge Filter

Användbara om data är inkomplett eller för snabbare testing.

---

## Advanced: Individuella Modules

### Cost-Aware Filter (Standalone)

```python
from src.risk.cost_aware_filter import CostAwareFilter

filter = CostAwareFilter()
analysis = filter.analyze_edge_after_costs(
    predicted_edge=0.8,
    ticker="SBB-B.ST",
    category="small_cap",
    position_size=10000
)

print(f"Net Edge: {analysis.net_edge:+.2f}%")
print(f"Profitable: {analysis.profitable}")
```

### Volatility Breakout (Standalone)

```python
from src.entry.volatility_breakout import VolatilityBreakoutFilter

filter = VolatilityBreakoutFilter()
analysis = filter.analyze_breakout(
    ticker="AAPL",
    prices=price_data,
    volumes=volume_data
)

print(f"Regime: {analysis.breakout_regime.value}")
print(f"Entry Confidence: {analysis.entry_confidence.value}")
```

### Monte Carlo (Quarterly Review)

```python
from src.analysis.monte_carlo import MonteCarloSimulator, TradingStats

stats = TradingStats(
    win_rate=0.55,
    avg_win=2.5,
    avg_loss=-1.2,
    num_trades=50,
    kelly_fraction=0.25
)

sim = MonteCarloSimulator()
result = sim.run_simulation(stats, num_simulations=10000)

print(f"Median Return: {result.median_return:.1f}%")
print(f"Prob(DD > 20%): {result.prob_20pct_dd*100:.1f}%")
```

### Profit Targeting (During Trade)

```python
from src.exit.profit_targeting import ProfitTargetingSystem

system = ProfitTargetingSystem(lookback_period=20)
target = system.calculate_profit_targets(prices)

exit_rec = system.check_exit_signal(current_price, target)
print(exit_rec.message)  # "EXIT 50% at +2σ" or "HOLD"
```

---

## Troubleshooting

### "No module named matplotlib"
Monte Carlo plotting kräver matplotlib. Installera:
```bash
pip install matplotlib
```
Eller skippa plotting - simulation fungerar ändå.

### "Data fetch failed"
Vissa instruments saknar 5 års data. Detta är normalt - de skippas automatiskt.

### "Breakout filter failed"
Vissa instruments har för korta volym-serier. Filter fallback till N/A.

---

## Nästa Steg

1. **Kör analysen:** `python run_screener_v22.py`
2. **Granska TOP OPPORTUNITIES:** Focus på "ENTER" recommendations
3. **Validera individuellt:** Djupdyk i 2-3 top candidates
4. **Quarterly Review:** Kör Monte Carlo på dina faktiska trades
5. **During Trade:** Använd Profit Targeting för exits

---

## Dokumentation

- `VERSION_2.2_FEATURES.md` - Detaljerad feature-guide
- `VERSION_2.1_FEATURES.md` - V2.1 risk controls
- `VERSION_2.0_COMPLETE.md` - V2.0 foundation
- `REPORTING_GUIDE.md` - Weekly/quarterly reports

---

**Filosofi:** "Kasinot vet exakt vad de kan förlora. Nu vet du också det."

**Co-Authored-By: Warp <agent@warp.dev>**
