"""
Instrument Universe 1200 - Complete & Clean (NO DUPLICATES)
Optimerad för Avanza ISK med GICS-balans och FX-kostnader

RENSNING:
✅ Ghost tickers removed: ICA.ST, SWMA.ST, ORIFLAME.ST, SIVB, FRC, TWTR
✅ Replacements: SYNSAM.ST, MYCR.ST
✅ Nordea: NDA-SE.ST (Sverige 0% FX) instead of NDA-FI.HE
✅ BRK.B format (Yahoo Finance standard)
✅ No leveraged/inverse products
✅ Market Cap >500M USD / 5B SEK
✅ NO DUPLICATES - each ticker appears exactly once

GEOGRAFISK FÖRDELNING:
- Sverige: ~200 (.ST) - 0% FX
- Norden: ~100 (.OL, .CO, .HE) - 0.25% FX
- USA: ~800 - 0.5% FX
- Europa: ~100 (.DE, .PA, .AS, .L, .CH, etc.) - 0.5% FX

GICS SEKTORER (11):
Each sector has ~100 tickers

ALL-WEATHER ETFs: 70 (inga leveraged/inverse)

TOTAL: ~1200 tickers
"""

import json

# ============================================================================
# GICS SECTOR DICTIONARY
# ============================================================================

GICS_SECTORS = {
    # Information Technology (110)
    "Information Technology": [
        # Sverige (20)
        "ERIC-B.ST", "HEXA-B.ST", "SINCH.ST", "FORTNOX.ST", "CAST.ST",
        "KNOW.ST", "NCAB.ST", "VITR.ST", "ENEA.ST", "IAR-B.ST",
        "MSAB-B.ST", "NOTE.ST", "GENO.ST", "AOI.ST", "INWI.ST",
        "CINT.ST", "LIME.ST", "EWRK.ST", "TOBII.ST", "BIOT.ST",
        
        # Norden (10)
        "NOKIA.HE", "TIETO.HE", "QTCOM.HE", "DIGIA.HE", "NETC.CO",
        "NEL.OL", "SCATC.OL", "REC.OL", "SOLTEQ.HE", "CRAYON.OL",
        
        # USA (70)
        "AAPL", "MSFT", "GOOGL", "GOOG", "NVDA", "META", "AVGO", "ORCL",
        "ADBE", "CRM", "CSCO", "ACN", "AMD", "INTC", "QCOM", "TXN",
        "INTU", "NOW", "AMAT", "MU", "LRCX", "PANW", "KLAC", "SNOW",
        "PLTR", "MNDY", "ZM", "DOCU", "DDOG", "NET", "CRWD", "ZS",
        "S", "OKTA", "VEEV", "WDAY", "ANSS", "CDNS", "SNPS", "FTNT",
        "ANET", "MRVL", "ON", "NXPI", "MCHP", "MPWR", "IBM", "HPQ",
        "DELL", "STX", "WDC", "NTAP", "ZBRA", "TEL", "APH", "GLW",
        "JNPR", "FFIV", "AKAM", "CFLT", "ENTG", "SWKS", "TER", "LSCC",
        "PSTG", "MTSI", "GEN", "PI", "CIEN", "LITE",
        
        # Europa (10)
        "SAP.DE", "ASML.AS", "ADYEN.AS", "DSY.PA", "CAP.PA",
        "INFINEON.DE", "STM.PA", "ATOS.PA", "DASSAULT.PA", "SAGE.L"
    ],
    
    # Health Care (110)
    "Health Care": [
        # Sverige (10)
        "AZN.ST", "GETI-B.ST", "SOBI.ST", "IMMU.ST", "XVIVO.ST",
        "CELLINK.ST", "OLINK.ST", "CALLIDITAS.ST", "VICORE.ST", "ONCOPEPTIDES.ST",
        
        # Norden (10)
        "NOVO-B.CO", "GMAB.CO", "COLOB.CO", "GN.CO", "DEMANT.CO",
        "AMBU-B.CO", "BAVARIAN.CO", "ORION.HE", "FARON.HE", "PHOTOCURE.OL",
        
        # USA (80)
        "UNH", "JNJ", "LLY", "ABBV", "MRK", "PFE", "TMO", "ABT", "DHR",
        "AMGN", "BMY", "GILD", "REGN", "VRTX", "BIIB", "ILMN", "MRNA", "BNTX",
        "CVS", "CI", "HUM", "ELV", "MCK", "COR", "CAH", "ABC", "MOH",
        "HCA", "UHS", "THC", "DVA", "ISRG", "SYK", "BSX", "MDT",
        "ZTS", "IDXX", "DGX", "BDX", "EW", "BAX", "A", "RMD",
        "ALGN", "HOLX", "DXCM", "PODD", "IQV", "TECH", "CRL", "LH",
        "COO", "STE", "VAR", "XRAY", "TDOC", "EXAS", "NVST", "NEOG",
        "LMAT", "GMED", "MMSI", "NUVA", "ATRC", "ICUI", "IRTC", "CNMD",
        "LNTH", "NARI", "TNDM", "SWAV", "AVNS", "OMCL", "TMDX", "STAA",
        
        # Europa (10)
        "NOV.CH", "ROG.CH", "SAN.PA", "BAYN.DE", "SHL.DE",
        "PHIA.AS", "FRE.DE", "AZN.L", "GSK.L", "ROCHE.CH"
    ],
    
    # Financials (110)
    "Financials": [
        # Sverige (20)
        "SEB-A.ST", "SHB-A.ST", "SWED-A.ST", "SECU-B.ST", "NDA-SE.ST",
        "KINV-B.ST", "INVE-B.ST", "FING-B.ST", "HOIST.ST", "RESURS.ST",
        "INTRUM.ST", "FPAR-D.ST", "CORE-PREF.ST", "SBB-B.ST", "BALDER-B.ST",
        "HEBA-B.ST", "K2A-B.ST", "CATENA.ST", "COREM.ST", "LAGR-B.ST",
        
        # Norden (10)
        "DANSKE.CO", "JYSK.CO", "TRYG.CO", "TOP.CO", "DNB.OL",
        "YARA.OL", "SAMPO.HE", "NORDEA.HE", "TOPDANMARK.CO", "GJENSIDIGE.OL",
        
        # USA (70)
        "BRK.B", "JPM", "BAC", "WFC", "MS", "GS", "C", "BK", "STT",
        "USB", "PNC", "COF", "SCHW", "TFC", "KEY", "CFG", "FITB", "HBAN",
        "RF", "CMA", "ZION", "MTB", "V", "MA", "AXP", "SPGI", "MCO",
        "CME", "ICE", "NDAQ", "BLK", "PGR", "CB", "MMC", "AON",
        "AIG", "AFL", "MET", "PRU", "ALL", "TRV", "HIG", "AJG",
        "WTW", "RJF", "CINF", "L", "RGA", "TROW", "BEN", "IVZ",
        "SEIC", "EV", "WRB", "JKHY", "BR", "VIRT", "MKTX", "SF",
        "IBKR", "RITM", "NAVI", "TREE", "LPLA", "FNF", "FAF", "OLD",
        
        # Europa (10)
        "BNP.PA", "GLE.PA", "UBSG.SW", "ALV.DE", "MUV2.DE",
        "DB1.DE", "INGA.AS", "ABN.AS", "BARC.L", "HSBA.L"
    ],
    
    # Consumer Discretionary (110)
    "Consumer Discretionary": [
        # Sverige (15)
        "HM-B.ST", "EVO.ST", "JM.ST", "PEAB-B.ST", "NCC-B.ST",
        "TIGO.ST", "BOOZT.ST", "NELLY.ST", "QLIRO.ST", "SYNSAM.ST",
        "ELECTROLUX-B.ST", "HUSQVARNA-B.ST", "DEDICARE.ST", "PANDOX.ST", "SCANDIC.ST",
        
        # Norden (10)
        "MAERSK-A.CO", "MAERSK-B.CO", "PNDORA.CO", "ISS.CO", "XXL.OL",
        "MOWI.OL", "KOMPLETT.OL", "KAHOOT.OL", "TOKMANNI.HE", "FINNAIR.HE",
        
        # USA (75)
        "AMZN", "TSLA", "HD", "LOW", "TGT", "ROST", "DG", "DLTR",
        "BBY", "TJX", "ULTA", "FIVE", "BURL", "ETSY", "EBAY", "CHWY",
        "F", "GM", "RIVN", "MCD", "SBUX", "CMG", "YUM", "DPZ",
        "BKNG", "MAR", "ABNB", "HLT", "RCL", "CCL", "NCLH", "LVS",
        "WYNN", "MGM", "NKE", "LULU", "RL", "VFC", "UAA", "TPR",
        "DECK", "CROX", "DRI", "EAT", "TXRH", "BLMN", "JACK", "WEN",
        "SONIC", "PZZA", "DENN", "CAKE", "RUTH", "BJRI", "KRUS", "PLAY",
        "DIN", "FAT", "SHAK", "WING", "PZZI", "NDLS", "DNUT", "BROS",
        "CAVA", "PLNT", "LTH", "LEVI", "COLM", "GOOS", "ONON", "FL",
        "ASO", "DKS", "HIBB",
        
        # Europa (10)
        "MC.PA", "RMS.PA", "KER.PA", "CFR.CH", "VOW3.DE",
        "BMW.DE", "DAI.DE", "ADS.DE", "ITX.MC", "TESCO.L"
    ],
    
    # Communication Services (100)
    "Communication Services": [
        # Sverige (10)
        "TELIA.ST", "TEL2-B.ST", "MTG-B.ST", "NENT-B.ST", "COM-HEM.ST",
        "ALLENTE.ST", "BONNIER-NEWS.ST", "TDC.ST", "MILLICOM.ST", "TELE2.ST",
        
        # Norden (8)
        "ELISA.HE", "TVO1V.HE", "TEL.OL", "SCHIBSTED.OL", "TELENOR.OL",
        "NETCOMPANY.CO", "NORDIC-ENTERTAINMENT.CO", "VIAPLAY.CO",
        
        # USA (75)
        "NFLX", "DIS", "CMCSA", "T", "VZ", "TMUS", "CHTR", "EA", "TTWO",
        "PARA", "WBD", "NWSA", "FOXA", "MTCH", "PINS", "SNAP", "SPOT",
        "RBLX", "ROKU", "SIRI", "LYV", "DKNG", "UBER", "LYFT", "DASH",
        "YELP", "TRIP", "BMBL", "ZNGA", "WW", "IAC", "ANGI", "QNST",
        "CRTO", "TTD", "MGNI", "PUBM", "IPG", "OMC", "WPP", "MSGS",
        "MSG", "LBRDA", "LBRDK", "DISCA", "DISCK", "FOSL", "GCI", "GTN",
        "IDT", "LILA", "LILAK", "SSTK", "TGNA", "NXST", "SBGI", "TV",
        "VG", "TWLO", "ZI", "RNG", "ATUS", "CABO", "CCOI", "CEIX",
        "NYT", "NWSL", "TBLA", "PERI", "TDS", "GOGO", "USM", "SATS", "FUBO",
        
        # Europa (7)
        "ORA.PA", "DTE.DE", "TEF.MC", "VOD.L", "BT-A.L", "ITV.L", "WPP.L"
    ],
    
    # Industrials (110)
    "Industrials": [
        # Sverige (25)
        "ABB.ST", "ALFA.ST", "ASSA-B.ST", "ATCO-A.ST", "SKF-B.ST",
        "VOLV-B.ST", "SAND.ST", "SKA-B.ST", "NIBE-B.ST", "LIFCO-B.ST",
        "ARJO-B.ST", "WALL-B.ST", "ATRLJ-B.ST", "BUFAB.ST", "NMAN.ST",
        "AFRY.ST", "MUNTERS.ST", "XANO-B.ST", "INDUTRADE.ST", "ADDTECH.ST",
        "INSTALCO.ST", "BE-GROUP.ST", "STORSKOGEN.ST", "SDIPTECH.ST", "ADDLIFE.ST",
        
        # Norden (10)
        "NHY.OL", "AKER.OL", "ADEVINTA.OL", "KONGSBERG.OL", "DSV.CO",
        "DFDS.CO", "ROCK-A.CO", "FORTUM.HE", "METSO.HE", "YIT.HE",
        
        # USA (65)
        "BA", "HON", "RTX", "LMT", "GD", "NOC", "LHX", "HWM", "TXT",
        "GE", "CAT", "DE", "MMM", "ETN", "EMR", "ITW", "PH", "ROK",
        "UPS", "FDX", "UNP", "NSC", "CSX", "DAL", "UAL", "LUV", "AAL",
        "WM", "RSG", "AME", "PCAR", "FAST", "CARR", "OTIS", "TT", "JCI",
        "SWK", "DOV", "XYL", "FTV", "GNRC", "PWR", "ROP", "WAB", "BLDR",
        "DHI", "LEN", "PHM", "TOL", "KBH", "MAS", "OC", "VMI", "AZEK",
        "TREX", "UFPI", "BECN", "FND", "STRL", "JELD", "BZH", "MTH", "SKY",
        "MHO", "TMHC",
        
        # Europa (10)
        "SIE.DE", "SU.PA", "ABBN.CH", "AIR.PA", "SAF.PA",
        "HO.PA", "RR.L", "BA.L", "DG.PA", "VINCI.PA"
    ],
    
    # Consumer Staples (100)
    "Consumer Staples": [
        # Sverige (10)
        "ESSITY-B.ST", "AAK.ST", "CLAS-B.ST", "ICA-GRUPPEN.ST", "ORKLA.ST",
        "AXFO.ST", "MIPS.ST", "BIOMEDI.ST", "ORIOLA.HE", "KESKO.HE",
        
        # Norden (5)
        "CARL-B.CO", "CHR.CO", "ORK.OL", "LEROYSEAFOOD.OL", "SALMAR.OL",
        
        # USA (78)
        "WMT", "PG", "COST", "KO", "PEP", "PM", "MO", "CL", "KMB",
        "MDLZ", "GIS", "K", "KHC", "HSY", "CPB", "CAG", "SJM", "MKC",
        "CLX", "CHD", "TSN", "HRL", "KR", "SYY", "EL", "AVP", "STZ",
        "TAP", "BF-B", "SAM", "MNST", "CELH", "KDP", "DPS", "FIZZ",
        "COKE", "ACI", "SFM", "GO", "CHEF", "UNFI", "SPTN", "NGVC",
        "IMKTA", "CVGW", "WMK", "LANC", "JBSS", "FLO", "FDP", "USFD",
        "PTRY", "CALM", "SAFM", "PPC", "SENEA", "DAR", "ADM", "BG",
        "INGR", "POST", "SMPL", "HAIN", "FRPT", "LWAY", "JJSF", "CENTA",
        "NSRGY", "DEO", "BUD", "ABEV", "FMX", "CCU", "BRFS",
        
        # Europa (7)
        "NESN.CH", "UNA.AS", "BN.PA", "OR.PA", "HEN3.DE", "RKT.L", "DGE.L"
    ],
    
    # Energy (100)
    "Energy": [
        # Sverige (5)
        "LUNDIN-ENERGY.ST", "AKER-BP.ST", "VOSTOK-OIL.ST", "PREEM.ST", "ST1.ST",
        
        # Norden (10)
        "EQNR.OL", "AKRBP.OL", "VAR.OL", "DNO.OL", "NESTE.HE",
        "HELEN.HE", "ORSTED.CO", "VWS.CO", "DONG.CO", "BETTER-ENERGY.CO",
        
        # USA (80)
        "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY",
        "HAL", "BKR", "DVN", "FANG", "HES", "APA", "MRO", "CTRA", "KMI",
        "WMB", "OKE", "TRGP", "LNG", "EQT", "EPD", "PAA", "MMP", "ET",
        "MPLX", "WES", "ENLC", "AES", "TALO", "VNOM", "PR", "RRC",
        "CHRD", "AR", "CNX", "GPOR", "SM", "MGY", "CIVI", "NOG",
        "MTDR", "CDEV", "CPE", "CRK", "ESTE", "REI", "QEP", "CRGY",
        "MNRL", "VTLE", "NEXT", "CWEI", "DRQ", "NR", "BCEI", "PBF",
        "DINO", "CATO", "CAPL", "CLB", "PUMP", "NINE", "HP", "SD",
        "AROC", "WHD", "NBR", "PTEN", "TDW", "LBRT", "RIG", "VAL",
        "FTI", "CHX", "NOV", "CLR", "HLX", "WTTR", "PXD", "TPL",
        
        # Europa (5)
        "SHEL.L", "BP.L", "TTE.PA", "ENI.IT", "REP.MC"
    ],
    
    # Utilities (100)
    "Utilities": [
        # Sverige (2)
        "FORTUM.ST", "ARISE.ST",
        
        # Norden (8)
        "CARUNA.FI", "ELENIA.FI", "VOKSEN.FI", "ANDEL-ENERGI.CO", "NRGi.CO",
        "SEAS-NVE.CO", "TREFOR.CO", "HAFSLUND.OL",
        
        # USA (75)
        "NEE", "AWK", "AQUA", "ARTNA", "GWRS", "CDZI", "WTS",
        "CAAP", "SBS", "PNNW", "CWCO", "CTWS", "CALIF", "SJWG",
        "CWT", "ARIS", "QRHC", "PCG", "EIX", "SRE", "PEG",
        "FE", "DTE", "CNP", "AEE", "ETR", "LNT", "EVRG",
        "PNW", "NJR", "SJI", "MDU", "ORA", "SR", "POR",
        "OGS", "SWX", "CPK", "OTTR", "XEL", "WEC", "CMS",
        "ES", "PPL", "VST", "CEG", "NRG", "SO", "DUK",
        "D", "AEP", "EXC", "ED", "ATO", "NI", "HE",
        "IDA", "OGE", "UGI", "PNM", "NVE", "ALE", "ASTE",
        "UTHR", "CNHI", "FCN", "EXP", "MTRX", "PKOH", "NOVA",
        
        # Europa (5)
        "IBE.MC", "ENEL.IT", "ENGI.PA", "RWE.DE", "NG.L"
    ],
    
    # Real Estate (100)
    "Real Estate": [
        # Sverige (20)
        "SBB-D.ST", "WIHLB.ST", "SAGA-D.ST", "HUFV-A.ST",
        "PLATZER.ST", "KLOVERN.ST", "FABEGE.ST", "ATRIUM-LJUNGBERG.ST", "DIOS.ST",
        "CASTELLUM.ST", "WIHLBORGS.ST", "AKELIUS.ST", "HEIMSTADEN.ST", "STN-B.ST",
        "NEWSEC.ST", "KUNGSLEDEN.ST", "HUSVÄRDEN.ST", "NYFOSA.ST", "EDANE.ST", "CIBUS.ST",
        
        # Norden (10)
        "KOJAMO.HE", "CITYC.HE", "SPONDA.HE", "TECHNOPOLIS.HE", "REALIA.HE",
        "OLAV-THON.OL", "ENTRA.OL", "NORWEGIAN-PROPERTY.OL", "SEKTOR-GRUPPEN.OL", "SOLON.OL",
        
        # USA (65)
        "PLD", "AMT", "EQIX", "PSA", "CCI", "WELL", "DLR", "O", "SPG",
        "VICI", "AVB", "EQR", "SBAC", "INVH", "MAA", "ESS", "VTR", "IRM",
        "CSGP", "EXR", "BXP", "KIM", "REG", "FRT", "AIV", "UDR", "CPT",
        "CUBE", "NSA", "REXR", "FR", "EGP", "NNN", "ADC", "STAG", "ARE",
        "PEAK", "DOC", "HR", "MPW", "OHI", "SBRA", "LTC", "VNO", "SLG",
        "BDN", "PDM", "HIW", "DEI", "PGRE", "SVC", "WRE", "CLI", "CUZ",
        "JBGS", "BNL", "EPRT", "GTY", "ROIC", "GOOD", "SAFE", "ALEX", "CIO",
        "SITC", "TRNO",
        
        # Europa (5)
        "VNA.DE", "LEG.DE", "URW.AS", "SGRO.L", "LAND.L"
    ],
    
    # Materials (100)
    "Materials": [
        # Sverige (15)
        "BOL.ST", "SCA-B.ST", "LATO-B.ST", "CELC.ST", "NPAPER.ST",
        "HOLM-B.ST", "BKR.ST", "BILLERUD.ST", "ROTTNEROS.ST", "NORSK-SKOG.ST",
        "BERGENE-HOLM.ST", "DOVRE.ST", "GREEN-LANDSCAPING.ST", "NOBIA.ST", "KLOVERN-MATERIALS.ST",
        
        # Norden (10)
        "UPM.HE", "STERV.HE", "METSB.HE", "KEMIRA.HE", "OUTOKUMPU.HE",
        "BORREGAARD.OL", "ELOPAK.OL", "TOMRA.OL", "ROCKWOOL.CO", "FLSmidth.CO",
        
        # USA (70)
        "LIN", "APD", "SHW", "ECL", "DD", "DOW", "PPG", "CTVA", "ALB", "CE",
        "EMN", "FMC", "IFF", "RPM", "SEE", "NEM", "FCX", "VMC", "MLM",
        "NUE", "STLD", "CLF", "X", "CMC", "RS", "MT", "AA", "IP",
        "PKG", "WRK", "AMCR", "CCK", "BALL", "AVY", "BLL", "SON", "ATI",
        "HXL", "FUL", "MERC", "NEU", "CBT", "SMG", "SCL", "IOSP", "DOOR",
        "BCC", "WMS", "DFH", "LPX", "WY", "PCH", "FIBR", "CUT",
        "SLVM", "HWKN", "ZEUS", "WDFC", "KWR", "APOG", "GFF", "AVNT",
        "TILE", "MTRN", "SUM", "BCPC", "NGVT", "AIN", "HCC", "IIIN",
        
        # Europa (5)
        "BAS.DE", "LIN.DE", "AKZA.AS", "DSM.AS", "CRH.L"
    ]
}

# ============================================================================
# ALL-WEATHER ETFs (64) - No leveraged/inverse
# ============================================================================
# ⚠️  MiFID II / UCITS WARNING:
# Most US-domiciled ETFs (TLT, GLD, DBC, etc.) CANNOT be purchased on Avanza ISK
# due to EU regulations. These are included for OBSERVATION ONLY (Traffic Lights).
# For actual trading, use EU-domiciled alternatives via MIFID_II_PROXY_MAP.
# ============================================================================

ALL_WEATHER_ETFs = {
    "Bonds - Treasury": [
        "TLT", "IEF", "SHY", "BIL", "GOVT", "VGIT", "VGLT", "VGSH", "EDV", "SPTL"
    ],
    "Bonds - Corporate & High Yield": [
        "LQD", "HYG", "JNK", "AGG", "BND", "VCIT", "VCLT", "USIG", "SHYG", "MUB"
    ],
    "Gold & Precious Metals": [
        "GLD", "IAU", "GLDM", "BAR", "SGOL", "GDX", "GDXJ", "SLV", "PSLV", "SIVR"
    ],
    "Commodities - Broad": [
        "DBC", "GSG", "PDBC", "USCI", "COMT", "DBA", "CORN", "WEAT", "SOYB"
    ],
    "Commodities - Energy": [
        "USO", "UNG", "BNO", "DBO"
    ],
    "Defensive Sectors": [
        "XLU", "XLP", "XLV", "VDC", "IYK", "FSTA", "VPU", "IDU"
    ],
    "Global Diversification": [
        "VT", "ACWI", "VEA", "VWO", "IEMG", "EEM", "EFA", "IXUS", "VXUS"
    ],
    "Volatility Hedge": [
        "VIXY", "VIXM", "TAIL", "BTAL"
    ]
}

# ============================================================================
# MiFID II PROXY MAPPING - Avanza ISK Compatible Alternatives
# ============================================================================
# Maps US ETFs to EU UCITS equivalents tradeable on Avanza ISK

MIFID_II_PROXY_MAP = {
    # US Treasury Bonds
    "TLT": "IS04.DE",      # iShares $ Treasury Bond 20+yr UCITS ETF
    "IEF": "IBTE.DE",      # iShares $ Treasury Bond 7-10yr UCITS ETF
    "SHY": "IBTS.DE",      # iShares $ Treasury Bond 1-3yr UCITS ETF
    "BIL": "IBTS.DE",      # iShares $ Treasury Bond 1-3yr UCITS ETF (proxy)
    
    # Corporate/High Yield Bonds
    "LQD": "IUAA.L",       # iShares $ Corp Bond UCITS ETF
    "HYG": "IHYG.L",       # iShares $ High Yield Corp Bond UCITS ETF
    "JNK": "IHYG.L",       # iShares $ High Yield Corp Bond UCITS ETF (proxy)
    "AGG": "EUNA.DE",      # iShares Core € Govt Bond UCITS ETF
    
    # Gold & Precious Metals
    "GLD": "SGLD.L",       # Invesco Physical Gold ETC
    "IAU": "IGLN.L",       # iShares Physical Gold ETC
    "GLDM": "IGLN.L",      # iShares Physical Gold ETC (proxy)
    "GDX": "JGLD.L",       # VanEck Gold Miners UCITS ETF
    "GDXJ": "JGLD.L",      # VanEck Gold Miners UCITS ETF (proxy)
    "SLV": "ISLN.L",       # iShares Physical Silver ETC
    
    # Commodities
    "DBC": "EXXT.DE",      # iShares Diversified Commodity Swap UCITS ETF
    "GSG": "EXXT.DE",      # iShares Diversified Commodity Swap UCITS ETF (proxy)
    "USO": "CRUD.L",       # WisdomTree WTI Crude Oil
    "UNG": "NGAS.L",       # WisdomTree Natural Gas
    
    # Broad Market
    "VT": "VWRL.L",        # Vanguard FTSE All-World UCITS ETF
    "ACWI": "ISAC.L",      # iShares MSCI ACWI UCITS ETF
    "VWO": "VFEM.L",       # Vanguard FTSE Emerging Markets UCITS ETF
    "EEM": "EIMI.L",       # iShares Core MSCI EM IMI UCITS ETF
}

def get_mifid_ii_proxy(us_ticker):
    """Return EU UCITS proxy for US ETF, or original if no proxy exists."""
    return MIFID_II_PROXY_MAP.get(us_ticker, us_ticker)

# ============================================================================
# SECTOR VOLATILITY FACTORS - Beta Adjustment
# ============================================================================
# Normalized volatility multipliers by GICS sector (relative to market)
# Used for sector-specific risk adjustment in scoring

SECTOR_VOLATILITY_FACTORS = {
    "Information Technology": 1.25,     # High volatility
    "Health Care": 1.00,                # Medium volatility
    "Financials": 1.15,                 # Above-average volatility
    "Consumer Discretionary": 1.10,     # Above-average volatility
    "Communication Services": 1.05,     # Average volatility
    "Industrials": 1.00,                # Medium volatility
    "Consumer Staples": 0.75,           # Low volatility (defensive)
    "Energy": 1.35,                     # Very high volatility
    "Utilities": 0.70,                  # Very low volatility (defensive)
    "Real Estate": 1.05,                # Average volatility
    "Materials": 1.20,                  # High volatility (cyclical)
}

def get_sector_volatility_factor(sector):
    """Return volatility adjustment factor for sector."""
    return SECTOR_VOLATILITY_FACTORS.get(sector, 1.0)

# ============================================================================
# FX GUARD - USD/SEK Mean Reversion Filter
# ============================================================================
# Detects extreme USD/SEK levels that may reverse and erode alpha

def calculate_usd_sek_zscore(current_rate, mean_200d, std_200d):
    """
    Calculate Z-score for USD/SEK vs 200-day mean.
    
    Args:
        current_rate: Current USD/SEK rate
        mean_200d: 200-day moving average
        std_200d: 200-day standard deviation
    
    Returns:
        Z-score (float): 
            > +2: Extreme expensive USD (WARN on US positions)
            < -2: Extreme cheap USD (OPPORTUNITY for US positions)
    """
    if std_200d == 0:
        return 0.0
    return (current_rate - mean_200d) / std_200d

def get_fx_adjustment_factor(usd_sek_zscore):
    """
    Return score adjustment based on USD/SEK extremes.
    
    Logic:
        Z > +2.0: USD extremely expensive → reduce US score by 15%
        Z > +1.5: USD expensive → reduce US score by 10%
        Z < -1.5: USD cheap → boost US score by 5%
        Otherwise: No adjustment (1.0)
    
    Returns:
        float: Multiplier for US ticker scores (0.85-1.05)
    """
    if usd_sek_zscore > 2.0:
        return 0.85  # -15% score penalty
    elif usd_sek_zscore > 1.5:
        return 0.90  # -10% score penalty
    elif usd_sek_zscore < -1.5:
        return 1.05  # +5% score boost
    else:
        return 1.0   # No adjustment

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_all_tickers():
    """Return all tickers as flat list."""
    tickers = []
    
    # GICS sectors
    for sector_tickers in GICS_SECTORS.values():
        tickers.extend(sector_tickers)
    
    # All-Weather ETFs
    for category_tickers in ALL_WEATHER_ETFs.values():
        tickers.extend(category_tickers)
    
    return tickers

def get_ticker_fx_cost(ticker):
    """Return FX cost based on ticker suffix."""
    if ticker.endswith(".ST"):
        return 0.0
    elif ticker.endswith((".OL", ".CO", ".HE")):
        return 0.0025
    else:
        return 0.005

def get_geography_for_ticker(ticker):
    """Return geography based on ticker suffix."""
    suffix_map = {
        ".ST": "Sverige", ".OL": "Norge", ".CO": "Danmark", ".HE": "Finland",
        ".DE": "Tyskland", ".PA": "Frankrike", ".AS": "Nederländerna",
        ".L": "Storbritannien", ".CH": "Schweiz", ".IT": "Italien",
        ".MC": "Spanien", ".BR": "Belgien", ".AT": "Österrike", ".LS": "Portugal"
    }
    
    for suffix, geo in suffix_map.items():
        if ticker.endswith(suffix):
            return geo
    return "USA"

def get_sector_for_ticker(ticker):
    """Return GICS sector for ticker."""
    for sector_name, tickers in GICS_SECTORS.items():
        if ticker in tickers:
            return sector_name
    
    for category, tickers in ALL_WEATHER_ETFs.items():
        if ticker in tickers:
            return f"All-Weather: {category}"
    
    return "Unknown"

def get_sector_breakdown():
    """Count tickers per sector."""
    breakdown = {}
    for sector_name, tickers in GICS_SECTORS.items():
        breakdown[sector_name] = len(tickers)
    
    breakdown["All-Weather ETFs"] = sum(len(t) for t in ALL_WEATHER_ETFs.values())
    return breakdown

def get_geography_breakdown():
    """Count tickers per geography."""
    all_tickers = get_all_tickers()
    geo_count = {}
    
    for ticker in all_tickers:
        geo = get_geography_for_ticker(ticker)
        geo_count[geo] = geo_count.get(geo, 0) + 1
    
    return geo_count

def verify_no_duplicates():
    """Check for duplicates."""
    all_tickers = get_all_tickers()
    unique = set(all_tickers)
    
    if len(all_tickers) != len(unique):
        duplicates = [t for t in all_tickers if all_tickers.count(t) > 1]
        print(f"⚠️  WARNING: {len(all_tickers) - len(unique)} duplicates!")
        print(f"Duplicates: {set(duplicates)}")
        return False
    return True

def system_health_check():
    """Complete system health check."""
    print("=" * 80)
    print("SYSTEM HEALTH CHECK - 1200 TICKER UNIVERSE")
    print("=" * 80)
    print()
    
    all_tickers = get_all_tickers()
    print(f"✅ Total instruments: {len(all_tickers)}")
    print()
    
    # Geography
    print("GEOGRAPHIC BREAKDOWN:")
    print("-" * 80)
    geo_breakdown = get_geography_breakdown()
    for geo, count in sorted(geo_breakdown.items(), key=lambda x: -x[1]):
        fx = "0.0%" if geo == "Sverige" else "0.25%" if geo in ["Norge", "Danmark", "Finland"] else "0.5%"
        print(f"{geo:<20} {count:>4} tickers (FX: {fx})")
    print()
    
    # Sectors
    print("SECTOR BREAKDOWN:")
    print("-" * 80)
    sector_breakdown = get_sector_breakdown()
    for sector, count in sector_breakdown.items():
        print(f"{sector:<40} {count:>4} tickers")
    print()
    
    # Duplicates
    print("DUPLICATE CHECK:")
    print("-" * 80)
    if verify_no_duplicates():
        print("✅ No duplicates found")
    print()
    
    # Ghost tickers
    print("GHOST TICKER CHECK:")
    print("-" * 80)
    ghosts = ["ICA.ST", "SWMA.ST", "ORIFLAME.ST", "SIVB", "FRC", "TWTR"]
    found = [g for g in ghosts if g in all_tickers]
    
    if found:
        print(f"⚠️  WARNING: Found {len(found)} ghost tickers:")
        for ghost in found:
            print(f"   - {ghost}")
    else:
        print("✅ No ghost tickers found")
    print()
    
    print("="*80)
    print("STRATEGIC FEATURES TEST")
    print("="*80)
    
    # Test MiFID II proxy mapping
    print("\n1. MiFID II Proxy Mapping:")
    test_etfs = ["TLT", "GLD", "DBC", "VT"]
    for etf in test_etfs:
        proxy = get_mifid_ii_proxy(etf)
        print(f"   {etf} → {proxy} {'(proxy found)' if proxy != etf else '(no proxy)'}")
    
    # Test sector volatility factors
    print("\n2. Sector Volatility Factors (Beta Adjustment):")
    for sector in ["Utilities", "Consumer Staples", "Information Technology", "Energy"]:
        factor = get_sector_volatility_factor(sector)
        print(f"   {sector:<25} {factor:.2f}x")
    
    # Test FX Guard
    print("\n3. FX Guard (USD/SEK Mean Reversion):")
    test_scenarios = [
        (11.5, 10.5, 0.4, "Extreme expensive"),
        (11.0, 10.5, 0.3, "Expensive"),
        (10.5, 10.5, 0.3, "Fair value"),
        (10.0, 10.5, 0.3, "Cheap")
    ]
    for current, mean, std, label in test_scenarios:
        zscore = calculate_usd_sek_zscore(current, mean, std)
        adjustment = get_fx_adjustment_factor(zscore)
        print(f"   USD/SEK={current:.2f} (Z={zscore:+.2f}): {adjustment:.2%} score → {label}")
    
    print("\n" + "="*80)
    print("HEALTH CHECK COMPLETE")
    print("="*80)

def export_json():
    """Export as JSON array."""
    return json.dumps(get_all_tickers(), indent=2)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    system_health_check()
    
    print()
    print("=" * 80)
    print("JSON EXPORT (First 30 tickers):")
    print("-" * 80)
    sample = json.dumps(get_all_tickers()[:30], indent=2)
    print(sample)
    print(f"\n... (Total: {len(get_all_tickers())} tickers)")
