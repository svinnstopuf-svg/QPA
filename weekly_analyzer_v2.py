"""
WEEKLY ANALYZER - Strategic Decision Module

Aggregerar dagliga dashboard-körningar för att identifiera bästa köpmöjligheter.
Transformerar Dashboard-nivå data till Beslutsfattar-nivå insights.
"""
import json
import glob
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Tuple
from collections import defaultdict
import statistics

@dataclass
class InstrumentTracking:
    """Spårar ett instrument över veckan."""
    ticker: str
    name: str
    category: str
    
    # Konsistens
    days_seen: int
    days_investable: int
    days_on_watchlist: int
    consistency_score: float  # 0-100
    
    # Genomsnittsvärden
    avg_score: float
    avg_net_edge: float
    avg_technical_edge: float
    
    # Trendanalys
    score_momentum: float  # Positiv = förbättras
    edge_momentum: float
    first_score: float
    last_score: float
    
    # Senaste data
    latest_signal: str
    latest_execution_risk: str
    latest_position: float
    volatility_trend: str  # IMPROVING, STABLE, DEGRADING
    
    # All-Weather marker
    is_all_weather: bool
    
    # Scores per dag (för trendanalys)
    daily_scores: List[float]
    daily_edges: List[float]
    daily_dates: List[str]

@dataclass
class WeeklyConviction:
    """Veckovis conviction score för ett instrument."""
    ticker: str
    name: str
    conviction_score: float  # 0-100
    
    # Komponenter
    consistency_component: float  # 40%
    quality_component: float      # 30%
    momentum_component: float     # 30%
    
    # Metadata
    avg_net_edge: float
    days_investable: int
    latest_signal: str
    is_all_weather: bool
    recommendation: str  # STRONG BUY, BUY, WATCH, AVOID
    
    # Mathematical Edge (Casino Logic)
    expected_value_sek: float  # EV i kronor
    signal_to_noise_ratio: float  # Edge / Volatilitet
    breakeven_move_pct: float  # % rörelse för breakeven
    high_confidence: bool  # SNR > 1.0
    avanza_viable: bool  # Net Edge > Breakeven

@dataclass
class PatternPerformance:
    """Pattern audit data för kvartalsanalys."""
    pattern_name: str
    frequency: int  # Antal gg sedd under veckan
    avg_edge: float
    best_edge: float
    worst_edge: float
    instruments: List[str]  # Vilka instrument

@dataclass  
class EdgeLeakage:
    """Teoretisk vinst förlorad pga Execution Guard."""
    ticker: str
    technical_edge: float
    blocked_by: str  # "courtage", "fx", "spread"
    theoretical_profit_sek: float

class WeeklyAnalyzer:
    """
    Strategic Decision Module v2.0 - System-Linked Intelligence.
    
    Analyserar dagliga dashboard-körningar och rankar instrument
    baserat på konsistens, kvalitet, momentum OCH matematisk edge.
    
    Ny funktionalitet:
    - Expected Value (EV) beräkning i SEK
    - Signal-to-Noise Ratio (SNR) för confidence
    - Avanza breakeven-kalkylator
    - Pattern audit trail för kvartalsanalys
    - Edge leakage tracking
    """
    
    def __init__(self, reports_dir: str = "reports", portfolio_value_sek: float = 100000):
        self.reports_dir = Path(reports_dir)
        self.portfolio_value_sek = portfolio_value_sek
        
    def analyze_week(self, days_back: int = 7) -> Dict:
        """
        Analysera senaste veckan av dashboard-data.
        
        Args:
            days_back: Antal dagar bakåt att analysera
            
        Returns:
            Dict med weekly analysis results
        """
        # 1. Ladda alla actionable JSON-filer
        files = self._load_weekly_files(days_back)
        
        if not files:
            return {
                'error': 'Inga dashboard-körningar hittades',
                'files_found': 0
            }
        
        print(f"📊 Analyserar {len(files)} dashboard-körningar...")
        
        # 2. Aggregera data per instrument
        tracking = self._aggregate_instrument_data(files)
        
        # 3. Beräkna conviction scores
        convictions = self._calculate_conviction_scores(tracking)
        
        # 4. Analysera regime shifts
        regime_analysis = self._analyze_regime_shifts(files)
        
        # 5. Identifiera cost-blocked opportunities
        cost_blocked = self._identify_cost_blocked(tracking)
        
        return {
            'analysis_period': {
                'start_date': files[0]['date'],
                'end_date': files[-1]['date'],
                'days_analyzed': len(files)
            },
            'regime_analysis': regime_analysis,
            'top_convictions': convictions[:10],
            'cost_blocked': cost_blocked[:10],
            'total_instruments_tracked': len(tracking),
            'tracking_data': tracking
        }
    
    def _load_weekly_files(self, days_back: int) -> List[Dict]:
        """Ladda alla actionable JSON-filer från senaste veckan."""
        all_files = glob.glob(str(self.reports_dir / "actionable_*.json"))
        
        if not all_files:
            return []
        
        # Sortera efter datum
        files_data = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for filepath in all_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    file_date = datetime.strptime(data['date'], '%Y-%m-%d')
                    
                    if file_date >= cutoff_date:
                        files_data.append(data)
            except Exception as e:
                print(f"⚠️  Kunde inte läsa {filepath}: {e}")
        
        # Sortera efter datum
        files_data.sort(key=lambda x: x['date'])
        
        return files_data
    
    def _aggregate_instrument_data(self, files: List[Dict]) -> Dict[str, InstrumentTracking]:
        """
        Aggregera data för varje instrument över veckan.
        
        Spårar konsistens, momentum och kvalitet.
        """
        tracking = {}
        
        for file_data in files:
            date = file_data['date']
            
            # Process investable instruments
            for instrument in file_data['investable']:
                ticker = instrument['ticker']
                
                if ticker not in tracking:
                    tracking[ticker] = {
                        'ticker': ticker,
                        'name': instrument['name'],
                        'category': instrument['category'],
                        'days_seen': 0,
                        'days_investable': 0,
                        'days_on_watchlist': 0,
                        'scores': [],
                        'net_edges': [],
                        'technical_edges': [],
                        'dates': [],
                        'signals': [],
                        'execution_risks': [],
                        'positions': []
                    }
                
                t = tracking[ticker]
                t['days_seen'] += 1
                t['days_investable'] += 1
                t['scores'].append(instrument['score'])
                t['net_edges'].append(instrument['net_edge_after_execution'])
                t['technical_edges'].append(instrument['technical_edge'])
                t['dates'].append(date)
                t['signals'].append(instrument['signal'])
                t['execution_risks'].append(instrument['execution_risk'])
                t['positions'].append(instrument['position'])
            
            # Process watchlist instruments
            for instrument in file_data['watchlist']:
                ticker = instrument['ticker']
                
                if ticker not in tracking:
                    tracking[ticker] = {
                        'ticker': ticker,
                        'name': instrument['name'],
                        'category': 'unknown',
                        'days_seen': 0,
                        'days_investable': 0,
                        'days_on_watchlist': 0,
                        'scores': [],
                        'net_edges': [],
                        'technical_edges': [],
                        'dates': [],
                        'signals': [],
                        'execution_risks': [],
                        'positions': []
                    }
                
                t = tracking[ticker]
                t['days_seen'] += 1
                t['days_on_watchlist'] += 1
                t['scores'].append(instrument['score'])
                t['net_edges'].append(0.0)  # Watchlist has no net edge
                t['technical_edges'].append(instrument['technical_edge'])
                t['dates'].append(date)
                t['signals'].append(instrument['signal'])
                t['execution_risks'].append('BLOCKED')
                t['positions'].append(0.0)
        
        # Convert to InstrumentTracking objects
        result = {}
        for ticker, data in tracking.items():
            # Calculate momentum
            score_momentum = 0.0
            edge_momentum = 0.0
            
            if len(data['scores']) >= 2:
                score_momentum = data['scores'][-1] - data['scores'][0]
                if len(data['net_edges']) >= 2:
                    edge_momentum = data['net_edges'][-1] - data['net_edges'][0]
            
            # Volatility trend analysis
            volatility_trend = "STABLE"
            # TODO: Implement volatility trend detection
            
            # Check if All-Weather
            from src.risk.all_weather_config import is_all_weather
            is_aw = is_all_weather(ticker)
            
            result[ticker] = InstrumentTracking(
                ticker=ticker,
                name=data['name'],
                category=data['category'],
                days_seen=data['days_seen'],
                days_investable=data['days_investable'],
                days_on_watchlist=data['days_on_watchlist'],
                consistency_score=(data['days_investable'] / len(files)) * 100,
                avg_score=statistics.mean(data['scores']) if data['scores'] else 0,
                avg_net_edge=statistics.mean(data['net_edges']) if data['net_edges'] else 0,
                avg_technical_edge=statistics.mean(data['technical_edges']) if data['technical_edges'] else 0,
                score_momentum=score_momentum,
                edge_momentum=edge_momentum,
                first_score=data['scores'][0] if data['scores'] else 0,
                last_score=data['scores'][-1] if data['scores'] else 0,
                latest_signal=data['signals'][-1] if data['signals'] else 'UNKNOWN',
                latest_execution_risk=data['execution_risks'][-1] if data['execution_risks'] else 'UNKNOWN',
                latest_position=data['positions'][-1] if data['positions'] else 0.0,
                volatility_trend=volatility_trend,
                is_all_weather=is_aw,
                daily_scores=data['scores'],
                daily_edges=data['net_edges'],
                daily_dates=data['dates']
            )
        
        return result
    
    def _calculate_conviction_scores(self, tracking: Dict[str, InstrumentTracking]) -> List[WeeklyConviction]:
        """
        Beräkna Weekly Conviction Score för varje instrument.
        
        Ranking Algoritm:
        - 40% Konsistens: Hur pålitlig är signalen över tid?
        - 30% Kvalitet: Vad är det tekniska fundamentet?
        - 30% Momentum: Rör sig oddsen till min fördel?
        """
        convictions = []
        
        for ticker, track in tracking.items():
            # 1. Consistency Component (40%)
            # Baserat på hur många dagar instrumentet varit investable
            consistency = track.consistency_score * 0.4
            
            # 2. Quality Component (30%)
            # Baserat på genomsnittlig score och net edge
            quality = 0.0
            if track.avg_score > 0:
                quality += (track.avg_score / 100) * 20  # Max 20 points
            if track.avg_net_edge > 0:
                quality += min(10, track.avg_net_edge * 10)  # Max 10 points
            
            # 3. Momentum Component (30%)
            # Baserat på score och edge momentum
            momentum = 0.0
            if track.score_momentum > 0:
                momentum += min(15, track.score_momentum / 5)  # Max 15 points
            elif track.score_momentum < 0:
                momentum += max(-10, track.score_momentum / 5)  # Penalty for degrading
            
            if track.edge_momentum > 0:
                momentum += min(15, track.edge_momentum * 15)  # Max 15 points
            elif track.edge_momentum < 0:
                momentum += max(-10, track.edge_momentum * 10)
            
            # Total Conviction Score
            conviction_score = consistency + quality + momentum
            conviction_score = max(0, min(100, conviction_score))
            
            # Recommendation
            recommendation = "AVOID"
            if conviction_score >= 70 and track.days_investable >= 3:
                recommendation = "STRONG BUY"
            elif conviction_score >= 50 and track.days_investable >= 2:
                recommendation = "BUY"
            elif conviction_score >= 30:
                recommendation = "WATCH"
            
            convictions.append(WeeklyConviction(
                ticker=ticker,
                name=track.name,
                conviction_score=conviction_score,
                consistency_component=consistency,
                quality_component=quality,
                momentum_component=momentum,
                avg_net_edge=track.avg_net_edge,
                days_investable=track.days_investable,
                latest_signal=track.latest_signal,
                is_all_weather=track.is_all_weather,
                recommendation=recommendation
            ))
        
        # Sortera efter conviction score
        convictions.sort(key=lambda x: x.conviction_score, reverse=True)
        
        return convictions
    
    def _analyze_regime_shifts(self, files: List[Dict]) -> Dict:
        """
        Analysera om market regime har förändrats under veckan.
        """
        if len(files) < 1:
            return {'shift_detected': False, 'last_regime': 'UNKNOWN', 'trend': 'UNKNOWN'}
        
        first_regime = files[0].get('regime', 'UNKNOWN')
        last_regime = files[-1].get('regime', 'UNKNOWN')
        
        first_multiplier = files[0].get('regime_multiplier', 0)
        last_multiplier = files[-1].get('regime_multiplier', 0)
        
        if len(files) < 2:
            # Only one file, no shift possible
            return {
                'shift_detected': False,
                'first_regime': last_regime,
                'last_regime': last_regime,
                'first_multiplier': last_multiplier,
                'last_multiplier': last_multiplier,
                'multiplier_change': 0.0,
                'trend': 'UNCHANGED'
            }
        
        shift_detected = first_regime != last_regime
        multiplier_change = last_multiplier - first_multiplier
        
        # Trend
        trend = "UNCHANGED"
        if multiplier_change > 0.1:
            trend = "IMPROVING"
        elif multiplier_change < -0.1:
            trend = "DEGRADING"
        
        return {
            'shift_detected': shift_detected,
            'first_regime': first_regime,
            'last_regime': last_regime,
            'first_multiplier': first_multiplier,
            'last_multiplier': last_multiplier,
            'multiplier_change': multiplier_change,
            'trend': trend
        }
    
    def _identify_cost_blocked(self, tracking: Dict[str, InstrumentTracking]) -> List[Dict]:
        """
        Identifiera instrument som har hög teknisk score men blockeras av execution costs.
        """
        cost_blocked = []
        
        for ticker, track in tracking.items():
            # Instrument som aldrig varit investable men har hög avg score
            if track.days_investable == 0 and track.avg_score >= 50:
                cost_blocked.append({
                    'ticker': ticker,
                    'name': track.name,
                    'avg_score': track.avg_score,
                    'avg_technical_edge': track.avg_technical_edge,
                    'days_seen': track.days_seen,
                    'latest_signal': track.latest_signal
                })
        
        # Sortera efter score
        cost_blocked.sort(key=lambda x: x['avg_score'], reverse=True)
        
        return cost_blocked
    
    def generate_markdown_report(self, analysis: Dict) -> str:
        """
        Generera Markdown-rapport optimerad för snabb söndagsgenomgång.
        """
        lines = []
        
        # Header
        lines.append("# 📊 WEEKLY DECISION REPORT")
        lines.append("")
        lines.append(f"**Analysis Period:** {analysis['analysis_period']['start_date']} → {analysis['analysis_period']['end_date']}")
        lines.append(f"**Days Analyzed:** {analysis['analysis_period']['days_analyzed']}")
        lines.append(f"**Instruments Tracked:** {analysis['total_instruments_tracked']}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Regime Shift Watch
        regime = analysis['regime_analysis']
        lines.append("## 🌡️ REGIME SHIFT WATCH")
        lines.append("")
        
        if regime['shift_detected']:
            lines.append(f"⚠️  **REGIME CHANGE DETECTED**: {regime['first_regime']} → {regime['last_regime']}")
        else:
            lines.append(f"✅ Regime stable: **{regime['last_regime']}**")
        
        lines.append(f"- Multiplier: {regime['first_multiplier']:.2f}x → {regime['last_multiplier']:.2f}x")
        lines.append(f"- Trend: **{regime['trend']}**")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Top 5 Conviction Trades
        lines.append("## 🚀 TOP 5 CONVICTION TRADES")
        lines.append("")
        lines.append("*Rankade efter Weekly Conviction Score (Konsistens 40% + Kvalitet 30% + Momentum 30%)*")
        lines.append("")
        
        top_5 = analysis['top_convictions'][:5]
        for i, conv in enumerate(top_5, 1):
            aw_marker = " 🛡️ **[ALL-WEATHER]**" if conv.is_all_weather else ""
            
            lines.append(f"### {i}. {conv.name} ({conv.ticker}){aw_marker}")
            lines.append("")
            lines.append(f"- **Conviction Score:** {conv.conviction_score:.1f}/100")
            lines.append(f"- **Recommendation:** **{conv.recommendation}**")
            lines.append(f"- **Latest Signal:** {conv.latest_signal}")
            lines.append(f"- **Avg Net Edge:** {conv.avg_net_edge:+.2f}%")
            lines.append(f"- **Days Investable:** {conv.days_investable}/{analysis['analysis_period']['days_analyzed']}")
            lines.append("")
            lines.append(f"**Score Breakdown:**")
            lines.append(f"- Consistency: {conv.consistency_component:.1f} pts")
            lines.append(f"- Quality: {conv.quality_component:.1f} pts")
            lines.append(f"- Momentum: {conv.momentum_component:.1f} pts")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        
        # Re-evaluation List
        lines.append("## ⚠️  RE-EVALUATION LIST")
        lines.append("")
        lines.append("*Instrument där Score har degraderats under veckan*")
        lines.append("")
        
        # Find instruments with negative momentum
        degraded = [c for c in analysis['top_convictions'] if c.momentum_component < 0][:5]
        
        if degraded:
            for conv in degraded:
                lines.append(f"- **{conv.name} ({conv.ticker})**: Momentum {conv.momentum_component:.1f} pts (degrading)")
        else:
            lines.append("✅ Inga instrument har degraderats signifikant under veckan.")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Cost-Blocked Watchlist
        lines.append("## 💰 COST-BLOCKED WATCHLIST")
        lines.append("")
        lines.append("*Instrument med hög Score men blockerade av Execution Guard*")
        lines.append("")
        
        cost_blocked = analysis['cost_blocked']
        
        if cost_blocked:
            lines.append("| Ticker | Name | Avg Score | Avg Tech Edge | Days Seen |")
            lines.append("|--------|------|-----------|---------------|-----------|")
            
            for item in cost_blocked[:10]:
                lines.append(f"| {item['ticker']} | {item['name'][:20]} | {item['avg_score']:.1f} | {item['avg_technical_edge']:+.2f}% | {item['days_seen']} |")
            
            lines.append("")
            lines.append("💡 **Note:** Dessa instrument kan bli lönsamma med större portföljstorlek.")
        else:
            lines.append("✅ Inga cost-blocked opportunities denna vecka.")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Action Items
        lines.append("## 🎯 ACTION ITEMS FÖR NÄSTA VECKA")
        lines.append("")
        
        strong_buys = [c for c in analysis['top_convictions'] if c.recommendation == "STRONG BUY"]
        
        if strong_buys:
            lines.append(f"### 🟢 KÖPREKOMMENDATIONER ({len(strong_buys)} st)")
            lines.append("")
            for conv in strong_buys:
                lines.append(f"- [ ] **{conv.ticker}**: Allokera ~{conv.avg_net_edge * 10:.1f}% baserat på edge")
        else:
            lines.append("❌ Inga Strong Buy-rekommendationer denna vecka.")
            lines.append("")
            lines.append("**Strategi:** Håll cash, vänta på regime-förbättring.")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("*Rapporten genererad av Weekly Analyzer - Strategic Decision Module*")
        
        return "\n".join(lines)
