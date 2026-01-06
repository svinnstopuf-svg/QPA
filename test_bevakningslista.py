"""
Quick test: Verify BEVAKNINGSLISTA shows blocked GREEN/YELLOW signals
"""

import sys
import io

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from instrument_screener_v22 import InstrumentScreenerV22, Signal
from src.risk.execution_guard import ExecutionGuard, AvanzaAccountType
from src.risk.isk_optimizer import CourtageTier

print('=' * 80)
print('SNABBTEST: BEVAKNINGSLISTA med blockerade signaler')
print('=' * 80)
print()

# Test instruments - mix of Swedish, US, and Nordic
test_instruments = [
    ('BILI-A.ST', 'Bilia A', 'stock_se'),
    ('VOLV-B.ST', 'Volvo B', 'stock_se'),
    ('AAPL', 'Apple Inc', 'stock_us_tech'),
    ('MSFT', 'Microsoft', 'stock_us_tech'),
    ('NOVO-B.ST', 'Novo Nordisk B', 'stock_se'),
    ('NOD.OL', 'Nordic Semiconductor', 'stock_nordic'),
    ('ERIC-B.ST', 'Ericsson B', 'stock_se'),
    ('TSLA', 'Tesla', 'stock_us'),
]

print(f'Testar {len(test_instruments)} instrument...\n')

# Initialize
screener = InstrumentScreenerV22(enable_v22_filters=True)
execution_guard = ExecutionGuard(
    account_type=AvanzaAccountType.SMALL,
    portfolio_value_sek=100000,
    use_isk_optimizer=True,
    isk_courtage_tier=CourtageTier.MINI
)

# Screen instruments
results = screener.screen_instruments(test_instruments)

print('STEG 1: Screening Results')
print('-' * 80)
for r in results:
    print(f'{r.ticker:12s} | Signal: {r.signal.name:6s} | Edge: {r.net_edge_after_costs:+.2f}% | '
          f'Alloc: {r.final_allocation:.4f}% | Entry: {r.entry_recommendation[:30]}')
print()

# Apply dashboard logic
print('STEG 2: Dashboard Kategorisering')
print('-' * 80)

# Include all GREEN/YELLOW signals
actionable = [r for r in results if r.signal in [Signal.GREEN, Signal.YELLOW]]
print(f'GREEN/YELLOW signaler: {len(actionable)}')
print()

investable = []
watchlist = []

for r in actionable:
    # Check if signal was already blocked by screener
    if "BLOCK" in r.entry_recommendation or r.final_allocation == 0.0:
        # Skip Execution Guard - already blocked
        watchlist.append(r)
        print(f'  → {r.ticker}: Blockerad av screener (position {r.final_allocation:.4f}%)')
        continue
    
    # Run Execution Guard
    exec_result = execution_guard.analyze(
        ticker=r.ticker,
        category=r.category if hasattr(r, 'category') else 'default',
        position_size_pct=r.final_allocation,
        net_edge_pct=r.net_edge_after_costs,
        product_name=r.name,
        holding_period_days=5
    )
    
    r.exec_result = exec_result
    
    # Categorize
    if exec_result.net_edge_after_execution > 0:
        investable.append(r)
        print(f'  ✅ {r.ticker}: INVESTERBAR (net edge: +{exec_result.net_edge_after_execution:.2f}%)')
    else:
        watchlist.append(r)
        print(f'  📋 {r.ticker}: BEVAKNINGSLISTA (net edge: {exec_result.net_edge_after_execution:.2f}%)')

print()
print('=' * 80)
print(f'RESULTAT: {len(investable)} INVESTERBARA | {len(watchlist)} PÅ BEVAKNING')
print('=' * 80)
print()

if investable:
    print('🚀 INVESTERBARA')
    print('-' * 80)
    for r in investable:
        print(f'  • {r.ticker:12s} | {r.signal.name:6s} | Position: {r.final_allocation:.2f}% | '
              f'Net edge: +{r.exec_result.net_edge_after_execution:.2f}%')
    print()

if watchlist:
    print('📋 BEVAKNINGSLISTA')
    print('-' * 80)
    for r in watchlist:
        # Extract blocking reason
        if "BLOCK" in r.entry_recommendation:
            block_reason = r.entry_recommendation.replace("BLOCK - ", "")
        elif hasattr(r, 'exec_result'):
            exec_result = r.exec_result
            if "AVSTÅ" in exec_result.avanza_recommendation:
                block_reason = exec_result.warnings[0] if exec_result.warnings else "Courtage-spärr"
            else:
                block_reason = "Negativ net edge efter kostnader"
        else:
            block_reason = "Blockerad av filter"
        
        print(f'  • {r.ticker:12s} | {r.signal.name:6s} | Teknisk: {r.net_edge_after_costs:+.1f}% | {block_reason}')
    print()
    print('💡 Dessa har tekniska signaler men blockeras av kostnader.')
else:
    print('📋 BEVAKNINGSLISTA: Tom')

print()
print('✅ Test komplett!')
