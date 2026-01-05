"""
All-Weather Portfolio Configuration

Defensive instruments that perform well during market stress/crisis.
These receive special treatment during CRISIS regime:
- Normal multiplier (1.0x) instead of crisis penalty (0.2x)
- Prioritized in dashboard during crashes

Philosophy:
"When the casino is on fire, we don't leave - we switch to the fireproof table."
"""

# All-Weather instruments (crisis-resistant)
# Total: 50+ instruments for comprehensive crisis protection
ALL_WEATHER_TICKERS = {
    # Inverse ETFs (profit when market falls)
    'SH', 'PSQ', 'DOG', 'RWM',  # Standard inverse
    'SQQQ', 'SPXS',  # 3x leveraged inverse
    
    # Precious Metals
    'GLD', 'IAU',  # Gold ETFs
    'GDX', 'GDXJ',  # Gold miners
    'SLV', 'PSLV',  # Silver
    'PHYS',  # Physical gold
    
    # Bonds (all maturities)
    'TLT', 'IEF', 'SHY', 'BIL',  # Treasuries by maturity
    'AGG', 'BND',  # Aggregate bonds
    'LQD',  # Investment grade corporate
    'HYG',  # High yield
    'MUB',  # Municipal
    'TIP',  # Inflation-protected
    
    # Commodities
    'USO', 'UNG',  # Energy (oil, gas)
    'XLE', 'VDE',  # Energy sector ETFs
    'DBA',  # Agriculture
    'DBC',  # Broad commodities
    
    # Defensive Sectors
    'XLU', 'XLP', 'VDC',  # Utilities, Consumer Staples
    'XLV', 'VHT',  # Healthcare
    
    # Volatility
    'VIXY', 'VIXM', 'UVXY',  # VIX exposure
    
    # International Diversification
    'EFA',  # Developed markets ex-US
    'VWO',  # Emerging markets
}

# Categories
ALL_WEATHER_CATEGORIES = {
    'inverse_etf': ['SH', 'PSQ', 'DOG', 'RWM', 'SQQQ', 'SPXS'],
    'precious_metals': ['GLD', 'IAU', 'GDX', 'GDXJ', 'SLV', 'PSLV', 'PHYS'],
    'bonds': ['TLT', 'IEF', 'SHY', 'BIL', 'AGG', 'BND', 'LQD', 'HYG', 'MUB', 'TIP'],
    'commodities': ['USO', 'UNG', 'DBA', 'DBC'],
    'energy': ['XLE', 'VDE'],
    'defensive_sectors': ['XLU', 'XLP', 'VDC', 'XLV', 'VHT'],
    'volatility': ['VIXY', 'VIXM', 'UVXY'],
    'international': ['EFA', 'VWO']
}


def is_all_weather(ticker: str) -> bool:
    """
    Check if ticker is an All-Weather instrument.
    
    Args:
        ticker: Instrument ticker
        
    Returns:
        True if All-Weather instrument
    """
    return ticker.upper() in ALL_WEATHER_TICKERS


def get_all_weather_category(ticker: str) -> str:
    """
    Get All-Weather category for ticker.
    
    Args:
        ticker: Instrument ticker
        
    Returns:
        Category name or None
    """
    ticker = ticker.upper()
    
    for category, tickers in ALL_WEATHER_CATEGORIES.items():
        if ticker in tickers:
            return category
    
    return None


# Defensive sectors that perform well in CRISIS
DEFENSIVE_SECTORS = {
    'XLU',   # Utilities
    'XLP',   # Consumer Staples
    'VDC',   # Vanguard Consumer Staples
}

# Avanza mappings for All-Weather instruments
AVANZA_MAPPINGS = {
    # Precious metals
    'GLD': 'XACT Guld (GULD)',
    'IAU': 'XACT Guld (GULD)',
    'GDX': 'Guldgruveaktier eller XACT Guld',
    'GDXJ': 'Guldgruveaktier junior',
    'SLV': 'Silverfonder eller certifikat',
    'PSLV': 'Silverfonder',
    'PHYS': 'Fysiskt guld',
    
    # Inverse ETFs
    'SH': 'XACT Bear',
    'PSQ': 'XACT Bear 2',
    'DOG': 'XACT Bear eller inverse certifikat',
    'RWM': 'Small cap inverse certifikat',
    'SQQQ': 'XACT Bear 2 (3x effekt via certifikat)',
    'SPXS': 'XACT Bear (3x effekt via certifikat)',
    
    # Bonds
    'TLT': 'Långa obligationsfonder (10+ år)',
    'IEF': 'Medellånga obligationsfonder (7-10 år)',
    'SHY': 'Korta obligationsfonder (1-3 år)',
    'BIL': 'Penningmarknadsfond',
    'AGG': 'Bred obligationsfond',
    'BND': 'Bred obligationsfond',
    'LQD': 'Företagsobligationer investment grade',
    'HYG': 'High yield obligationer',
    'MUB': 'Kommunobligationer',
    'TIP': 'Inflationsskyddade obligationer',
    
    # Commodities
    'USO': 'Råoljefonder eller certifikat',
    'UNG': 'Naturgascertifikat',
    'DBA': 'Jordbruksråvaror',
    'DBC': 'Bred råvaruexponering',
    
    # Energy sectors
    'XLE': 'Energisektorfonder',
    'VDE': 'Energisektorfonder',
    
    # Defensive sectors
    'XLU': 'Utility-sektorfonder',
    'XLP': 'Dagligvarufonder',
    'VDC': 'Dagligvarufonder',
    'XLV': 'Hälsovårdsfonder',
    'VHT': 'Hälsovårdsfonder',
    
    # Volatility
    'VIXY': 'Volatilitetscertifikat',
    'VIXM': 'Volatilitetscertifikat',
    'UVXY': 'Volatilitetscertifikat (2x)',
    
    # International
    'EFA': 'Europa/Asien-fonder',
    'VWO': 'Tillväxtmarknadsfonder',
}


def is_defensive_sector(ticker: str) -> bool:
    """
    Check if ticker is a defensive sector ETF.
    
    Args:
        ticker: Instrument ticker
        
    Returns:
        True if defensive sector
    """
    return ticker.upper() in DEFENSIVE_SECTORS


def get_crisis_multiplier(ticker: str, base_multiplier: float, signal_strength: str = None) -> float:
    """
    Get position size multiplier for ticker during crisis.
    
    Args:
        ticker: Instrument ticker
        base_multiplier: Standard regime multiplier (e.g. 0.2 for CRISIS)
        signal_strength: GREEN/YELLOW/etc (optional)
        
    Returns:
        Adjusted multiplier
    """
    # All-Weather instruments get full size during crisis
    if is_all_weather(ticker):
        return 1.0
    
    # Defensive sectors get 0.5x during crisis IF they have GREEN signal
    if is_defensive_sector(ticker) and signal_strength == 'GREEN':
        return 0.5
    
    return base_multiplier


def get_avanza_alternative(ticker: str) -> str:
    """
    Get Avanza-friendly alternative for ticker.
    
    Args:
        ticker: Instrument ticker
        
    Returns:
        Avanza alternative description or None
    """
    return AVANZA_MAPPINGS.get(ticker.upper())
