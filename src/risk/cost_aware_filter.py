"""
Cost-Aware Edge Filter

Kasinot räknar alltid med driftskostnader. Ett "grönt" mönster med 0.8% edge
i en småbolagsaktie med 1.0% totalkostnad är en förlustaffär.

Philosophy:
- Net Edge = Predicted Edge - Transaction Costs
- Only trade when Net Edge > 0
- Different costs for different instruments
"""

import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum


class InstrumentType(Enum):
    """Instrument type for cost estimation."""
    LARGE_CAP = "LARGE_CAP"  # Stora aktier, tight spread
    SMALL_CAP = "SMALL_CAP"  # Små aktier, wide spread
    INDEX_ETF = "INDEX_ETF"  # ETF:er, låg kostnad
    SECTOR_ETF = "SECTOR_ETF"  # Sektor-ETF
    BOND_ETF = "BOND_ETF"  # Obligations-ETF
    INTERNATIONAL = "INTERNATIONAL"  # Internationella aktier


@dataclass
class TradingCosts:
    """Trading cost breakdown."""
    courtage: float  # Courtage per trade
    spread_pct: float  # Bid-ask spread %
    fx_cost_pct: float  # FX conversion cost %
    total_pct: float  # Total round-trip cost %


@dataclass
class CostAnalysis:
    """Cost-aware edge analysis."""
    predicted_edge: float  # Original edge prediction
    trading_costs: TradingCosts
    net_edge: float  # Edge after costs
    profitable: bool  # Net edge > 0
    recommendation: str
    min_edge_required: float  # Min edge to be profitable


class CostAwareFilter:
    """
    Filters trades based on cost-adjusted edge.
    
    Rules:
    1. Calculate total round-trip cost (courtage + spread + FX)
    2. Subtract from predicted edge
    3. Only allow trades with positive net edge
    
    Example:
    - Small-cap: Edge 0.8%, Cost 1.0% → Net -0.2% → BLOCK
    - Large-cap: Edge 0.8%, Cost 0.3% → Net +0.5% → ALLOW
    """
    
    def __init__(
        self,
        courtage_per_trade: float = 0.0,  # SEK per trade (0 for Avanza Zero)
        min_courtage: float = 0.0,  # Minimum courtage
        fx_conversion_cost: float = 0.0025  # 0.25% for USD/SEK
    ):
        """
        Initialize cost-aware filter.
        
        Args:
            courtage_per_trade: Courtage per trade (SEK)
            min_courtage: Minimum courtage (SEK)
            fx_conversion_cost: FX conversion cost (%)
        """
        self.courtage_per_trade = courtage_per_trade
        self.min_courtage = min_courtage
        self.fx_conversion_cost = fx_conversion_cost
        
        # Typical spread estimates by instrument type
        self.spread_estimates = {
            InstrumentType.LARGE_CAP: 0.0015,  # 0.15%
            InstrumentType.SMALL_CAP: 0.0100,  # 1.00%
            InstrumentType.INDEX_ETF: 0.0010,  # 0.10%
            InstrumentType.SECTOR_ETF: 0.0020,  # 0.20%
            InstrumentType.BOND_ETF: 0.0015,  # 0.15%
            InstrumentType.INTERNATIONAL: 0.0030  # 0.30%
        }
    
    def estimate_instrument_type(
        self,
        ticker: str,
        category: str = None,
        market_cap: float = None
    ) -> InstrumentType:
        """
        Estimate instrument type from ticker and metadata.
        
        Args:
            ticker: Ticker symbol
            category: Category from instruments_universe
            market_cap: Market capitalization (if available)
            
        Returns:
            InstrumentType classification
        """
        # Check category first
        if category:
            if 'large' in category.lower():
                return InstrumentType.LARGE_CAP
            elif 'small' in category.lower() or 'mid' in category.lower():
                return InstrumentType.SMALL_CAP
            elif 'etf_broad' in category.lower():
                return InstrumentType.INDEX_ETF
            elif 'etf_sector' in category.lower():
                return InstrumentType.SECTOR_ETF
        
        # Check ticker patterns
        if ticker.endswith('.ST'):  # Swedish stocks
            # Assume large cap unless proven otherwise
            return InstrumentType.LARGE_CAP
        
        # US stocks - check common large caps
        large_caps = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 
                     'TSLA', 'JPM', 'JNJ', 'V', 'MA', 'WMT', 'PG']
        if ticker in large_caps:
            return InstrumentType.LARGE_CAP
        
        # ETF patterns
        if any(ticker.startswith(x) for x in ['SPY', 'QQQ', 'IWM', 'VOO', 'VTI']):
            return InstrumentType.INDEX_ETF
        if any(ticker.startswith(x) for x in ['XL', 'VG', 'IY']):
            return InstrumentType.SECTOR_ETF
        if any(ticker.startswith(x) for x in ['AGG', 'BND', 'TLT', 'LQD']):
            return InstrumentType.BOND_ETF
        
        # International ADRs
        if any(ticker in ['NVO', 'ASML', 'SAP', 'TTE', 'BP', 'SHEL', 'DEO'] for ticker in [ticker]):
            return InstrumentType.INTERNATIONAL
        
        # Default to small cap (conservative)
        return InstrumentType.SMALL_CAP
    
    def calculate_costs(
        self,
        instrument_type: InstrumentType,
        position_size: float,  # SEK
        is_foreign: bool = False
    ) -> TradingCosts:
        """
        Calculate total round-trip trading costs.
        
        Args:
            instrument_type: Type of instrument
            position_size: Position size in SEK
            is_foreign: Whether foreign exchange is involved
            
        Returns:
            TradingCosts breakdown
        """
        # Courtage (round-trip = 2x)
        courtage_per_direction = max(self.courtage_per_trade, self.min_courtage)
        total_courtage = courtage_per_direction * 2  # Buy + Sell
        
        if position_size > 0:
            courtage_pct = (total_courtage / position_size) * 100
        else:
            courtage_pct = 0
        
        # Spread (round-trip = 2x one-way spread)
        spread_one_way = self.spread_estimates.get(instrument_type, 0.005)
        spread_pct = spread_one_way * 2 * 100  # Convert to %
        
        # FX cost (if foreign, round-trip = 2x)
        if is_foreign:
            fx_pct = self.fx_conversion_cost * 2 * 100  # Convert to %
        else:
            fx_pct = 0
        
        # Total
        total_pct = courtage_pct + spread_pct + fx_pct
        
        return TradingCosts(
            courtage=total_courtage,
            spread_pct=spread_pct,
            fx_cost_pct=fx_pct,
            total_pct=total_pct
        )
    
    def analyze_edge_after_costs(
        self,
        predicted_edge: float,  # % per period
        ticker: str,
        category: str = None,
        position_size: float = 10000,  # Default 10k SEK
        is_foreign: bool = False
    ) -> CostAnalysis:
        """
        Analyze if predicted edge is profitable after costs.
        
        Args:
            predicted_edge: Predicted edge (%)
            ticker: Ticker symbol
            category: Instrument category
            position_size: Position size (SEK)
            is_foreign: Whether foreign instrument
            
        Returns:
            CostAnalysis with net edge
        """
        # Estimate instrument type
        instrument_type = self.estimate_instrument_type(ticker, category)
        
        # Calculate costs
        costs = self.calculate_costs(instrument_type, position_size, is_foreign)
        
        # Net edge
        net_edge = predicted_edge - costs.total_pct
        
        # Determine if profitable
        profitable = net_edge > 0
        
        # Minimum edge required
        min_edge_required = costs.total_pct
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            predicted_edge, net_edge, profitable, costs
        )
        
        return CostAnalysis(
            predicted_edge=predicted_edge,
            trading_costs=costs,
            net_edge=net_edge,
            profitable=profitable,
            recommendation=recommendation,
            min_edge_required=min_edge_required
        )
    
    def _generate_recommendation(
        self,
        predicted_edge: float,
        net_edge: float,
        profitable: bool,
        costs: TradingCosts
    ) -> str:
        """Generate trading recommendation."""
        if not profitable:
            return (
                f"BLOCK - Net edge {net_edge:+.2f}% negative after "
                f"{costs.total_pct:.2f}% costs"
            )
        
        if net_edge < 0.1:
            return (
                f"MARGINAL - Net edge {net_edge:+.2f}% barely positive "
                f"(costs {costs.total_pct:.2f}%)"
            )
        
        if net_edge < 0.3:
            return (
                f"ACCEPTABLE - Net edge {net_edge:+.2f}% after "
                f"{costs.total_pct:.2f}% costs"
            )
        
        return (
            f"STRONG - Net edge {net_edge:+.2f}% after "
            f"{costs.total_pct:.2f}% costs"
        )
    
    def batch_analyze_costs(
        self,
        instruments_data: Dict[str, Dict]
    ) -> Dict[str, CostAnalysis]:
        """
        Analyze costs for multiple instruments.
        
        Args:
            instruments_data: Dict mapping ticker to data with:
                - predicted_edge: Edge %
                - category: Instrument category
                - position_size: Position size (SEK)
                - is_foreign: Bool
                
        Returns:
            Dict mapping ticker to CostAnalysis
        """
        results = {}
        
        for ticker, data in instruments_data.items():
            analysis = self.analyze_edge_after_costs(
                predicted_edge=data.get('predicted_edge', 0),
                ticker=ticker,
                category=data.get('category'),
                position_size=data.get('position_size', 10000),
                is_foreign=data.get('is_foreign', False)
            )
            results[ticker] = analysis
        
        return results
    
    def filter_profitable_only(
        self,
        analyses: Dict[str, CostAnalysis]
    ) -> Dict[str, CostAnalysis]:
        """Filter to keep only profitable trades after costs."""
        return {
            ticker: analysis
            for ticker, analysis in analyses.items()
            if analysis.profitable
        }


def format_cost_report(analyses: Dict[str, CostAnalysis]) -> str:
    """Format cost analysis report."""
    lines = []
    lines.append("=" * 80)
    lines.append("COST-AWARE EDGE FILTER")
    lines.append("=" * 80)
    lines.append("")
    
    # Sort by net edge
    sorted_items = sorted(
        analyses.items(),
        key=lambda x: x[1].net_edge,
        reverse=True
    )
    
    # Separate profitable vs unprofitable
    profitable = [(t, a) for t, a in sorted_items if a.profitable]
    unprofitable = [(t, a) for t, a in sorted_items if not a.profitable]
    
    # Profitable trades
    if profitable:
        lines.append(f"✅ PROFITABLE AFTER COSTS: {len(profitable)}")
        lines.append("-" * 80)
        lines.append(f"{'Ticker':<10} {'Edge':<10} {'Costs':<10} {'Net Edge':<12} {'Status':<10}")
        lines.append("-" * 80)
        
        for ticker, analysis in profitable[:15]:  # Top 15
            lines.append(
                f"{ticker:<10} "
                f"{analysis.predicted_edge:>7.2f}% "
                f"{analysis.trading_costs.total_pct:>7.2f}% "
                f"{analysis.net_edge:>+9.2f}% "
                f"✅"
            )
        
        lines.append("")
    
    # Unprofitable trades
    if unprofitable:
        lines.append(f"❌ BLOCKED (Negative Net Edge): {len(unprofitable)}")
        lines.append("-" * 80)
        lines.append(f"{'Ticker':<10} {'Edge':<10} {'Costs':<10} {'Net Edge':<12} {'Status':<10}")
        lines.append("-" * 80)
        
        for ticker, analysis in unprofitable[:10]:  # Top 10 worst
            lines.append(
                f"{ticker:<10} "
                f"{analysis.predicted_edge:>7.2f}% "
                f"{analysis.trading_costs.total_pct:>7.2f}% "
                f"{analysis.net_edge:>+9.2f}% "
                f"❌"
            )
        
        lines.append("")
    
    # Summary
    total = len(analyses)
    profitable_count = len(profitable)
    blocked_count = len(unprofitable)
    
    lines.append("=" * 80)
    lines.append("SAMMANFATTNING")
    lines.append(f"Total: {total} | Profitable: {profitable_count} | Blocked: {blocked_count}")
    
    if profitable:
        avg_net_edge = np.mean([a.net_edge for _, a in profitable])
        lines.append(f"Avg Net Edge (profitable): {avg_net_edge:+.2f}%")
    
    lines.append("=" * 80)
    
    return "\n".join(lines)


if __name__ == "__main__":
    print("Cost-Aware Edge Filter")
    print("Usage:")
    print("  from src.risk.cost_aware_filter import CostAwareFilter")
    print("  filter = CostAwareFilter()")
    print("  analysis = filter.analyze_edge_after_costs(edge=0.8, ticker='SBB-B.ST')")
