"""
Factor Quality Score - The 'Company' Filter

Evaluates fundamental quality of companies based on:
1. Profitability: ROE > 15% (40 points)
2. Solvency: Debt/Equity < 1.0 (40 points)
3. Value: P/E below sector average (20 points)

Total Quality Score: 0-100
- Score < 40 = TRASH/HIGH RISK (Value Trap warning)
- Score >= 40 = Acceptable quality
- Score >= 80 = High quality company
"""

from dataclasses import dataclass
from typing import Optional
import yfinance as yf


@dataclass
class QualityScoreAnalysis:
    """Results of quality score analysis"""
    ticker: str
    quality_score: float  # 0-100
    
    # Profitability metrics
    roe: Optional[float]  # Return on Equity
    roe_score: float  # 0-40 points
    
    # Solvency metrics
    debt_to_equity: Optional[float]
    debt_score: float  # 0-40 points
    
    # Value metrics
    trailing_pe: Optional[float]
    sector_avg_pe: Optional[float]
    value_score: float  # 0-20 points
    
    # Classification
    risk_category: str  # "HIGH QUALITY", "ACCEPTABLE", "HIGH RISK/TRASH"
    value_trap_warning: bool
    
    # Additional context
    company_name: Optional[str]
    sector: Optional[str]
    industry: Optional[str]
    
    @property
    def summary(self) -> str:
        """Get one-line summary of quality"""
        if self.quality_score >= 80:
            return f"✅ HIGH QUALITY ({self.quality_score:.0f}/100)"
        elif self.quality_score >= 40:
            return f"⚠️ ACCEPTABLE ({self.quality_score:.0f}/100)"
        else:
            warning = " - VALUE TRAP WARNING!" if self.value_trap_warning else ""
            return f"🚨 HIGH RISK/TRASH ({self.quality_score:.0f}/100){warning}"


class QualityScoreAnalyzer:
    """
    Analyzes fundamental quality of companies
    """
    
    # Thresholds
    ROE_TARGET = 0.15  # 15%
    DEBT_TARGET = 1.0  # Debt/Equity < 1.0
    
    # Sector average P/E (approximate benchmarks)
    SECTOR_PE_BENCHMARKS = {
        "Technology": 25.0,
        "Healthcare": 20.0,
        "Financial Services": 12.0,
        "Consumer Cyclical": 18.0,
        "Consumer Defensive": 20.0,
        "Industrials": 18.0,
        "Energy": 15.0,
        "Basic Materials": 16.0,
        "Communication Services": 20.0,
        "Utilities": 18.0,
        "Real Estate": 22.0,
    }
    DEFAULT_SECTOR_PE = 18.0  # Default if sector unknown
    
    def __init__(self):
        pass
    
    def analyze_quality(self, ticker: str) -> QualityScoreAnalysis:
        """
        Analyze fundamental quality of a company
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            QualityScoreAnalysis with quality score and metrics
        """
        
        try:
            # Fetch company info
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info
            
            # Extract metrics
            company_name = info.get('longName', ticker)
            sector = info.get('sector', 'Unknown')
            industry = info.get('industry', 'Unknown')
            
            # 1. Profitability: ROE
            roe = info.get('returnOnEquity')
            roe_score = self._calculate_roe_score(roe)
            
            # 2. Solvency: Debt/Equity
            debt_to_equity = info.get('debtToEquity')
            debt_score = self._calculate_debt_score(debt_to_equity)
            
            # 3. Value: P/E vs sector
            trailing_pe = info.get('trailingPE')
            sector_avg_pe = self.SECTOR_PE_BENCHMARKS.get(sector, self.DEFAULT_SECTOR_PE)
            value_score = self._calculate_value_score(trailing_pe, sector_avg_pe)
            
            # Calculate total quality score
            quality_score = roe_score + debt_score + value_score
            
            # Determine risk category
            if quality_score >= 80:
                risk_category = "HIGH QUALITY"
                value_trap_warning = False
            elif quality_score >= 40:
                risk_category = "ACCEPTABLE"
                value_trap_warning = False
            else:
                risk_category = "HIGH RISK/TRASH"
                # Value trap if low quality but appears "cheap" on P/E
                value_trap_warning = (trailing_pe is not None and 
                                     trailing_pe < sector_avg_pe and
                                     quality_score < 40)
            
            return QualityScoreAnalysis(
                ticker=ticker,
                quality_score=quality_score,
                roe=roe,
                roe_score=roe_score,
                debt_to_equity=debt_to_equity,
                debt_score=debt_score,
                trailing_pe=trailing_pe,
                sector_avg_pe=sector_avg_pe,
                value_score=value_score,
                risk_category=risk_category,
                value_trap_warning=value_trap_warning,
                company_name=company_name,
                sector=sector,
                industry=industry
            )
        
        except Exception as e:
            print(f"   ⚠️ Quality analysis failed for {ticker}: {e}")
            # Return default/unavailable analysis
            return QualityScoreAnalysis(
                ticker=ticker,
                quality_score=0.0,
                roe=None,
                roe_score=0.0,
                debt_to_equity=None,
                debt_score=0.0,
                trailing_pe=None,
                sector_avg_pe=self.DEFAULT_SECTOR_PE,
                value_score=0.0,
                risk_category="DATA UNAVAILABLE",
                value_trap_warning=False,
                company_name=ticker,
                sector="Unknown",
                industry="Unknown"
            )
    
    def _calculate_roe_score(self, roe: Optional[float]) -> float:
        """
        Calculate ROE score (0-40 points)
        
        Target: ROE > 15% = 40 points
        
        Args:
            roe: Return on Equity (as decimal, e.g., 0.20 for 20%)
        
        Returns:
            Score 0-40
        """
        if roe is None or roe <= 0:
            return 0.0
        
        # ROE > 15% = full 40 points
        if roe >= self.ROE_TARGET:
            return 40.0
        
        # Scale linearly from 0 to 40 points for ROE 0% to 15%
        score = (roe / self.ROE_TARGET) * 40.0
        return max(0.0, min(40.0, score))
    
    def _calculate_debt_score(self, debt_to_equity: Optional[float]) -> float:
        """
        Calculate Debt/Equity score (0-40 points)
        
        Target: D/E < 1.0 = 40 points
        Lower debt = higher score
        
        Args:
            debt_to_equity: Debt to Equity ratio (can be in % or ratio format from yfinance)
        
        Returns:
            Score 0-40
        """
        if debt_to_equity is None:
            return 0.0
        
        # yfinance sometimes returns D/E as percentage (e.g., 50.0 for 0.5)
        # Normalize to ratio format
        if debt_to_equity > 10:  # Likely percentage
            debt_to_equity = debt_to_equity / 100.0
        
        # Negative debt/equity (net cash position) = full points
        if debt_to_equity <= 0:
            return 40.0
        
        # D/E < 1.0 = full 40 points
        if debt_to_equity < self.DEBT_TARGET:
            return 40.0
        
        # Scale down for higher debt
        # D/E = 1.0 → 40 points
        # D/E = 2.0 → 20 points
        # D/E = 3.0 → 10 points
        # D/E > 4.0 → 0 points
        score = 40.0 * (4.0 - debt_to_equity) / 3.0
        return max(0.0, min(40.0, score))
    
    def _calculate_value_score(self, trailing_pe: Optional[float], 
                               sector_avg_pe: float) -> float:
        """
        Calculate Value score (0-20 points)
        
        Target: P/E below sector average = 20 points
        
        Args:
            trailing_pe: Trailing P/E ratio
            sector_avg_pe: Sector average P/E
        
        Returns:
            Score 0-20
        """
        if trailing_pe is None or trailing_pe <= 0:
            return 0.0
        
        # P/E below sector average = 20 points
        if trailing_pe < sector_avg_pe:
            # Linear scale: 50% below sector avg = 20 points
            discount_pct = (sector_avg_pe - trailing_pe) / sector_avg_pe
            score = min(20.0, discount_pct * 40.0)  # 50% discount = 20 pts
            return score
        
        # P/E at or above sector average = reduced points
        # P/E = sector avg → 10 points
        # P/E = 2x sector avg → 0 points
        if trailing_pe >= sector_avg_pe * 2:
            return 0.0
        
        premium_pct = (trailing_pe - sector_avg_pe) / sector_avg_pe
        score = 10.0 * (1.0 - premium_pct)
        return max(0.0, min(10.0, score))


def format_quality_summary(analysis: QualityScoreAnalysis) -> str:
    """
    Format quality analysis into readable summary
    
    Args:
        analysis: QualityScoreAnalysis object
    
    Returns:
        Multi-line string summary
    """
    summary = []
    summary.append(f"QUALITY SCORE: {analysis.quality_score:.0f}/100")
    summary.append(f"Category: {analysis.risk_category}")
    if analysis.value_trap_warning:
        summary.append("🚨 VALUE TRAP WARNING - Low quality despite cheap valuation")
    summary.append("")
    
    summary.append(f"Company: {analysis.company_name}")
    summary.append(f"Sector: {analysis.sector}")
    summary.append(f"Industry: {analysis.industry}")
    summary.append("")
    
    summary.append("PROFITABILITY (0-40 pts):")
    if analysis.roe is not None:
        summary.append(f"  ROE: {analysis.roe*100:.1f}% (target: >15%)")
        summary.append(f"  Score: {analysis.roe_score:.0f}/40")
    else:
        summary.append(f"  ROE: N/A")
        summary.append(f"  Score: 0/40")
    summary.append("")
    
    summary.append("SOLVENCY (0-40 pts):")
    if analysis.debt_to_equity is not None:
        # Display in ratio format
        de_ratio = analysis.debt_to_equity / 100 if analysis.debt_to_equity > 10 else analysis.debt_to_equity
        summary.append(f"  Debt/Equity: {de_ratio:.2f} (target: <1.0)")
        summary.append(f"  Score: {analysis.debt_score:.0f}/40")
    else:
        summary.append(f"  Debt/Equity: N/A")
        summary.append(f"  Score: 0/40")
    summary.append("")
    
    summary.append("VALUE (0-20 pts):")
    if analysis.trailing_pe is not None:
        summary.append(f"  P/E: {analysis.trailing_pe:.1f}")
        summary.append(f"  Sector Avg P/E: {analysis.sector_avg_pe:.1f}")
        discount = ((analysis.sector_avg_pe - analysis.trailing_pe) / analysis.sector_avg_pe) * 100
        summary.append(f"  vs Sector: {discount:+.1f}%")
        summary.append(f"  Score: {analysis.value_score:.0f}/20")
    else:
        summary.append(f"  P/E: N/A")
        summary.append(f"  Score: 0/20")
    
    return "\n".join(summary)
