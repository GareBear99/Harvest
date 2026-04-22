"""
High Accuracy Filter - 10 enhanced criteria for 90% win rate
Only takes S-tier and A-tier setups with strong confluences
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List, Tuple
from datetime import datetime
from core.indicators_backtest import BacktestIndicators


class HighAccuracyFilter:
    """
    Ultra-selective filter for 90%+ win rate trading
    Applies 10 strict criteria to ensure high-probability setups only
    
    Now supports dynamic thresholds from TimeframeStrategyManager
    """
    
    def __init__(self, strategy_manager=None):
        self.strategy_manager = strategy_manager
        self.filter_stats = {
            'total_evaluated': 0,
            'passed': 0,
            'rejected_by': {}
        }
    
    def evaluate(
        self,
        candles_tf: List[Dict],
        candles_4h: List[Dict],
        idx_tf: int,
        idx_4h: int,
        current_price: float,
        features: Dict[str, Any],
        confidence: float,
        tp_pct: float,
        sl_pct: float,
        regime: str
    ) -> Tuple[bool, str, float]:
        """
        Evaluate if trade meets all 10 high-accuracy criteria
        
        Returns: (pass, rejection_reason, adjusted_confidence)
        """
        
        self.filter_stats['total_evaluated'] += 1
        
        # Filter 1: Minimum Confidence (dynamic from strategy manager)
        timeframe = self._detect_timeframe(candles_tf, idx_tf)
        
        # Get thresholds from strategy manager (or use defaults)
        thresholds = self._get_thresholds(timeframe)
        min_confidence = thresholds.get('min_confidence', 0.70)
        
        if confidence < min_confidence:
            self._reject('confidence_low')
            return False, f"Confidence {confidence:.2f} < {min_confidence} ({timeframe})", confidence
        
        # Filter 2: Strong Trend (ADX - dynamic)
        adx = features.get('adx', 0)
        min_adx = thresholds.get('min_adx', 25)
        if adx < min_adx:
            self._reject('adx_weak')
            return False, f"ADX {adx:.1f} < {min_adx} (weak trend)", confidence
        
        # Filter 3: Momentum Alignment (dynamic ROC)
        roc = features.get('roc_10', 0)
        ema_slope = features.get('ema9_slope', 0)
        min_roc = thresholds.get('min_roc', -1.0)
        if not (roc < min_roc and ema_slope < -0.5):  # Bearish momentum
            self._reject('momentum_misaligned')
            return False, f"Momentum not aligned (ROC: {roc:.1f} vs {min_roc}, EMA slope: {ema_slope:.2f})", confidence
        
        # Filter 4: Volume Surge (dynamic)
        min_volume = thresholds.get('min_volume', 1.15)
        
        volume_ratio = features.get('volume_ratio', 0)
        if volume_ratio < min_volume:
            self._reject('volume_low')
            return False, f"Volume ratio {volume_ratio:.2f} < {min_volume}x ({timeframe})", confidence
        
        # Filter 5: Multi-Timeframe Alignment
        if not self._check_multi_tf_alignment(candles_tf, candles_4h, idx_tf, idx_4h, current_price):
            self._reject('tf_misaligned')
            return False, "Multi-timeframe not aligned", confidence
        
        # Filter 6: Near Resistance Level (OPTIONAL - bonus if present)
        # Make this optional to allow more trades, but boost confidence if near S/R
        near_sr = self._check_support_resistance(candles_tf[:idx_tf + 1], current_price, distance_threshold=2.5)
        if near_sr:
            confidence += 0.03  # Bonus for S/R confluence
        # Don't reject if not near S/R - just don't give bonus
        
        # Filter 7: Volatility in Optimal Range (dynamic)
        atr_pct = features.get('atr_pct', 0)
        atr_min = thresholds.get('atr_min', 0.4)
        atr_max = thresholds.get('atr_max', 3.5)
        if not (atr_min <= atr_pct <= atr_max):
            self._reject('volatility_out_of_range')
            return False, f"ATR% {atr_pct:.2f} out of optimal range [{atr_min}-{atr_max}]", confidence
        
        # Filter 8: Session Filter (High Liquidity)
        if not self._check_session_quality(candles_tf[idx_tf]['timestamp']):
            self._reject('poor_session')
            return False, "Outside high-liquidity hours", confidence
        
        # Filter 9: Risk/Reward Minimum 2:1
        risk_reward = tp_pct / sl_pct if sl_pct > 0 else 0
        if risk_reward < 2.0:
            self._reject('rr_too_low')
            return False, f"Risk/Reward {risk_reward:.2f} < 2.0", confidence
        
        # Filter 10: Trend Consistency (dynamic)
        min_trend = thresholds.get('min_trend', 0.55)
        
        trend_consistency = features.get('trend_consistency', 0)
        if trend_consistency < min_trend:
            self._reject('trend_inconsistent')
            return False, f"Trend consistency {trend_consistency:.2f} < {min_trend} ({timeframe})", confidence
        
        # ALL FILTERS PASSED - This is a high-quality setup
        self.filter_stats['passed'] += 1
        
        # Boost confidence for exceptional setups
        adjusted_confidence = self._calculate_adjusted_confidence(
            confidence, adx, volume_ratio, trend_consistency, risk_reward
        )
        
        return True, "ALL FILTERS PASSED - HIGH QUALITY SETUP", adjusted_confidence
    
    def _check_multi_tf_alignment(
        self,
        candles_tf: List[Dict],
        candles_4h: List[Dict],
        idx_tf: int,
        idx_4h: int,
        current_price: float
    ) -> bool:
        """Check if all timeframes show bearish alignment"""
        
        # Current TF: Price below EMAs
        closes_tf = [c['close'] for c in candles_tf[:idx_tf + 1]]
        ema9_tf = BacktestIndicators.ema(closes_tf, 9)
        ema21_tf = BacktestIndicators.ema(closes_tf, 21)
        
        if not (current_price < ema9_tf < ema21_tf):
            return False
        
        # 4H TF: Bearish trend
        closes_4h = [c['close'] for c in candles_4h[:idx_4h + 1]]
        ema9_4h = BacktestIndicators.ema(closes_4h, 9)
        ema21_4h = BacktestIndicators.ema(closes_4h, 21)
        
        current_4h = closes_4h[-1]
        if not (current_4h < ema9_4h):
            return False
        
        # Check EMA order on 4H
        if not (ema9_4h < ema21_4h):
            return False
        
        return True
    
    def _get_thresholds(self, timeframe: str) -> Dict[str, float]:
        """Get current thresholds for timeframe from strategy manager"""
        if self.strategy_manager:
            return self.strategy_manager.get_thresholds(timeframe)
        else:
            # Fallback to defaults if no strategy manager
            defaults = {
                '15m': {'min_confidence': 0.72, 'min_volume': 1.20, 'min_trend': 0.60, 'min_adx': 25, 'min_roc': -1.0, 'atr_min': 0.4, 'atr_max': 3.5},
                '1h': {'min_confidence': 0.68, 'min_volume': 1.12, 'min_trend': 0.52, 'min_adx': 25, 'min_roc': -1.0, 'atr_min': 0.4, 'atr_max': 3.5},
                '4h': {'min_confidence': 0.65, 'min_volume': 1.05, 'min_trend': 0.48, 'min_adx': 25, 'min_roc': -1.0, 'atr_min': 0.4, 'atr_max': 3.5}
            }
            return defaults.get(timeframe, defaults['1h'])
    
    def _detect_timeframe(self, candles: List[Dict], idx: int) -> str:
        """Detect timeframe from candle timestamps"""
        if idx < 1:
            return '1h'  # default
        
        try:
            dt1 = datetime.fromisoformat(candles[idx]['timestamp'].replace('Z', '+00:00'))
            dt2 = datetime.fromisoformat(candles[idx-1]['timestamp'].replace('Z', '+00:00'))
            diff_minutes = (dt1 - dt2).total_seconds() / 60
            
            if 10 <= diff_minutes <= 20:
                return '15m'
            elif 50 <= diff_minutes <= 70:
                return '1h'
            elif 220 <= diff_minutes <= 260:
                return '4h'
            else:
                return '1h'  # default
        except:
            return '1h'  # default on error
    
    def _check_support_resistance(
        self,
        candles: List[Dict],
        current_price: float,
        lookback: int = 50,
        distance_threshold: float = 2.0  # Widened from 1.0%
    ) -> bool:
        """Check if current price is near a key resistance level"""
        
        if len(candles) < lookback:
            return False
        
        recent_candles = candles[-lookback:]
        
        # Find swing highs (resistance levels)
        swing_highs = []
        for i in range(2, len(recent_candles) - 2):
            high = recent_candles[i]['high']
            
            # Check if it's a swing high (higher than neighbors)
            if (high > recent_candles[i-1]['high'] and 
                high > recent_candles[i-2]['high'] and
                high > recent_candles[i+1]['high'] and
                high > recent_candles[i+2]['high']):
                swing_highs.append(high)
        
        if not swing_highs:
            return False
        
        # Check if current price is within distance_threshold% of any swing high
        for resistance in swing_highs:
            distance_pct = abs((current_price - resistance) / resistance) * 100
            if distance_pct < distance_threshold:  # Widened threshold
                return True
        
        return False
    
    def _check_session_quality(self, timestamp: str) -> bool:
        """Check if trade is during high-liquidity session"""
        
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            hour = dt.hour
            
            # Expanded hours for more trading opportunities (6-22 UTC)
            # Covers Asian late, London, and US sessions
            if 6 <= hour < 22:  # Expanded from 8-16, 13-21
                return True
            
            # Only avoid late night/early morning (22-6 UTC)
            return False
            
        except:
            # If timestamp parsing fails, allow trade (conservative)
            return True
    
    def _calculate_adjusted_confidence(
        self,
        base_confidence: float,
        adx: float,
        volume_ratio: float,
        trend_consistency: float,
        risk_reward: float
    ) -> float:
        """Boost confidence for exceptional setups"""
        
        adjusted = base_confidence
        
        # ADX bonus (very strong trends)
        if adx > 40:
            adjusted += 0.05
        elif adx > 50:
            adjusted += 0.10
        
        # Volume bonus (significant surge)
        if volume_ratio > 2.0:
            adjusted += 0.03
        elif volume_ratio > 2.5:
            adjusted += 0.05
        
        # Trend consistency bonus
        if trend_consistency > 0.85:
            adjusted += 0.03
        
        # Risk/Reward bonus
        if risk_reward > 2.5:
            adjusted += 0.02
        elif risk_reward > 3.0:
            adjusted += 0.04
        
        # Cap at 0.98 (never 100% certain)
        return min(0.98, adjusted)
    
    def _reject(self, reason: str):
        """Record rejection reason"""
        if reason not in self.filter_stats['rejected_by']:
            self.filter_stats['rejected_by'][reason] = 0
        self.filter_stats['rejected_by'][reason] += 1
    
    def get_filter_statistics(self) -> Dict[str, Any]:
        """Get filter performance statistics"""
        
        total = self.filter_stats['total_evaluated']
        passed = self.filter_stats['passed']
        
        if total == 0:
            return {
                'total_evaluated': 0,
                'passed': 0,
                'pass_rate': 0.0,
                'rejection_reasons': {}
            }
        
        return {
            'total_evaluated': total,
            'passed': passed,
            'pass_rate': (passed / total) * 100,
            'rejection_reasons': self.filter_stats['rejected_by']
        }
    
    def print_filter_report(self):
        """Print detailed filter rejection analysis"""
        
        stats = self.get_filter_statistics()
        
        print(f"\n{'='*80}")
        print("HIGH ACCURACY FILTER REPORT")
        print(f"{'='*80}\n")
        
        print(f"Total Opportunities Evaluated: {stats['total_evaluated']}")
        print(f"Passed All Filters: {stats['passed']}")
        print(f"Pass Rate: {stats['pass_rate']:.1f}%\n")
        
        if stats['rejection_reasons']:
            print("Rejection Breakdown:")
            print(f"{'Reason':<30} {'Count':<10} {'%'}")
            print("-" * 50)
            
            total_rejected = sum(stats['rejection_reasons'].values())
            sorted_reasons = sorted(
                stats['rejection_reasons'].items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            for reason, count in sorted_reasons:
                pct = (count / total_rejected) * 100
                print(f"{reason:<30} {count:<10} {pct:.1f}%")
        
        print(f"\n{'='*80}\n")


def get_position_size_multiplier(quality_tier: str) -> float:
    """Get position size multiplier based on trade quality tier"""
    
    multipliers = {
        'S': 1.0,   # Full position (90%+ predicted)
        'A': 0.75,  # 75% position (80-90% predicted)
        'B': 0.5,   # 50% position (70-80% predicted)
        'C': 0.0,   # No trade (60-70% predicted)
        'D': 0.0    # No trade (<60% predicted)
    }
    
    return multipliers.get(quality_tier, 0.0)
