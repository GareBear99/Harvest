"""
Intelligent Learning Engine - Identifies WHY predictions fail and learns adaptively
Tracks recurring errors, categorizes failures, and adjusts weights based on patterns
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict


class IntelligentLearner:
    """
    Advanced learning system that:
    1. Categorizes prediction failures (why we were wrong)
    2. Tracks recurring vs new issues
    3. Adjusts weights based on error patterns
    4. Suggests improvements for persistent problems
    """
    
    def __init__(self, data_file: str = "ml/intelligent_learning_data.json"):
        self.data_file = data_file
        
        # Error categorization
        self.error_patterns = {
            'trend_reversal': {'count': 0, 'features': [], 'severity': 0},
            'false_breakout': {'count': 0, 'features': [], 'severity': 0},
            'volatility_spike': {'count': 0, 'features': [], 'severity': 0},
            'time_decay': {'count': 0, 'features': [], 'severity': 0},
            'wrong_confluence': {'count': 0, 'features': [], 'severity': 0},
            'premature_exit': {'count': 0, 'features': [], 'severity': 0}
        }
        
        # Track individual feature performance
        def make_feature_dict():
            return {
                'correct': 0,
                'wrong': 0,
                'error_types': defaultdict(int)
            }
        self.feature_errors = defaultdict(make_feature_dict)
        
        # Recent predictions for analysis
        self.recent_predictions = []
        
        # Load existing data
        self.load_learning_data()
        
        print("🧠 Intelligent Learner initialized")
        print(f"   Error patterns tracked: {len(self.error_patterns)}")
        if self.error_patterns['trend_reversal']['count'] > 0:
            print(f"   Most common error: {self._get_most_common_error()}")
    
    def load_learning_data(self):
        """Load previously learned error patterns"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.error_patterns = data.get('error_patterns', self.error_patterns)
                    # Convert defaultdict from JSON
                    feature_errors_raw = data.get('feature_errors', {})
                    for feature, errors in feature_errors_raw.items():
                        self.feature_errors[feature] = {
                            'correct': errors.get('correct', 0),
                            'wrong': errors.get('wrong', 0),
                            'error_types': defaultdict(int, errors.get('error_types', {}))
                        }
                print(f"✅ Loaded learning data with {sum(p['count'] for p in self.error_patterns.values())} tracked errors")
        except Exception as e:
            print(f"⚠️  Could not load learning data: {e}")
    
    def save_learning_data(self):
        """Save learned error patterns"""
        try:
            data = {
                'error_patterns': self.error_patterns,
                'feature_errors': dict(self.feature_errors),
                'last_updated': datetime.now().isoformat(),
                'total_errors': sum(p['count'] for p in self.error_patterns.values())
            }
            
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"💾 Saved learning data")
        except Exception as e:
            print(f"❌ Error saving learning data: {e}")
    
    def analyze_failure(
        self,
        prediction: Dict,
        actual_outcome: Dict,
        features: Dict
    ) -> Dict:
        """
        Analyze WHY a prediction failed and categorize the error
        
        Args:
            prediction: Original prediction made
            actual_outcome: What actually happened
            features: Market features at time of trade
            
        Returns:
            Analysis with error category and recommended adjustments
        """
        
        predicted_win = prediction.get('predicted_win_prob', 0.5)
        predicted_duration = prediction.get('predicted_duration_min', 60)
        predicted_pnl = prediction.get('predicted_pnl', 0)
        
        actual_win = actual_outcome.get('won', False)
        actual_duration = actual_outcome.get('duration_min', 0)
        actual_pnl = actual_outcome.get('pnl', 0)
        
        # Categorize the failure
        error_category = self._categorize_error(
            prediction, actual_outcome, features
        )
        
        # Track this error
        self.error_patterns[error_category]['count'] += 1
        self.error_patterns[error_category]['severity'] = self._calculate_severity(error_category)
        
        # Identify problematic features
        problematic_features = self._identify_problematic_features(
            error_category, features
        )
        
        # Update feature error tracking
        for feature in problematic_features:
            self.feature_errors[feature]['wrong'] += 1
            self.feature_errors[feature]['error_types'][error_category] += 1
        
        # Determine if this is a recurring error
        is_recurring = self.error_patterns[error_category]['count'] >= 3
        
        # Calculate adaptive weight adjustment
        weight_adjustment = self._calculate_adaptive_adjustment(
            error_category, is_recurring, problematic_features
        )
        
        analysis = {
            'error_category': error_category,
            'is_recurring': is_recurring,
            'occurrence_count': self.error_patterns[error_category]['count'],
            'problematic_features': problematic_features,
            'weight_adjustments': weight_adjustment,
            'severity': self.error_patterns[error_category]['severity'],
            'recommendation': self._generate_recommendation(error_category, is_recurring)
        }
        
        # Save updated data
        self.save_learning_data()
        
        return analysis
    
    def _categorize_error(
        self,
        prediction: Dict,
        actual: Dict,
        features: Dict
    ) -> str:
        """Categorize what type of error occurred"""
        
        predicted_win = prediction.get('predicted_win_prob', 0.5)
        actual_win = actual.get('won', False)
        actual_duration = actual.get('duration_min', 0)
        exit_type = actual.get('exit_type', 'unknown')
        
        # False breakout: Hit SL very quickly
        if exit_type == 'SL' and actual_duration < 30:
            return 'false_breakout'
        
        # Trend reversal: Hit SL after extended time
        if exit_type == 'SL' and actual_duration > 120:
            return 'trend_reversal'
        
        # Time decay: Hit time limit without reaching TP
        if exit_type == 'TIME':
            return 'time_decay'
        
        # Volatility spike: Large unexpected move
        if exit_type == 'SL' and features.get('atr_pct', 0) > 2.0:
            return 'volatility_spike'
        
        # Premature exit: TP hit but smaller than expected
        if exit_type == 'TP' and actual.get('pnl', 0) < prediction.get('predicted_pnl', 0) * 0.5:
            return 'premature_exit'
        
        # Wrong confluence: Predicted high prob but failed
        if predicted_win > 0.80 and not actual_win:
            return 'wrong_confluence'
        
        return 'wrong_confluence'  # Default
    
    def _identify_problematic_features(
        self,
        error_category: str,
        features: Dict
    ) -> List[str]:
        """Identify which features led to this error"""
        
        problematic = []
        
        if error_category == 'trend_reversal':
            # Trend indicators failed
            if features.get('trend_consistency', 0) < 0.70:
                problematic.append('trend_consistency')
            if features.get('adx', 0) < 30:
                problematic.append('adx')
            problematic.append('ema9_slope')
            problematic.append('ema21_slope')
        
        elif error_category == 'false_breakout':
            # Entry timing was wrong
            problematic.append('volume_ratio')
            problematic.append('roc_10')
            if features.get('atr_pct', 0) > 1.5:
                problematic.append('atr_pct')
        
        elif error_category == 'volatility_spike':
            # Volatility indicators missed it
            problematic.append('atr_pct')
            if features.get('volume_ratio', 0) > 1.5:
                problematic.append('volume_ratio')
        
        elif error_category == 'time_decay':
            # Momentum wasn't strong enough
            problematic.append('roc_10')
            problematic.append('adx')
        
        elif error_category == 'wrong_confluence':
            # Multiple indicators gave false signals
            problematic.extend([
                'trend_consistency',
                'volume_ratio',
                'distance_from_ema9'
            ])
        
        return problematic
    
    def _calculate_adaptive_adjustment(
        self,
        error_category: str,
        is_recurring: bool,
        problematic_features: List[str]
    ) -> Dict[str, float]:
        """Calculate adaptive weight adjustments based on error pattern"""
        
        adjustments = {}
        
        occurrence_count = self.error_patterns[error_category]['count']
        
        for feature in problematic_features:
            if occurrence_count == 1:
                # First time: standard penalty
                adjustments[feature] = -0.10
            elif occurrence_count == 2:
                # Second time: increased penalty
                adjustments[feature] = -0.15
            elif occurrence_count >= 3:
                # Persistent issue: aggressive penalty
                adjustments[feature] = -0.25
            else:
                adjustments[feature] = -0.10
        
        return adjustments
    
    def _calculate_severity(self, error_category: str) -> float:
        """Calculate severity of error type (0-1)"""
        count = self.error_patterns[error_category]['count']
        
        # Normalize to 0-1 scale (cap at 20 occurrences)
        return min(count / 20.0, 1.0)
    
    def _generate_recommendation(
        self,
        error_category: str,
        is_recurring: bool
    ) -> str:
        """Generate actionable recommendation based on error"""
        
        recommendations = {
            'trend_reversal': "Consider tightening trend_consistency threshold or requiring stronger ADX",
            'false_breakout': "Increase volume requirement or add momentum confirmation",
            'volatility_spike': "Lower maximum ATR threshold or add volatility buffer",
            'time_decay': "Reduce time limit or require stronger momentum (ROC)",
            'wrong_confluence': "Re-evaluate feature weights - multiple indicators giving false signals",
            'premature_exit': "Review TP calculation - may be hitting profit too early"
        }
        
        rec = recommendations.get(error_category, "Review filter configuration")
        
        if is_recurring:
            rec = f"🚨 RECURRING ISSUE: {rec} (occurred {self.error_patterns[error_category]['count']} times)"
        
        return rec
    
    def record_success(self, features: Dict):
        """Record successful prediction for comparison"""
        for feature_name in features.keys():
            self.feature_errors[feature_name]['correct'] += 1
    
    def _get_most_common_error(self) -> str:
        """Get the most frequently occurring error"""
        return max(
            self.error_patterns.items(),
            key=lambda x: x[1]['count']
        )[0]
    
    def get_error_summary(self) -> Dict:
        """Get summary of all errors"""
        total_errors = sum(p['count'] for p in self.error_patterns.values())
        
        if total_errors == 0:
            return {'message': 'No errors recorded yet'}
        
        summary = {
            'total_errors': total_errors,
            'error_breakdown': {},
            'most_problematic_features': self._get_worst_features(3),
            'recurring_issues': []
        }
        
        for error_type, data in self.error_patterns.items():
            if data['count'] > 0:
                summary['error_breakdown'][error_type] = {
                    'count': data['count'],
                    'percentage': (data['count'] / total_errors) * 100,
                    'severity': data['severity']
                }
                
                if data['count'] >= 3:
                    summary['recurring_issues'].append(error_type)
        
        return summary
    
    def _get_worst_features(self, top_n: int = 3) -> List[Dict]:
        """Get features with worst performance"""
        feature_performance = []
        
        for feature, stats in self.feature_errors.items():
            total = stats['correct'] + stats['wrong']
            if total > 0:
                accuracy = stats['correct'] / total
                feature_performance.append({
                    'feature': feature,
                    'accuracy': accuracy,
                    'correct': stats['correct'],
                    'wrong': stats['wrong'],
                    'error_types': dict(stats['error_types'])
                })
        
        # Sort by accuracy (worst first)
        feature_performance.sort(key=lambda x: x['accuracy'])
        
        return feature_performance[:top_n]
    
    def print_learning_report(self):
        """Print comprehensive learning report"""
        print(f"\n{'='*80}")
        print("INTELLIGENT LEARNING REPORT")
        print(f"{'='*80}\n")
        
        summary = self.get_error_summary()
        
        if 'message' in summary:
            print(summary['message'])
            return
        
        print(f"Total Prediction Errors: {summary['total_errors']}\n")
        
        print("Error Type Breakdown:")
        for error_type, data in summary['error_breakdown'].items():
            print(f"  {error_type:20s} {data['count']:3d} ({data['percentage']:5.1f}%) "
                  f"Severity: {data['severity']:.2f}")
        
        if summary['recurring_issues']:
            print(f"\n🚨 Recurring Issues ({len(summary['recurring_issues'])}):") 
            for issue in summary['recurring_issues']:
                count = self.error_patterns[issue]['count']
                print(f"  • {issue} (occurred {count} times)")
        
        print(f"\n📉 Worst Performing Features:")
        for feat_data in summary['most_problematic_features']:
            print(f"  {feat_data['feature']:20s} "
                  f"Accuracy: {feat_data['accuracy']:.1%} "
                  f"({feat_data['correct']}✅/{feat_data['wrong']}❌)")
            if feat_data['error_types']:
                top_error = max(feat_data['error_types'].items(), key=lambda x: x[1])
                print(f"    → Most common: {top_error[0]} ({top_error[1]} times)")
        
        print(f"\n{'='*80}\n")


def demo():
    """Demonstrate intelligent learning"""
    learner = IntelligentLearner()
    
    # Simulate a failed prediction
    prediction = {
        'predicted_win_prob': 0.83,
        'predicted_duration_min': 30,
        'predicted_pnl': 0.25
    }
    
    actual = {
        'won': False,
        'duration_min': 5,
        'pnl': -0.10,
        'exit_type': 'SL'
    }
    
    features = {
        'adx': 28,
        'trend_consistency': 0.60,
        'volume_ratio': 1.20,
        'atr_pct': 1.1,
        'roc_10': -1.8
    }
    
    print("\n🎮 DEMO: Analyzing failed prediction...\n")
    
    analysis = learner.analyze_failure(prediction, actual, features)
    
    print(f"Error Category: {analysis['error_category']}")
    print(f"Is Recurring: {analysis['is_recurring']}")
    print(f"Occurrence Count: {analysis['occurrence_count']}")
    print(f"Severity: {analysis['severity']:.2f}")
    print(f"\nProblematic Features:")
    for feature in analysis['problematic_features']:
        adj = analysis['weight_adjustments'].get(feature, 0)
        print(f"  • {feature}: {adj:+.2f}")
    
    print(f"\n💡 Recommendation:")
    print(f"   {analysis['recommendation']}")
    
    # Print full report
    learner.print_learning_report()
    
    return learner


if __name__ == "__main__":
    demo()
