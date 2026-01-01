"""
Exempelskript för att köra kvantitativ mönsteranalys.

Detta visar hur man använder analysverktyget.
"""

import numpy as np
from datetime import datetime, timedelta
from src import QuantPatternAnalyzer, MarketData
from src.utils.data_fetcher import DataFetcher


def create_sample_data(n_days: int = 500) -> MarketData:
    """
    Skapar simulerad marknadsdata för demonstration.
    
    Denna funktion är kvar för testing, men main() använder nu riktig data.
    """
    np.random.seed(42)
    
    # Generera tidsstämplar
    start_date = datetime(2022, 1, 1)
    timestamps = np.array([start_date + timedelta(days=i) for i in range(n_days)])
    
    # Generera priser med random walk
    returns = np.random.normal(0.0005, 0.02, n_days)
    close_prices = 100 * np.cumprod(1 + returns)
    
    # Generera OHLC från close
    high_prices = close_prices * (1 + np.abs(np.random.normal(0, 0.01, n_days)))
    low_prices = close_prices * (1 - np.abs(np.random.normal(0, 0.01, n_days)))
    open_prices = np.roll(close_prices, 1)
    open_prices[0] = close_prices[0]
    
    # Generera volym
    volume = np.random.lognormal(15, 1, n_days)
    
    return MarketData(
        timestamps=timestamps,
        open_prices=open_prices,
        high_prices=high_prices,
        low_prices=low_prices,
        close_prices=close_prices,
        volume=volume
    )


def main():
    """Huvudfunktion för att köra analys."""
    
    print("=" * 80)
    print("QUANT PATTERN ANALYZER")
    print("Ett statistiskt observationsinstrument för finansiella marknader")
    print("=" * 80)
    print()
    
    # Marknadsmeny
    print("Välj marknad att analysera:")
    print("1. S&P 500 (USA)")
    print("2. OMX Stockholm 30 (Sverige)")
    print("3. OMX Helsinki 25 (Finland)")
    print("4. OMX Copenhagen 25 (Danmark)")
    print("5. OBX (Norge)")
    print("6. Dow Jones Industrial Average (USA)")
    print("7. NASDAQ Composite (USA)")
    print("8. FTSE 100 (Storbritannien)")
    print("9. Anpassat ticker")
    print()
    
    # Marknadsdefinitioner
    markets = {
        "1": ("^GSPC", "S&P 500"),
        "2": ("^OMX", "OMX Stockholm 30"),
        "3": ("^OMXH25", "OMX Helsinki 25"),
        "4": ("^OMXC25", "OMX Copenhagen 25"),
        "5": ("^OSEAX", "OBX Oslo"),
        "6": ("^DJI", "Dow Jones Industrial Average"),
        "7": ("^IXIC", "NASDAQ Composite"),
        "8": ("^FTSE", "FTSE 100")
    }
    
    # Låt användaren välja
    choice = input("Ditt val (1-9): ").strip()
    
    if choice == "9":
        ticker = input("Ange ticker-symbol (t.ex. AAPL, MSFT): ").strip()
        market_name = ticker
    elif choice in markets:
        ticker, market_name = markets[choice]
    else:
        print(f"Ogiltigt val '{choice}'. Använder S&P 500 som standard.\n")
        ticker, market_name = markets["1"]
    
    period = "2y"  # 2 års historik
    
    print()
    print(f"Hämtar marknadsdata för {market_name} ({ticker}) - {period} historik...")
    
    # Hämta riktig marknadsdata
    data_fetcher = DataFetcher()
    market_data = data_fetcher.fetch_stock_data(ticker, period=period)
    
    if market_data is None:
        print("\nKunde inte hämta marknadsdata. Kontrollera din internetanslutning.")
        print("Kör med simulerad data istället...\n")
        market_data = create_sample_data(n_days=500)
        print(f"Laddat {len(market_data)} dagars simulerad data")
        print(f"Period: {market_data.timestamps[0].date()} till {market_data.timestamps[-1].date()}")
    
    print()
    
    # Initiera analysverktyget
    analyzer = QuantPatternAnalyzer(
        min_occurrences=30,
        min_confidence=0.70,
        forward_periods=1
    )
    
    # Kör analys
    print("Startar mönsteranalys...")
    print()
    analysis_results = analyzer.analyze_market_data(market_data)
    print()
    
    # Visa sammanfattningstabell
    print("SAMMANFATTNING AV SIGNIFIKANTA MÖNSTER")
    print("=" * 80)
    summary_table = analyzer.create_summary_table(analysis_results)
    print(summary_table)
    print()
    
    # Generera detaljerad rapport
    print("DETALJERAD RAPPORT")
    print("=" * 80)
    report = analyzer.generate_report(analysis_results)
    print(report)
    
    # Övervaka mönsters hälsa
    if analysis_results['significant_patterns']:
        print("\n")
        pattern_statuses = analyzer.monitor_patterns(analysis_results)
        monitoring_report = analyzer.generate_monitoring_report(pattern_statuses)
        print(monitoring_report)
    
    # Analysera nuvarande marknadssituation
    print("\n" + "=" * 80)
    print("NUVARANDE MARKNADSSITUATION")
    print("=" * 80)
    current_situation = analyzer.get_current_market_situation(market_data, lookback_window=50)
    
    if current_situation['active_situations']:
        print(f"\nAktiva situationer (baserat på senaste {current_situation['lookback_window']} perioderna):")
        for situation in current_situation['active_situations']:
            print(f"  - {situation['description']}")
        
        # Korrelationsvarning
        if len(current_situation['active_situations']) > 2:
            print("\n[VIKTIGT] Flera signaler aktiva samtidigt:")
            print("Dessa kan vara korrelerade (ej oberoende).")
            print("Kombinera inte deras 'styrka' - risken är double-counting.")
    else:
        print("\nInga speciella situationer identifierade för närvarande.")
    
    print("\n" + "=" * 80)
    print("ANALYS SLUTFÖRD")
    print("=" * 80)
    print("\nOBS: Detta är ett statistiskt observationsinstrument.")
    print("Historiskt beteende är ingen garanti för framtida resultat.")
    print("Inga investeringsrekommendationer ges.")


if __name__ == "__main__":
    main()
