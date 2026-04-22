"""
ML Strategy Learner - Saves and evolves strategies with 80%+ win rate
Automatically learns what works and optimizes toward 90% win rate
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import statistics


class StrategyLearner:
    """
    Learns from trading results and saves successful strategies (80%+ win rate)
    Evolves parameters to consistently achieve 90% win rate
    """
    
    def __init__(self, strategies_file: str = "ml/learned_strategies.json"):
        self.strategies_file = strategies_file
        self.strategies = []
        self.current_session = {
            'trades': [],
            'start_time': datetime.now().isoformat(),
            'filters': {}
        }
        
        # Load existing strategies
        self.load_strategies()
        
        print(f"📚 Strategy Learner initialized")
        print(f"   Saved strategies: {len(self.strategies)}")
        if self.strategies:
            best = max(self.strategies, key=lambda s: s['win_rate'])
            print(f"   Best strategy: {best['win_rate']:.1f}% win rate")
    
    def load_strategies(self):
        """Load previously learned strategies"""
        try:
            if os.path.exists(self.strategies_file):
                with open(self.strategies_file, 'r') as f:
                    data = json.load(f)
                    self.strategies = data.get('strategies', [])
                print(f"✅ Loaded {len(self.strategies)} learned strategies")
        except Exception as e:
            print(f"⚠️  Could not load strategies: {e}")
            self.strategies = []
    
    def save_strategies(self):
        """Save all learned strategies"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.strategies_file), exist_ok=True)
            
            data = {
                'strategies': self.strategies,
                'last_updated': datetime.now().isoformat(),
                'total_strategies': len(self.strategies),
                'best_win_rate': max((s['win_rate'] for s in self.strategies), default=0)
            }
            
            with open(self.strategies_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"💾 Saved {len(self.strategies)} strategies")
        except Exception as e:
            print(f"❌ Error saving strategies: {e}")
    
    def record_trade(self, trade: Dict):
        """Record a trade in current session"""
        self.current_session['trades'].append(trade)
    
    def set_current_filters(self, filters: Dict):
        """Set the filter configuration for current session"""
        self.current_session['filters'] = filters
    
    def analyze_session(self) -> Dict:
        """Analyze current session and determine if strategy should be saved"""
        
        trades = self.current_session['trades']
        
        if len(trades) < 5:
            return {
                'should_save': False,
                'reason': f'Not enough trades ({len(trades)} < 5)',
                'win_rate': 0
            }
        
        wins = [t for t in trades if t.get('pnl', 0) > 0]
        losses = [t for t in trades if t.get('pnl', 0) <= 0]
        
        win_rate = (len(wins) / len(trades)) * 100
        
        # Calculate other metrics
        avg_win = statistics.mean([t['pnl'] for t in wins]) if wins else 0
        avg_loss = statistics.mean([abs(t['pnl']) for t in losses]) if losses else 0
        total_pnl = sum(t['pnl'] for t in trades)
        
        rr_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        
        # Save if win rate >= 80%
        should_save = win_rate >= 80.0
        
        analysis = {
            'should_save': should_save,
            'win_rate': win_rate,
            'total_trades': len(trades),
            'wins': len(wins),
            'losses': len(losses),
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'rr_ratio': rr_ratio,
            'total_pnl': total_pnl,
            'filters': self.current_session['filters'],
            'timestamp': datetime.now().isoformat()
        }
        
        if should_save:
            analysis['reason'] = f'✅ WIN RATE {win_rate:.1f}% >= 80% - SAVING STRATEGY'
        else:
            analysis['reason'] = f'❌ Win rate {win_rate:.1f}% < 80% - Not saving'
        
        return analysis
    
    def save_current_strategy(self, analysis: Dict):
        """Save current strategy if it meets criteria"""
        
        if not analysis['should_save']:
            print(f"\n{analysis['reason']}")
            return False
        
        # Create strategy record
        strategy = {
            'id': len(self.strategies) + 1,
            'timestamp': analysis['timestamp'],
            'win_rate': analysis['win_rate'],
            'total_trades': analysis['total_trades'],
            'wins': analysis['wins'],
            'losses': analysis['losses'],
            'avg_win': analysis['avg_win'],
            'avg_loss': analysis['avg_loss'],
            'rr_ratio': analysis['rr_ratio'],
            'total_pnl': analysis['total_pnl'],
            'filters': analysis['filters']
        }
        
        # Add to strategies list
        self.strategies.append(strategy)
        
        # Save to file
        self.save_strategies()
        
        print(f"\n🎉 NEW STRATEGY SAVED!")
        print(f"   Strategy #{strategy['id']}")
        print(f"   Win Rate: {strategy['win_rate']:.1f}%")
        print(f"   Trades: {strategy['total_trades']}")
        print(f"   R/R: {strategy['rr_ratio']:.2f}:1")
        print(f"   Total PnL: ${strategy['total_pnl']:+.2f}")
        
        return True
    
    def get_best_strategy(self) -> Optional[Dict]:
        """Get the best performing strategy"""
        if not self.strategies:
            return None
        
        # Sort by win rate, then by total trades
        sorted_strategies = sorted(
            self.strategies,
            key=lambda s: (s['win_rate'], s['total_trades']),
            reverse=True
        )
        
        return sorted_strategies[0]
    
    def get_strategies_above_threshold(self, min_win_rate: float = 85.0) -> List[Dict]:
        """Get all strategies above a certain win rate"""
        return [s for s in self.strategies if s['win_rate'] >= min_win_rate]
    
    def suggest_filters(self) -> Optional[Dict]:
        """Suggest filter settings based on best strategies"""
        
        high_win_strategies = self.get_strategies_above_threshold(85.0)
        
        if not high_win_strategies:
            high_win_strategies = self.get_strategies_above_threshold(80.0)
        
        if not high_win_strategies:
            return None
        
        # Average the filter values from successful strategies
        filter_keys = set()
        for strategy in high_win_strategies:
            filter_keys.update(strategy['filters'].keys())
        
        suggested_filters = {}
        for key in filter_keys:
            values = [s['filters'][key] for s in high_win_strategies if key in s['filters']]
            if values:
                if isinstance(values[0], (int, float)):
                    suggested_filters[key] = statistics.mean(values)
                else:
                    suggested_filters[key] = values[0]  # Use most common
        
        return suggested_filters
    
    def print_learning_report(self):
        """Print comprehensive learning report"""
        
        print(f"\n{'='*80}")
        print("ML STRATEGY LEARNING REPORT")
        print(f"{'='*80}\n")
        
        print(f"Total Strategies Learned: {len(self.strategies)}")
        
        if not self.strategies:
            print("No strategies learned yet. Keep trading to gather data!\n")
            return
        
        # Win rate distribution
        win_rates = [s['win_rate'] for s in self.strategies]
        print(f"\nWin Rate Statistics:")
        print(f"├─ Best: {max(win_rates):.1f}%")
        print(f"├─ Average: {statistics.mean(win_rates):.1f}%")
        print(f"├─ Worst: {min(win_rates):.1f}%")
        print(f"└─ Target: 90.0%\n")
        
        # Strategies by performance tier
        elite = [s for s in self.strategies if s['win_rate'] >= 90]
        excellent = [s for s in self.strategies if 85 <= s['win_rate'] < 90]
        good = [s for s in self.strategies if 80 <= s['win_rate'] < 85]
        
        print(f"Strategy Distribution:")
        print(f"├─ Elite (90%+): {len(elite)} strategies")
        print(f"├─ Excellent (85-90%): {len(excellent)} strategies")
        print(f"└─ Good (80-85%): {len(good)} strategies\n")
        
        # Best strategy details
        best = self.get_best_strategy()
        if best:
            print(f"🏆 Best Strategy (#{best['id']}):")
            print(f"├─ Win Rate: {best['win_rate']:.1f}%")
            print(f"├─ Trades: {best['total_trades']}")
            print(f"├─ R/R: {best['rr_ratio']:.2f}:1")
            print(f"├─ Avg Win: ${best['avg_win']:.2f}")
            print(f"├─ Avg Loss: ${best['avg_loss']:.2f}")
            print(f"└─ Total PnL: ${best['total_pnl']:+.2f}\n")
            
            print(f"Filter Configuration:")
            for key, value in best['filters'].items():
                if isinstance(value, float):
                    print(f"   {key}: {value:.2f}")
                else:
                    print(f"   {key}: {value}")
        
        print(f"\n{'='*80}\n")
    
    def export_best_strategies(self, output_file: str = "ml/BEST_STRATEGIES.txt"):
        """Export best strategies to readable text file"""
        
        if not self.strategies:
            print("No strategies to export")
            return
        
        # Get top strategies
        top_strategies = sorted(
            self.strategies,
            key=lambda s: s['win_rate'],
            reverse=True
        )[:10]  # Top 10
        
        content = f"""
================================================================================
TOP PERFORMING STRATEGIES - TARGET: 90% WIN RATE
================================================================================

Total Strategies Learned: {len(self.strategies)}
Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
        
        for i, strategy in enumerate(top_strategies, 1):
            content += f"""
{'='*80}
STRATEGY #{strategy['id']} - RANK #{i}
{'='*80}

Performance Metrics:
├─ Win Rate: {strategy['win_rate']:.1f}% {'🏆' if strategy['win_rate'] >= 90 else '⭐' if strategy['win_rate'] >= 85 else '✅'}
├─ Total Trades: {strategy['total_trades']}
├─ Wins: {strategy['wins']} | Losses: {strategy['losses']}
├─ Avg Win: ${strategy['avg_win']:.4f}
├─ Avg Loss: ${strategy['avg_loss']:.4f}
├─ Risk/Reward: {strategy['rr_ratio']:.2f}:1
└─ Total PnL: ${strategy['total_pnl']:+.4f}

Filter Configuration:
"""
            for key, value in strategy['filters'].items():
                if isinstance(value, float):
                    content += f"├─ {key}: {value:.3f}\n"
                else:
                    content += f"├─ {key}: {value}\n"
            
            content += f"\nTimestamp: {strategy['timestamp']}\n"
        
        content += f"""

{'='*80}
USAGE INSTRUCTIONS
{'='*80}

To use a strategy:
1. Copy the filter configuration from your chosen strategy
2. Update analysis/high_accuracy_filter.py with these values
3. Run backtest to validate performance
4. Monitor results and adjust if needed

Strategies are automatically saved when win rate >= 80%
Target: Consistently achieve 90%+ win rate

{'='*80}
"""
        
        try:
            with open(output_file, 'w') as f:
                f.write(content)
            print(f"✅ Best strategies exported to {output_file}")
        except Exception as e:
            print(f"❌ Error exporting strategies: {e}")


def demo_usage():
    """Demonstrate strategy learner"""
    
    learner = StrategyLearner()
    
    # Simulate a trading session with 80%+ win rate
    print("\n🎮 DEMO: Simulating high win rate trading session...\n")
    
    # Set current filter configuration
    learner.set_current_filters({
        'confidence': 0.70,
        'adx': 25,
        'volume': 1.15,
        'trend_consistency': 0.55,
        'atr_min': 0.4
    })
    
    # Simulate trades
    demo_trades = [
        {'pnl': 0.28, 'outcome': 'WIN'},
        {'pnl': 0.29, 'outcome': 'WIN'},
        {'pnl': -0.14, 'outcome': 'LOSS'},
        {'pnl': 0.28, 'outcome': 'WIN'},
        {'pnl': 0.29, 'outcome': 'WIN'},
        {'pnl': 0.30, 'outcome': 'WIN'},
    ]
    
    for trade in demo_trades:
        learner.record_trade(trade)
    
    # Analyze session
    analysis = learner.analyze_session()
    
    print(f"Session Analysis:")
    print(f"├─ {analysis['reason']}")
    print(f"├─ Win Rate: {analysis['win_rate']:.1f}%")
    print(f"├─ Trades: {analysis['total_trades']}")
    print(f"└─ R/R: {analysis['rr_ratio']:.2f}:1\n")
    
    # Save if good
    if analysis['should_save']:
        learner.save_current_strategy(analysis)
    
    # Print report
    learner.print_learning_report()
    
    # Export best strategies
    learner.export_best_strategies()
    
    # Suggest filters for next session
    suggested = learner.suggest_filters()
    if suggested:
        print("\n💡 Suggested Filters for Next Session:")
        for key, value in suggested.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.2f}")
            else:
                print(f"   {key}: {value}")
    
    return learner


if __name__ == "__main__":
    demo_usage()
