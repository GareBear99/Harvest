"""
Prediction Tracker - Pre-trade predictions and post-trade validation
Learns from prediction errors to improve accuracy over time
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, Optional, List
from ml.database_schema import TradeDatabase
from datetime import datetime


class PredictionTracker:
    """Tracks predictions vs actual outcomes and learns from errors"""
    
    def __init__(self, db_path: str = "ml/trade_history.db"):
        self.db = TradeDatabase(db_path)
        self.active_predictions = {}  # timeframe -> prediction_id
        self.feature_weights = self.db.get_latest_weights()
    
    def generate_prediction(
        self,
        symbol: str,
        timeframe: str,
        entry_price: float,
        tp_price: float,
        sl_price: float,
        confidence: float,
        features: Dict[str, Any],
        position_size: float,
        margin: float
    ) -> Dict[str, Any]:
        """
        Generate pre-trade prediction based on historical patterns
        
        Returns prediction with expected win rate, duration, and PnL
        """
        
        # Find similar historical trades
        search_features = {
            'symbol': symbol,
            'timeframe': timeframe,
            **features
        }
        
        similar_trades = self.db.get_similar_trades(search_features, limit=30)
        
        # Calculate predictions from similar trades
        if len(similar_trades) >= 5:
            # Historical-based prediction
            win_count = sum(1 for t in similar_trades if t['outcome'] == 'TP')
            predicted_win_prob = win_count / len(similar_trades)
            
            avg_duration = sum(t['actual_duration_min'] for t in similar_trades) / len(similar_trades)
            avg_pnl = sum(t['actual_pnl'] for t in similar_trades) / len(similar_trades)
            
            # Weight by similarity
            weighted_win_prob = sum(
                (1 if t['outcome'] == 'TP' else 0) * t['similarity'] 
                for t in similar_trades
            ) / sum(t['similarity'] for t in similar_trades)
            
            predicted_win_prob = weighted_win_prob
            
        else:
            # Confidence-based prediction (no sufficient history)
            predicted_win_prob = self._confidence_to_win_prob(confidence, features)
            avg_duration = self._estimate_duration(timeframe, features)
            avg_pnl = self._estimate_pnl(entry_price, tp_price, sl_price, 
                                         position_size, predicted_win_prob)
        
        # Calculate expected PnL percentage
        tp_pct = abs((tp_price - entry_price) / entry_price) * 100
        sl_pct = abs((sl_price - entry_price) / entry_price) * 100
        expected_pnl_pct = (predicted_win_prob * tp_pct) - ((1 - predicted_win_prob) * sl_pct)
        expected_pnl_pct_on_margin = (expected_pnl_pct / entry_price) * position_size * entry_price / margin * 100
        
        # Determine trade quality tier
        quality_tier = self._get_quality_tier(predicted_win_prob, features)
        
        # Build prediction object
        prediction = {
            'timestamp': datetime.utcnow().isoformat(),
            'symbol': symbol,
            'timeframe': timeframe,
            'entry_price': entry_price,
            'tp_price': tp_price,
            'sl_price': sl_price,
            'confidence': confidence,
            'features': features,
            'predicted_win_prob': predicted_win_prob,
            'predicted_duration_min': avg_duration,
            'predicted_pnl': avg_pnl,
            'predicted_pnl_pct': expected_pnl_pct_on_margin,
            'quality_tier': quality_tier,
            'similar_trades_count': len(similar_trades)
        }
        
        # Store prediction in database
        prediction_id = self.db.store_prediction(prediction)
        self.active_predictions[timeframe] = prediction_id
        
        return {
            'prediction_id': prediction_id,
            'allow_trade': predicted_win_prob >= 0.70,  # Minimum 70% to trade
            **prediction
        }
    
    def validate_outcome(
        self,
        timeframe: str,
        outcome: str,
        exit_price: float,
        actual_pnl: float,
        actual_pnl_pct: float,
        duration_minutes: float
    ) -> Dict[str, Any]:
        """
        Validate prediction against actual outcome
        Updates ML weights based on accuracy
        """
        
        if timeframe not in self.active_predictions:
            return {'error': 'No active prediction for timeframe'}
        
        prediction_id = self.active_predictions[timeframe]
        
        # Build outcome object
        outcome_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'outcome': outcome,
            'actual_duration_min': duration_minutes,
            'actual_pnl': actual_pnl,
            'actual_pnl_pct': actual_pnl_pct,
            'exit_price': exit_price
        }
        
        # Store outcome and calculate errors
        outcome_id = self.db.store_outcome(prediction_id, outcome_data)
        
        # Get prediction for weight updates
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM predictions WHERE id = ?", (prediction_id,))
        prediction = dict(cursor.fetchone())
        
        cursor.execute("SELECT * FROM outcomes WHERE id = ?", (outcome_id,))
        outcome_record = dict(cursor.fetchone())
        
        # Update feature weights based on prediction accuracy
        self._update_weights(prediction, outcome_record)
        
        # Clear active prediction
        del self.active_predictions[timeframe]
        
        return {
            'outcome_id': outcome_id,
            'win_prediction_error': outcome_record['win_prediction_error'],
            'duration_error_min': outcome_record['duration_error_min'],
            'pnl_error': outcome_record['pnl_error']
        }
    
    def _confidence_to_win_prob(self, confidence: float, features: Dict) -> float:
        """Convert confidence score to win probability using feature weights"""
        
        # Apply feature weights
        weighted_confidence = 0.0
        total_weight = 0.0
        
        for feature_name, feature_value in features.items():
            if feature_name in self.feature_weights:
                weight = self.feature_weights[feature_name]
                weighted_confidence += confidence * weight
                total_weight += weight
        
        if total_weight > 0:
            weighted_confidence /= total_weight
        else:
            weighted_confidence = confidence
        
        # Conservative adjustment (reduce overconfidence)
        win_prob = weighted_confidence * 0.85
        
        return max(0.0, min(1.0, win_prob))
    
    def _estimate_duration(self, timeframe: str, features: Dict) -> float:
        """Estimate trade duration based on timeframe and volatility"""
        
        # Base duration by timeframe
        base_duration = {
            '15m': 60,   # 1 hour average
            '1h': 360,   # 6 hours average
            '4h': 1080   # 18 hours average
        }.get(timeframe, 180)
        
        # Adjust by trend strength (stronger trend = faster resolution)
        adx = features.get('adx', 25)
        if adx > 40:
            base_duration *= 0.7  # Fast moves
        elif adx < 20:
            base_duration *= 1.5  # Slow moves
        
        return base_duration
    
    def _estimate_pnl(
        self,
        entry: float,
        tp: float,
        sl: float,
        position_size: float,
        win_prob: float
    ) -> float:
        """Estimate expected PnL based on win probability"""
        
        tp_pnl = (entry - tp) * position_size
        sl_pnl = (entry - sl) * position_size
        
        expected_pnl = (win_prob * tp_pnl) + ((1 - win_prob) * sl_pnl)
        
        return expected_pnl
    
    def _get_quality_tier(self, win_prob: float, features: Dict) -> str:
        """Determine trade quality tier based on predicted win rate"""
        
        # Additional quality checks
        adx = features.get('adx', 0)
        trend_consistency = features.get('trend_consistency', 0)
        volume_ratio = features.get('volume_ratio', 0)
        
        # Bonus for strong technical setup
        quality_bonus = 0.0
        if adx > 35:
            quality_bonus += 0.03
        if trend_consistency > 0.8:
            quality_bonus += 0.03
        if volume_ratio > 1.5:
            quality_bonus += 0.02
        
        adjusted_prob = win_prob + quality_bonus
        
        if adjusted_prob >= 0.90:
            return 'S'  # Superior (90%+)
        elif adjusted_prob >= 0.80:
            return 'A'  # Excellent (80-90%)
        elif adjusted_prob >= 0.70:
            return 'B'  # Good (70-80%)
        elif adjusted_prob >= 0.60:
            return 'C'  # Acceptable (60-70%)
        else:
            return 'D'  # Poor (<60%)
    
    def _update_weights(self, prediction: Dict, outcome: Dict):
        """Update feature weights based on prediction accuracy"""
        
        import json
        features = json.loads(prediction['features'])
        
        # Calculate prediction accuracy
        was_correct = (
            (outcome['outcome'] == 'TP' and prediction['predicted_win_prob'] >= 0.5) or
            (outcome['outcome'] != 'TP' and prediction['predicted_win_prob'] < 0.5)
        )
        
        # Determine weight adjustment
        if was_correct:
            adjustment = 0.05  # Increase weight for good predictions
        else:
            adjustment = -0.10  # Decrease weight for bad predictions
        
        # Update weights for all features used
        new_weights = {}
        for feature_name in self.feature_weights.keys():
            old_weight = self.feature_weights[feature_name]
            
            # Only adjust if feature was significant
            if feature_name in features:
                new_weight = max(0.1, min(2.0, old_weight + adjustment))  # Clamp [0.1, 2.0]
            else:
                new_weight = old_weight
            
            new_weights[feature_name] = new_weight
        
        # Store updated weights
        self.db.update_weights(outcome['id'], new_weights)
        
        # Update local weights
        self.feature_weights = new_weights
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall prediction accuracy statistics"""
        return self.db.get_statistics()
    
    def should_trade(
        self,
        predicted_win_prob: float,
        quality_tier: str,
        min_win_rate: float = 0.85
    ) -> tuple[bool, str]:
        """
        Determine if trade should be taken based on prediction
        
        Returns: (allow_trade, reason)
        """
        
        if predicted_win_prob < min_win_rate:
            return False, f"Win probability {predicted_win_prob:.1%} below minimum {min_win_rate:.1%}"
        
        if quality_tier in ['D', 'C']:
            return False, f"Quality tier {quality_tier} too low"
        
        return True, f"High quality setup: {quality_tier}-tier, {predicted_win_prob:.1%} predicted"
    
    def close(self):
        """Close database connection"""
        self.db.close()
