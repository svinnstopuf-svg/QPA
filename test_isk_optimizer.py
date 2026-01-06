"""
Test ISK Optimizer - Tre scenarion
===================================

1. ERO.TO - Kanadensisk aktie med FX-kostnad
2. Liten position - Courtage äter edge
3. Bull certifikat - Urholkningsrisk
"""

from src.risk.isk_optimizer import ISKOptimizer, CourtageTier, format_isk_report


def test_scenario_1_foreign_stock():
    """Scenario 1: Kanadensisk aktie (ERO.TO) - FX-kostnad"""
    print("\n" + "=" * 80)
    print("SCENARIO 1: ERO.TO (Ero Copper, Kanada)")
    print("=" * 80)
    
    optimizer = ISKOptimizer(
        courtage_tier=CourtageTier.MINI,
        portfolio_size=100000,
    )
    
    result = optimizer.optimize(
        ticker="ERO.TO",
        expected_edge=0.008,  # 0.8% edge
        position_size_sek=5000,
        holding_period_days=5,
        product_name="Ero Copper Corp",
    )
    
    print(format_isk_report(result))
    print(f"\n💡 ANALYS:")
    print(f"Edge före ISK: 0.80%")
    print(f"FX-kostnad: {result.fx_conversion_cost_pct:.2%}")
    print(f"Courtage: {result.courtage_pct * 2:.2%} (roundtrip)")
    print(f"Net edge: {result.net_edge_after_isk:.2%}")
    print(f"\nKonklusion: Edge är för låg efter FX-växling!")


def test_scenario_2_small_position():
    """Scenario 2: Liten position (2000 SEK) - Courtage äter edge"""
    print("\n\n" + "=" * 80)
    print("SCENARIO 2: Liten position (2000 SEK)")
    print("=" * 80)
    
    optimizer = ISKOptimizer(
        courtage_tier=CourtageTier.MINI,
        portfolio_size=100000,
    )
    
    result = optimizer.optimize(
        ticker="AAPL",
        expected_edge=0.012,  # 1.2% edge
        position_size_sek=2000,
        holding_period_days=5,
        product_name="Apple Inc",
    )
    
    print(format_isk_report(result))
    print(f"\n💡 ANALYS:")
    print(f"Edge före ISK: 1.20%")
    print(f"Courtage per trade: {result.courtage_cost_sek:.0f} SEK ({result.courtage_pct:.2%})")
    print(f"Courtage roundtrip: {result.courtage_cost_sek * 2:.0f} SEK ({result.courtage_pct * 2:.2%})")
    print(f"FX-kostnad: {result.fx_conversion_cost_pct:.2%}")
    print(f"Net edge: {result.net_edge_after_isk:.2%}")
    print(f"\nKonklusion: Minsta courtage (39 SEK) äter nästan 2% av positionen!")
    print(f"Rekommendation: Öka till minst {result.courtage_cost_sek / 0.005:.0f} SEK")


def test_scenario_3_leveraged_certificate():
    """Scenario 3: Bull certifikat med hävstång - Urholkningsrisk"""
    print("\n\n" + "=" * 80)
    print("SCENARIO 3: Bull Guld X2 (Hävstång)")
    print("=" * 80)
    
    optimizer = ISKOptimizer(
        courtage_tier=CourtageTier.MINI,
        portfolio_size=100000,
    )
    
    result = optimizer.optimize(
        ticker="BULL-GOLD-X2.ST",
        expected_edge=0.015,  # 1.5% edge
        position_size_sek=10000,
        holding_period_days=10,  # Längre innehavstid
        product_name="Bull Guld X2 Avanza",
    )
    
    print(format_isk_report(result))
    print(f"\n💡 ANALYS:")
    print(f"Edge före ISK: 1.50%")
    print(f"Product Health Score: {result.product_health_score}/100")
    print(f"Innehavskostnad: {result.holding_cost_pct_per_year:.2%}/år")
    print(f"Holding period: 10 dagar")
    print(f"Net edge: {result.net_edge_after_isk:.2%}")
    print(f"\nKonklusion: Daglig ombalansering riskerar urholkning i sidledes marknad!")
    print(f"Rekommendation: Byt till fysiskt backad ETF för längre trades")


def test_scenario_4_swedish_stock():
    """Scenario 4: Svensk aktie - Optimalt för ISK"""
    print("\n\n" + "=" * 80)
    print("SCENARIO 4: NOVO-B.ST (Novo Nordisk, Sverige)")
    print("=" * 80)
    
    optimizer = ISKOptimizer(
        courtage_tier=CourtageTier.MINI,
        portfolio_size=100000,
    )
    
    result = optimizer.optimize(
        ticker="NOVO-B.ST",
        expected_edge=0.015,  # 1.5% edge
        position_size_sek=10000,
        holding_period_days=5,
        product_name="Novo Nordisk B",
    )
    
    print(format_isk_report(result))
    print(f"\n💡 ANALYS:")
    print(f"Edge före ISK: 1.50%")
    print(f"FX-kostnad: {result.fx_conversion_cost_pct:.2%} (ingen - svensk aktie)")
    print(f"Courtage: {result.courtage_pct * 2:.2%} (roundtrip)")
    print(f"Product Health: {result.product_health_score}/100")
    print(f"Net edge: {result.net_edge_after_isk:.2%}")
    print(f"\nKonklusion: Svensk aktie = lägsta ISK-kostnader! ✅")


if __name__ == "__main__":
    print("=" * 80)
    print("ISK OPTIMIZER - TESTSCENARIER")
    print("=" * 80)
    print("\nTestar tre scenarion där ISK-kostnader påverkar handelsbeslut:")
    print("1. Utländsk aktie med FX-växlingskostnad")
    print("2. För liten position där courtage äter edge")
    print("3. Hävstångsprodukt med urholkningsrisk")
    print("4. Svensk aktie (optimalt för ISK)")
    
    test_scenario_1_foreign_stock()
    test_scenario_2_small_position()
    test_scenario_3_leveraged_certificate()
    test_scenario_4_swedish_stock()
    
    print("\n\n" + "=" * 80)
    print("SAMMANFATTNING")
    print("=" * 80)
    print("""
ISK-optimering hjälper dig undvika tre vanliga misstag:

1. 🚫 FX-FÄLLAN
   - Köpa utländska aktier när edge < 1.0%
   - FX-växling kostar 0.5% (0.25% köp + 0.25% sälj)
   - Lösning: Sök svenska alternativ eller öka edge

2. 🚫 COURTAGE-FÄLLAN  
   - För små positioner där minimicourtage (39 SEK) äter >0.5% av beloppet
   - Exempel: 2000 SEK position → 78 SEK courtage (3.9%)
   - Lösning: Öka position till minst 7800 SEK eller avstå

3. 🚫 URHOLKNINGSFÄLLAN
   - Bull/Bear-produkter med daglig ombalansering
   - Läcker pengar i sidledes marknader
   - Lösning: Använd endast för korta trades (<3 dagar)

✅ BÄSTA PRAXIS FÖR ISK:
   - Svenska aktier = inga FX-kostnader
   - Positioner > 7800 SEK = effektivt courtage
   - Fysiskt backade ETF:er = låga innehavskostnader
   - Edge efter ISK > 1.0% = hållbar strategi
""")
    
    print("=" * 80)
    print("TEST SLUTFÖRT")
    print("=" * 80)
