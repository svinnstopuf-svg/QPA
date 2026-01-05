"""
Test All-Weather Crisis Mode
"""
from instrument_screener_v22 import InstrumentScreenerV22
from src.risk.all_weather_config import is_all_weather, get_crisis_multiplier

# Test instruments
test_instruments = [
    ("GLD", "SPDR Gold Trust", "etf_all_weather"),
    ("SH", "ProShares Short S&P500", "etf_all_weather"),
    ("TLT", "iShares 20+ Year Treasury", "etf_broad"),
    ("XLU", "Utilities Select Sector", "etf_sector"),
    ("AAPL", "Apple", "stock_us_tech"),  # Regular stock for comparison
]

print("=" * 80)
print("🛡️ ALL-WEATHER SYSTEM TEST")
print("=" * 80)
print()

# Test 1: All-Weather detection
print("TEST 1: All-Weather Detection")
print("-" * 80)
for ticker, name, cat in test_instruments:
    is_aw = is_all_weather(ticker)
    print(f"{ticker:6} - {name:35} - All-Weather: {'YES' if is_aw else 'NO'}")
print()

# Test 2: Crisis multipliers
print("TEST 2: Crisis Multipliers (base=0.2)")
print("-" * 80)
base_mult = 0.2
for ticker, name, cat in test_instruments:
    mult_green = get_crisis_multiplier(ticker, base_mult, 'GREEN')
    mult_red = get_crisis_multiplier(ticker, base_mult, 'RED')
    print(f"{ticker:6} - GREEN: {mult_green:.1f}x | RED: {mult_red:.1f}x")
print()

# Test 3: Run screening on subset
print("TEST 3: Screening Test")
print("-" * 80)
print("Analyzing All-Weather instruments...")
print()

screener = InstrumentScreenerV22(enable_v22_filters=True)

# Analyze just All-Weather instruments
aw_instruments = [i for i in test_instruments if i[0] in ['GLD', 'SH', 'TLT', 'XLU']]
results = screener.screen_instruments(aw_instruments)

print()
print("=" * 80)
print("RESULTS")
print("=" * 80)
for r in results:
    print(f"{r.ticker:6} - Signal: {r.signal.name:7} - Multiplier: {r.regime_multiplier:.1f}x - Alloc: {r.final_allocation:.2f}%")

print()
print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)
