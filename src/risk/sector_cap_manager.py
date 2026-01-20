"""
Sector Cap Manager - Correlation Risk Control
==============================================

Prevents over-concentration in correlated sectors by enforcing
a maximum exposure limit per sector (default 40%).

Key Concept:
- If multiple stocks in same sector trigger BUY, pick highest SNR
- Prevents "all eggs in one basket" during sector-specific crashes
- Maintains diversification even during strong sector trends

Usage:
sector_mgr = SectorCapManager(max_sector_pct=0.40)
filtered_signals = sector_mgr.apply_sector_cap(signals, portfolio_value)
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class SectorExposure:
    """Sector exposure analysis."""
    sector: str
    total_allocation_pct: float
    instruments: List[str]
    exceeds_cap: bool
    recommended_instruments: List[str]  # Top SNR picks if cap exceeded


@dataclass
class SectorCapResult:
    """Results from sector cap analysis."""
    original_count: int
    filtered_count: int
    sectors_over_cap: List[str]
    exposures: List[SectorExposure]
    recommendation: str


class SectorCapManager:
    """
    Manages sector exposure limits to prevent correlation risk.
    
    Philosophy:
    - Correlation kills diversification
    - One sector crash can wipe out entire portfolio
    - Better to miss some alpha than take correlated bets
    """
    
    # Sector mappings (expand as needed)
    SECTOR_MAP = {
        # Swedish stocks - based on industry
        'BILI-A.ST': 'Automotive',
        'BILI-B.ST': 'Automotive',
        'VOLV-A.ST': 'Automotive',
        'VOLV-B.ST': 'Automotive',
        'ELUX-A.ST': 'Consumer Durables',
        'ELUX-B.ST': 'Consumer Durables',
        'HUSQ-A.ST': 'Consumer Durables',
        'HUSQ-B.ST': 'Consumer Durables',
        'ABB.ST': 'Industrials',
        'ALFA.ST': 'Industrials',
        'ATCO-A.ST': 'Industrials',
        'ATCO-B.ST': 'Industrials',
        'NOLA-B.ST': 'Industrials',  # Nolato - Medical technology & industrial plastics
        'SBB-B.ST': 'Real Estate',
        'SBB-D.ST': 'Real Estate',
        'SAGA-A.ST': 'Real Estate',
        'SAGA-B.ST': 'Real Estate',
        'SAGA-D.ST': 'Real Estate',
        'HM-B.ST': 'Retail',
        'ICA.ST': 'Retail',
        'ASSA-B.ST': 'Security',
        'BOL.ST': 'Materials',  # Boliden - Mining (copper, zinc, gold)
        'GETI-B.ST': 'Healthcare',
        
        # US stocks - based on ticker patterns (simplified)
        'AAPL': 'Technology',
        'MSFT': 'Technology',
        'GOOGL': 'Technology',
        'META': 'Technology',
        'NVDA': 'Technology',
        'AMD': 'Technology',
        'INTC': 'Technology',
        'TXN': 'Technology',
        'SNOW': 'Technology',
        'ZS': 'Technology',
        'JPM': 'Financials',
        'BAC': 'Financials',
        'GS': 'Financials',
        'MS': 'Financials',
        'XOM': 'Energy',
        'CVX': 'Energy',
        'VLO': 'Energy',
        'PFE': 'Healthcare',
        'JNJ': 'Healthcare',
        'UNH': 'Healthcare',
        'MLM': 'Materials',
        'NEM': 'Materials',
        
        # ETFs - by type
        'SPY': 'Broad Market',
        'QQQ': 'Technology',
        'IWM': 'Small Cap',
        'BND': 'Fixed Income',
        'AGG': 'Fixed Income',
        'TLT': 'Fixed Income',
        'GLD': 'Commodities',
        'SLV': 'Commodities',
    }
    
    def __init__(self, max_sector_pct: float = 0.40):
        """
        Initialize sector cap manager.
        
        Args:
            max_sector_pct: Maximum % of portfolio per sector (default 40%)
        """
        self.max_sector_pct = max_sector_pct
    
    def get_sector(self, ticker: str) -> str:
        """
        Get sector for a ticker.
        
        Args:
            ticker: Stock ticker
            
        Returns:
            Sector name (or 'Unknown' if not mapped)
        """
        return self.SECTOR_MAP.get(ticker, 'Unknown')
    
    def analyze_sector_exposure(
        self,
        signals: List[Dict],
        portfolio_value_sek: float = 100000
    ) -> SectorCapResult:
        """
        Analyze sector exposure across all signals.
        
        Args:
            signals: List of signal dicts with ticker, position, snr
            portfolio_value_sek: Total portfolio value
            
        Returns:
            SectorCapResult with exposure analysis
        """
        # Group by sector
        sector_groups = defaultdict(list)
        
        for signal in signals:
            ticker = signal.get('ticker', '')
            sector = self.get_sector(ticker)
            sector_groups[sector].append(signal)
        
        # Calculate exposures
        exposures = []
        sectors_over_cap = []
        
        for sector, sector_signals in sector_groups.items():
            # Calculate total allocation for this sector
            total_allocation = sum(s.get('position', 0) for s in sector_signals)
            
            # Check if over cap
            exceeds_cap = total_allocation > self.max_sector_pct * 100
            
            if exceeds_cap:
                sectors_over_cap.append(sector)
            
            # Sort by SNR (highest first)
            sorted_signals = sorted(
                sector_signals,
                key=lambda x: x.get('snr', 0),
                reverse=True
            )
            
            # Recommend top SNR instruments up to cap
            recommended = []
            cumulative_allocation = 0
            max_allocation = self.max_sector_pct * 100
            
            for sig in sorted_signals:
                position = sig.get('position', 0)
                if cumulative_allocation + position <= max_allocation:
                    recommended.append(sig['ticker'])
                    cumulative_allocation += position
                elif cumulative_allocation < max_allocation:
                    # Partial allocation to hit cap exactly
                    recommended.append(sig['ticker'])
                    break
            
            exposures.append(SectorExposure(
                sector=sector,
                total_allocation_pct=total_allocation,
                instruments=[s['ticker'] for s in sector_signals],
                exceeds_cap=exceeds_cap,
                recommended_instruments=recommended
            ))
        
        # Generate recommendation
        if sectors_over_cap:
            recommendation = f"⚠️ {len(sectors_over_cap)} sector(s) over {self.max_sector_pct*100:.0f}% cap: {', '.join(sectors_over_cap)}"
        else:
            recommendation = f"✅ All sectors within {self.max_sector_pct*100:.0f}% cap"
        
        return SectorCapResult(
            original_count=len(signals),
            filtered_count=sum(len(exp.recommended_instruments) for exp in exposures),
            sectors_over_cap=sectors_over_cap,
            exposures=exposures,
            recommendation=recommendation
        )
    
    def apply_sector_cap(
        self,
        signals: List[Dict],
        portfolio_value_sek: float = 100000
    ) -> Tuple[List[Dict], SectorCapResult]:
        """
        Apply sector cap and filter signals.
        
        Args:
            signals: List of signal dicts
            portfolio_value_sek: Total portfolio value
            
        Returns:
            Tuple of (filtered_signals, analysis_result)
        """
        # Analyze exposures
        analysis = self.analyze_sector_exposure(signals, portfolio_value_sek)
        
        # Build set of recommended tickers
        recommended_tickers = set()
        for exposure in analysis.exposures:
            recommended_tickers.update(exposure.recommended_instruments)
        
        # Filter signals
        filtered_signals = [
            sig for sig in signals
            if sig['ticker'] in recommended_tickers
        ]
        
        return filtered_signals, analysis
    
    def format_exposure_report(self, result: SectorCapResult) -> str:
        """
        Format sector exposure report for display.
        
        Args:
            result: SectorCapResult to format
            
        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 80)
        lines.append("📊 SECTOR EXPOSURE ANALYSIS")
        lines.append("=" * 80)
        lines.append(f"\nSignals: {result.original_count} → {result.filtered_count} (after cap)")
        lines.append(f"Max Sector Cap: {self.max_sector_pct*100:.0f}%")
        lines.append(f"\n{result.recommendation}\n")
        
        # Sort exposures by allocation (highest first)
        sorted_exposures = sorted(
            result.exposures,
            key=lambda x: x.total_allocation_pct,
            reverse=True
        )
        
        lines.append("SECTOR BREAKDOWN:")
        lines.append("-" * 80)
        lines.append(f"{'Sector':<20} {'Allocation':<12} {'Count':<8} {'Status':<15} {'Recommended'}")
        lines.append("-" * 80)
        
        for exp in sorted_exposures:
            if exp.total_allocation_pct == 0:
                continue
            
            status = "⚠️ OVER CAP" if exp.exceeds_cap else "✅ OK"
            recommended = ", ".join(exp.recommended_instruments[:3])
            if len(exp.recommended_instruments) > 3:
                recommended += f" +{len(exp.recommended_instruments) - 3} more"
            
            lines.append(
                f"{exp.sector:<20} "
                f"{exp.total_allocation_pct:>6.1f}%      "
                f"{len(exp.instruments):<8} "
                f"{status:<15} "
                f"{recommended}"
            )
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
