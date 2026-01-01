"""
Exempelskript för att köra kvantitativ mönsteranalys.

Detta visar hur man använder analysverktyget.
"""

import numpy as np
from datetime import datetime, timedelta
from src import QuantPatternAnalyzer, MarketData


def create_sample_data(n_days: int = 500) -> MarketData:
    """
    Skapar simulerad marknadsdata för demonstration.
    
    I en verklig applikation skulle detta läsas från en datakälla
    som CSV, databas, eller API.
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
    
    # Skapa eller ladda marknadsdata
    print("Laddar marknadsdata...")
    market_data = create_sample_data(n_days=500)
    print(f"Laddat {len(market_data)} dagars data")
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
    
    # Analysera nuvarande marknadssituation
    print("\n" + "=" * 80)
    print("NUVARANDE MARKNADSSITUATION")
    print("=" * 80)
    current_situation = analyzer.get_current_market_situation(market_data, lookback_window=50)
    
    if current_situation['active_situations']:
        print(f"\nAktiva situationer (baserat på senaste {current_situation['lookback_window']} perioderna):")
        for situation in current_situation['active_situations']:
            print(f"  - {situation['description']}")
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
