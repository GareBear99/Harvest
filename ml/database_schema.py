"""
SQLite Database Schema for Prediction Tracking
Stores predictions, outcomes, and ML weights for deterministic learning
"""

import sqlite3
from typing import Dict, Any, Optional
import json
from datetime import datetime


class TradeDatabase:
    """Manages SQLite database for prediction tracking"""
    
    def __init__(self, db_path: str = "ml/trade_history.db"):
        self.db_path = db_path
        self.conn = None
        self.initialize_database()
    
    def initialize_database(self):
        """Create database tables if they don't exist"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        
        # Predictions table (pre-trade)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                
                -- Entry conditions
                entry_price REAL NOT NULL,
                tp_price REAL NOT NULL,
                sl_price REAL NOT NULL,
                confidence REAL NOT NULL,
                
                -- Features (JSON for flexibility)
                features TEXT NOT NULL,
                
                -- Predictions
                predicted_win_prob REAL NOT NULL,
                predicted_duration_min REAL NOT NULL,
                predicted_pnl REAL NOT NULL,
                predicted_pnl_pct REAL NOT NULL,
                
                -- Trade quality tier
                quality_tier TEXT NOT NULL,
                
                -- Outcome (filled after trade closes)
                outcome_id INTEGER,
                
                FOREIGN KEY (outcome_id) REFERENCES outcomes(id)
            )
        """)
        
        # Outcomes table (post-trade)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                
                -- Actual results
                outcome TEXT NOT NULL,
                actual_duration_min REAL NOT NULL,
                actual_pnl REAL NOT NULL,
                actual_pnl_pct REAL NOT NULL,
                exit_price REAL NOT NULL,
                
                -- Prediction errors
                win_prediction_error REAL NOT NULL,
                duration_error_min REAL NOT NULL,
                pnl_error REAL NOT NULL,
                pnl_pct_error REAL NOT NULL,
                
                -- Learning
                weight_update_applied INTEGER DEFAULT 0,
                
                FOREIGN KEY (prediction_id) REFERENCES predictions(id)
            )
        """)
        
        # Feature weights table (ML learning)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feature_weights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                feature_name TEXT NOT NULL,
                weight REAL NOT NULL,
                update_count INTEGER DEFAULT 0,
                avg_accuracy REAL DEFAULT 0.0,
                
                UNIQUE(version, feature_name)
            )
        """)
        
        # Weight updates log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weight_updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                outcome_id INTEGER NOT NULL,
                feature_name TEXT NOT NULL,
                old_weight REAL NOT NULL,
                new_weight REAL NOT NULL,
                reason TEXT NOT NULL,
                
                FOREIGN KEY (outcome_id) REFERENCES outcomes(id)
            )
        """)
        
        # Create indices for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_predictions_symbol_tf 
            ON predictions(symbol, timeframe)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_predictions_timestamp 
            ON predictions(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_outcomes_prediction 
            ON outcomes(prediction_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_weights_version 
            ON feature_weights(version)
        """)
        
        self.conn.commit()
    
    def store_prediction(self, prediction: Dict[str, Any]) -> int:
        """Store pre-trade prediction"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO predictions (
                timestamp, symbol, timeframe,
                entry_price, tp_price, sl_price, confidence,
                features,
                predicted_win_prob, predicted_duration_min, 
                predicted_pnl, predicted_pnl_pct,
                quality_tier
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prediction['timestamp'],
            prediction['symbol'],
            prediction['timeframe'],
            prediction['entry_price'],
            prediction['tp_price'],
            prediction['sl_price'],
            prediction['confidence'],
            json.dumps(prediction['features']),
            prediction['predicted_win_prob'],
            prediction['predicted_duration_min'],
            prediction['predicted_pnl'],
            prediction['predicted_pnl_pct'],
            prediction['quality_tier']
        ))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def store_outcome(self, prediction_id: int, outcome: Dict[str, Any]) -> int:
        """Store post-trade outcome and calculate errors"""
        cursor = self.conn.cursor()
        
        # Get prediction
        cursor.execute("SELECT * FROM predictions WHERE id = ?", (prediction_id,))
        pred = dict(cursor.fetchone())
        
        # Calculate errors
        win_error = abs((1.0 if outcome['outcome'] == 'TP' else 0.0) - pred['predicted_win_prob'])
        duration_error = abs(outcome['actual_duration_min'] - pred['predicted_duration_min'])
        pnl_error = abs(outcome['actual_pnl'] - pred['predicted_pnl'])
        pnl_pct_error = abs(outcome['actual_pnl_pct'] - pred['predicted_pnl_pct'])
        
        # Store outcome
        cursor.execute("""
            INSERT INTO outcomes (
                prediction_id, timestamp,
                outcome, actual_duration_min, actual_pnl, actual_pnl_pct, exit_price,
                win_prediction_error, duration_error_min, pnl_error, pnl_pct_error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prediction_id,
            outcome['timestamp'],
            outcome['outcome'],
            outcome['actual_duration_min'],
            outcome['actual_pnl'],
            outcome['actual_pnl_pct'],
            outcome['exit_price'],
            win_error,
            duration_error,
            pnl_error,
            pnl_pct_error
        ))
        
        outcome_id = cursor.lastrowid
        
        # Update prediction with outcome reference
        cursor.execute("""
            UPDATE predictions SET outcome_id = ? WHERE id = ?
        """, (outcome_id, prediction_id))
        
        self.conn.commit()
        return outcome_id
    
    def get_similar_trades(self, features: Dict[str, Any], limit: int = 50) -> list:
        """Find historical trades with similar features"""
        cursor = self.conn.cursor()
        
        # Get all completed trades
        cursor.execute("""
            SELECT p.*, o.outcome, o.actual_duration_min, o.actual_pnl
            FROM predictions p
            JOIN outcomes o ON p.outcome_id = o.id
            WHERE p.symbol = ? AND p.timeframe = ?
            ORDER BY p.timestamp DESC
            LIMIT ?
        """, (features.get('symbol', 'ETHUSDT'), features.get('timeframe', '15m'), limit * 2))
        
        all_trades = [dict(row) for row in cursor.fetchall()]
        
        # Filter by feature similarity
        similar = []
        for trade in all_trades:
            trade_features = json.loads(trade['features'])
            similarity = self._calculate_similarity(features, trade_features)
            
            if similarity > 0.7:  # 70% similarity threshold
                trade['similarity'] = similarity
                similar.append(trade)
        
        # Sort by similarity
        similar.sort(key=lambda x: x['similarity'], reverse=True)
        return similar[:limit]
    
    def _calculate_similarity(self, features1: Dict, features2: Dict) -> float:
        """Calculate feature similarity score (0-1)"""
        score = 0.0
        count = 0
        
        # Compare key features
        key_features = ['adx', 'rsi', 'trend_consistency', 'volume_ratio', 'atr_pct']
        
        for key in key_features:
            if key in features1 and key in features2:
                val1 = features1[key]
                val2 = features2[key]
                
                # Normalize difference (closer = higher score)
                if key == 'adx':
                    diff = abs(val1 - val2) / 100
                elif key == 'rsi':
                    diff = abs(val1 - val2) / 100
                elif key == 'trend_consistency':
                    diff = abs(val1 - val2)
                elif key == 'volume_ratio':
                    diff = abs(val1 - val2) / 3
                elif key == 'atr_pct':
                    diff = abs(val1 - val2) / 5
                else:
                    diff = abs(val1 - val2)
                
                score += max(0, 1.0 - diff)
                count += 1
        
        return score / count if count > 0 else 0.0
    
    def get_latest_weights(self) -> Dict[str, float]:
        """Get latest feature weights"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT feature_name, weight
            FROM feature_weights
            WHERE version = (SELECT MAX(version) FROM feature_weights)
        """)
        
        weights = {row['feature_name']: row['weight'] for row in cursor.fetchall()}
        return weights if weights else self._get_default_weights()
    
    def _get_default_weights(self) -> Dict[str, float]:
        """Default feature weights (all equal)"""
        return {
            'adx': 1.0,
            'trend_consistency': 1.0,
            'rsi': 1.0,
            'ema9_slope': 1.0,
            'volume_ratio': 1.0,
            'volume_trend': 1.0,
            'atr_pct': 1.0,
            'distance_to_high': 1.0,
            'roc_10': 1.0
        }
    
    def update_weights(self, outcome_id: int, weight_updates: Dict[str, float]):
        """Update feature weights based on prediction accuracy"""
        cursor = self.conn.cursor()
        
        # Get current version
        cursor.execute("SELECT MAX(version) as max_ver FROM feature_weights")
        result = cursor.fetchone()
        current_version = result['max_ver'] if result['max_ver'] else 0
        new_version = current_version + 1
        
        timestamp = datetime.utcnow().isoformat()
        
        # Get old weights
        old_weights = self.get_latest_weights()
        
        # Store updated weights
        for feature_name, new_weight in weight_updates.items():
            cursor.execute("""
                INSERT INTO feature_weights (version, timestamp, feature_name, weight, update_count)
                VALUES (?, ?, ?, ?, 1)
            """, (new_version, timestamp, feature_name, new_weight))
            
            # Log update
            old_weight = old_weights.get(feature_name, 1.0)
            cursor.execute("""
                INSERT INTO weight_updates (timestamp, outcome_id, feature_name, old_weight, new_weight, reason)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (timestamp, outcome_id, feature_name, old_weight, new_weight, 
                  "Performance-based adjustment"))
        
        self.conn.commit()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall prediction accuracy statistics"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_trades,
                AVG(CASE WHEN o.outcome = 'TP' THEN 1.0 ELSE 0.0 END) as win_rate,
                AVG(o.win_prediction_error) as avg_win_error,
                AVG(o.duration_error_min) as avg_duration_error,
                AVG(o.pnl_error) as avg_pnl_error,
                AVG(o.actual_pnl) as avg_profit
            FROM outcomes o
        """)
        
        stats = dict(cursor.fetchone())
        return stats
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
