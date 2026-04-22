"""
Adaptive Threshold Adjuster - Severity-based strategy adjustments
Calculates adjustment magnitude based on distance from 72% target win rate
Integrates intelligent learner insights for feature-specific adjustments
"""

from typing import Dict, Optional


class AdaptiveThresholdAdjuster:
    """
    Calculates and applies severity-based threshold adjustments
    
    Severity zones:
    - 80%+: Optimal (no adjustment)
    - 72-80%: Sweet spot (minimal adjustment, 2%)
    - 65-72%: Below target (gradual, up to 10%)
    - 50-65%: Significant gap (moderate, up to 20%)
    - <50%: Critical (aggressive, up to 30%)
    """
    
    def __init__(self, target_wr: float = 0.72):
        self.target_wr = target_wr
        
        # Safety bounds for each threshold
        self.bounds = {
            'min_confidence': (0.50, 0.90),
            'min_volume': (1.0, 2.0),
            'min_trend': (0.30, 0.80),
            'min_adx': (15, 40),
            'min_roc': (-3.0, -0.5),
            'atr_min': (0.2, 0.8),
            'atr_max': (2.0, 5.0)
        }
    
    def calculate_severity(self, current_wr: float, target_wr: float = None) -> float:
        """
        Calculate adjustment severity based on distance from target
        
        Args:
            current_wr: Current win rate (0.0-1.0)
            target_wr: Target win rate (default 0.72)
        
        Returns:
            Severity multiplier (0.0-0.30)
        """
        if target_wr is None:
            target_wr = self.target_wr
        
        distance = target_wr - current_wr
        
        # Win rate zones
        if current_wr >= 0.80:
            # Optimal - no adjustment needed
            return 0.0
        elif 0.72 <= current_wr < 0.80:
            # Sweet spot - minimal adjustment
            return 0.02
        elif 0.65 <= current_wr < 0.72:
            # Below target - gradual adjustment
            return min(0.10, distance * 0.7)
        elif 0.50 <= current_wr < 0.65:
            # Significant gap - moderate adjustment
            return min(0.20, distance * 1.0)
        else:  # < 0.50
            # Critical - aggressive adjustment
            return min(0.30, distance * 1.5)
    
    def calculate_adjustments(
        self,
        timeframe: str,
        current_thresholds: Dict[str, float],
        severity: float,
        phase_magnitude: float = 1.0,
        error_insights: Optional[Dict] = None,
        current_wr: float = 0.5
    ) -> Dict[str, float]:
        """
        Calculate new threshold values based on severity and error insights
        
        Args:
            timeframe: '15m', '1h', or '4h'
            current_thresholds: Current threshold values
            severity: Adjustment severity (0.0-0.30)
            phase_magnitude: Phase-based scaling (0.3-1.0)
            error_insights: Insights from intelligent_learner
            current_wr: Current win rate to determine direction
        
        Returns:
            Dict of new threshold values
        """
        # Apply phase magnitude to severity
        adjusted_severity = severity * phase_magnitude
        
        # Determine if we need to tighten or loosen
        if current_wr < 0.72:
            # Below target - TIGHTEN filters
            direction = 1  # Increase thresholds
        elif current_wr > 0.85:
            # Too high - LOOSEN for more trades
            direction = -1  # Decrease thresholds
        else:
            # In range - maintain
            return current_thresholds.copy()
        
        # Base adjustments
        new_thresholds = {}
        for key, value in current_thresholds.items():
            if key in ['min_confidence', 'min_volume', 'min_trend', 'min_adx']:
                # Parameters that increase when tightening
                multiplier = 1 + (adjusted_severity * direction)
                if key == 'min_trend':
                    # Less aggressive on trend
                    multiplier = 1 + (adjusted_severity * 0.7 * direction)
                new_thresholds[key] = value * multiplier
            
            elif key == 'min_roc':
                # ROC: more negative = stricter (tightening means more negative)
                adjustment = adjusted_severity * 0.5 * direction
                new_thresholds[key] = value - adjustment
            
            elif key == 'atr_max':
                # ATR max: lower = stricter
                multiplier = 1 - (adjusted_severity * 0.5 * direction)
                new_thresholds[key] = value * multiplier
            
            elif key == 'atr_min':
                # ATR min: keep relatively stable
                new_thresholds[key] = value
            
            else:
                # Unknown key - keep unchanged
                new_thresholds[key] = value
        
        # Apply intelligent learner insights
        if error_insights and direction == 1:  # Only when tightening
            new_thresholds = self._apply_error_insights(
                new_thresholds, 
                error_insights,
                adjusted_severity
            )
        
        # Apply safety bounds
        new_thresholds = self._apply_bounds(new_thresholds)
        
        return new_thresholds
    
    def _apply_error_insights(
        self,
        thresholds: Dict[str, float],
        error_insights: Dict,
        severity: float
    ) -> Dict[str, float]:
        """
        Apply intelligent learner insights for feature-specific adjustments
        
        Args:
            thresholds: Current threshold values
            error_insights: From intelligent_learner.get_error_summary()
            severity: Base severity
        
        Returns:
            Adjusted thresholds
        """
        recurring_errors = error_insights.get('recurring_issues', [])
        
        # Extra tightening based on recurring error types
        for error_type in recurring_errors:
            if error_type == 'false_breakout':
                # False breakouts = insufficient volume/momentum
                if 'min_volume' in thresholds:
                    thresholds['min_volume'] *= (1 + severity * 0.15)  # Extra 15%
                if 'min_roc' in thresholds:
                    thresholds['min_roc'] -= (severity * 0.4)  # Stricter momentum
            
            elif error_type == 'trend_reversal':
                # Trend reversals = weak trend indicators
                if 'min_trend' in thresholds:
                    thresholds['min_trend'] *= (1 + severity * 0.20)  # Extra 20%
                if 'min_adx' in thresholds:
                    thresholds['min_adx'] += (severity * 5)  # +5 ADX per severity
            
            elif error_type == 'volatility_spike':
                # Volatility spikes = ATR range too wide
                if 'atr_max' in thresholds:
                    thresholds['atr_max'] *= (1 - severity * 0.15)  # Tighter range
            
            elif error_type == 'time_decay':
                # Time decay = momentum not strong enough
                if 'min_roc' in thresholds:
                    thresholds['min_roc'] -= (severity * 0.3)
                if 'min_adx' in thresholds:
                    thresholds['min_adx'] += (severity * 3)
            
            elif error_type == 'wrong_confluence':
                # Multiple indicators failing - tighten everything slightly
                for key in ['min_confidence', 'min_volume', 'min_trend']:
                    if key in thresholds:
                        thresholds[key] *= (1 + severity * 0.10)
        
        return thresholds
    
    def _apply_bounds(self, thresholds: Dict[str, float]) -> Dict[str, float]:
        """Apply safety bounds to prevent extreme values"""
        bounded = {}
        for key, value in thresholds.items():
            if key in self.bounds:
                min_val, max_val = self.bounds[key]
                bounded[key] = max(min_val, min(max_val, value))
            else:
                bounded[key] = value
        return bounded
    
    def get_adjustment_direction(self, current_wr: float, target_wr: float = None) -> str:
        """
        Get human-readable adjustment direction
        
        Returns: 'tighten', 'loosen', or 'maintain'
        """
        if target_wr is None:
            target_wr = self.target_wr
        
        if current_wr < 0.72:
            return 'tighten'
        elif current_wr > 0.85:
            return 'loosen'
        else:
            return 'maintain'
    
    def format_adjustment_summary(
        self,
        old_thresholds: Dict[str, float],
        new_thresholds: Dict[str, float],
        severity: float,
        direction: str
    ) -> str:
        """Generate human-readable adjustment summary"""
        lines = [f"\n🔧 THRESHOLD ADJUSTMENT ({direction.upper()}, severity: {severity:.1%})"]
        lines.append("=" * 60)
        
        for key in sorted(old_thresholds.keys()):
            old_val = old_thresholds[key]
            new_val = new_thresholds[key]
            change_pct = ((new_val - old_val) / old_val) * 100 if old_val != 0 else 0
            
            if abs(change_pct) > 0.1:  # Only show changed values
                lines.append(
                    f"  {key:20s}: {old_val:6.2f} → {new_val:6.2f} "
                    f"({change_pct:+.1f}%)"
                )
        
        return "\n".join(lines)


def test_adjuster():
    """Test the adjuster with various scenarios"""
    adjuster = AdaptiveThresholdAdjuster()
    
    print("🧪 TESTING ADAPTIVE THRESHOLD ADJUSTER\n")
    
    # Test case 1: 57% WR (current system)
    print("Test 1: Current system (57% WR, 14.9% below target)")
    print("-" * 60)
    
    current_thresholds = {
        'min_confidence': 0.70,
        'min_volume': 1.15,
        'min_trend': 0.55,
        'min_adx': 25,
        'min_roc': -1.0,
        'atr_min': 0.4,
        'atr_max': 3.5
    }
    
    severity = adjuster.calculate_severity(0.571)
    print(f"Severity: {severity:.1%}")
    print(f"Direction: {adjuster.get_adjustment_direction(0.571)}")
    
    # Simulate false_breakout recurring
    error_insights = {
        'recurring_issues': ['false_breakout'],
        'most_problematic_features': [
            {'feature': 'volume_ratio', 'accuracy': 0.0},
            {'feature': 'roc_10', 'accuracy': 0.0}
        ]
    }
    
    new_thresholds = adjuster.calculate_adjustments(
        timeframe='15m',
        current_thresholds=current_thresholds,
        severity=severity,
        phase_magnitude=1.0,  # Exploration phase
        error_insights=error_insights,
        current_wr=0.571
    )
    
    print(adjuster.format_adjustment_summary(
        current_thresholds, new_thresholds, severity, 'tighten'
    ))
    
    # Test case 2: 75% WR (in sweet spot)
    print("\n\nTest 2: Sweet spot (75% WR)")
    print("-" * 60)
    
    severity2 = adjuster.calculate_severity(0.75)
    print(f"Severity: {severity2:.1%}")
    print(f"Direction: {adjuster.get_adjustment_direction(0.75)}")
    print("Result: MAINTAIN (locked)")
    
    # Test case 3: 40% WR (critical)
    print("\n\nTest 3: Critical (40% WR, 32% below target)")
    print("-" * 60)
    
    severity3 = adjuster.calculate_severity(0.40)
    print(f"Severity: {severity3:.1%}")
    print(f"Direction: {adjuster.get_adjustment_direction(0.40)}")
    
    new_thresholds3 = adjuster.calculate_adjustments(
        timeframe='15m',
        current_thresholds=current_thresholds,
        severity=severity3,
        phase_magnitude=1.0,
        error_insights=None,
        current_wr=0.40
    )
    
    print(adjuster.format_adjustment_summary(
        current_thresholds, new_thresholds3, severity3, 'tighten'
    ))


if __name__ == "__main__":
    test_adjuster()
