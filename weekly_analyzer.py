"""
WEEKLY ANALYZER - Strategic Decision Module

Aggregerar dagliga dashboard-körningar för att identifiera bästa köpmöjligheter.
Transformerar Dashboard-nivå data till Beslutsfattar-nivå insights.
"""
import json
import glob
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import numpy as np
import yfinance as yf
from collections import defaultdict
import statistics

# V3.0: Recency Weighting (Week 2 MEDIUM PRIORITY)
from src.filters.recency_weighting import RecencyWeighting
# V3.0: Sector Cap (Week 3 - portfolio intelligence)
from src.risk.sector_cap_manager import SectorCapManager
# V3.0: Beta-Alpha Separation (Week 2 - quality filter)
from src.analysis.beta_alpha_separator import BetaAlphaSeparator
# V3.0: MAE Optimizer (Week 3 - stop-loss calculation)
from src.risk.mae_optimizer import MAEOptimizer

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
    
    # V3.0: Signal Decay
    days_since_last_investable: int = 0  # Staleness metric

@dataclass
class RiskAnalysis:
    """Probabilistic risk analysis för ett instrument."""
    ticker: str
    probability_of_stopout: float  # 0-100%, risk att träffa -5% drawdown
    mean_return_10d: float  # Förväntad avkastning 10 dagar
    worst_case_10d: float  # 5th percentile
    best_case_10d: float  # 95th percentile
    risk_rating: str  # LOW RISK, STABLE, DANGEROUS
    monte_carlo_paths: int = 500

@dataclass
class CorrelationCluster:
    """Grupp av instrument med hög korrelation."""
    tickers: List[str]
    avg_correlation: float
    recommended_ticker: str  # Den med högst SNR
    risk_warning: str

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
    
    # Mathematical Edge (Casino Logic) - Modul 1
    expected_value_sek: float = 0.0  # Net EV (efter courtage) - POCKET MONEY
    theoretical_ev_sek: float = 0.0  # Theoretical EV (utan courtage) - ARCHITECT'S OPPORTUNITY
    signal_to_noise_ratio: float = 0.0
    breakeven_move_pct: float = 0.0
    high_confidence: bool = False
    avanza_viable: bool = False
    
    # Probabilistic Risk (Modul 5)
    risk_analysis: Optional[RiskAnalysis] = None
    in_correlation_cluster: bool = False
    cluster_warning: str = ""
    
    # Re-Entry Trigger (Modul 6)
    re_entry_trigger: str = ""  # Vad krävs för att gå från AVOID till BUY?
    
    # V3.0: Beta-Alpha Separation
    alpha_vs_benchmark: float = 0.0  # Alpha vs OMXS30
    beta: float = 0.0  # Beta coefficient
    has_positive_alpha: bool = False
    
    # V3.0: Sector Cap
    sector: str = "unknown"
    sector_allocation_pct: float = 0.0  # Portfolio % in this sector
    exceeds_sector_cap: bool = False
    
    # V3.0: MAE Stop-Loss
    optimal_stop_loss_pct: float = 0.0  # MAE-based stop
    mae_confidence: str = "UNKNOWN"  # LOW, MEDIUM, HIGH

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
    
    def __init__(self, reports_dir: str = "reports", portfolio_value_sek: float = 100000, use_backfill: bool = False):
        self.portfolio_value_sek = portfolio_value_sek
        self.use_backfill = use_backfill
        
        # V3.0: Initialize Recency Weighting
        self.recency_weighting = RecencyWeighting(
            full_strength_days=30,
            half_strength_days=60,
            minimum_weight=0.1
        )
        
        # V3.0: Initialize Sector Cap Manager
        self.sector_cap = SectorCapManager(max_sector_pct=0.40)
        
        # V3.0: Initialize Beta-Alpha Separator
        self.beta_alpha = BetaAlphaSeparator(market_ticker="^OMX")
        
        # V3.0: Initialize MAE Optimizer
        self.mae_optimizer = MAEOptimizer()
        
        # Smart directory selection: kolla båda platser
        backfill_dir = Path("reports/backfill")
        normal_dir = Path(reports_dir)
        
        # Räkna filer i båda directories
        backfill_files = list(backfill_dir.glob("actionable_*.json")) if backfill_dir.exists() else []
        normal_files = list(normal_dir.glob("actionable_*.json")) if normal_dir.exists() else []
        
        # Använd den med flest filer (eller backfill om lika många)
        if len(backfill_files) > len(normal_files):
            self.reports_dir = backfill_dir
            self.use_backfill = True
            print(f"⚡ Auto-detected: Använder backfill directory ({len(backfill_files)} filer)")
        else:
            self.reports_dir = normal_dir
            self.use_backfill = False if not use_backfill else True
            if len(normal_files) > 0:
                print(f"⚡ Auto-detected: Använder normal directory ({len(normal_files)} filer)")
        
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
        
        # 6. Analysera portföljhälsa (Modul 3: Portfolio Intelligence)
        portfolio_health = self._analyze_portfolio_health(convictions)
        
        # 7. Probabilistic Risk Module (Modul 5)
        print("\n🎲 Kör Probabilistic Risk Analysis (Monte Carlo + Correlation)...")
        
        # Run Monte Carlo for top convictions
        for conv in convictions[:10]:
            # ATR estimate baserat på volatility_trend
            atr_pct = {
                'EXPLOSIVE': 3.0,
                'EXPANDING': 2.0,
                'STABLE': 1.0,
                'CONTRACTING': 0.5
            }.get(tracking[conv.ticker].volatility_trend if conv.ticker in tracking else 'STABLE', 1.5)
            
            # Run Monte Carlo
            risk_analysis = self._run_mini_monte_carlo(conv.ticker, atr_pct)
            conv.risk_analysis = risk_analysis
            
            # Risk-of-Ruin Filter: Ändra recommendation om risk är för hög
            if risk_analysis.probability_of_stopout > 35:
                conv.recommendation = "AVOID"
            elif risk_analysis.probability_of_stopout > 20 and conv.recommendation in ["BUY", "STRONG BUY"]:
                conv.recommendation = "SPECULATIVE"
            
            # === RE-ENTRY TRIGGER (Modul 6) ===
            # Vad krävs för att matematiken vänder till din fördel?
            re_entry_trigger = ""
            
            if conv.recommendation in ["AVOID", "WATCH"]:
                triggers = []
                
                # 1. Conviction Score trigger
                if conv.conviction_score < 50:
                    target_score = 50
                    triggers.append(f"Score → {target_score}+")
                
                # 2. Net Edge trigger (om blockerad av kostnader)
                if conv.avg_net_edge <= 0 and conv.theoretical_ev_sek > 0:
                    triggers.append(f"Net Edge → +{conv.breakeven_move_pct:.2f}% (Avanza breakeven)")
                
                # 3. Consistency trigger
                if conv.days_investable < 2:
                    triggers.append(f"Investable days → 2+")
                
                # 4. SNR trigger
                if conv.signal_to_noise_ratio < 1.0:
                    triggers.append(f"SNR → 1.0+ (high confidence)")
                
                # 5. Stop-Out risk trigger
                if conv.risk_analysis and conv.risk_analysis.probability_of_stopout > 20:
                    triggers.append(f"Stop-Out Risk → <20%")
                
                if triggers:
                    re_entry_trigger = " OR ".join(triggers)
                else:
                    re_entry_trigger = "Redan nära BUY-nivå"
            
            conv.re_entry_trigger = re_entry_trigger
        
        # Check correlation clusters
        correlation_clusters = self._check_correlation_clusters(convictions)
        
        # Mark instruments in clusters
        for cluster in correlation_clusters:
            for ticker in cluster.tickers:
                for conv in convictions:
                    if conv.ticker == ticker:
                        conv.in_correlation_cluster = True
                        if ticker != cluster.recommended_ticker:
                            conv.cluster_warning = f"⚠️  {cluster.risk_warning} - Välj {cluster.recommended_ticker} istället"
                        else:
                            conv.cluster_warning = f"✅ Rekommenderad från cluster (högst SNR)"
        
        # 8. Cash Drag Analysis - Opportunity cost of staying in cash
        cash_drag = self._calculate_cash_drag(len(files))
        
        # 9. Regime Exit Threshold - När går vi från CRISIS till RECOVERY?
        regime_exit_threshold = self._calculate_regime_exit_threshold(files[-1] if files else {})
        
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
            'tracking_data': tracking,
            'portfolio_health': portfolio_health,
            'correlation_clusters': correlation_clusters,
            'risk_analysis_enabled': True,
            'cash_drag': cash_drag,
            'regime_exit_threshold': regime_exit_threshold
        }
    
    def _load_weekly_files(self, days_back: int) -> List[Dict]:
        """Ladda alla actionable JSON-filer från senaste veckan."""
        all_files = glob.glob(str(self.reports_dir / "actionable_*.json"))
        
        if not all_files:
            return []
        
        # Sortera efter datum
        files_data = []
        
        # Smart file loading: om vi har backfill data, använd ALLT
        # Annars använd senaste X dagar
        
        # Kolla om vi har backfill-typ data (mer än 7 dagar)
        if len(all_files) > 7:
            # Läs ALLA filer (troligen backfill eller lång historik)
            for filepath in all_files:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        files_data.append(data)
                except Exception as e:
                    print(f"⚠️  Kunde inte läsa {filepath}: {e}")
        else:
            # Få filer: använd alla oavsett datum
            for filepath in all_files:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
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
                        'positions': [],
                        'investable_flags': []  # V3.0: For recency-weighted consistency
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
                t['investable_flags'].append(True)  # V3.0: Always True for investable
            
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
                'positions': [],
                'execution_risks': [],
                'dates': [],
                'signals': [],
                'investable_flags': []  # V3.0: For recency-weighted consistency
            }
                
                t = tracking[ticker]
                t['days_seen'] += 1
                
                # 100K SYSTEMATIC OVERLAY: Count 1500-floor positions as investable
                # If entry_recommendation starts with "ENTER", it's a valid position
                # (includes "ENTER - 1500 floor" from systematic overlay)
                entry_rec = instrument.get('entry_recommendation', '')
                if entry_rec.startswith('ENTER'):
                    t['days_investable'] += 1
                    # Use actual net edge after execution and position
                    t['net_edges'].append(instrument.get('net_edge_after_execution', 0.0))
                    t['positions'].append(instrument.get('position', 0.0))
                    t['execution_risks'].append(instrument.get('execution_risk', 'UNKNOWN'))
                else:
                    t['days_on_watchlist'] += 1
                    t['net_edges'].append(0.0)  # Blocked watchlist has no net edge
                    t['positions'].append(0.0)
                    t['execution_risks'].append('BLOCKED')
                
                t['scores'].append(instrument['score'])
                t['technical_edges'].append(instrument['technical_edge'])
                t['dates'].append(date)
                t['signals'].append(instrument['signal'])
                
                # V3.0: Track investable flags for recency-weighted consistency
                t['investable_flags'].append(entry_rec.startswith('ENTER'))
        
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
            
            # V3.0: Calculate days since last investable (signal decay metric)
            days_since_last_investable = 0
            if data['dates']:
                # Find the most recent date where instrument was investable
                last_investable_date = None
                for i in range(len(data['dates']) - 1, -1, -1):
                    # Check if this was an investable day (has net edge)
                    if data['net_edges'][i] > 0:
                        last_investable_date = data['dates'][i]
                        break
                
                if last_investable_date:
                    # Calculate days since then
                    try:
                        from datetime import datetime
                        last_date = datetime.strptime(last_investable_date, "%Y-%m-%d")
                        most_recent = datetime.strptime(data['dates'][-1], "%Y-%m-%d")
                        days_since_last_investable = (most_recent - last_date).days
                    except:
                        days_since_last_investable = 0
            
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
                daily_dates=data['dates'],
                days_since_last_investable=days_since_last_investable
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
            # V3.0: Recency-Weighted Consistency - Recent investable days weigh more
            # Old: unweighted consistency_score
            # New: weighted consistency based on recency
            
            # Build investable flags from daily_edges (>0 = investable)
            investable_flags = [edge > 0 for edge in track.daily_edges]
            
            if investable_flags and track.daily_dates:
                weighted_consistency = self.recency_weighting.calculate_weighted_consistency(
                    investable_flags,
                    track.daily_dates
                )
            else:
                # Fallback to unweighted
                weighted_consistency = track.consistency_score
            
            consistency = weighted_consistency * 0.4
            
            # 2. Quality Component (30%)
            # Baserat på genomsnittlig score och net edge
            quality = 0.0
            if track.avg_score > 0:
                quality += (track.avg_score / 100) * 20  # Max 20 points
            if track.avg_net_edge > 0:
                quality += min(10, track.avg_net_edge * 10)  # Max 10 points
            
            # 3. Momentum Component (30%)
            # Baserat på score och edge momentum
            # UPPDATERING: Full penalty range (-15 till +15) för crash protection
            momentum = 0.0
            
            # Score momentum: -15 till +15 poäng
            score_momentum_points = track.score_momentum / 5  # Dividera med 5 för scaling
            score_momentum_points = max(-15, min(15, score_momentum_points))  # Clamp to [-15, +15]
            momentum += score_momentum_points
            
            # Edge momentum: -15 till +15 poäng
            edge_momentum_points = track.edge_momentum * 15  # Multiplicera för scaling
            edge_momentum_points = max(-15, min(15, edge_momentum_points))  # Clamp to [-15, +15]
            momentum += edge_momentum_points
            
            # Total Conviction Score (before decay)
            conviction_score = consistency + quality + momentum
            conviction_score = max(0, min(100, conviction_score))
            
            # V3.0: Signal Decay - Stale signals lose conviction
            # decay_factor = 0.75 ** days_since_last_investable
            # After 3 days: 0.75^3 = 0.42 (conviction halves)
            # After 7 days: 0.75^7 = 0.13 (conviction dies)
            decay_factor = 1.0
            if track.days_since_last_investable > 0:
                decay_factor = 0.75 ** track.days_since_last_investable
                conviction_score *= decay_factor
            
            # === MODUL 1: MATHEMATICAL EDGE ENGINE (Casino Logic) ===
            
            # 1. Expected Value (EV) i SEK
            # Net EV = Vad hamnar i din ficka efter courtage
            position_size_sek = self.portfolio_value_sek * (track.latest_position / 100)
            net_ev_sek = position_size_sek * (track.avg_net_edge / 100)
            
            # Theoretical EV = Vad du kunde tjänat utan courtage (Architect's Opportunity)
            theoretical_ev_sek = 0.0
            if track.avg_technical_edge > 0:
                # Antag en rimlig positionsstorlek baserat på score
                theoretical_position_pct = min(5.0, track.avg_score / 20)  # Max 5% position
                theoretical_position_sek = self.portfolio_value_sek * (theoretical_position_pct / 100)
                theoretical_ev_sek = theoretical_position_sek * (track.avg_technical_edge / 100)
            
            # 2. Signal-to-Noise Ratio (SNR): Edge / Volatilitet
            # Estimera ATR från volatility_trend
            atr_estimate = {
                'EXPLOSIVE': 3.0,
                'EXPANDING': 2.0,
                'STABLE': 1.0,
                'CONTRACTING': 0.5,
                'IMPROVING': 1.5,
                'DEGRADING': 2.5
            }.get(track.volatility_trend, 1.5)
            
            # V3.0: Recency-Weighted SNR - Recent edges weigh more
            # Old SNR (unweighted): avg_net_edge / ATR
            # New SNR (weighted): weighted_avg_net_edge / ATR
            weighted_net_edge = self.recency_weighting.calculate_weighted_average(
                track.daily_edges,
                track.daily_dates
            ) if track.daily_edges and track.daily_dates else track.avg_net_edge
            
            # SNR på Net Edge (efter kostnader) - för BUY-beslut
            snr = weighted_net_edge / atr_estimate if atr_estimate > 0 else 0
            high_confidence = snr > 1.0
            
            # SNR på Technical Edge (innan kostnader) - för Architect's Opportunity
            snr_technical = track.avg_technical_edge / atr_estimate if atr_estimate > 0 else 0
            
            # 3. Avanza Breakeven Calculator
            # Svensk aktie: courtage ~0.25%, Utländsk: courtage + FX ~0.75%
            is_foreign = not ticker.endswith('.ST')
            breakeven_pct = 0.75 if is_foreign else 0.25
            avanza_viable = track.avg_net_edge > breakeven_pct
            
            # === V3.0: BETA-ALPHA SEPARATION ===
            # Calculate alpha vs OMXS30 to filter out pure beta plays
            alpha = 0.0
            beta = 0.0
            has_positive_alpha = False
            try:
                result = self.beta_alpha.analyze(ticker, lookback_days=90)
                alpha = result.alpha_pct
                beta = result.beta
                has_positive_alpha = result.has_alpha
            except:
                pass  # Skip if no data available
            
            # === V3.0: MAE OPTIMIZER ===
            # Calculate optimal stop-loss from historical MAE
            optimal_stop_pct = 0.0
            mae_confidence = "UNKNOWN"
            try:
                mae_result = self.mae_optimizer.calculate_optimal_stop(ticker)
                optimal_stop_pct = mae_result.optimal_stop_pct
                mae_confidence = mae_result.confidence_level
            except:
                pass  # Skip if no data available
            
            # Recommendation (justerad med matematisk edge + V3.0 filters)
            # UPPDATERING: Högre krav på consistency (5 och 10 dagar istället för 2 och 3)
            # V3.0: Also require positive alpha for STRONG BUY
            recommendation = "AVOID"
            if conviction_score >= 70 and track.days_investable >= 10 and high_confidence and has_positive_alpha:
                recommendation = "STRONG BUY"
            elif conviction_score >= 50 and track.days_investable >= 5 and avanza_viable:
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
                recommendation=recommendation,
                expected_value_sek=net_ev_sek,
                theoretical_ev_sek=theoretical_ev_sek,
                signal_to_noise_ratio=snr,
                breakeven_move_pct=breakeven_pct,
                high_confidence=high_confidence,
                avanza_viable=avanza_viable,
                # V3.0: Beta-Alpha
                alpha_vs_benchmark=alpha,
                beta=beta,
                has_positive_alpha=has_positive_alpha,
                # V3.0: Sector Cap (will be filled after sorting)
                sector="unknown",
                sector_allocation_pct=0.0,
                exceeds_sector_cap=False,
                # V3.0: MAE Stop-Loss
                optimal_stop_loss_pct=optimal_stop_pct,
                mae_confidence=mae_confidence
            ))
        
        # Sortera efter conviction score
        convictions.sort(key=lambda x: x.conviction_score, reverse=True)
        
        # === V3.0: SECTOR CAP ENFORCEMENT ===
        # Apply sector cap to prevent correlation risk
        # Build portfolio from top convictions and track sector exposure
        sector_allocations = {}  # sector -> total_pct
        
        for conv in convictions:
            # Get sector classification
            try:
                sector_info = self.sector_cap.classify_ticker(conv.ticker)
                conv.sector = sector_info.sector
            except:
                conv.sector = "unknown"
            
            # Calculate position size for this conviction
            position_pct = conv.avg_net_edge * 0.5 if conv.avg_net_edge > 0 else 0  # Rough estimate
            
            # Check if adding this would exceed sector cap
            current_sector_pct = sector_allocations.get(conv.sector, 0.0)
            if current_sector_pct + position_pct > 40.0:
                conv.exceeds_sector_cap = True
            else:
                conv.exceeds_sector_cap = False
                sector_allocations[conv.sector] = current_sector_pct + position_pct
            
            conv.sector_allocation_pct = sector_allocations.get(conv.sector, 0.0)
        
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
    
    def generate_audit_trail(self, analysis: Dict, week_number: int, year: int) -> Dict:
        """
        Generera Pattern Audit Trail för kvartalsvis system review.
        Loggar patternprestanda, degradering, och edge leakage.
        """
        audit = {
            'week': f"{year}_W{week_number:02d}",
            'analysis_period': analysis['analysis_period'],
            'regime': analysis['regime_analysis']['last_regime'],
            'regime_multiplier': analysis['regime_analysis']['last_multiplier'],
            
            # Pattern Performance Tracking
            'pattern_performance': [],
            
            # Pattern Degradation Watch (>30% score drop)
            'degraded_patterns': [],
            
            # Edge Leakage Log
            'edge_leakage': {
                'total_blocked_instruments': len(analysis['cost_blocked']),
                'total_technical_edge_lost': sum(item['avg_technical_edge'] for item in analysis['cost_blocked']),
                'blocked_opportunities': analysis['cost_blocked']
            },
            
            # High Confidence Summary
            'high_confidence_summary': {
                'count': len([c for c in analysis['top_convictions'] if c.high_confidence]),
                'avg_snr': 0.0,
                'total_expected_value': 0.0
            }
        }
        
        # Track pattern performance for all convictions
        for conv in analysis['top_convictions']:
            audit['pattern_performance'].append({
                'ticker': conv.ticker,
                'name': conv.name,
                'conviction_score': conv.conviction_score,
                'net_edge': conv.avg_net_edge,
                'days_investable': conv.days_investable,
                'recommendation': conv.recommendation,
                'expected_value_sek': conv.expected_value_sek,
                'snr': conv.signal_to_noise_ratio,
                'high_confidence': conv.high_confidence
            })
        
        # Identify degraded patterns (negative momentum)
        degraded = [c for c in analysis['top_convictions'] if c.momentum_component < -5]
        for conv in degraded:
            degradation_pct = (conv.momentum_component / conv.conviction_score * 100) if conv.conviction_score > 0 else 0
            audit['degraded_patterns'].append({
                'ticker': conv.ticker,
                'name': conv.name,
                'conviction_score': conv.conviction_score,
                'momentum_component': conv.momentum_component,
                'degradation_pct': degradation_pct,
                'urgent': degradation_pct < -30
            })
        
        # High confidence summary
        high_conf = [c for c in analysis['top_convictions'] if c.high_confidence]
        if high_conf:
            audit['high_confidence_summary']['avg_snr'] = sum(c.signal_to_noise_ratio for c in high_conf) / len(high_conf)
            audit['high_confidence_summary']['total_expected_value'] = sum(c.expected_value_sek for c in high_conf)
        
        return audit
    
    def _run_mini_monte_carlo(self, ticker: str, atr_pct: float, days: int = 10, paths: int = 500) -> RiskAnalysis:
        """
        Kör Mini Monte Carlo (500 paths) för att simulera prisscenarier.
        Räknar ut Probability of Stop-Out (-5% drawdown).
        
        Args:
            ticker: Instrument ticker
            atr_pct: ATR i procent (daglig volatilitet) - används som fallback
            days: Antal handelsdagar att simulera (default 10)
            paths: Antal Monte Carlo-paths (default 500)
        
        Returns:
            RiskAnalysis med probability of stop-out och scenarier
        """
        # Försök hämta verklig historisk volatilitet
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)  # 90 dagar för volatilitetsberäkning
            
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)['Close']
            
            if not data.empty and len(data) > 20:
                returns = data.pct_change().dropna()
                if len(returns) > 10:
                    # Använd faktisk historisk volatilitet
                    actual_vol = returns.std()
                    # Använd mean return (kan vara positiv eller negativ)
                    actual_mean = returns.mean()
                    
                    # REGIME-ADJUSTED VOLATILITY
                    # I CRISIS/EXPLOSIVE conditions, använd max(historical, ATR estimate)
                    # Detta fångar "nuvarande panik" som historisk data kanske missar
                    atr_vol = atr_pct / 100
                    adjusted_vol = max(actual_vol, atr_vol)
                    
                    # För CRISIS (ATR > 2%), lägg på extra volatilitets-buffer
                    # Volatility Normalization: Vol tenderar att "klustra" i kriser
                    if atr_pct >= 2.0:
                        adjusted_vol = adjusted_vol * 1.5  # 50% volatility spike (30% + 20% crisis buffer)
                    
                    # KRITISK FIX: Skala INTE volatiliteten per dag - den är redan daglig
                    # Men vi behöver simulera kumulativa rörelser korrekt
                    # Simulera med regime-adjusted volatilitet (daglig)
                    daily_returns = np.random.normal(actual_mean, adjusted_vol, (paths, days))
                    
                    # === FAT TAIL SIMULATOR (Crisis Factor) ===
                    # I CRISIS: Injicera "Black Swan" events (extrema ras)
                    # 5% chans per path att få en "dålig dag" på -3% till -5%
                    if atr_pct >= 2.0:  # CRISIS/EXPLOSIVE regime
                        for path_idx in range(paths):
                            # 5% chans för Black Swan event
                            if np.random.random() < 0.05:
                                # Injicera en extremt dålig dag någonstans i perioden
                                bad_day_idx = np.random.randint(0, days)
                                black_swan_move = np.random.uniform(-0.05, -0.03)  # -3% till -5%
                                daily_returns[path_idx, bad_day_idx] = black_swan_move
                else:
                    # Fallback till ATR estimate
                    daily_returns = np.random.normal(0, atr_pct/100, (paths, days))
            else:
                # Fallback till ATR estimate
                daily_returns = np.random.normal(0, atr_pct/100, (paths, days))
        
        except Exception:
            # Om något går fel, använd ATR estimate
            daily_returns = np.random.normal(0, atr_pct/100, (paths, days))
        
        # KRITISK FIX: Kumulativa returns i PROCENT (multiplicera med 100)
        # cumsum av dagliga returns ger total return i decimal form
        cumulative_returns = np.cumsum(daily_returns, axis=1) * 100  # Konvertera till procent
        
        # Släng på första dagen (start vid 0)
        cumulative_returns = np.hstack([np.zeros((paths, 1)), cumulative_returns])
        
        # Räkna paths som träffar -5% drawdown
        stopout_threshold = -5.0  # -5%
        paths_stopped_out = np.any(cumulative_returns <= stopout_threshold, axis=1)
        probability_of_stopout = np.sum(paths_stopped_out) / paths * 100
        
        # Slutavkastning dag 10 (redan i procent)
        final_returns = cumulative_returns[:, -1]
        mean_return_10d = np.mean(final_returns)  # Redan i %
        worst_case_10d = np.percentile(final_returns, 5)  # Redan i %
        best_case_10d = np.percentile(final_returns, 95)  # Redan i %
        
        # Risk Rating (inte köprekommendation - bara riskbedömning)
        if probability_of_stopout > 35:
            risk_rating = "DANGEROUS"
        elif probability_of_stopout > 15:
            risk_rating = "STABLE"
        else:
            risk_rating = "LOW RISK"
        
        return RiskAnalysis(
            ticker=ticker,
            probability_of_stopout=probability_of_stopout,
            mean_return_10d=mean_return_10d,
            worst_case_10d=worst_case_10d,
            best_case_10d=best_case_10d,
            risk_rating=risk_rating,
            monte_carlo_paths=paths
        )
    
    def _check_correlation_clusters(self, convictions: List[WeeklyConviction], lookback_days: int = 60, corr_threshold: float = 0.6) -> List[CorrelationCluster]:
        """
        Kontrollera korrelation mellan top conviction instruments.
        Identifiera 'Risk Clusters' med korrelation > 0.6 (sänkt från 0.7 för bättre detektering).
        
        Args:
            convictions: Lista av WeeklyConviction
            lookback_days: Antal dagar för korrelationsberäkning
        
        Returns:
            Lista av CorrelationCluster
        """
        if len(convictions) < 2:
            return []
        
        # Hämta historisk data för alla tickers
        tickers = [c.ticker for c in convictions[:10]]  # Top 10
        
        try:
            # Hämta data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days + 30)  # Extra margin
            
            data = yf.download(tickers, start=start_date, end=end_date, progress=False)['Close']
            
            if data.empty or len(data) < 20:
                return []
            
            # Beräkna dagliga returns
            returns = data.pct_change(fill_method=None).dropna()
            
            if len(returns) < 20:
                return []
            
            # Beräkna korrelationsmatrix
            corr_matrix = returns.corr()
            
            # Hitta clusters med korrelation > 0.7
            clusters = []
            processed = set()
            
            for i, ticker1 in enumerate(tickers):
                if ticker1 in processed:
                    continue
                
                cluster_tickers = [ticker1]
                
                for j, ticker2 in enumerate(tickers):
                    if i != j and ticker2 not in processed:
                        try:
                            corr = corr_matrix.loc[ticker1, ticker2]
                            if corr > corr_threshold:
                                cluster_tickers.append(ticker2)
                                processed.add(ticker2)
                        except KeyError:
                            continue
                
                if len(cluster_tickers) > 1:
                    # Beräkna average correlation inom cluster
                    cluster_corrs = []
                    for t1 in cluster_tickers:
                        for t2 in cluster_tickers:
                            if t1 != t2:
                                try:
                                    cluster_corrs.append(corr_matrix.loc[t1, t2])
                                except KeyError:
                                    continue
                    
                    avg_corr = np.mean(cluster_corrs) if cluster_corrs else 0.0
                    
                    # Välj ticker med högst SNR
                    conv_map = {c.ticker: c for c in convictions}
                    cluster_convictions = [conv_map[t] for t in cluster_tickers if t in conv_map]
                    
                    if cluster_convictions:
                        best_snr_conv = max(cluster_convictions, key=lambda c: c.signal_to_noise_ratio)
                        
                        clusters.append(CorrelationCluster(
                            tickers=cluster_tickers,
                            avg_correlation=avg_corr,
                            recommended_ticker=best_snr_conv.ticker,
                            risk_warning=f"Risk Cluster: {len(cluster_tickers)} instrument med korr {avg_corr:.2f}"
                        ))
                    
                    processed.add(ticker1)
            
            return clusters
        
        except Exception as e:
            # Om något går fel, returnera tom lista
            print(f"\n⚠️  Kunde inte beräkna korrelationer: {e}")
            return []
    
    def _calculate_regime_exit_threshold(self, latest_file: Dict) -> Dict:
        """
        Beräkna vad som krävs för att gå från CRISIS (0.2x) till RECOVERY (0.5x).
        Baserat på marknadsbredd (% gröna signals).
        """
        if not latest_file:
            return {'available': False}
        
        # Hämta market stats från senaste filen
        market_stats = latest_file.get('market_stats', {})
        
        total_analyzed = market_stats.get('total_analyzed', 0)
        green_signals = market_stats.get('green_signals', 0)
        yellow_signals = market_stats.get('yellow_signals', 0)
        
        if total_analyzed == 0:
            return {'available': False}
        
        # Nuvarande marknadsbredd
        current_breadth_pct = (green_signals / total_analyzed) * 100
        current_positive_pct = ((green_signals + yellow_signals) / total_analyzed) * 100
        
        # Threshold för regime-övergång (historiskt baserat)
        # CRISIS → RECOVERY: Kräver ~20% gröna eller ~40% positiva (grön+gul)
        green_threshold = 20.0
        positive_threshold = 40.0
        
        return {
            'available': True,
            'current_regime': latest_file.get('regime', 'UNKNOWN'),
            'current_multiplier': latest_file.get('regime_multiplier', 0),
            'current_green_pct': current_breadth_pct,
            'current_positive_pct': current_positive_pct,
            'green_threshold': green_threshold,
            'positive_threshold': positive_threshold,
            'green_signals_needed': int((green_threshold / 100 * total_analyzed) - green_signals),
            'days_to_recovery': 'Unknown - Övervaka dagligen'
        }
    
    def _calculate_regime_exit_threshold(self, latest_file: Dict) -> Dict:
        """
        Beräkna vad som krävs för att gå från CRISIS (0.2x) till RECOVERY (0.5x).
        Baserat på marknadsbredd (% gröna signals).
        """
        if not latest_file:
            return {'available': False}
        
        # Hämta market stats från senaste filen
        market_stats = latest_file.get('market_stats', {})
        
        total_analyzed = market_stats.get('total_analyzed', 0)
        green_signals = market_stats.get('green_signals', 0)
        yellow_signals = market_stats.get('yellow_signals', 0)
        
        if total_analyzed == 0:
            return {'available': False}
        
        # Nuvarande marknadsbredd
        current_breadth_pct = (green_signals / total_analyzed) * 100
        current_positive_pct = ((green_signals + yellow_signals) / total_analyzed) * 100
        
        # Threshold för regime-övergång
        green_threshold = 20.0
        positive_threshold = 40.0
        
        return {
            'available': True,
            'current_regime': latest_file.get('regime', 'UNKNOWN'),
            'current_multiplier': latest_file.get('regime_multiplier', 0),
            'current_green_pct': current_breadth_pct,
            'current_positive_pct': current_positive_pct,
            'green_threshold': green_threshold,
            'positive_threshold': positive_threshold,
            'green_signals_needed': int((green_threshold / 100 * total_analyzed) - green_signals)
        }
    
    def _calculate_cash_drag(self, days_analyzed: int) -> Dict:
        """
        Beräkna opportunity cost av att stå utanför marknaden.
        Jämför med inflation och ISK-ränta.
        """
        # Antag inflation ~2% per år
        inflation_rate_annual = 0.02
        
        # Antag ISK-ränta (statslåneränta) ~3% per år
        isk_rate_annual = 0.03
        
        # Konvertera till daglig rate (approximation)
        days_per_year = 252  # Handelsdagar
        inflation_daily = (1 + inflation_rate_annual) ** (1/days_per_year) - 1
        isk_daily = (1 + isk_rate_annual) ** (1/days_per_year) - 1
        
        # Beräkna förlust/vinst för perioden
        inflation_loss_pct = (1 + inflation_daily) ** days_analyzed - 1
        isk_gain_pct = (1 + isk_daily) ** days_analyzed - 1
        
        # Net opportunity cost = vad du hade fått i ISK - inflation
        net_opportunity_pct = isk_gain_pct - inflation_loss_pct
        
        return {
            'days_in_cash': days_analyzed,
            'inflation_loss_pct': inflation_loss_pct * 100,
            'isk_gain_pct': isk_gain_pct * 100,
            'net_opportunity_pct': net_opportunity_pct * 100,
            'inflation_rate_annual': inflation_rate_annual * 100,
            'isk_rate_annual': isk_rate_annual * 100
        }
    
    def _analyze_portfolio_health(self, convictions: List[WeeklyConviction], positions_file: str = "my_positions.json") -> Dict:
        """
        Analysera portföljens hälsa genom att jämföra aktuella positioner med veckoanalys.
        Modul 3: Portfolio Intelligence.
        """
        portfolio_health = {
            'positions_tracked': [],
            'urgent_reevaluation': [],
            'relative_strength_watch': [],
            'positions_file_exists': False
        }
        
        # Försök läsa my_positions.json
        try:
            import json
            from pathlib import Path
            
            pos_path = Path(positions_file)
            if not pos_path.exists():
                return portfolio_health
            
            portfolio_health['positions_file_exists'] = True
            
            with open(pos_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                positions = data.get('positions', [])
            
            # Filter out example positions
            real_positions = [p for p in positions if 'example' not in p.get('notes', '').lower()]
            
            if not real_positions:
                return portfolio_health
            
            # Create conviction lookup
            conviction_map = {c.ticker: c for c in convictions}
            
            for position in real_positions:
                ticker = position.get('ticker', '')
                
                if ticker in conviction_map:
                    conv = conviction_map[ticker]
                    
                    # Track position
                    pos_data = {
                        'ticker': ticker,
                        'entry_date': position.get('entry_date', 'N/A'),
                        'current_conviction': conv.conviction_score,
                        'current_edge': conv.avg_net_edge,
                        'recommendation': conv.recommendation,
                        'momentum': conv.momentum_component
                    }
                    portfolio_health['positions_tracked'].append(pos_data)
                    
                    # Urgent re-evaluation: degradation > 30% eller momentum < -10
                    if conv.momentum_component < -10:
                        portfolio_health['urgent_reevaluation'].append({
                            'ticker': ticker,
                            'reason': f"Stark nedgång: {conv.momentum_component:.1f} pts momentum",
                            'current_edge': conv.avg_net_edge,
                            'recommendation': 'ÖVERVÄG EXIT'
                        })
                    
                    # Relative Strength Watch: position finns men conviction < 30
                    if conv.conviction_score < 30:
                        portfolio_health['relative_strength_watch'].append({
                            'ticker': ticker,
                            'conviction_score': conv.conviction_score,
                            'reason': 'Låg conviction - andra opportunities kan vara bättre'
                        })
                else:
                    # Position inte längre i top convictions - varningssignal
                    portfolio_health['urgent_reevaluation'].append({
                        'ticker': ticker,
                        'reason': 'Ingen längre i weekly top convictions',
                        'current_edge': 'N/A',
                        'recommendation': 'GRANSKA OMEDELBART'
                    })
            
            return portfolio_health
        
        except Exception as e:
            # Om något går fel, returnera tom data
            portfolio_health['error'] = str(e)
            return portfolio_health
    
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
        
        # Data Quality Warning/Stamp
        days_analyzed = analysis['analysis_period']['days_analyzed']
        if self.use_backfill:
            lines.append("✅ **BACKFILLED DATA QUALITY: HIGH**")
            lines.append(f"- Point-in-Time Analysis: {days_analyzed} handelsdagar")
            lines.append("- Synthetic Consistency: Baserad på daglig screening")
            lines.append("- Cost-Adjusted: Alla signaler körda genom Execution Guard")
            lines.append("")
        elif days_analyzed < 4:
            lines.append("⚠️  **DATA QUALITY WARNING:**")
            lines.append(f"- Endast {days_analyzed} dagars data analyserad")
            lines.append("- **Consistency Score** (40% av vägning) är statistiskt missvisande")
            lines.append("- Rekommendation: Kör dashboard dagligen för mer robust analys")
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
        
        # Regime Exit Threshold
        regime_exit = analysis.get('regime_exit_threshold', {})
        if regime_exit.get('available') and regime_exit.get('current_multiplier', 0) <= 0.3:
            lines.append("🎯 **Regime Exit Threshold:**")
            lines.append(f"- Nuvarande marknadsbredd: {regime_exit['current_green_pct']:.1f}% gröna")
            lines.append(f"- Behöver: {regime_exit['green_threshold']:.0f}% gröna för RECOVERY")
            if regime_exit['green_signals_needed'] > 0:
                lines.append(f"- **Gap:** +{regime_exit['green_signals_needed']} instrument behöver bli gröna")
            else:
                lines.append(f"- ✅ **Tröskel uppnådd!** Regime kan förbättras snart.")
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
            hc_marker = " ✨ **[HIGH CONFIDENCE]**" if conv.high_confidence else ""
            
            lines.append(f"### {i}. {conv.name} ({conv.ticker}){aw_marker}{hc_marker}")
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
            lines.append(f"**Mathematical Edge (Casino Logic):**")
            lines.append(f"- 💰 **Net EV (After Costs):** {conv.expected_value_sek:+.0f} SEK per trade")
            lines.append(f"- SNR (Net Edge): {conv.signal_to_noise_ratio:.2f} (edge/volatility)")
            lines.append(f"- Avanza Breakeven: {conv.breakeven_move_pct:.2f}% ({'✅ VIABLE' if conv.avanza_viable else '❌ BLOCKED'})")  
            
            # Visa Theoretical EV och SNR Technical om olika från Net
            if conv.theoretical_ev_sek > 0 and conv.theoretical_ev_sek != conv.expected_value_sek:
                # Hämta tracking data för SNR technical
                track = analysis['tracking_data'].get(conv.ticker)
                if track:
                    atr_est = 1.5  # Default
                    snr_tech = track.avg_technical_edge / atr_est
                    lines.append(f"- 💡 **Architect's Opportunity:** {conv.theoretical_ev_sek:+.0f} SEK (SNR Tech: {snr_tech:.2f})")
                else:
                    lines.append(f"- 💡 **Architect's Opportunity:** {conv.theoretical_ev_sek:+.0f} SEK (utan courtage)")
            
            lines.append("")
            
            # Probabilistic Risk Analysis
            if conv.risk_analysis:
                risk = conv.risk_analysis
                risk_icon = "🟢" if risk.probability_of_stopout < 20 else "🟡" if risk.probability_of_stopout < 35 else "🔴"
                
                lines.append(f"**🎲 Probabilistic Risk (Monte Carlo 500 paths, 10 days):**")
                lines.append(f"- {risk_icon} Probability of Stop-Out (-5%): {risk.probability_of_stopout:.1f}%")
                lines.append(f"- Risk Rating: **{risk.risk_rating}**")
                lines.append(f"- Expected Return (10d): {risk.mean_return_10d:+.2f}%")
                lines.append(f"- Worst Case (5th percentile): {risk.worst_case_10d:+.2f}%")
                lines.append(f"- Best Case (95th percentile): {risk.best_case_10d:+.2f}%")
                
                # Add explanatory note if stop-out is 0 but worst case is close to threshold
                if risk.probability_of_stopout == 0.0 and abs(risk.worst_case_10d) > 2.0:
                    lines.append(f"- 💡 **Note:** Låg Stop-Out risk men worst case nära {risk.worst_case_10d:+.2f}%")
                
                lines.append("")
            
            # Correlation Cluster Warning
            if conv.in_correlation_cluster and conv.cluster_warning:
                lines.append(f"**🔗 Correlation Cluster:**")
                lines.append(f"- {conv.cluster_warning}")
                lines.append("")
            
            # Re-Entry Trigger (Modul 6)
            if conv.re_entry_trigger and conv.recommendation in ["AVOID", "WATCH"]:
                lines.append(f"**🎯 Re-Entry Trigger:**")
                lines.append(f"- {conv.re_entry_trigger}")
                lines.append("")
        
        lines.append("---")
        lines.append("")
        
        # High Confidence Signals (SNR > 1.0)
        lines.append("## ✨ HIGH CONFIDENCE SIGNALS (SNR > 1.0)")
        lines.append("")
        lines.append("*Signaler där edge överstiger volatility - matematiskt fördelaktiga trades*")
        lines.append("")
        
        high_conf = [c for c in analysis['top_convictions'] if c.high_confidence]
        
        if high_conf:
            lines.append("| Ticker | Name | SNR | Exp Value | Net Edge | Avanza? |")
            lines.append("|--------|------|-----|-----------|----------|---------|")
            
            for conv in high_conf[:10]:
                viable_icon = "✅" if conv.avanza_viable else "❌"
                lines.append(f"| {conv.ticker} | {conv.name[:15]} | {conv.signal_to_noise_ratio:.2f} | {conv.expected_value_sek:+.0f} SEK | {conv.avg_net_edge:+.2f}% | {viable_icon} |")
            
            lines.append("")
            lines.append(f"**🎯 Total High Confidence Opportunities:** {len(high_conf)}")
            lines.append("")
            lines.append("**Architect's Note:** SNR > 1.0 innebär att den förväntade positiva rörelsen överstiger typisk")
            lines.append("volatility. Detta är matematiskt likvärdigt med ett positivt casino-spel.")
        else:
            lines.append("❌ Inga high-confidence signals (SNR > 1.0) denna vecka.")
            lines.append("")
            lines.append("**Strategi:** Avvakta eller reducera positionsstorlekar tills SNR förbättras.")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Systemic Risk Clusters (Price-based correlation)
        correlation_clusters = analysis.get('correlation_clusters', [])
        
        if correlation_clusters:
            lines.append("🔗 SYSTEMIC RISK CLUSTERS (Correlation > 0.6)")
            lines.append("")
            lines.append("*Instrument som rör sig tillsammans - välj endast ett per cluster*")
            lines.append("")
            
            for cluster in correlation_clusters:
                lines.append(f"### Cluster: {', '.join(cluster.tickers)}")
                lines.append("")
                lines.append(f"- Avg Correlation: {cluster.avg_correlation:.2f}")
                lines.append(f"- ✅ **Rekommenderad:** {cluster.recommended_ticker} (högst SNR)")
                lines.append(f"- ⚠️  **Risk:** {cluster.risk_warning}")
                lines.append("")
                
                # Portfolio concentration warning
                cluster_pct = (len(cluster.tickers) / min(5, len(analysis['top_convictions']))) * 100
                if cluster_pct > 40:
                    lines.append(f"🚨 **Portfolio Risk:** {cluster_pct:.0f}% av dina Top 5 är i detta cluster!")
                    lines.append("Vid ränteuppgång/sektor-kris faller allt samtidigt.")
                    lines.append("")
                
                lines.append("**💡 Diversification Tip:** Att köpa flera instrument i samma cluster")
                lines.append("ger INTE diversifiering - de kommer falla/stiga tillsammans.")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        else:
            # Om inga clusters hittas, visa ändå en not om att vi sökt
            if days_analyzed >= 2:
                lines.append("🔗 SYSTEMIC RISK CLUSTERS")
                lines.append("")
                lines.append("✅ Inga signifikanta korrelations-clusters (>0.6) hittades bland Top 10.")
                lines.append("")
                lines.append("**Note:** Med få dagar av data kan korrelationer vara underskättade.")
                lines.append("")
                lines.append("---")
                lines.append("")
        
        # Re-evaluation List
        lines.append("⚠️  RE-EVALUATION LIST")
        lines.append("")
        lines.append("*Instrument där Score har degraderats under veckan*")
        lines.append("")
        
        # Find instruments with negative momentum (but exclude near-zero values)
        degraded = [c for c in analysis['top_convictions'] if c.momentum_component < -0.5][:5]
        
        if degraded:
            for conv in degraded:
                lines.append(f"- **{conv.name} ({conv.ticker})**: Momentum {conv.momentum_component:.1f} pts (degrading)")
        else:
            lines.append("✅ Inga instrument har degraderats signifikant under veckan.")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Cost-Blocked Watchlist with Edge Leakage
        lines.append("## 💰 COST-BLOCKED WATCHLIST & EDGE LEAKAGE")
        lines.append("")
        lines.append("*Instrument med hög Score men blockerade av Execution Guard*")
        lines.append("")
        
        cost_blocked = analysis['cost_blocked']
        
        if cost_blocked:
            lines.append("| Ticker | Name | Avg Score | Avg Tech Edge | Days Seen |")
            lines.append("|--------|------|-----------|---------------|-----------|")
            
            total_leaked_edge = 0.0
            for item in cost_blocked[:10]:
                lines.append(f"| {item['ticker']} | {item['name'][:20]} | {item['avg_score']:.1f} | {item['avg_technical_edge']:+.2f}% | {item['days_seen']} |")
                total_leaked_edge += item['avg_technical_edge']
            
            lines.append("")
            lines.append(f"🚨 **Edge Leakage Analysis:**")
            lines.append(f"- Total Technical Edge Blocked: {total_leaked_edge:+.2f}%")
            avg_leaked = total_leaked_edge / len(cost_blocked[:10]) if len(cost_blocked[:10]) > 0 else 0.0
            lines.append(f"- Avg Edge per Blocked Signal: {avg_leaked:+.2f}%")
            lines.append(f"- Opportunities Lost to Costs: {len(cost_blocked)} instruments")
            lines.append("")
            
            # Optimal Portfolio Size (Skalbarhetssimulering)
            # Antag Avanza courtage: 0.25% för SE, 0.75% för utländska
            # För att låsa upp: position_size * edge > courtage
            # Med 100k SEK och 3% position = 3000 SEK * 1.24% edge = 37 SEK vinst
            # Courtage 3000 * 0.0025 = 7.5 SEK → Net = 29.5 SEK (funkar!)
            # Men med 100k och 1% edge: 3000 * 0.01 = 30 SEK, courtage 7.5 SEK → Net = 22.5 SEK
            # Om edge = 0.5%, behövs 6000 SEK position = 6% av portfölj → 100k/0.06 = knappt
            
            # Rough estimate: För avg edge 0.96%, position 3% behövs ~150k-200k
            if avg_leaked > 0.5:
                optimal_portfolio = int(self.portfolio_value_sek * 2.5)  # 2.5x för avg 1% edge
                unlockable = int(len(cost_blocked) * 0.7)  # ~70% skulle låsas upp
                
                lines.append("📊 **Optimal Portfolio Size (Skalbarhet):**")
                lines.append(f"- Med {optimal_portfolio:,} SEK portfölj: ~{unlockable} av {len(cost_blocked)} blockerade affärer låses upp")
                lines.append(f"- **Sparkmål:** {optimal_portfolio - self.portfolio_value_sek:,} SEK för att maximera edge")
                lines.append("")
            
            lines.append("💡 **Note:** Dessa instrument kan bli lönsamma med större portföljstorlek.")
        else:
            lines.append("✅ Inga cost-blocked opportunities denna vecka.")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Portfolio Health (Modul 3: Portfolio Intelligence)
        portfolio_health = analysis.get('portfolio_health', {})
        
        if portfolio_health.get('positions_file_exists', False):
            lines.append("## 🛡️ PORTFOLIO HEALTH CHECK")
            lines.append("")
            lines.append("*Analys av dina aktuella positioner*")
            lines.append("")
            
            positions_tracked = portfolio_health.get('positions_tracked', [])
            urgent = portfolio_health.get('urgent_reevaluation', [])
            relative_strength = portfolio_health.get('relative_strength_watch', [])
            
            if positions_tracked:
                lines.append("### 📊 Positions Tracked")
                lines.append("")
                lines.append("| Ticker | Conviction | Net Edge | Momentum | Recommendation |")
                lines.append("|--------|-----------|----------|----------|----------------|")
                
                for pos in positions_tracked:
                    lines.append(f"| {pos['ticker']} | {pos['current_conviction']:.1f} | {pos['current_edge']:+.2f}% | {pos['momentum']:+.1f} | {pos['recommendation']} |")
                
                lines.append("")
            
            if urgent:
                lines.append("### ⚠️  URGENT RE-EVALUATION REQUIRED")
                lines.append("")
                for item in urgent:
                    lines.append(f"- **{item['ticker']}**: {item['reason']}")
                    lines.append(f"  - Current Edge: {item['current_edge']}")
                    lines.append(f"  - **Recommendation: {item['recommendation']}**")
                    lines.append("")
            
            if relative_strength:
                lines.append("### 📉 Relative Strength Watch")
                lines.append("")
                lines.append("*Positioner med låg conviction - överväg rebalansering*")
                lines.append("")
                for item in relative_strength:
                    lines.append(f"- **{item['ticker']}**: Conviction {item['conviction_score']:.1f}/100")
                    lines.append(f"  - {item['reason']}")
                    lines.append("")
            
            if not urgent and not relative_strength and positions_tracked:
                lines.append("✅ **Alla positioner ser bra ut!** Ingen omedelbar action krävs.")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        # Cash Drag Analysis (Modul B)
        cash_drag = analysis.get('cash_drag', {})
        strong_buys = [c for c in analysis['top_convictions'] if c.recommendation == "STRONG BUY"]
        
        if not strong_buys and cash_drag:
            lines.append("💵 CASH DRAG ANALYSIS")
            lines.append("")
            lines.append("*Opportunity cost av att stå utanför marknaden*")
            lines.append("")
            
            lines.append(f"- **Days in Cash:** {cash_drag.get('days_in_cash', 0)}")
            lines.append(f"- **Inflation Loss:** {cash_drag.get('inflation_loss_pct', 0):.3f}% (Annual: {cash_drag.get('inflation_rate_annual', 2):.1f}%)")
            lines.append(f"- **ISK Opportunity Gain:** {cash_drag.get('isk_gain_pct', 0):.3f}% (Annual: {cash_drag.get('isk_rate_annual', 3):.1f}%)")
            lines.append(f"- **Net Opportunity Cost:** {cash_drag.get('net_opportunity_pct', 0):.3f}%")
            lines.append("")
            lines.append("💡 **Note:** Du förlorar pengarna till inflation, men ISK-räntan ger dig positiv avkastning.")
            lines.append(f"Med 100k SEK portfölj: ~{self.portfolio_value_sek * cash_drag.get('net_opportunity_pct', 0) / 100:.0f} SEK net opportunity cost.")
            lines.append("")
            lines.append("---")
            lines.append("")
        
        # Action Items
        lines.append("🎯 ACTION ITEMS FÖR NÄSTA VECKA")
        lines.append("")
        
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
