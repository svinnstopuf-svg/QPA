"""
Expanded Instrument Universe för Quant Pattern Analyzer - 800 Tickers
Optimerad för Avanza ISK med fokus på likviditet och låga avgifter

Total: 800 instrument

Fördelning:
1. Sverige (241 tickers) - 0% FX-avgift, lågt courtage
   - OMXS30 (30), Mid Cap (85), Small Cap (75), Nordiska grannländer (62)
2. USA (302 tickers) - Högt likvida S&P 500 och NASDAQ-100
   - Tech, Finans, Healthcare, Industrials, Consumer, Energy, Materials, REITs, Utilities
3. All-Weather & Hedge (124 tickers) - Krisskydd, volatilitet, inversa produkter
   - Bonds, Guld/Silver, Inverse/Bear, Volatilitet, Råvaror, Defensiva sektorer
4. Sektorer & REITs (80 tickers) - Sektor-ETFer och fastighetsbolag
   - SPDR/Vanguard/iShares sektor-ETFer, REITs, Materials
5. Globala & Emerging Markets (53 tickers) - Geografisk diversifiering
   - Kina, Indien, Brasilien, EM Broad, Europa, Japan, Pacific, Global

Alla instrument:
- Kompatibla med Yahoo Finance API (yfinance)
- Minst 10 års historik (där möjligt)
- Tillräcklig likviditet för mönsteranalys
"""

# ============================================================================
# 1. SVERIGE (250 tickers) - 0% FX-avgift
# ============================================================================

SWEDISH_INSTRUMENTS = [
    # OMXS30 (30 tickers) - De största svenska bolagen
    "ABB.ST", "ALFA.ST", "ALIV-SDB.ST", "ASSA-B.ST", "ATCO-A.ST", "ATCO-B.ST",
    "AZN.ST", "BOL.ST", "ELUX-B.ST", "ERIC-B.ST", "ESSITY-B.ST",
    "EVO.ST", "GETI-B.ST", "HEXA-B.ST", "HM-B.ST", "INVE-B.ST",
    "KINV-B.ST", "NDA-SE.ST", "SAND.ST", "SBB-B.ST", "SEB-A.ST",
    "SECU-B.ST", "SHB-A.ST", "SKA-B.ST", "SKF-B.ST", "SWED-A.ST",
    "TELIA.ST", "VOLV-B.ST", "SCA-B.ST", "TEL2-B.ST",
    
    # Mid Cap (85 tickers) - Medelstora bolag med god likviditet
    "AXFO.ST", "ICA.ST", "CAST.ST", "SINCH.ST", "KNOW.ST", "NCAB.ST",
    "LUND-B.ST", "INDT.ST", "RESURS.ST", "BUFAB.ST", "NIBE-B.ST",
    "LAGR-B.ST", "FPAR-D.ST", "LATO-B.ST", "TIGO.ST", "BOOZT.ST",
    "NMAN.ST", "GARO.ST", "XVIVO.ST", "SDIP-B.ST", "NOTE.ST",
    "VITR.ST", "BIOT.ST", "ENEA.ST", "INDU-C.ST", "CATE.ST",
    "IAR-B.ST", "MSAB-B.ST", "GENO.ST", "ADD.ST", "AOI.ST",
    "TREL-B.ST", "HPOL-B.ST", "INWI.ST", "CORE-PREF.ST", "DOM.ST",
    "BILI-A.ST", "IMMU.ST", "AAK.ST", "HTRO.ST", "KLED.ST",
    "BEIJ-B.ST", "FAGERHULT.ST", "WALL-B.ST", "BALDER-B.ST",
    "FING-B.ST", "WIHL.ST", "ATRLJ-B.ST", "INVE-A.ST", "SWMA.ST",
    "HUSQ-B.ST", "MTG-B.ST", "PEAB-B.ST", "ELUX-A.ST", "KARO.ST",
    "LIFCO-B.ST", "INDU-A.ST", "ARJO-B.ST", "KINV-A.ST", "ORIFLAME.ST",
    "SEMC.ST", "PCELL.ST", "NOBI.ST", "CTM.ST", "BINV.ST",
    "SAGA-D.ST", "NCC-B.ST", "JM.ST", "FABG.ST", "TOBII.ST",
    "EPIS-B.ST", "LIAB.ST", "ORES.ST", "SBB-D.ST", "ALIF-B.ST",
    "CAMX.ST", "HEBA-B.ST", "ACTI.ST",
    
    # Small Cap (75 tickers) - Valda småbolag med likviditet
    "MUNTERS.ST", "MSON-B.ST", "BRG-B.ST", "PROFI.ST", "ALLT-B.ST",
    "PACT.ST", "ORIO.ST", "VOLO.ST", "ITAB.ST", "XANO-B.ST",
    "HOIST.ST", "SYNSAM.ST", "DUNI.ST", "BEF.ST", "QLINEA.ST",
    "ELTEL.ST", "FENIX.ST", "COIC.ST", "LIME.ST", "EWRK.ST",
    "K2A-B.ST", "MCAP.ST", "FORTNOX.ST", "THULE.ST", "JHSF.ST",
    "AFRY.ST", "KAHL.ST", "CORE-B.ST", "MEKO.ST", "TAGM-B.ST",
    "HEMF.ST", "RATO-B.ST", "TRNE-B.ST", "CTT.ST", "VPLAY-B.ST",
    "BHG.ST", "BONAV-B.ST", "QLIRO.ST", "OPUS.ST", "SECT-B.ST",
    "COMH.ST", "SOBI.ST", "DOME.ST", "SPEC.ST", "BETCO.ST",
    "FPAR-A.ST", "INTRUM.ST", "CINT.ST", "RAIL.ST", "DORO.ST",
    "OASM.ST", "BULTEN.ST", "DUST.ST", "CLAS-B.ST", "CELC.ST",
    "MSEK-B.ST", "TETY.ST", "ANOD-B.ST", "SENS.ST", "HOLM-B.ST",
    "G5EN.ST", "ODD.ST", "RVRC.ST", "NOLA-B.ST", "STORY-B.ST",
    "EMBRAC-B.ST", "TROAX.ST", "NPAPER.ST", "PDYN.ST", "BMAX.ST",
    "CEVI.ST",
    
    # Nordiska grannländer - KORRIGERADE SUFFIX (62 tickers)
    # Danmark (.CO) - 20 tickers
    "GMAB.CO", "NOVO-B.CO", "ORSTED.CO", "COLOB.CO", "PNDORA.CO",
    "DANSKE.CO", "VWS.CO", "MAERSK-A.CO", "MAERSK-B.CO", "ISS.CO",
    "GN.CO", "DEMANT.CO", "CHR.CO", "CARL-B.CO", "ROCK-A.CO",
    "ROCK-B.CO", "NETC.CO", "TRYG.CO", "TOP.CO", "JYSK.CO",
    
    # Norge (.OL) - 20 tickers  
    "DNB.OL", "YARA.OL", "EQNR.OL", "MOWI.OL", "NHY.OL",
    "SALM.OL", "XXL.OL", "AKRBP.OL", "AFG.OL", "KAHOT.OL",
    "AKER.OL", "SCATC.OL", "NEL.OL", "REC.OL", "BAKKA.OL",
    "SDRL.OL", "ORK.OL", "SUBC.OL", "GOGL.OL", "HAVILA.OL",
    
    # Finland (.HE) - 20 tickers
    "NOKIA.HE", "SAMPO.HE", "FORTUM.HE", "UPM.HE", "STERV.HE",
    "KEMIRA.HE", "WRT1V.HE", "METSO.HE", "OUT1V.HE", "TVO1V.HE",
    "ORNBV.HE", "TIKS.HE", "KNEBV.HE", "NESTE.HE", "ELISA.HE",
    "TIETO.HE", "KESKOB.HE", "YIT.HE", "FIA1S.HE", "QTCOM.HE",
    
    # Sverige extra (2 tickers) - behåll .ST
    "BRAV.ST", "RAP1V.ST"
]

# ============================================================================
# 2. USA (300 tickers) - Högst likvida aktier från S&P 500 och NASDAQ-100
# ============================================================================

US_LARGE_CAP = [
    # Mega Cap Tech (25)
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA",
    "AVGO", "ORCL", "ADBE", "CRM", "CSCO", "ACN", "AMD", "INTC",
    "QCOM", "TXN", "INTU", "NOW", "AMAT", "MU", "LRCX", "PANW", "KLAC",
    
    # Communication Services (15)
    "NFLX", "DIS", "CMCSA", "T", "VZ", "TMUS", "CHTR", "EA", "TTWO",
    "PARA", "WBD", "NWSA", "FOXA", "MTCH", "PINS",
    
    # Consumer Cyclical (33)
    "HD", "MCD", "NKE", "SBUX", "LOW", "TGT", "BKNG",
    "MAR", "ABNB", "CMG", "YUM", "ROST", "DG", "DLTR", "ORLY", "AZO",
    "BBY", "TJX", "ULTA", "LULU", "RCL", "CCL", "NCLH", "LVS", "WYNN",
    "MGM", "F", "GM", "RIVN", "LCID", "HLT", "EXPE", "EBAY",
    
    # Consumer Defensive (20)
    "WMT", "PG", "COST", "KO", "PEP", "PM", "MO", "CL", "KMB",
    "MDLZ", "GIS", "K", "KHC", "HSY", "CPB", "CAG", "SJM", "MKC",
    "CLX", "CHD",
    
    # Energy (20)
    "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY",
    "HAL", "BKR", "DVN", "FANG", "HES", "KMI", "WMB", "OKE", "TRGP",
    "LNG", "EQT",
    
    # Financials (40)
    "BRK-B", "JPM", "V", "MA", "BAC", "WFC", "MS", "GS", "SPGI",
    "BLK", "C", "AXP", "PGR", "CB", "MMC", "AON", "AIG", "TFC",
    "USB", "PNC", "COF", "BK", "STT", "SCHW", "CME", "ICE", "NDAQ",
    "MCO", "AFL", "MET", "PRU", "ALL", "TRV", "HIG", "AJG", "WTW",
    "RJF", "SIVB", "FRC", "KEY",
    
    # Healthcare (40)
    "UNH", "JNJ", "LLY", "ABBV", "MRK", "PFE", "TMO", "ABT", "DHR",
    "AMGN", "BMY", "GILD", "CVS", "CI", "HUM", "ELV", "MCK", "COR",
    "REGN", "VRTX", "ISRG", "SYK", "BSX", "MDT", "ZTS", "IDXX", "DGX",
    "BDX", "EW", "BAX", "A", "RMD", "ALGN", "HOLX", "DXCM", "PODD",
    "IQV", "TECH", "CRL", "LH",
    
    # Industrials (40)
    "BA", "HON", "UPS", "RTX", "CAT", "GE", "LMT", "DE", "MMM", "UNP",
    "FDX", "NSC", "CSX", "ETN", "EMR", "ITW", "PH", "ROK", "WM", "RSG",
    "AME", "PCAR", "FAST", "CARR", "OTIS", "TT", "JCI", "IEX", "VRSK",
    "PAYX", "CTAS", "TDY", "SWK", "DOV", "XYL", "FTV", "GNRC", "PWR",
    "ROP", "WAB",
    
    # Materials (15)
    "LIN", "APD", "SHW", "ECL", "DD", "NEM", "FCX", "VMC", "MLM",
    "NUE", "DOW", "PPG", "CTVA", "ALB", "CE",
    
    # Real Estate (10)
    "IRM", "CSGP", "EXR", "BXP", "KIM", "REG", "FRT", "AIV", "UDR", "CPT",
    
    # Technology (continued - 30)
    "IBM", "SNOW", "PLTR", "MNDY", "ZM", "DOCU", "DDOG", "NET", "CRWD",
    "ZS", "S", "OKTA", "VEEV", "WDAY", "ANSS", "CDNS", "SNPS", "FTNT",
    "ANET", "MRVL", "ON", "NXPI", "MCHP", "MPWR", "ENPH", "FSLR", "SEDG",
    "TER", "SWKS", "QRVO",
    
    # Utilities (14)
    "NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "PEG", "XEL", "ED",
    "ES", "AWK", "WEC", "PPL"
]

# ============================================================================
# 3. ALL-WEATHER & HEDGE (120 tickers) - Krisskydd och volatilitet
# ============================================================================

ALL_WEATHER_HEDGE = [
    # Bonds - Long Duration (10)
    "TLT", "EDV", "VGLT", "ZROZ", "TMF", "IEF", "TLH", "GOVT", "SPTL", "VGIT",
    
    # Bonds - Short/Medium (10)
    "SHY", "SHV", "VGSH", "SCHO", "IEI", "BIL", "SGOV", "TBIL", "NEAR", "TFLO",
    
    # Bonds - Aggregate/Corp (10)
    "AGG", "BND", "VCIT", "LQD", "VCLT", "USIG", "IG", "IGIB", "IGSB", "SLQD",
    
    # Bonds - High Yield & Muni (5)
    "HYG", "JNK", "SHYG", "MUB", "TFI",
    
    # Gold & Precious Metals (15)
    "GLD", "IAU", "GLDM", "BAR", "SGOL", "PHYS", "AAAU", "GDX", "GDXJ",
    "RING", "JNUG", "GOEX", "OUNZ", "PALL", "PPLT",
    
    # Silver (5)
    "SLV", "PSLV", "SIVR", "AGQ", "USLV",
    
    # Inverse/Bear - S&P 500 (10)
    "SH", "SDS", "SPXS", "SPXU", "RWM", "TWM", "DOG", "DXD", "SDOW", "UDOW",
    
    # Inverse/Bear - NASDAQ/Tech (8)
    "PSQ", "QID", "SQQQ", "TECS", "SRTY", "TZA", "SKF", "REK",
    
    # Volatility Products (10)
    "VIXY", "VIXM", "UVXY", "SVXY", "VXX", "TVIX", "UVIX", "SVIX", "TAIL", "BTAL",
    
    # Commodities - Energy (10)
    "USO", "UNG", "BNO", "USL", "DBO", "UGA", "CRUD", "NRGU", "ERX", "DRIP",
    
    # Commodities - Agriculture & Broad (10)
    "DBA", "CORN", "WEAT", "SOYB", "DBC", "GSG", "PDBC", "USCI", "GCC", "COMT",
    
    # Defensive - Utilities & Staples (8)
    "FUTY", "FSTA", "KXI", "FXG", "RYU", "IUSU", "KSPI", "REGL",
    
    # Defensive - Healthcare (3)
    "FHLC", "IXJ", "RYH",
    
    # Currency/FX Hedge (5)
    "UUP", "UDN", "FXE", "FXY", "FXB",
    
    # Alternative - Managed Futures (5)
    "DBMF", "KMLM", "CTA", "WTMF", "FMF"
]

# ============================================================================
# 4. SEKTORER & FASTIGHETER (80 tickers) - REITs och sektor-ETFer
# ============================================================================

SECTORS_REITS = [
    # SPDR Sector Select ETFs (11)
    "XLK", "XLV", "XLF", "XLE", "XLI", "XLY", "XLP", "XLU", "XLRE", "XLC", "XLB",
    
    # Vanguard Sector ETFs (8)
    "VGT", "VHT", "VFH", "VDE", "VIS", "VCR", "VOX", "VAW",
    
    # iShares Sector ETFs (7)
    "IYW", "IYF", "IYE", "IYJ", "IYC", "IYZ", "ITB",
    
    # Specialized Tech/Semiconductor (3)
    "SOXX", "SMH", "XSD",
    
    # Biotech & Pharma (5)
    "XBI", "IBB", "BBH", "PBE", "LABU",
    
    # Financial Sub-sectors (3)
    "KRE", "KBE", "IAK",
    
    # REITs - Diversified (5)
    "RWR", "SCHH", "USRT", "FREL", "ICF",
    
    # REITs - Individual Large Cap (20)
    "PLD", "AMT", "EQIX", "PSA", "CCI", "WELL", "DLR", "O", "SPG", "VICI",
    "AVB", "EQR", "SBAC", "WY", "INVH", "MAA", "ESS", "VTR", "ARE", "PEAK",
    
    # Materials & Commodities (13)
    "XOP", "IEO", "OIH", "FCG", "AMLP", "XME", "PICK", "REMX", "LIT",
    "COPX", "SIL", "GNR", "MOO",
    
    # Real Estate - Additional (5)
    "MORT", "REM", "BBRE", "SRVR", "HOMZ"
]

# ============================================================================
# 5. GLOBALA & EMERGING MARKETS (50 tickers) - Geografisk diversifiering
# ============================================================================

GLOBAL_EMERGING = [
    # China (10)
    "FXI", "MCHI", "KWEB", "CQQQ", "GXC", "ASHR", "YINN", "YANG", "CHIQ", "PGJ",
    
    # India (5)
    "INDA", "EPI", "INDY", "PIN", "SMIN",
    
    # Brazil (5)
    "EWZ", "BRZU", "EWZS", "ILF", "UBR",
    
    # Emerging Markets Broad (10)
    "EEM", "VWO", "IEMG", "SCHE", "DEM", "SPEM", "EWX", "EMXC", "FNDE", "DFEM",
    
    # Europe (10)
    "VGK", "EZU", "FEZ", "IEUR", "HEDJ", "DFE", "DBEU", "IEV", "EPU", "EWG",
    
    # Japan (5)
    "EWJ", "DXJ", "DBJP", "JPXN", "BBJP",
    
    # Pacific/Asia ex-Japan (3)
    "AAXJ", "EPP", "GMF",
    
    # Global/World (2)
    "VT", "ACWI",
    
    # Frontier Markets & Other (3)
    "FM", "FRN", "EEMV"
]

# ============================================================================
# KOMBINERA ALLA 800 TICKERS
# ============================================================================

def get_all_800_tickers():
    """Returnera alla 800 tickers som en ren lista (utan namn/kategorier)."""
    return (
        SWEDISH_INSTRUMENTS +
        US_LARGE_CAP +
        ALL_WEATHER_HEDGE +
        SECTORS_REITS +
        GLOBAL_EMERGING
    )


def get_all_800_instruments():
    """
    Returnera alla 800 instrument i samma format som tidigare:
    (ticker, name, category)
    """
    instruments = []
    
    # Sverige
    for ticker in SWEDISH_INSTRUMENTS:
        instruments.append((ticker, f"Swedish - {ticker}", "stock_swedish"))
    
    # USA
    for ticker in US_LARGE_CAP:
        instruments.append((ticker, f"US Large Cap - {ticker}", "stock_us_large"))
    
    # All-Weather & Hedge
    for ticker in ALL_WEATHER_HEDGE:
        instruments.append((ticker, f"All-Weather - {ticker}", "etf_all_weather"))
    
    # Sektorer & REITs
    for ticker in SECTORS_REITS:
        instruments.append((ticker, f"Sector/REIT - {ticker}", "etf_sector_reit"))
    
    # Global & Emerging
    for ticker in GLOBAL_EMERGING:
        instruments.append((ticker, f"Global/EM - {ticker}", "etf_global_em"))
    
    return instruments


def get_ticker_json():
    """Returnera en ren JSON-array med 800 tickers."""
    import json
    return json.dumps(get_all_800_tickers(), indent=2)


def verify_no_duplicates():
    """Verifiera att inga dubbletter finns."""
    tickers = get_all_800_tickers()
    unique = set(tickers)
    if len(tickers) != len(unique):
        duplicates = [t for t in tickers if tickers.count(t) > 1]
        print(f"⚠️  VARNING: {len(tickers) - len(unique)} dubbletter hittade!")
        print(f"Dubbletter: {set(duplicates)}")
        return False
    return True


def get_category_breakdown():
    """Visa fördelning per kategori."""
    return {
        "Sverige": len(SWEDISH_INSTRUMENTS),
        "USA": len(US_LARGE_CAP),
        "All-Weather & Hedge": len(ALL_WEATHER_HEDGE),
        "Sektorer & REITs": len(SECTORS_REITS),
        "Global & Emerging": len(GLOBAL_EMERGING),
        "TOTAL": len(get_all_800_tickers())
    }


if __name__ == "__main__":
    print("=" * 80)
    print("800-TICKER UNIVERSE - ÖVERSIKT")
    print("=" * 80)
    print()
    
    breakdown = get_category_breakdown()
    for category, count in breakdown.items():
        print(f"{category:<30} {count:>3} tickers")
    
    print()
    print("=" * 80)
    print("DUBBLETTSKONTROLL")
    print("=" * 80)
    
    if verify_no_duplicates():
        print("✅ Inga dubbletter hittade!")
    
    print()
    print("=" * 80)
    print("JSON EXPORT")
    print("=" * 80)
    print()
    print(get_ticker_json()[:500] + "...")
    print()
    print(f"Total längd: {len(get_ticker_json())} tecken")
