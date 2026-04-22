"""
Adaptive Filter Optimizer - Automatically adjusts filter thresholds
based on recent performance to maintain 75-90% win rate
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List
import json
from datetime import datetime


class AdaptiveOptimizer:
    """
    Learns from trading results and adjusts filter thresholds
    to maintain optimal win rate (75-90%) with 5-15 trades/month
    """
    
    def __init__(self, target_win_rate: float = 0.80, config_file: str = "filter_config.json"):
        self.target_win_rate = target_win_rate
        self.config_file = config_file
        
        # Default filter thresholds (current optimized settings)
        self.thresholds = {
            'confidence': 0.69,
            'adx': 25.0,
            'roc': -1.0,
            'volume': 1.15,
            'atr_min': 0.4,
            'atr_max': 3.5,
            'trend_consistency': 0.55,
            'min_win_rate': 0.72,
            'session_hours_min': 6,
            'session_hours_max': 22
        }
        
        # Performance tracking
        self.performance_history = []
        self.recent_trades = []
        self.adjustments_made = 0
        
        # Load saved config if exists
        self.load_config()
    
    def load_config(self):
        """Load saved filter configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.thresholds = data.get('thresholds', self.thresholds)
                    self.performance_history = data.get('performance_history', [])
                    print(f"📊 Loaded saved config: {len(self.performance_history)} performance records")
        except Exception as e:
            print(f"⚠️  Could not load config: {e}")
    
    def save_config(self):
        """Save current filter configuration"""
        try:
            data = {
                'thresholds': self.thresholds,
                'performance_history': self.performance_history[-50:],  # Keep last 50 records
                'last_updated': datetime.now().isoformat(),
                'adjustments_made': self.adjustments_made
            }
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"💾 Saved config with {len(self.performance_history)} records")
        except Exception as e:
            print(f"⚠️  Could not save config: {e}")
    
    def record_performance(
        self,
        total_trades: int,
        wins: int,
        losses: int,
        win_rate: float,
        total_return: float,
        trades_per_day: float
    ):
        """Record backtest/live performance"""
        
        record = {
            'timestamp': datetime.now().isoformat(),
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'total_return': total_return,
            'trades_per_day': trades_per_day,
            'thresholds': self.thresholds.copy()
        }
        
        self.performance_history.append(record)
        print(f"\n📊 Performance Recorded:")
        print(f"   Trades: {total_trades}, Win Rate: {win_rate:.1%}, Return: {total_return:+.2%}")
    
    def should_adjust(self) -> bool:
        """Determine if filters should be adjusted based on recent performance"""
        
        if len(self.performance_history) < 2:
            return False  # Need at least 2 records
        
        recent = self.performance_history[-1]
        
        # Adjust if:
        # 1. Win rate too low (<70%)
        # 2. Win rate too high (>95%) with too few trades
        # 3. Too many trades (>20/month) with low win rate
        # 4. Too few trades (<3/month)
        
        win_rate = recent['win_rate']
        trades_per_day = recent['trades_per_day']
        trades_per_month = trades_per_day * 30
        
        if win_rate < 0.70:
            print(f"⚠️  Win rate {win_rate:.1%} < 70% - Need to TIGHTEN filters")
            return True
        
        if win_rate > 0.95 and trades_per_month < 5:
            print(f"⚠️  Win rate {win_rate:.1%} > 95% but only {trades_per_month:.1f} trades/month - Need to LOOSEN filters")
            return True
        
        if trades_per_month > 20 and win_rate < 0.80:
            print(f"⚠️  Too many trades ({trades_per_month:.1f}/month) with low win rate {win_rate:.1%} - Need to TIGHTEN filters")
            return True
        
        if trades_per_month < 3:
            print(f"⚠️  Only {trades_per_month:.1f} trades/month - Need to LOOSEN filters")
            return True
        
        return False
    
    def auto_adjust(self):
        """Automatically adjust filters based on recent performance"""
        
        if not self.should_adjust():
            print("✅ Filters are well-calibrated - no adjustment needed")
            return
        
        recent = self.performance_history[-1]
        win_rate = recent['win_rate']
        trades_per_day = recent['trades_per_day']
        trades_per_month = trades_per_day * 30
        
        print(f"\n🔧 AUTO-ADJUSTING FILTERS...")
        print(f"   Current: Win Rate {win_rate:.1%}, {trades_per_month:.1f} trades/month")
        
        # Strategy: Adjust most impactful filters first
        
        # Case 1: Win rate too low - TIGHTEN
        if win_rate < 0.70:
            self.thresholds['confidence'] += 0.02
            self.thresholds['volume'] += 0.05
            self.thresholds['adx'] += 2
            self.thresholds['min_win_rate'] += 0.03
            print(f"   🔒 TIGHTENED: Confidence→{self.thresholds['confidence']:.2f}, Volume→{self.thresholds['volume']:.2f}x")
        
        # Case 2: Win rate too high, few trades - LOOSEN
        elif win_rate > 0.95 and trades_per_month < 5:
            self.thresholds['confidence'] -= 0.02
            self.thresholds['volume'] -= 0.05
            self.thresholds['trend_consistency'] -= 0.05
            print(f"   🔓 LOOSENED: Confidence→{self.thresholds['confidence']:.2f}, Volume→{self.thresholds['volume']:.2f}x")
        
        # Case 3: Too many trades, low win rate - TIGHTEN aggressively
        elif trades_per_month > 20 and win_rate < 0.80:
            self.thresholds['confidence'] += 0.03
            self.thresholds['volume'] += 0.10
            self.thresholds['adx'] += 3
            print(f"   🔒 TIGHTENED (aggressive): Confidence→{self.thresholds['confidence']:.2f}, ADX→{self.thresholds['adx']:.0f}")
        
        # Case 4: Too few trades - LOOSEN
        elif trades_per_month < 3:
            self.thresholds['confidence'] -= 0.03
            self.thresholds['volume'] -= 0.05
            self.thresholds['atr_min'] -= 0.05
            self.thresholds['trend_consistency'] -= 0.05
            print(f"   🔓 LOOSENED (aggressive): Confidence→{self.thresholds['confidence']:.2f}")
        
        # Apply bounds
        self.thresholds['confidence'] = max(0.50, min(0.90, self.thresholds['confidence']))
        self.thresholds['volume'] = max(1.0, min(2.0, self.thresholds['volume']))
        self.thresholds['adx'] = max(15, min(40, self.thresholds['adx']))
        self.thresholds['trend_consistency'] = max(0.30, min(0.80, self.thresholds['trend_consistency']))
        self.thresholds['min_win_rate'] = max(0.65, min(0.85, self.thresholds['min_win_rate']))
        
        self.adjustments_made += 1
        self.save_config()
        
        print(f"   ✅ Adjustments made: {self.adjustments_made} total")
        print(f"   💾 Config saved to {self.config_file}")
    
    def get_thresholds(self) -> Dict[str, float]:
        """Get current filter thresholds"""
        return self.thresholds.copy()
    
    def print_report(self):
        """Print performance and adjustment report"""
        
        print(f"\n{'='*80}")
        print("ADAPTIVE OPTIMIZER REPORT")
        print(f"{'='*80}\n")
        
        print(f"Current Filter Thresholds:")
        print(f"├─ Confidence: {self.thresholds['confidence']:.2f}")
        print(f"├─ ADX: {self.thresholds['adx']:.0f}")
        print(f"├─ ROC: {self.thresholds['roc']:.1f}")
        print(f"├─ Volume: {self.thresholds['volume']:.2f}x")
        print(f"├─ ATR: {self.thresholds['atr_min']:.1f}-{self.thresholds['atr_max']:.1f}%")
        print(f"├─ Trend Consistency: {self.thresholds['trend_consistency']:.2f}")
        print(f"├─ Min Win Rate: {self.thresholds['min_win_rate']:.0%}")
        print(f"└─ Session Hours: {self.thresholds['session_hours_min']}-{self.thresholds['session_hours_max']} UTC\n")
        
        if self.performance_history:
            print(f"Performance History: {len(self.performance_history)} records")
            print(f"Total Adjustments: {self.adjustments_made}\n")
            
            if len(self.performance_history) >= 5:
                recent_5 = self.performance_history[-5:]
                avg_win_rate = sum(r['win_rate'] for r in recent_5) / len(recent_5)
                avg_trades = sum(r['trades_per_day'] for r in recent_5) * 30 / len(recent_5)
                avg_return = sum(r['total_return'] for r in recent_5) / len(recent_5)
                
                print(f"Recent 5 Sessions Average:")
                print(f"├─ Win Rate: {avg_win_rate:.1%}")
                print(f"├─ Trades/Month: {avg_trades:.1f}")
                print(f"└─ Return: {avg_return:+.2%}\n")
        
        print(f"{'='*80}\n")
    
    def get_recommendation(self) -> str:
        """Get recommendation based on current performance"""
        
        if not self.performance_history:
            return "No performance data yet. Run backtests to generate data."
        
        recent = self.performance_history[-1]
        win_rate = recent['win_rate']
        trades_per_month = recent['trades_per_day'] * 30
        
        if 0.75 <= win_rate <= 0.90 and 5 <= trades_per_month <= 15:
            return "✅ OPTIMAL - Filters are well-calibrated. Ready for live trading."
        
        if win_rate < 0.70:
            return "⚠️  WIN RATE TOO LOW - Tighten filters to improve quality."
        
        if win_rate > 0.95 and trades_per_month < 5:
            return "⚠️  TOO SELECTIVE - Loosen filters to increase opportunities."
        
        if trades_per_month < 3:
            return "⚠️  NOT ENOUGH TRADES - Loosen filters significantly."
        
        if trades_per_month > 20 and win_rate < 0.80:
            return "⚠️  TOO MANY LOW-QUALITY TRADES - Tighten filters."
        
        return "📊 MONITORING - Performance is acceptable but could be optimized."


def example_usage():
    """Example of how to use the adaptive optimizer"""
    
    optimizer = AdaptiveOptimizer(target_win_rate=0.80)
    
    # Simulate backtest results
    optimizer.record_performance(
        total_trades=6,
        wins=4,
        losses=2,
        win_rate=0.667,
        total_return=0.0495,
        trades_per_day=0.29
    )
    
    # Check if adjustment needed
    optimizer.auto_adjust()
    
    # Get updated thresholds
    thresholds = optimizer.get_thresholds()
    print(f"\nUpdated Thresholds: {thresholds}")
    
    # Print report
    optimizer.print_report()
    
    # Get recommendation
    recommendation = optimizer.get_recommendation()
    print(f"Recommendation: {recommendation}")


if __name__ == "__main__":
    example_usage()
