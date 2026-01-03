"""
Quick test för Version 2.0 förbättringar
Testar med färre instrument för snabbare körning
"""

import sys
from instrument_screener import InstrumentScreener, format_screener_report

def main():
    # Test med bara några instrument från olika kategorier
    instruments = [
        # Index
        ("^OMX", "OMX Stockholm 30", "index_etf"),
        ("^GSPC", "S&P 500", "index_etf"),
        
        # Svenska aktier
        ("VOLV-B.ST", "Volvo B", "stock_swedish"),
        ("ERIC-B.ST", "Ericsson B", "stock_swedish"),
        
        # US Tech
        ("AAPL", "Apple", "stock_us_tech"),
        ("MSFT", "Microsoft", "stock_us_tech"),
        
        # US Defensive
        ("JNJ", "Johnson & Johnson", "stock_us_defensive"),
        ("KO", "Coca-Cola", "stock_us_defensive"),
        
        # US Finance
        ("JPM", "JPMorgan Chase", "stock_us_finance"),
        ("V", "Visa", "stock_us_finance"),
    ]
    
    # Initiera screener
    screener = InstrumentScreener(
        min_data_years=5.0,
        min_avg_volume=50000,
        max_beta=1.5
    )
    
    # Kör screening
    results = screener.screen_instruments(instruments)
    
    # Visa resultat
    if results:
        report = format_screener_report(results)
        print("\n\n")
        print(report)
    else:
        print("\n❌ Inga instrument uppfyllde kriterierna.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
