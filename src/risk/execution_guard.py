"""
Execution Guard - Minimize Hidden Costs

Ensures theoretical edge actually lands in your account by accounting for:
1. Currency risk (FX Shield) - USD/SEK volatility
2. Transaction fees - Avanza courtage
3. Spreads - Bid-ask spread costs
4. Liquidity - Slippage risk

Philosophy: "Don't let execution costs eat your edge"
"""

import yfinance as yf
import numpy as np
from dataclasses import dataclass
from typing import Optional, Dict
from enum import Enum


class AvanzaAccountType(Enum):
    """Avanza account types with different fee structures"""
    START = "START"  # 0.25% courtage, min 1 SEK
    SMALL = "SMALL"  # 0.15% courtage, min 39 SEK
    MEDIUM = "MEDIUM"  # 0.10% courtage, min 69 SEK


@dataclass
class FXRiskAnalysis:
    """Currency risk analysis"""
    current_rate: float  # Current USD/SEK rate
    mean_rate: float  # 20-day SMA
    std_dev: float  # 20-day standard deviation
    sigma_level: float  # How many sigmas from mean
    is_expensive: bool  # > +2 sigma
    risk_level: str  # LOW, MEDIUM, HIGH, EXTREME
    message: str


@dataclass
class FeeAnalysis:
    """Transaction fee analysis"""
    courtage_sek: float  # Courtage in SEK
    courtage_pct: float  # Courtage as % of position
    spread_cost_pct: float  # Estimated spread cost
    total_cost_pct: float  # Total execution cost %
    cost_to_edge_ratio: float  # Cost / Net Edge
    is_acceptable: bool  # < 30% of edge
    message: str


@dataclass
class LiquidityAnalysis:
    """Liquidity and slippage analysis"""
    avg_volume: float  # Average daily volume
    position_vs_volume_pct: float  # Position size / daily volume
    estimated_slippage_pct: float  # Expected slippage
    has_liquidity_risk: bool  # Position > 2% of volume
    message: str


@dataclass
class ExecutionGuardResult:
    """Complete execution guard analysis"""
    fx_risk: Optional[FXRiskAnalysis]
    fee_analysis: FeeAnalysis
    liquidity: LiquidityAnalysis
    total_execution_cost_pct: float  # All costs combined
    execution_risk_level: str  # LOW, MEDIUM, HIGH, EXTREME
    warnings: list  # List of warning messages
    avanza_recommendation: str  # Product recommendation


class ExecutionGuard:
    """
    Guards against execution costs eating your edge.
    
    Professional traders know: It's not just about finding edge,
    it's about keeping it after execution.
    """
    
    # Estimated spreads by instrument type (%)
    SPREADS = {
        'stock_us_liquid': 0.05,  # Large cap US stocks
        'stock_us_small': 0.15,   # Small cap US stocks
        'stock_swedish': 0.10,    # Swedish stocks
        'etf_liquid': 0.05,       # Liquid ETFs (SPY, QQQ)
        'etf_sector': 0.10,       # Sector ETFs
        'etf_commodity': 0.20,    # Commodity ETFs
        'etf_inverse': 0.25,      # Inverse/leveraged ETFs
        'default': 0.15
    }
    
    def __init__(
        self,
        account_type: AvanzaAccountType = AvanzaAccountType.SMALL,
        portfolio_value_sek: float = 100000
    ):
        """
        Initialize execution guard.
        
        Args:
            account_type: Avanza account type (START/SMALL/MEDIUM)
            portfolio_value_sek: Total portfolio value in SEK
        """
        self.account_type = account_type
        self.portfolio_value_sek = portfolio_value_sek
    
    def analyze_fx_risk(self, ticker: str) -> Optional[FXRiskAnalysis]:
        """
        Analyze currency risk for USD instruments.
        
        Checks if USD/SEK is trading at extremes (>+2 sigma).
        You don't want to buy at the dollar top!
        
        Args:
            ticker: Instrument ticker
            
        Returns:
            FXRiskAnalysis or None if not USD instrument or data unavailable
        """
        # Check if US instrument (needs FX consideration)
        if not any(x in ticker for x in ['^', 'US', 'stock_us', 'etf_']) and '.ST' in ticker:
            return None  # Swedish stock, no FX risk
        
        try:
            # Fetch USD/SEK data
            usdsek = yf.Ticker("SEK=X")
            hist = usdsek.history(period="3mo")
            
            if hist.empty or len(hist) < 20:
                return None
            
            # Calculate 20-day SMA and std dev
            recent = hist['Close'].tail(20)
            current_rate = hist['Close'].iloc[-1]
            mean_rate = recent.mean()
            std_dev = recent.std()
            
            # Calculate sigma level
            sigma_level = (current_rate - mean_rate) / std_dev if std_dev > 0 else 0
            
            is_expensive = sigma_level > 2.0
            
            # Determine risk level
            if sigma_level > 3.0:
                risk_level = "EXTREME"
                message = f"🚨 USD EXTREMT DYR (+{sigma_level:.1f}σ) - vänta på bättre FX-läge!"
            elif sigma_level > 2.0:
                risk_level = "HIGH"
                message = f"⚠️ USD DYR (+{sigma_level:.1f}σ) - överväg SEK-säkrat alternativ"
            elif sigma_level > 1.0:
                risk_level = "MEDIUM"
                message = f"USD något dyr (+{sigma_level:.1f}σ) - FX-risk finns"
            elif sigma_level < -2.0:
                risk_level = "LOW"
                message = f"✅ USD BILLIG ({sigma_level:.1f}σ) - bra FX-läge!"
            else:
                risk_level = "LOW"
                message = f"USD neutral ({sigma_level:+.1f}σ)"
            
            return FXRiskAnalysis(
                current_rate=current_rate,
                mean_rate=mean_rate,
                std_dev=std_dev,
                sigma_level=sigma_level,
                is_expensive=is_expensive,
                risk_level=risk_level,
                message=message
            )
            
        except Exception as e:
            print(f"⚠️ Kunde inte hämta FX data: {e}")
            return None
    
    def analyze_fees(
        self,
        position_size_pct: float,
        net_edge_pct: float,
        instrument_type: str = 'default'
    ) -> FeeAnalysis:
        """
        Analyze transaction fees and spreads.
        
        Args:
            position_size_pct: Position size as % of portfolio
            net_edge_pct: Expected net edge %
            instrument_type: Type for spread estimation
            
        Returns:
            FeeAnalysis
        """
        # Calculate position value in SEK
        position_value_sek = (position_size_pct / 100) * self.portfolio_value_sek
        
        # Calculate courtage based on account type
        if self.account_type == AvanzaAccountType.START:
            courtage_rate = 0.0025  # 0.25%
            min_courtage = 1
        elif self.account_type == AvanzaAccountType.SMALL:
            courtage_rate = 0.0015  # 0.15%
            min_courtage = 39
        else:  # MEDIUM
            courtage_rate = 0.0010  # 0.10%
            min_courtage = 69
        
        courtage_sek = max(position_value_sek * courtage_rate, min_courtage)
        courtage_pct = (courtage_sek / position_value_sek) * 100 if position_value_sek > 0 else 0
        
        # Estimate spread cost
        spread_cost_pct = self.SPREADS.get(instrument_type, self.SPREADS['default'])
        
        # Total cost (round-trip: buy + sell)
        total_cost_pct = (courtage_pct * 2) + (spread_cost_pct * 2)
        
        # Cost to edge ratio
        cost_to_edge_ratio = total_cost_pct / net_edge_pct if net_edge_pct > 0 else float('inf')
        
        # Is this acceptable? (<30% of edge)
        is_acceptable = cost_to_edge_ratio < 0.30
        
        # Generate message
        if cost_to_edge_ratio > 0.50:
            message = f"🚨 HÖGA KOSTNADER: {total_cost_pct:.2f}% äter {cost_to_edge_ratio*100:.0f}% av edgen!"
        elif cost_to_edge_ratio > 0.30:
            message = f"⚠️ HÖGA KOSTNADER: {total_cost_pct:.2f}% är {cost_to_edge_ratio*100:.0f}% av edgen"
        elif cost_to_edge_ratio > 0.15:
            message = f"Kostnader OK: {total_cost_pct:.2f}% ({cost_to_edge_ratio*100:.0f}% av edge)"
        else:
            message = f"✅ Låga kostnader: {total_cost_pct:.2f}%"
        
        return FeeAnalysis(
            courtage_sek=courtage_sek,
            courtage_pct=courtage_pct,
            spread_cost_pct=spread_cost_pct,
            total_cost_pct=total_cost_pct,
            cost_to_edge_ratio=cost_to_edge_ratio,
            is_acceptable=is_acceptable,
            message=message
        )
    
    def analyze_liquidity(
        self,
        ticker: str,
        position_value_sek: float,
        avg_price: float = 100
    ) -> LiquidityAnalysis:
        """
        Analyze liquidity and slippage risk.
        
        Args:
            ticker: Instrument ticker
            position_value_sek: Position size in SEK
            avg_price: Average price for shares calculation
            
        Returns:
            LiquidityAnalysis
        """
        try:
            # Fetch volume data
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1mo")
            
            if hist.empty:
                return LiquidityAnalysis(
                    avg_volume=0,
                    position_vs_volume_pct=0,
                    estimated_slippage_pct=0,
                    has_liquidity_risk=False,
                    message="⚠️ Ingen volymdata tillgänglig"
                )
            
            avg_volume = hist['Volume'].mean()
            
            # Estimate shares to buy (assuming USD/SEK ~10 for simplicity)
            usd_to_sek = 10
            shares_to_buy = position_value_sek / (avg_price * usd_to_sek)
            
            # Position vs daily volume
            position_vs_volume_pct = (shares_to_buy / avg_volume) * 100 if avg_volume > 0 else 0
            
            # Estimate slippage based on position size
            if position_vs_volume_pct > 5:
                estimated_slippage_pct = 1.0  # Very high slippage
                has_liquidity_risk = True
                message = f"🚨 LIKVIDITETSRISK: Position är {position_vs_volume_pct:.1f}% av volymen!"
            elif position_vs_volume_pct > 2:
                estimated_slippage_pct = 0.5
                has_liquidity_risk = True
                message = f"⚠️ LÅG LIKVIDITET: Position är {position_vs_volume_pct:.1f}% av volymen"
            elif position_vs_volume_pct > 1:
                estimated_slippage_pct = 0.2
                has_liquidity_risk = False
                message = f"Måttlig likviditet ({position_vs_volume_pct:.1f}% av volym)"
            else:
                estimated_slippage_pct = 0.05
                has_liquidity_risk = False
                message = f"✅ God likviditet ({position_vs_volume_pct:.2f}% av volym)"
            
            return LiquidityAnalysis(
                avg_volume=avg_volume,
                position_vs_volume_pct=position_vs_volume_pct,
                estimated_slippage_pct=estimated_slippage_pct,
                has_liquidity_risk=has_liquidity_risk,
                message=message
            )
            
        except Exception as e:
            return LiquidityAnalysis(
                avg_volume=0,
                position_vs_volume_pct=0,
                estimated_slippage_pct=0.1,
                has_liquidity_risk=False,
                message=f"⚠️ Kunde inte analysera likviditet: {e}"
            )
    
    def get_avanza_recommendation(
        self,
        ticker: str,
        category: str,
        fx_risk: Optional[FXRiskAnalysis]
    ) -> str:
        """
        Recommend best Avanza product type.
        
        Args:
            ticker: Instrument ticker
            category: Instrument category
            fx_risk: FX risk analysis
            
        Returns:
            Product recommendation string
        """
        # US stocks with high FX risk
        if fx_risk and fx_risk.is_expensive and 'stock_us' in category:
            return "Överväg SEK-säkrat certifikat eller vänta på bättre FX-läge"
        
        # Inverse/leveraged products
        if ticker in ['SH', 'PSQ', 'SQQQ', 'SPXS', 'VIXY', 'UVXY']:
            return "⚠️ VARNING: Daily reset - endast för kortsiktig hedging!"
        
        # Commodities
        if 'commodity' in category or ticker in ['GLD', 'SLV', 'USO', 'UNG']:
            return "Prioritera XACT eller iShares ETF framför certifikat (lägre avgifter)"
        
        # Swedish stocks
        if '.ST' in ticker:
            return "Köp direkt - inga FX-risker"
        
        # Default
        return "Köp lämpligaste produkt på Avanza"
    
    def analyze(
        self,
        ticker: str,
        category: str,
        position_size_pct: float,
        net_edge_pct: float
    ) -> ExecutionGuardResult:
        """
        Complete execution guard analysis.
        
        Args:
            ticker: Instrument ticker
            category: Instrument category
            position_size_pct: Position size as % of portfolio
            net_edge_pct: Expected net edge %
            
        Returns:
            ExecutionGuardResult with all analyses
        """
        # FX risk analysis
        fx_risk = self.analyze_fx_risk(ticker)
        
        # Fee analysis
        fee_analysis = self.analyze_fees(position_size_pct, net_edge_pct, category)
        
        # Liquidity analysis
        position_value_sek = (position_size_pct / 100) * self.portfolio_value_sek
        liquidity = self.analyze_liquidity(ticker, position_value_sek)
        
        # Total execution cost
        total_execution_cost_pct = fee_analysis.total_cost_pct + liquidity.estimated_slippage_pct
        if fx_risk and fx_risk.is_expensive:
            total_execution_cost_pct += 1.0  # Add FX risk premium
        
        # Collect warnings
        warnings = []
        if fx_risk and fx_risk.risk_level in ["HIGH", "EXTREME"]:
            warnings.append(fx_risk.message)
        if not fee_analysis.is_acceptable:
            warnings.append(fee_analysis.message)
        if liquidity.has_liquidity_risk:
            warnings.append(liquidity.message)
        
        # Determine overall execution risk level
        if len(warnings) >= 3 or (fx_risk and fx_risk.risk_level == "EXTREME"):
            execution_risk_level = "EXTREME"
        elif len(warnings) >= 2:
            execution_risk_level = "HIGH"
        elif len(warnings) >= 1:
            execution_risk_level = "MEDIUM"
        else:
            execution_risk_level = "LOW"
        
        # Get Avanza recommendation
        avanza_rec = self.get_avanza_recommendation(ticker, category, fx_risk)
        
        return ExecutionGuardResult(
            fx_risk=fx_risk,
            fee_analysis=fee_analysis,
            liquidity=liquidity,
            total_execution_cost_pct=total_execution_cost_pct,
            execution_risk_level=execution_risk_level,
            warnings=warnings,
            avanza_recommendation=avanza_rec
        )


if __name__ == "__main__":
    # Test execution guard
    print("🛡️ TESTING EXECUTION GUARD")
    print("=" * 80)
    
    guard = ExecutionGuard(
        account_type=AvanzaAccountType.SMALL,
        portfolio_value_sek=100000
    )
    
    # Test NVDA (US stock)
    result = guard.analyze(
        ticker="NVDA",
        category="stock_us_tech",
        position_size_pct=2.5,
        net_edge_pct=1.5
    )
    
    print(f"\nTicker: NVDA")
    print(f"Position: 2.5% (2,500 SEK)")
    print(f"Net Edge: 1.5%")
    print()
    
    if result.fx_risk:
        print(f"FX Risk: {result.fx_risk.message}")
    print(f"Fees: {result.fee_analysis.message}")
    print(f"Liquidity: {result.liquidity.message}")
    print()
    print(f"Total Execution Cost: {result.total_execution_cost_pct:.2f}%")
    print(f"Execution Risk: {result.execution_risk_level}")
    print(f"\nAvanza Recommendation: {result.avanza_recommendation}")
    
    if result.warnings:
        print(f"\n⚠️ WARNINGS:")
        for w in result.warnings:
            print(f"  - {w}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
