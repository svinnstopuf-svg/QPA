import yfinance as yf
from datetime import datetime

# Test with a common ticker
print("Testing Yahoo Finance API connectivity...")
print("=" * 60)

tickers = ["AAPL", "CALM", "AWK", "CEG", "TREX", "KBH"]

for ticker_symbol in tickers:
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="5d")
        
        if hist.empty:
            print(f"{ticker_symbol}: ❌ NO DATA (empty DataFrame)")
        else:
            latest_date = hist.index[-1]
            latest_close = hist['Close'].iloc[-1]
            age_days = (datetime.now() - latest_date).days
            print(f"{ticker_symbol}: ✅ {latest_date.strftime('%Y-%m-%d')} | ${latest_close:.2f} | {age_days} days old")
    except Exception as e:
        print(f"{ticker_symbol}: ❌ ERROR - {str(e)[:50]}")

print("=" * 60)
