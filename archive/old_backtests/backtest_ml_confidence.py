#!/usr/bin/env python3
"""
ML Confidence-Filtered Backtest
Only trades setups with confidence >= threshold for 90%+ win rate
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.indicators_backtest import BacktestIndicators
from core.tier_manager import TierManager
from core.position_sizer import PositionSizer
from core.profit_locker import ProfitLocker
from core.leverage_scaler import LeverageScaler
from analysis.ml_confidence_model import extract_features, calculate_rule_based_confidence


def backtest_ml_confidence(data_file: str, starting_balance: float = 10.0, confidence_threshold: float = 0.90):
    """Backtest with ML confidence filtering"""
    
    print(f"\n{'='*80}")
    print(f"ML CONFIDENCE BACKTEST: {data_file.split('/')[-1]}")
    print(f"Confidence Threshold: {confidence_threshold:.2f}")
    print(f"{'='*80}\n")
    
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    candles = data['candles']
    symbol = data_file.split('/')[-1].split('_')[0].upper()
    
    # Aggregate timeframes
    candles_1h = BacktestIndicators.aggregate_candles(candles, 60)
    candles_4h = BacktestIndicators.aggregate_candles(candles, 240)
    
    # Initialize systems
    tier_mgr = TierManager()
    position_sizer = PositionSizer()
    profit_locker = ProfitLocker()
    leverage_scaler = LeverageScaler()
    
    balance = starting_balance
    total_balance = balance
    locked_profit = 0.0
    active_position = None
    trades = []
    
    print(f"Starting Balance: ${balance:.2f}")
    print(f"Starting Date: {candles[0]['timestamp']}")
    print(f"End Date: {candles[-1]['timestamp']}")
    print(f"\nSearching for high-confidence setups...")
    print("-" * 80)
    
    # Backtest loop
    for i in range(len(candles)):
        timestamp = candles[i]['timestamp']
        close = candles[i]['close']
        
        idx_1h = i // 60
        idx_4h = i // 240
        
        # Skip if insufficient history
        if idx_4h < 20 or idx_1h < 50:
            continue
        
        # Check existing position
        if active_position:
            minutes_held = i - active_position['entry_idx']
            
            # Check TP (SHORT)
            if candles[i]['low'] <= active_position['tp_price']:
                pnl = (active_position['entry_price'] - active_position['tp_price']) * active_position['position_size']
                pnl_pct = (pnl / active_position['margin']) * 100
                
                balance += pnl
                total_balance = balance + locked_profit
                
                # Check for profit locking milestone
                lock_result = profit_locker.check_and_lock(total_balance)
                if lock_result['locked']:
                    locked_profit = lock_result['locked_balance']
                    lock_amount = lock_result['lock_amount'] - (locked_profit - lock_result['lock_amount'])
                    balance = lock_result['tradeable_balance']
                    total_balance = balance + locked_profit
                    print(f"  🔒 PROFIT LOCKED: ${lock_result['lock_amount']:.2f} at ${lock_result['milestone_reached']:.2f} milestone")
                
                trades.append({
                    'entry_time': active_position['entry_time'],
                    'exit_time': timestamp,
                    'entry_price': active_position['entry_price'],
                    'exit_price': active_position['tp_price'],
                    'direction': 'SHORT',
                    'outcome': 'TP',
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'balance': balance,
                    'total_balance': total_balance,
                    'minutes_held': minutes_held,
                    'tier': active_position['tier'],
                    'confidence': active_position['confidence'],
                    'tp_pct': active_position['tp_pct'],
                    'sl_pct': active_position['sl_pct']
                })
                
                print(f"✅ TP HIT  | ${active_position['entry_price']:.2f} → ${active_position['tp_price']:.2f} | "
                      f"+${pnl:.2f} ({pnl_pct:+.1f}%) | {minutes_held}m | "
                      f"Conf: {active_position['confidence']:.2f} | Balance: ${total_balance:.2f}")
                
                active_position = None
                continue
            
            # Check SL (SHORT)
            if candles[i]['high'] >= active_position['sl_price']:
                pnl = (active_position['entry_price'] - active_position['sl_price']) * active_position['position_size']
                pnl_pct = (pnl / active_position['margin']) * 100
                
                balance += pnl
                total_balance = balance + locked_profit
                
                trades.append({
                    'entry_time': active_position['entry_time'],
                    'exit_time': timestamp,
                    'entry_price': active_position['entry_price'],
                    'exit_price': active_position['sl_price'],
                    'direction': 'SHORT',
                    'outcome': 'SL',
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'balance': balance,
                    'total_balance': total_balance,
                    'minutes_held': minutes_held,
                    'tier': active_position['tier'],
                    'confidence': active_position['confidence'],
                    'tp_pct': active_position['tp_pct'],
                    'sl_pct': active_position['sl_pct']
                })
                
                print(f"❌ SL HIT  | ${active_position['entry_price']:.2f} → ${active_position['sl_price']:.2f} | "
                      f"-${abs(pnl):.2f} ({pnl_pct:+.1f}%) | {minutes_held}m | "
                      f"Conf: {active_position['confidence']:.2f} | Balance: ${total_balance:.2f}")
                
                active_position = None
                continue
            
            # Check time limit (12 hours)
            if minutes_held >= 720:
                exit_price = close
                pnl = (active_position['entry_price'] - exit_price) * active_position['position_size']
                pnl_pct = (pnl / active_position['margin']) * 100
                
                balance += pnl
                total_balance = balance + locked_profit
                
                trades.append({
                    'entry_time': active_position['entry_time'],
                    'exit_time': timestamp,
                    'entry_price': active_position['entry_price'],
                    'exit_price': exit_price,
                    'direction': 'SHORT',
                    'outcome': 'Time',
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'balance': balance,
                    'total_balance': total_balance,
                    'minutes_held': minutes_held,
                    'tier': active_position['tier'],
                    'confidence': active_position['confidence'],
                    'tp_pct': active_position['tp_pct'],
                    'sl_pct': active_position['sl_pct']
                })
                
                print(f"⏱️  TIME   | ${active_position['entry_price']:.2f} → ${exit_price:.2f} | "
                      f"{pnl:+.2f} ({pnl_pct:+.1f}%) | {minutes_held}m | "
                      f"Conf: {active_position['confidence']:.2f} | Balance: ${total_balance:.2f}")
                
                active_position = None
                continue
        
        # Look for new entry
        if not active_position and balance > 0:
            # Get regime
            regime = BacktestIndicators.get_market_regime(
                candles_1h[:idx_1h + 1],
                candles_4h[:idx_4h + 1]
            )
            
            if regime != 'BEAR':
                continue
            
            # Minimal entry filters - let confidence do the heavy lifting
            closes_1h = [c['close'] for c in candles_1h[:idx_1h + 1]]
            ema9 = BacktestIndicators.ema(closes_1h, period=9)
            ema21 = BacktestIndicators.ema(closes_1h, period=21)
            
            # Only require basic trend alignment
            if not (close < ema9 < ema21):
                continue
            
            # Extract features for confidence scoring
            features = extract_features(candles_1h, candles_4h, idx_1h, idx_4h, close)
            
            if features is None:
                continue
            
            # Calculate confidence
            confidence = calculate_rule_based_confidence(features)
            
            # FILTER: Only trade if confidence >= threshold
            if confidence < confidence_threshold:
                continue
            
            # Calculate ATR-normalized TP/SL
            atr = BacktestIndicators.atr(candles_1h[:idx_1h + 1], period=14)
            atr_pct = (atr / close) * 100
            
            tp_pct = atr_pct * 2.0  # 2× ATR
            sl_pct = atr_pct * 1.0  # 1× ATR
            
            # Update tier based on balance
            tier_info = tier_mgr.update_tier(total_balance)
            tier = tier_info['new_tier']
            tier_config = tier_mgr.get_config(tier)
            
            # Calculate leverage based on total balance
            leverage = leverage_scaler.get_leverage(total_balance)
            
            # Calculate position size
            # Risk amount in dollars
            risk_amount = balance * (tier_config.max_risk_per_trade_pct / 100)
            
            # Position value in dollars = risk / stop_loss_pct * leverage
            # This gives us the notional value we can trade
            position_value = (risk_amount / (sl_pct / 100)) * leverage
            
            # Cap position value at balance * leverage (full exposure)
            max_position_value = balance * leverage
            position_value = min(position_value, max_position_value)
            
            # Margin required = position_value / leverage
            margin = position_value / leverage
            
            # Position size in units = position_value / price
            position_size = position_value / close
            
            if margin > balance:
                continue
            
            # Enter position
            tp_price = close * (1 - tp_pct / 100)
            sl_price = close * (1 + sl_pct / 100)
            
            active_position = {
                'entry_time': timestamp,
                'entry_idx': i,
                'entry_price': close,
                'tp_price': tp_price,
                'sl_price': sl_price,
                'tp_pct': tp_pct,
                'sl_pct': sl_pct,
                'position_size': position_size,
                'margin': margin,
                'leverage': leverage,
                'tier': tier,
                'confidence': confidence
            }
            
            print(f"🎯 ENTRY   | ${close:.2f} | TP: ${tp_price:.2f} ({tp_pct:.2f}%) | "
                  f"SL: ${sl_price:.2f} ({sl_pct:.2f}%) | Lev: {leverage:.0f}× | "
                  f"Conf: {confidence:.2f} ⭐")
    
    # Final results
    print(f"\n{'='*80}")
    print("RESULTS")
    print(f"{'='*80}\n")
    
    if not trades:
        print("❌ NO TRADES met confidence threshold")
        return
    
    total_return = ((total_balance - starting_balance) / starting_balance) * 100
    wins = [t for t in trades if t['pnl'] > 0]
    losses = [t for t in trades if t['pnl'] <= 0]
    win_rate = (len(wins) / len(trades)) * 100
    
    print(f"Symbol: {symbol}")
    print(f"Total Trades: {len(trades)}")
    print(f"Wins: {len(wins)} | Losses: {len(losses)}")
    print(f"Win Rate: {win_rate:.1f}%")
    print(f"\nStarting Balance: ${starting_balance:.2f}")
    print(f"Ending Balance: ${balance:.2f}")
    print(f"Locked Profit: ${locked_profit:.2f}")
    print(f"Total Balance: ${total_balance:.2f}")
    print(f"Total Return: {total_return:+.2f}%")
    
    if trades:
        avg_win = sum(t['pnl'] for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t['pnl'] for t in losses) / len(losses) if losses else 0
        print(f"\nAvg Win: ${avg_win:.2f}")
        print(f"Avg Loss: ${avg_loss:.2f}")
        
        avg_tp = sum(t['tp_pct'] for t in trades) / len(trades)
        avg_sl = sum(t['sl_pct'] for t in trades) / len(trades)
        print(f"Avg TP/SL: {avg_tp:.2f}% / {avg_sl:.2f}%")
        
        # Breakdown by outcome
        outcomes = {}
        for t in trades:
            outcome = t['outcome']
            outcomes[outcome] = outcomes.get(outcome, 0) + 1
        
        print(f"\nOutcomes:")
        for outcome, count in sorted(outcomes.items()):
            pct = (count / len(trades)) * 100
            print(f"  {outcome}: {count} ({pct:.1f}%)")
        
        # Max drawdown
        balances = [t['total_balance'] for t in trades]
        peak = starting_balance
        max_dd = 0
        for bal in balances:
            if bal > peak:
                peak = bal
            dd = ((peak - bal) / peak) * 100
            if dd > max_dd:
                max_dd = dd
        
        print(f"\nMax Drawdown: {max_dd:.2f}%")
        
        # Confidence stats
        avg_conf = sum(t['confidence'] for t in trades) / len(trades)
        print(f"\nAvg Confidence: {avg_conf:.2f}")
        
        # Show top trades by confidence
        print(f"\nTop 5 Trades by Confidence:")
        sorted_trades = sorted(trades, key=lambda x: x['confidence'], reverse=True)
        for i, t in enumerate(sorted_trades[:5]):
            result = "✅" if t['pnl'] > 0 else "❌"
            print(f"  {i+1}. {result} Conf: {t['confidence']:.2f} | {t['outcome']} | PnL: ${t['pnl']:+.2f}")


if __name__ == "__main__":
    # Test lower thresholds for daily trading frequency
    for threshold in [0.50, 0.60, 0.65]:
        print(f"\n{'#'*80}")
        print(f"TESTING THRESHOLD: {threshold:.2f}")
        print(f"{'#'*80}")
        
        backtest_ml_confidence('data/eth_21days.json', starting_balance=10.0, confidence_threshold=threshold)
        backtest_ml_confidence('data/btc_21days.json', starting_balance=10.0, confidence_threshold=threshold)
