"""
Expanded Instrument Universe för Quant Pattern Analyzer
Omfattande lista med 250+ aktier, index, ETF:er som är handelbara via Avanza

Totalt: 250 instrument

Kategorier (13 st):
- index_global: Globala marknadsindex (5)
- index_regional: Regionala index Europa/Asien/Norden (11)
- stock_swedish_large: Svenska storbolag OMXS30 (19)
- stock_swedish_mid: Svenska medelstora bolag (15)
- stock_us_tech: Amerikanska tech-aktier inkl. FAANG+ (35)
- stock_us_defensive: Defensiva aktier - healthcare/staples/utilities (32)
- stock_us_consumer: Konsumentaktier - retail/automotive/travel (21)
- stock_us_finance: Amerikanska finansbolag och betalningslösningar (10)
- stock_us_industrial: Amerikanska industribolag (18)
- stock_us_energy: Amerikanska energibolag (12)
- stock_european: Stora europeiska bolag via ADR (19)
- etf_broad: Breda marknads-ETF:er USA/International/Bonds (24)
- etf_sector: Sektor-ETF:er inkl. specialized (29)

Alla instrument:
- Har minst 5 års historik
- Är tillgängliga via Yahoo Finance
- Kan handlas via Avanza (direkta aktier eller ADR:er)
- Har tillräcklig likviditet (>50k avg daily volume)
"""

# GLOBALA OCH REGIONALA INDEX
GLOBAL_INDICES = [
    # USA
    ("^GSPC", "S&P 500", "index_global"),
    ("^DJI", "Dow Jones Industrial", "index_global"),
    ("^IXIC", "NASDAQ Composite", "index_global"),
    ("^RUT", "Russell 2000", "index_global"),
    ("^VIX", "CBOE Volatility Index", "index_global"),
    
    # Europa
    ("^FTSE", "FTSE 100 (UK)", "index_regional"),
    ("^GDAXI", "DAX (Tyskland)", "index_regional"),
    ("^FCHI", "CAC 40 (Frankrike)", "index_regional"),
    ("^STOXX50E", "EURO STOXX 50", "index_regional"),
    ("^IBEX", "IBEX 35 (Spanien)", "index_regional"),
    
    # Norden
    ("^OMX", "OMX Stockholm 30", "index_regional"),
    ("^OMXH25", "OMX Helsinki 25", "index_regional"),
    ("^OMXC25", "OMX Copenhagen 25", "index_regional"),
    ("^OSEAX", "Oslo Børs (Norge)", "index_regional"),
    
    # Asien & Emerging (kan ha begränsad tillgång)
    ("^N225", "Nikkei 225 (Japan)", "index_regional"),
    ("^HSI", "Hang Seng (Hong Kong)", "index_regional"),
    # Notera: Vissa asiatiska index kan ha begränsad data via Yahoo Finance
    # ("000001.SS", "Shanghai Composite", "index_regional"),  # Ofta problematisk
    # ("^BVSP", "Bovespa (Brasilien)", "index_regional"),  # Kan vara problematisk
]

# SVENSKA STORBOLAG (OMXS30 + andra stora)
SWEDISH_LARGE_CAP = [
    # Industri
    ("VOLV-B.ST", "Volvo B", "stock_swedish_large"),
    ("ATCO-A.ST", "Atlas Copco A", "stock_swedish_large"),
    ("SAND.ST", "Sandvik", "stock_swedish_large"),
    ("SKF-B.ST", "SKF B", "stock_swedish_large"),
    ("ABB.ST", "ABB", "stock_swedish_large"),
    
    # Tech/Telecom
    ("ERIC-B.ST", "Ericsson B", "stock_swedish_large"),
    ("TELIA.ST", "Telia Company", "stock_swedish_large"),
    
    # Finans
    ("SEB-A.ST", "SEB A", "stock_swedish_large"),
    ("SHB-A.ST", "Handelsbanken A", "stock_swedish_large"),
    ("SWED-A.ST", "Swedbank A", "stock_swedish_large"),
    ("INVE-B.ST", "Investor B", "stock_swedish_large"),
    
    # Konsument
    ("HM-B.ST", "H&M B", "stock_swedish_large"),
    ("ESSITY-B.ST", "Essity B", "stock_swedish_large"),
    ("AXFO.ST", "Axfood", "stock_swedish_large"),
    ("ICA.ST", "ICA Gruppen", "stock_swedish_large"),
    
    # Fastighet
    ("SBB-B.ST", "Samhällsbyggnadsbolaget B", "stock_swedish_large"),
    ("WALL-B.ST", "Wallenstam B", "stock_swedish_large"),
    
    # Läkemedel/Hälsa
    ("AZN.ST", "AstraZeneca", "stock_swedish_large"),
    ("GETI-B.ST", "Getinge B", "stock_swedish_large"),
]

# SVENSKA MEDELSTORA BOLAG
SWEDISH_MID_CAP = [
    ("KINV-B.ST", "Kinnevik B", "stock_swedish_mid"),
    ("LUND-B.ST", "Lundbergföretagen B", "stock_swedish_mid"),
    ("NCAB.ST", "NCAB Group", "stock_swedish_mid"),
    ("ELUX-B.ST", "Electrolux B", "stock_swedish_mid"),
    ("ALFA.ST", "Alfa Laval", "stock_swedish_mid"),
    ("ASSA-B.ST", "ASSA ABLOY B", "stock_swedish_mid"),
    ("HEXA-B.ST", "Hexagon B", "stock_swedish_mid"),
    ("EVO.ST", "Evolution", "stock_swedish_mid"),
    ("BOL.ST", "Boliden", "stock_swedish_mid"),
    ("SECU-B.ST", "Securitas B", "stock_swedish_mid"),
    ("ELUX-A.ST", "Electrolux Professional A", "stock_swedish_mid"),
    ("KNOW.ST", "Know IT", "stock_swedish_mid"),
    ("NDA-SE.ST", "Nordea Bank", "stock_swedish_mid"),
    ("SINCH.ST", "Sinch", "stock_swedish_mid"),
    ("CAST.ST", "Castellum", "stock_swedish_mid"),
]

# AMERIKANSKA TECH-GIGANTER
US_TECH = [
    # FAANG+
    ("AAPL", "Apple", "stock_us_tech"),
    ("MSFT", "Microsoft", "stock_us_tech"),
    ("GOOGL", "Alphabet (Google)", "stock_us_tech"),
    ("AMZN", "Amazon", "stock_us_tech"),
    ("META", "Meta (Facebook)", "stock_us_tech"),
    ("NVDA", "Nvidia", "stock_us_tech"),
    ("TSLA", "Tesla", "stock_us_tech"),
    
    # Andra tech-jättar
    ("NFLX", "Netflix", "stock_us_tech"),
    ("ADBE", "Adobe", "stock_us_tech"),
    ("CRM", "Salesforce", "stock_us_tech"),
    ("ORCL", "Oracle", "stock_us_tech"),
    ("INTC", "Intel", "stock_us_tech"),
    ("AMD", "AMD", "stock_us_tech"),
    ("CSCO", "Cisco", "stock_us_tech"),
    ("AVGO", "Broadcom", "stock_us_tech"),
    ("QCOM", "Qualcomm", "stock_us_tech"),
    ("TXN", "Texas Instruments", "stock_us_tech"),
    ("MU", "Micron Technology", "stock_us_tech"),
    ("AMAT", "Applied Materials", "stock_us_tech"),
    ("LRCX", "Lam Research", "stock_us_tech"),
    ("KLAC", "KLA Corporation", "stock_us_tech"),
    ("SNPS", "Synopsys", "stock_us_tech"),
    ("CDNS", "Cadence Design Systems", "stock_us_tech"),
    ("MRVL", "Marvell Technology", "stock_us_tech"),
    ("PANW", "Palo Alto Networks", "stock_us_tech"),
    ("CRWD", "CrowdStrike", "stock_us_tech"),
    ("ZS", "Zscaler", "stock_us_tech"),
    ("NOW", "ServiceNow", "stock_us_tech"),
    ("WDAY", "Workday", "stock_us_tech"),
    ("TEAM", "Atlassian", "stock_us_tech"),
    ("DDOG", "Datadog", "stock_us_tech"),
    ("SNOW", "Snowflake", "stock_us_tech"),
    ("PLTR", "Palantir", "stock_us_tech"),
    ("IBM", "IBM", "stock_us_tech"),
    ("HPE", "Hewlett Packard Enterprise", "stock_us_tech"),
]

# AMERIKANSKA DEFENSIVA AKTIER
US_DEFENSIVE = [
    # Healthcare/Pharma
    ("JNJ", "Johnson & Johnson", "stock_us_defensive"),
    ("UNH", "UnitedHealth Group", "stock_us_defensive"),
    ("PFE", "Pfizer", "stock_us_defensive"),
    ("ABBV", "AbbVie", "stock_us_defensive"),
    ("LLY", "Eli Lilly", "stock_us_defensive"),
    ("BMY", "Bristol-Myers Squibb", "stock_us_defensive"),
    ("MRK", "Merck & Co", "stock_us_defensive"),
    ("GILD", "Gilead Sciences", "stock_us_defensive"),
    ("AMGN", "Amgen", "stock_us_defensive"),
    ("REGN", "Regeneron Pharmaceuticals", "stock_us_defensive"),
    ("VRTX", "Vertex Pharmaceuticals", "stock_us_defensive"),
    ("CVS", "CVS Health", "stock_us_defensive"),
    ("CI", "Cigna", "stock_us_defensive"),
    ("HUM", "Humana", "stock_us_defensive"),
    
    # Consumer Staples
    ("PG", "Procter & Gamble", "stock_us_defensive"),
    ("KO", "Coca-Cola", "stock_us_defensive"),
    ("PEP", "PepsiCo", "stock_us_defensive"),
    ("WMT", "Walmart", "stock_us_defensive"),
    ("COST", "Costco", "stock_us_defensive"),
    ("MCD", "McDonald's", "stock_us_defensive"),
    ("CL", "Colgate-Palmolive", "stock_us_defensive"),
    ("KMB", "Kimberly-Clark", "stock_us_defensive"),
    ("GIS", "General Mills", "stock_us_defensive"),
    ("K", "Kellogg Company", "stock_us_defensive"),
    ("HSY", "Hershey", "stock_us_defensive"),
    ("MO", "Altria Group", "stock_us_defensive"),
    
    # Utilities
    ("NEE", "NextEra Energy", "stock_us_defensive"),
    ("DUK", "Duke Energy", "stock_us_defensive"),
    ("SO", "Southern Company", "stock_us_defensive"),
    ("D", "Dominion Energy", "stock_us_defensive"),
    ("AEP", "American Electric Power", "stock_us_defensive"),
    ("EXC", "Exelon", "stock_us_defensive"),
]

# AMERIKANSKA FINANSBOLAG
US_FINANCE = [
    ("JPM", "JPMorgan Chase", "stock_us_finance"),
    ("BAC", "Bank of America", "stock_us_finance"),
    ("WFC", "Wells Fargo", "stock_us_finance"),
    ("C", "Citigroup", "stock_us_finance"),
    ("GS", "Goldman Sachs", "stock_us_finance"),
    ("MS", "Morgan Stanley", "stock_us_finance"),
    ("V", "Visa", "stock_us_finance"),
    ("MA", "Mastercard", "stock_us_finance"),
    ("AXP", "American Express", "stock_us_finance"),
    ("BLK", "BlackRock", "stock_us_finance"),
]

# AMERIKANSKA KONSUMENTBOLAG (Discretionary)
US_CONSUMER = [
    # Retail
    ("HD", "Home Depot", "stock_us_consumer"),
    ("LOW", "Lowe's", "stock_us_consumer"),
    ("TGT", "Target", "stock_us_consumer"),
    ("TJX", "TJX Companies", "stock_us_consumer"),
    ("ROST", "Ross Stores", "stock_us_consumer"),
    
    # Automotive
    ("F", "Ford", "stock_us_consumer"),
    ("GM", "General Motors", "stock_us_consumer"),
    
    # Entertainment/Media
    ("DIS", "Disney", "stock_us_consumer"),
    ("CMCSA", "Comcast", "stock_us_consumer"),
    ("PARA", "Paramount Global", "stock_us_consumer"),
    
    # Travel & Leisure
    ("BKNG", "Booking Holdings", "stock_us_consumer"),
    ("MAR", "Marriott", "stock_us_consumer"),
    ("HLT", "Hilton", "stock_us_consumer"),
    ("CCL", "Carnival", "stock_us_consumer"),
    ("NCLH", "Norwegian Cruise Line", "stock_us_consumer"),
    
    # Apparel
    ("NKE", "Nike", "stock_us_consumer"),
    ("LULU", "Lululemon", "stock_us_consumer"),
    ("UAA", "Under Armour", "stock_us_consumer"),
    
    # Restaurants
    ("SBUX", "Starbucks", "stock_us_consumer"),
    ("CMG", "Chipotle", "stock_us_consumer"),
    ("YUM", "Yum! Brands", "stock_us_consumer"),
]

# AMERIKANSKA INDUSTRIBOLAG
US_INDUSTRIAL = [
    ("BA", "Boeing", "stock_us_industrial"),
    ("CAT", "Caterpillar", "stock_us_industrial"),
    ("GE", "General Electric", "stock_us_industrial"),
    ("MMM", "3M", "stock_us_industrial"),
    ("HON", "Honeywell", "stock_us_industrial"),
    ("UPS", "United Parcel Service", "stock_us_industrial"),
    ("RTX", "Raytheon Technologies", "stock_us_industrial"),
    ("DE", "Deere & Company", "stock_us_industrial"),
    ("LMT", "Lockheed Martin", "stock_us_industrial"),
    ("NOC", "Northrop Grumman", "stock_us_industrial"),
    ("GD", "General Dynamics", "stock_us_industrial"),
    ("EMR", "Emerson Electric", "stock_us_industrial"),
    ("ETN", "Eaton", "stock_us_industrial"),
    ("ITW", "Illinois Tool Works", "stock_us_industrial"),
    ("PH", "Parker Hannifin", "stock_us_industrial"),
    ("FDX", "FedEx", "stock_us_industrial"),
    ("NSC", "Norfolk Southern", "stock_us_industrial"),
    ("UNP", "Union Pacific", "stock_us_industrial"),
]

# AMERIKANSKA ENERGIBOLAG
US_ENERGY = [
    ("XOM", "ExxonMobil", "stock_us_energy"),
    ("CVX", "Chevron", "stock_us_energy"),
    ("COP", "ConocoPhillips", "stock_us_energy"),
    ("SLB", "Schlumberger", "stock_us_energy"),
    ("EOG", "EOG Resources", "stock_us_energy"),
    ("MPC", "Marathon Petroleum", "stock_us_energy"),
    ("PSX", "Phillips 66", "stock_us_energy"),
    ("VLO", "Valero Energy", "stock_us_energy"),
    ("OXY", "Occidental Petroleum", "stock_us_energy"),
    ("HAL", "Halliburton", "stock_us_energy"),
    ("BKR", "Baker Hughes", "stock_us_energy"),
    ("KMI", "Kinder Morgan", "stock_us_energy"),
]

# STORA EUROPEISKA BOLAG (endast de med US ADR eller brett tillgängliga)
EUROPEAN_STOCKS = [
    # Företag med ADR på US-börser (lättare tillgång via Avanza)
    ("SAP", "SAP SE", "stock_european"),
    ("TTE", "TotalEnergies", "stock_european"),
    ("NVO", "Novo Nordisk (ADR)", "stock_european"),
    ("ASML", "ASML Holding (ADR)", "stock_european"),
    ("BP", "BP plc (ADR)", "stock_european"),
    ("SAN", "Banco Santander (ADR)", "stock_european"),
    ("SHEL", "Shell plc (ADR)", "stock_european"),
    ("UL", "Unilever (ADR)", "stock_european"),
    ("AZN", "AstraZeneca (ADR)", "stock_european"),
    ("GSK", "GSK plc (ADR)", "stock_european"),
    ("SNY", "Sanofi (ADR)", "stock_european"),
    ("BHP", "BHP Group (ADR)", "stock_european"),
    ("RIO", "Rio Tinto (ADR)", "stock_european"),
    ("DEO", "Diageo (ADR)", "stock_european"),
    ("BTI", "British American Tobacco (ADR)", "stock_european"),
    ("BBVA", "Banco Bilbao Vizcaya (ADR)", "stock_european"),
    ("ING", "ING Group (ADR)", "stock_european"),
    ("NVS", "Novartis (ADR)", "stock_european"),
    ("STM", "STMicroelectronics (ADR)", "stock_european"),
    # Notera: Många europeiska aktier kräver .L, .PA, .DE suffix som kan vara problematiska
    # Bättre att fokusera på ADRs eller direkta US-listningar
]

# BREDA ETF:ER (om tillgängliga via Yahoo Finance)
BROAD_ETFS = [
    # USA Market
    ("SPY", "SPDR S&P 500 ETF", "etf_broad"),
    ("VOO", "Vanguard S&P 500 ETF", "etf_broad"),
    ("IVV", "iShares Core S&P 500", "etf_broad"),
    ("QQQ", "Invesco QQQ (NASDAQ-100)", "etf_broad"),
    ("DIA", "SPDR Dow Jones Industrial", "etf_broad"),
    ("IWM", "iShares Russell 2000", "etf_broad"),
    ("VTI", "Vanguard Total Stock Market", "etf_broad"),
    ("VTV", "Vanguard Value ETF", "etf_broad"),
    ("VUG", "Vanguard Growth ETF", "etf_broad"),
    
    # International
    ("EFA", "iShares MSCI EAFE", "etf_broad"),
    ("VEA", "Vanguard FTSE Developed Markets", "etf_broad"),
    ("VWO", "Vanguard FTSE Emerging", "etf_broad"),
    ("EEM", "iShares MSCI Emerging Markets", "etf_broad"),
    ("IEMG", "iShares Core MSCI Emerging", "etf_broad"),
    ("VGK", "Vanguard FTSE Europe", "etf_broad"),
    ("EWJ", "iShares MSCI Japan", "etf_broad"),
    ("FXI", "iShares China Large-Cap", "etf_broad"),
    
    # Bonds
    ("AGG", "iShares Core US Aggregate Bond", "etf_broad"),
    ("BND", "Vanguard Total Bond Market", "etf_broad"),
    ("TLT", "iShares 20+ Year Treasury", "etf_broad"),
    ("IEF", "iShares 7-10 Year Treasury", "etf_broad"),
    ("LQD", "iShares iBoxx Investment Grade", "etf_broad"),
    ("HYG", "iShares iBoxx High Yield", "etf_broad"),
    ("MUB", "iShares National Muni Bond", "etf_broad"),
]

# SEKTOR-ETF:ER
SECTOR_ETFS = [
    # SPDR Sector Select
    ("XLK", "Technology Select Sector", "etf_sector"),
    ("XLV", "Health Care Select Sector", "etf_sector"),
    ("XLF", "Financial Select Sector", "etf_sector"),
    ("XLE", "Energy Select Sector", "etf_sector"),
    ("XLI", "Industrial Select Sector", "etf_sector"),
    ("XLY", "Consumer Discretionary", "etf_sector"),
    ("XLP", "Consumer Staples", "etf_sector"),
    ("XLU", "Utilities Select Sector", "etf_sector"),
    ("XLRE", "Real Estate Select Sector", "etf_sector"),
    ("XLC", "Communication Services", "etf_sector"),
    ("XLB", "Materials Select Sector", "etf_sector"),
    
    # Vanguard Sector
    ("VGT", "Vanguard Information Technology", "etf_sector"),
    ("VHT", "Vanguard Health Care", "etf_sector"),
    ("VFH", "Vanguard Financials", "etf_sector"),
    ("VDE", "Vanguard Energy", "etf_sector"),
    ("VIS", "Vanguard Industrials", "etf_sector"),
    ("VCR", "Vanguard Consumer Discretionary", "etf_sector"),
    ("VDC", "Vanguard Consumer Staples", "etf_sector"),
    
    # Specialized
    ("SOXX", "iShares Semiconductor", "etf_sector"),
    ("SMH", "VanEck Semiconductor", "etf_sector"),
    ("XBI", "SPDR S&P Biotech", "etf_sector"),
    ("IBB", "iShares Biotechnology", "etf_sector"),
    ("KRE", "SPDR S&P Regional Banking", "etf_sector"),
    ("IYR", "iShares U.S. Real Estate", "etf_sector"),
    ("VNQ", "Vanguard Real Estate", "etf_sector"),
    ("GDX", "VanEck Gold Miners", "etf_sector"),
    ("GDXJ", "VanEck Junior Gold Miners", "etf_sector"),
    ("USO", "United States Oil Fund", "etf_sector"),
    ("UNG", "United States Natural Gas", "etf_sector"),
]

# ALL-WEATHER / DEFENSIVE ETF:ER (Crisis Protection)
# Fokus: Avanza-tillgängliga instruments (US ETFs som proxy för Avanza-alternativ)
ALL_WEATHER_ETFS = [
    # Inverse ETFs (profit when market falls)
    # Avanza-alternativ: XACT Bear, XACT Bear 2, diverse inversen certifikat
    ("SH", "ProShares Short S&P500", "etf_all_weather"),
    ("PSQ", "ProShares Short QQQ", "etf_all_weather"),
    ("DOG", "ProShares Short Dow30", "etf_all_weather"),
    ("RWM", "ProShares Short Russell 2000", "etf_all_weather"),
    ("SQQQ", "ProShares UltraPro Short QQQ", "etf_all_weather"),  # 3x inverse Nasdaq
    ("SPXS", "Direxion Daily S&P 500 Bear 3X", "etf_all_weather"),  # 3x inverse S&P
    
    # Safe havens - Gold/Precious Metals
    # Avanza: XACT Guld (GULD), fysiskt guld, guldgruveaktier
    ("GLD", "SPDR Gold Trust", "etf_all_weather"),
    ("IAU", "iShares Gold Trust", "etf_all_weather"),
    ("GDX", "VanEck Gold Miners", "etf_all_weather"),
    ("GDXJ", "VanEck Junior Gold Miners", "etf_all_weather"),
    ("SLV", "iShares Silver Trust", "etf_all_weather"),
    ("PSLV", "Sprott Physical Silver Trust", "etf_all_weather"),
    ("PHYS", "Sprott Physical Gold Trust", "etf_all_weather"),
    
    # Safe havens - Bonds
    # Avanza: Obligationsfonder (korta/långa räntor), penningmarknadsfonder
    ("TLT", "iShares 20+ Year Treasury", "etf_all_weather"),
    ("IEF", "iShares 7-10 Year Treasury", "etf_all_weather"),
    ("SHY", "iShares 1-3 Year Treasury", "etf_all_weather"),
    ("BIL", "SPDR 1-3 Month T-Bill", "etf_all_weather"),
    ("AGG", "iShares Core US Aggregate Bond", "etf_all_weather"),
    ("BND", "Vanguard Total Bond Market", "etf_all_weather"),
    ("LQD", "iShares iBoxx Investment Grade", "etf_all_weather"),  # Corporate bonds
    ("HYG", "iShares iBoxx High Yield", "etf_all_weather"),  # High yield bonds
    ("MUB", "iShares National Muni Bond", "etf_all_weather"),  # Municipal bonds
    ("TIP", "iShares TIPS Bond", "etf_all_weather"),  # Inflation-protected
    
    # Commodities - Energy
    # Avanza: Råoljefonder, energicertifikat
    ("USO", "United States Oil Fund", "etf_all_weather"),
    ("UNG", "United States Natural Gas", "etf_all_weather"),
    ("XLE", "Energy Select Sector", "etf_all_weather"),  # Energy sector
    ("VDE", "Vanguard Energy", "etf_all_weather"),
    
    # Commodities - Broad/Agriculture
    # Avanza: Råvarufonder
    ("DBA", "Invesco DB Agriculture", "etf_all_weather"),  # Agriculture
    ("DBC", "Invesco DB Commodity", "etf_all_weather"),  # Broad commodities
    
    # Defensive Sectors (perform better in crisis)
    # Avanza: Sektor-ETFer tillgängliga
    ("XLU", "Utilities Select Sector", "etf_all_weather"),  # Utilities
    ("XLP", "Consumer Staples", "etf_all_weather"),  # Consumer staples
    ("VDC", "Vanguard Consumer Staples", "etf_all_weather"),
    
    # Healthcare (defensive)
    # Avanza: Hälsovårdsfonder
    ("XLV", "Health Care Select Sector", "etf_all_weather"),
    ("VHT", "Vanguard Health Care", "etf_all_weather"),
    
    # Volatility plays
    # Avanza: Volatilitetscertifikat
    ("VIXY", "ProShares VIX Short-Term", "etf_all_weather"),
    ("VIXM", "ProShares VIX Mid-Term", "etf_all_weather"),
    ("UVXY", "ProShares Ultra VIX Short-Term", "etf_all_weather"),  # 2x VIX
    
    # International Safe Havens
    # Avanza: Europa/Emerging Markets ETFer
    ("EFA", "iShares MSCI EAFE", "etf_all_weather"),  # Developed markets ex-US
    ("VWO", "Vanguard FTSE Emerging", "etf_all_weather"),  # Emerging markets
]


def get_all_instruments():
    """Returnera alla instrument som en sammanslagen lista."""
    return (
        GLOBAL_INDICES +
        SWEDISH_LARGE_CAP +
        SWEDISH_MID_CAP +
        US_TECH +
        US_DEFENSIVE +
        US_CONSUMER +
        US_FINANCE +
        US_INDUSTRIAL +
        US_ENERGY +
        EUROPEAN_STOCKS +
        BROAD_ETFS +
        SECTOR_ETFS +
        ALL_WEATHER_ETFS
    )


def get_instruments_by_category(category: str):
    """Hämta instrument för en specifik kategori."""
    all_instruments = get_all_instruments()
    return [inst for inst in all_instruments if inst[2] == category]


def get_instrument_count():
    """Räkna totalt antal instrument."""
    return len(get_all_instruments())


def get_category_counts():
    """Returnera antal instrument per kategori."""
    all_instruments = get_all_instruments()
    counts = {}
    for _, _, category in all_instruments:
        counts[category] = counts.get(category, 0) + 1
    return counts


if __name__ == "__main__":
    print("=" * 80)
    print("INSTRUMENT UNIVERSE - ÖVERSIKT")
    print("=" * 80)
    print()
    print(f"Totalt antal instrument: {get_instrument_count()}")
    print()
    print("Fördelning per kategori:")
    for category, count in sorted(get_category_counts().items()):
        print(f"  {category:<30} {count:>3} instrument")
    print()
    print("=" * 80)
