"""
ISK Optimizer - Svensk ISK-specifik kostnadsoptimering
========================================================

Tre huvudkomponenter:
1. FX-Växlingsvakt: 0.5% kostnad för utländska aktier
2. Tracking Error Filter: Rangordna instrument efter innehavskostnad
3. Courtage-trappan: Skydda mot ineffektiva positionsstorlekar

Renaissance-princip: "Varje baspunkt räknas. Döda dolda kostnader."
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class ProductType(Enum):
    """Instrumenttyper rangordnade efter innehavskostnad"""
    PHYSICAL_ETF = "Fysiskt backad ETF"
    SWEDISH_STOCK = "Svensk aktie"
    FOREIGN_STOCK = "Utländsk aktie"
    OPENEND_CERTIFICATE = "Open-end certifikat"
    BULL_BEAR_NO_LEVERAGE = "Bull/Bear utan hävstång"
    BULL_BEAR_LEVERAGED = "Bull/Bear med hävstång"


class CourtageTier(Enum):
    """Avanza courtagemodeller för ISK"""
    START = {"name": "Start", "percent": 0.0025, "min": 39, "max": 99}
    MINI = {"name": "Mini", "percent": 0.0019, "min": 39, "max": 89}
    SMALL = {"name": "Small", "percent": 0.0015, "min": 39, "max": 79}
    MEDIUM = {"name": "Medium", "percent": 0.0010, "min": 39, "max": 69}
    LARGE = {"name": "Large", "percent": 0.0007, "min": 29, "max": 49}


@dataclass
class ISKOptimizationResult:
    """Resultat från ISK-optimering"""
    
    # FX-Växlingsvakt
    is_foreign: bool
    fx_conversion_cost_pct: float
    currency_warning: Optional[str]
    
    # Tracking Error Filter
    product_type: ProductType
    product_health_score: int
    holding_cost_pct_per_year: float
    daily_reset_warning: Optional[str]
    
    # Courtage-trappan
    courtage_tier: CourtageTier
    position_size_sek: float
    courtage_cost_sek: float
    courtage_pct: float
    courtage_warning: Optional[str]
    
    # Totalkostnad ISK
    total_isk_cost_pct: float
    net_edge_after_isk: float
    recommendation: str


class ISKOptimizer:
    """
    ISK-specifik kostnadsoptimering för svenska investerare.
    
    Renaissance-princip:
    "En edge på 0.8% är värdelös om 0.5% försvinner i växling."
    """
    
    # FX-växlingskostnader
    FX_COST_BUY = 0.0025  # 0.25%
    FX_COST_SELL = 0.0025  # 0.25%
    FX_TOTAL_ROUNDTRIP = FX_COST_BUY + FX_COST_SELL  # 0.5%
    
    # Suffixer för utländska marknader
    FOREIGN_SUFFIXES = ['.TO', '.V', '', '.US', '.L', '.PA', '.DE', '.HK']
    SWEDISH_SUFFIXES = ['.ST', '.OL', '.HE', '.CO']
    
    # Product health scores (0-100)
    PRODUCT_HEALTH = {
        ProductType.PHYSICAL_ETF: {"score": 100, "holding_cost": 0.0015},
        ProductType.SWEDISH_STOCK: {"score": 95, "holding_cost": 0.0000},
        ProductType.FOREIGN_STOCK: {"score": 85, "holding_cost": 0.0000},
        ProductType.OPENEND_CERTIFICATE: {"score": 60, "holding_cost": 0.0100},
        ProductType.BULL_BEAR_NO_LEVERAGE: {"score": 40, "holding_cost": 0.0150},
        ProductType.BULL_BEAR_LEVERAGED: {"score": 20, "holding_cost": 0.0200},
    }
    
    def __init__(
        self,
        courtage_tier: CourtageTier = CourtageTier.MINI,
        portfolio_size: float = 100000,
        min_edge_threshold: float = 0.010,
    ):
        """
        Args:
            courtage_tier: Din Avanza-klass (START, MINI, SMALL, MEDIUM, LARGE)
            portfolio_size: Total portföljstorlek
            min_edge_threshold: Minsta edge efter ISK-kostnader (1.0% default)
        """
        self.courtage_tier = courtage_tier
        self.portfolio_size = portfolio_size
        self.min_edge_threshold = min_edge_threshold
    
    def _detect_market(self, ticker: str) -> tuple[bool, str]:
        """
        Detektera om ticker är utländsk (kräver valutaväxling).
        
        Returns:
            (is_foreign, market_name)
        """
        ticker_upper = ticker.upper()
        
        # Kolla svenska/nordiska suffixer först
        for suffix in self.SWEDISH_SUFFIXES:
            if ticker_upper.endswith(suffix):
                return False, self._get_market_name(suffix)
        
        # Om inget nordiskt suffix, anta utländsk
        for suffix in self.FOREIGN_SUFFIXES:
            if suffix == '' and '.' not in ticker_upper:
                return True, "USA"
            elif suffix and ticker_upper.endswith(suffix):
                return True, self._get_market_name(suffix)
        
        return True, "Unknown"
    
    def _get_market_name(self, suffix: str) -> str:
        """Översätt suffix till marknadsnamn"""
        mapping = {
            '.ST': 'Stockholm', '.OL': 'Oslo', '.HE': 'Helsinki', '.CO': 'Copenhagen',
            '.TO': 'Toronto', '.V': 'Vancouver', '': 'USA', '.US': 'USA',
            '.L': 'London', '.PA': 'Paris', '.DE': 'Frankfurt', '.HK': 'Hong Kong',
        }
        return mapping.get(suffix, 'Unknown')
    
    def _classify_product(self, ticker: str, name: str = "") -> ProductType:
        """Klassificera produkttyp baserat på ticker och namn"""
        ticker_upper = ticker.upper()
        name_upper = name.upper()
        
        # Fysiskt backade ETF:er
        if any(x in name_upper for x in ['PHYSICAL', 'WISDOMTREE', 'GZUR', 'ISHARES PHYSICAL']):
            return ProductType.PHYSICAL_ETF
        
        # Bull/Bear med hävstång - förbättrad detektion
        # Leta efter BULL eller BEAR följt av X2/X3/X5/X10
        is_bull_bear = any(x in name_upper for x in ['BULL', 'BEAR', 'LEVERAGE', 'HÄVSTÅNG'])
        has_leverage = any(x in name_upper for x in ['X2', 'X3', 'X5', 'X10', 'X 2', 'X 3', 'X 5', 'X 10'])
        
        if is_bull_bear:
            if has_leverage:
                return ProductType.BULL_BEAR_LEVERAGED
            return ProductType.BULL_BEAR_NO_LEVERAGE
        
        # Certifikat
        if any(x in name_upper for x in ['CERTIFIKAT', 'MINI', 'TURBO']):
            return ProductType.OPENEND_CERTIFICATE
        
        # Aktier
        is_foreign, _ = self._detect_market(ticker)
        return ProductType.FOREIGN_STOCK if is_foreign else ProductType.SWEDISH_STOCK
    
    def _calculate_courtage(self, position_size_sek: float) -> tuple[float, float]:
        """
        Beräkna courtage enligt Avanzas modell.
        
        Returns:
            (courtage_sek, courtage_pct)
        """
        tier = self.courtage_tier.value
        courtage_pct_amount = position_size_sek * tier['percent']
        courtage_sek = max(tier['min'], min(courtage_pct_amount, tier['max']))
        courtage_pct = courtage_sek / position_size_sek if position_size_sek > 0 else 0
        return courtage_sek, courtage_pct
    
    def optimize(
        self,
        ticker: str,
        expected_edge: float,
        position_size_sek: float,
        holding_period_days: int = 5,
        product_name: str = "",
    ) -> ISKOptimizationResult:
        """
        Huvudfunktion: Optimera ISK-specifika kostnader.
        
        Args:
            ticker: Ticker-symbol (t.ex. "ERO.TO", "AAPL", "NOVO-B.ST")
            expected_edge: Förväntad edge i procent (t.ex. 0.008 = 0.8%)
            position_size_sek: Positionsstorlek i SEK
            holding_period_days: Förväntad innehavstid i dagar
            product_name: Produktnamn (för klassificering)
        
        Returns:
            ISKOptimizationResult med alla varningar och rekommendationer
        """
        
        # 1. FX-VÄXLINGSVAKT
        is_foreign, market_name = self._detect_market(ticker)
        fx_cost = self.FX_TOTAL_ROUNDTRIP if is_foreign else 0.0
        
        currency_warning = None
        if is_foreign:
            net_after_fx = expected_edge - fx_cost
            if net_after_fx < self.min_edge_threshold:
                currency_warning = (
                    f"⚠️ FX-VARNING: Edge efter valutaväxling ({net_after_fx:.2%}) är låg. "
                    f"Växling kostar {fx_cost:.2%} för {market_name}. "
                    f"Sök svenskt alternativ eller öka edge."
                )
        
        # 2. TRACKING ERROR FILTER
        product_type = self._classify_product(ticker, product_name)
        product_health = self.PRODUCT_HEALTH[product_type]
        product_health_score = product_health['score']
        holding_cost_per_year = product_health['holding_cost']
        holding_cost_total = (holding_cost_per_year / 365) * holding_period_days
        
        daily_reset_warning = None
        if product_type in [ProductType.BULL_BEAR_LEVERAGED, ProductType.BULL_BEAR_NO_LEVERAGE]:
            if holding_period_days > 3:
                daily_reset_warning = (
                    f"⚠️ URHOLKNINGSRISK: {product_type.value} har daglig ombalansering. "
                    f"För positioner längre än 3-4 dagar riskerar du urholkning i sidledes marknad. "
                    f"Rekommendation: Byt till fysiskt backad ETF."
                )
        
        # 3. COURTAGE-TRAPPAN
        courtage_sek, courtage_pct = self._calculate_courtage(position_size_sek)
        
        courtage_warning = None
        if courtage_pct > 0.005:
            courtage_warning = (
                f"🚫 COURTAGE-SPÄRR: Position för liten. Courtage ({courtage_pct:.2%}) äter "
                f"för stor del av din edge. Minsta courtage: {courtage_sek:.0f} SEK. "
                f"Rekommendation: Öka insats till minst {courtage_sek / 0.005:.0f} SEK eller avstå."
            )
        
        # TOTALKOSTNAD
        total_courtage_roundtrip = courtage_pct * 2
        total_isk_cost = fx_cost + total_courtage_roundtrip + holding_cost_total
        net_edge_after_isk = expected_edge - total_isk_cost
        
        # REKOMMENDATION
        if net_edge_after_isk < 0:
            recommendation = "🔴 AVSTÅ - ISK-kostnader överstiger edge"
        elif net_edge_after_isk < self.min_edge_threshold:
            recommendation = "🟡 MARGINELLT - Edge efter ISK är för smal (<1.0%)"
        elif courtage_warning:
            recommendation = "🟡 ÖKA POSITION - Courtage för högt relativt positionsstorlek"
        elif daily_reset_warning:
            recommendation = "🟡 BÄTTRE ALTERNATIV FINNS - Undvik urholkning"
        elif currency_warning:
            recommendation = "🟡 ÖVERVÄG SVENSKT ALTERNATIV - Valutakostnad äter edge"
        else:
            recommendation = "🟢 OK ATT HANDLA - ISK-kostnader acceptabla"
        
        return ISKOptimizationResult(
            is_foreign=is_foreign,
            fx_conversion_cost_pct=fx_cost,
            currency_warning=currency_warning,
            product_type=product_type,
            product_health_score=product_health_score,
            holding_cost_pct_per_year=holding_cost_per_year,
            daily_reset_warning=daily_reset_warning,
            courtage_tier=self.courtage_tier,
            position_size_sek=position_size_sek,
            courtage_cost_sek=courtage_sek,
            courtage_pct=courtage_pct,
            courtage_warning=courtage_warning,
            total_isk_cost_pct=total_isk_cost,
            net_edge_after_isk=net_edge_after_isk,
            recommendation=recommendation,
        )


def format_isk_report(result: ISKOptimizationResult) -> str:
    """Formatera ISK-rapport för utskrift"""
    lines = []
    lines.append("=" * 80)
    lines.append("ISK-OPTIMERING (Svensk Investeringssparkonto)")
    lines.append("=" * 80)
    
    # FX-Växlingsvakt
    lines.append("\n📊 FX-VÄXLINGSVAKT")
    lines.append("-" * 80)
    if result.is_foreign:
        lines.append(f"Utländsk aktie: Ja (Valutaväxling krävs)")
        lines.append(f"FX-kostnad: {result.fx_conversion_cost_pct:.2%} (0.25% köp + 0.25% sälj)")
        if result.currency_warning:
            lines.append(f"\n{result.currency_warning}")
    else:
        lines.append(f"Svensk/Nordisk aktie: Ingen valutaväxling")
    
    # Tracking Error Filter
    lines.append("\n\n📈 TRACKING ERROR FILTER")
    lines.append("-" * 80)
    lines.append(f"Produkttyp: {result.product_type.value}")
    lines.append(f"Product Health Score: {result.product_health_score}/100")
    lines.append(f"Innehavskostnad: {result.holding_cost_pct_per_year:.2%}/år")
    if result.daily_reset_warning:
        lines.append(f"\n{result.daily_reset_warning}")
    
    # Courtage-trappan
    lines.append("\n\n💰 COURTAGE-TRAPPAN")
    lines.append("-" * 80)
    lines.append(f"Courtageklass: {result.courtage_tier.value['name']}")
    lines.append(f"Positionsstorlek: {result.position_size_sek:,.0f} SEK")
    lines.append(f"Courtage (enkel): {result.courtage_cost_sek:.0f} SEK ({result.courtage_pct:.2%})")
    lines.append(f"Courtage (köp+sälj): {result.courtage_cost_sek * 2:.0f} SEK ({result.courtage_pct * 2:.2%})")
    if result.courtage_warning:
        lines.append(f"\n{result.courtage_warning}")
    
    # Total ISK-kostnad
    lines.append("\n\n💸 TOTAL ISK-KOSTNAD")
    lines.append("-" * 80)
    lines.append(f"FX-växling: {result.fx_conversion_cost_pct:.2%}")
    lines.append(f"Courtage (roundtrip): {result.courtage_pct * 2:.2%}")
    lines.append(f"Innehavskostnad: {result.holding_cost_pct_per_year / 365 * 5:.3%} (5 dagar)")
    lines.append(f"{'=' * 40}")
    lines.append(f"TOTALT: {result.total_isk_cost_pct:.2%}")
    lines.append(f"\nNet edge efter ISK: {result.net_edge_after_isk:.2%}")
    
    # Rekommendation
    lines.append("\n\n" + "=" * 80)
    lines.append(f"REKOMMENDATION: {result.recommendation}")
    lines.append("=" * 80)
    
    return "\n".join(lines)
