"""
Additional methods for backtest_90_percent.py
Copy these into the MultiTimeframeBacktest class
"""

def _validate_pnl_calculation(self, position: dict, exit_price: float, pnl: float, pnl_pct: float, outcome: str):
    """Validate PnL calculation accuracy"""
    
    # Manual calculation
    expected_pnl = (position['entry_price'] - exit_price) * position['position_size']
    expected_pnl_pct = (expected_pnl / position['margin']) * 100
    
    # Check if calculations match
    pnl_error = abs(pnl - expected_pnl)
    pnl_pct_error = abs(pnl_pct - expected_pnl_pct)
    
    validation = {
        'timestamp': position['entry_time'],
        'outcome': outcome,
        'entry_price': position['entry_price'],
        'exit_price': exit_price,
        'position_size': position['position_size'],
        'margin': position['margin'],
        'calculated_pnl': pnl,
        'expected_pnl': expected_pnl,
        'pnl_error': pnl_error,
        'calculated_pnl_pct': pnl_pct,
        'expected_pnl_pct': expected_pnl_pct,
        'pnl_pct_error': pnl_pct_error,
        'valid': pnl_error < 0.01 and pnl_pct_error < 0.1
    }
    
    self.calculation_checks.append(validation)
    
    # Alert if calculation is off
    if not validation['valid']:
        print(f"  ⚠️ CALCULATION WARNING: PnL error ${pnl_error:.4f}, PnL% error {pnl_pct_error:.2f}%")


def check_entry_opportunity(self, minute_index: int, timeframe: str):
    \"\"\"Check for entry opportunity with HIGH ACCURACY FILTER and PREDICTION TRACKING\"\"\"
    
    if not self.can_open_position(timeframe):
        return
    
    if self.balance <= 0:
        return
    
    config = TIMEFRAME_CONFIGS[timeframe]
    candles_tf = self.candles_by_tf[timeframe]
    
    # Calculate indices
    idx_tf = minute_index // config['aggregation_minutes']
    idx_4h = minute_index // 240
    
    # Need sufficient history
    if idx_tf < 50 or idx_4h < 20 or idx_tf >= len(candles_tf):
        return
    
    # Get regime
    regime = BacktestIndicators.get_market_regime(
        candles_tf[:idx_tf + 1],
        self.candles_by_tf['4h'][:idx_4h + 1]
    )
    
    if regime != 'BEAR':
        return
    
    # Check basic trend alignment
    closes = [c['close'] for c in candles_tf[:idx_tf + 1]]
    ema9 = BacktestIndicators.ema(closes, period=9)
    ema21 = BacktestIndicators.ema(closes, period=21)
    
    current_price = self.candles[minute_index]['close']
    
    if not (current_price < ema9 < ema21):
        return
    
    # Extract features for confidence
    features = extract_features(
        candles_tf, 
        self.candles_by_tf['4h'],
        idx_tf, 
        idx_4h, 
        current_price
    )
    
    if features is None:
        return
    
    confidence = calculate_rule_based_confidence(features)
    
    # Calculate ATR-based TP/SL
    atr = BacktestIndicators.atr(candles_tf[:idx_tf + 1], period=14)
    atr_pct = (atr / current_price) * 100
    
    tp_pct = atr_pct * config['tp_multiplier']
    sl_pct = atr_pct * config['sl_multiplier']
    
    # ===================================================================
    # HIGH ACCURACY FILTER - 10 CRITERIA
    # ===================================================================
    filter_passed, rejection_reason, adjusted_confidence = self.high_accuracy_filter.evaluate(
        candles_tf,
        self.candles_by_tf['4h'],
        idx_tf,
        idx_4h,
        current_price,
        features,
        confidence,
        tp_pct,
        sl_pct,
        regime
    )
    
    if not filter_passed:
        # Uncomment to see rejections:
        # print(f"  ⛔ {timeframe} Rejected: {rejection_reason}")
        return
    
    # ===================================================================
    # PREDICTION GENERATION
    # ===================================================================
    
    # Get tier and leverage
    total_balance = self.get_total_balance()
    tier_info = self.tier_mgr.update_tier(total_balance)
    tier = tier_info['new_tier']
    tier_config = self.tier_mgr.get_config(tier)
    leverage = self.leverage_scaler.get_leverage(total_balance)
    
    # Calculate position size
    risk_amount = self.balance * (tier_config.max_risk_per_trade_pct / 100)
    risk_amount *= config['position_size_multiplier']  # Adjust for timeframe
    
    # Position value needed so that sl_pct loss = risk_amount (unleveraged)
    position_value = risk_amount / (sl_pct / 100)
    max_position_value = self.balance * leverage
    position_value = min(position_value, max_position_value)
    
    margin = position_value / leverage
    
    if margin > self.balance:
        return
    
    position_size = position_value / current_price
    
    # Calculate TP/SL prices
    tp_price = current_price * (1 - tp_pct / 100)
    sl_price = current_price * (1 + sl_pct / 100)
    
    # Generate prediction
    prediction = self.prediction_tracker.generate_prediction(
        symbol=self.symbol,
        timeframe=timeframe,
        entry_price=current_price,
        tp_price=tp_price,
        sl_price=sl_price,
        confidence=adjusted_confidence,
        features=features,
        position_size=position_size,
        margin=margin
    )
    
    # Check if trade meets prediction requirements (85%+ win rate)
    allow_trade, reason = self.prediction_tracker.should_trade(
        prediction['predicted_win_prob'],
        prediction['quality_tier'],
        min_win_rate=0.85  # 85% minimum predicted win rate
    )
    
    if not allow_trade:
        print(f"  🚫 {timeframe} Prediction Reject: {reason}")
        return
    
    # ===================================================================
    # POSITION SIZE ADJUSTMENT BY QUALITY TIER
    # ===================================================================
    tier_multiplier = get_position_size_multiplier(prediction['quality_tier'])
    if tier_multiplier == 0:
        print(f"  🚫 {timeframe} Quality tier too low: {prediction['quality_tier']}")
        return
    
    # Adjust position size by quality
    position_size *= tier_multiplier
    position_value *= tier_multiplier
    margin *= tier_multiplier
    
    # Final margin check
    if margin > self.balance:
        print(f"  ⚠️ {timeframe} Margin ${margin:.2f} exceeds balance ${self.balance:.2f} after tier adjustment")
        return
    
    # ===================================================================
    # ENTER POSITION
    # ===================================================================
    
    self.active_positions[timeframe] = {
        'entry_time': self.candles[minute_index]['timestamp'],
        'entry_minute': minute_index,
        'entry_price': current_price,
        'tp_price': tp_price,
        'sl_price': sl_price,
        'position_size': position_size,
        'margin': margin,
        'leverage': leverage,
        'confidence': adjusted_confidence,
        'prediction_id': prediction['prediction_id'],
        'quality_tier': prediction['quality_tier'],
        'predicted_win_prob': prediction['predicted_win_prob'],
        'predicted_duration_min': prediction['predicted_duration_min'],
        'predicted_pnl': prediction['predicted_pnl']
    }
    
    print(f"🎯 ENTRY {timeframe:3s} | ${current_price:.2f} | TP: ${tp_price:.2f} ({tp_pct:.2f}%) | "
          f"SL: ${sl_price:.2f} ({sl_pct:.2f}%) | Lev: {leverage:.0f}× | "
          f"Conf: {adjusted_confidence:.2f} | Tier: {prediction['quality_tier']} | "
          f"PredWin: {prediction['predicted_win_prob']:.1%} ⭐⭐")


def print_enhanced_results(self):
    \"\"\"Print enhanced results with daily profits, prediction accuracy, and filter stats\"\"\"
    
    print(f"\\n{'='*80}")
    print("RESULTS - 90% WIN RATE SYSTEM")
    print(f"{'='*80}\\n")
    
    if not self.all_trades:
        print("❌ NO TRADES")
        self.high_accuracy_filter.print_filter_report()
        return
    
    total_balance = self.get_total_balance()
    total_return = ((total_balance - self.starting_balance) / self.starting_balance) * 100
    
    wins = [t for t in self.all_trades if t['pnl'] > 0]
    losses = [t for t in self.all_trades if t['pnl'] <= 0]
    win_rate = (len(wins) / len(self.all_trades)) * 100
    
    # Calculate by timeframe
    tf_stats = {}
    for tf in ['15m', '1h', '4h']:
        tf_trades = [t for t in self.all_trades if t['timeframe'] == tf]
        if tf_trades:
            tf_wins = [t for t in tf_trades if t['pnl'] > 0]
            tf_stats[tf] = {
                'trades': len(tf_trades),
                'wins': len(tf_wins),
                'win_rate': (len(tf_wins) / len(tf_trades)) * 100,
                'total_pnl': sum(t['pnl'] for t in tf_trades)
            }
    
    print(f"Symbol: {self.symbol}")
    print(f"Total Trades: {len(self.all_trades)}")
    print(f"Wins: {len(wins)} | Losses: {len(losses)}")
    print(f"Win Rate: {win_rate:.1f}% {'🎯' if win_rate >= 90 else '⚠️' if win_rate >= 80 else '❌'}")
    
    print(f"\\n📊 By Timeframe:")
    for tf in ['15m', '1h', '4h']:
        if tf in tf_stats:
            stats = tf_stats[tf]
            print(f"  {tf}: {stats['trades']} trades, {stats['win_rate']:.1f}% win rate, "
                  f"${stats['total_pnl']:+.2f} PnL")
    
    # Daily stats
    num_days = len(self.candles) / 1440
    trades_per_day = len(self.all_trades) / num_days
    pnl_per_day = (total_balance - self.starting_balance) / num_days
    
    print(f"\\n💰 Performance:")
    print(f"Starting Balance: ${self.starting_balance:.2f}")
    print(f"Ending Balance: ${self.balance:.2f}")
    print(f"Locked Profit: ${self.locked_profit:.2f}")
    print(f"Total Balance: ${total_balance:.2f}")
    print(f"Total Return: {total_return:+.2f}%")
    print(f"\\nTrades/Day: {trades_per_day:.2f}")
    print(f"Profit/Day: ${pnl_per_day:+.2f}")
    
    if wins:
        avg_win = sum(t['pnl'] for t in wins) / len(wins)
        avg_loss = sum(t['pnl'] for t in losses) / len(losses) if losses else 0
        print(f"\\nAvg Win: ${avg_win:.2f}")
        print(f"Avg Loss: ${avg_loss:.2f}")
        if avg_loss != 0:
            rr = abs(avg_win / avg_loss)
            print(f"Risk/Reward: {rr:.2f}:1")
    
    # Max drawdown
    balances = [t['total_balance'] for t in self.all_trades]
    peak = self.starting_balance
    max_dd = 0
    for bal in balances:
        if bal > peak:
            peak = bal
        dd = ((peak - bal) / peak) * 100
        if dd > max_dd:
            max_dd = dd
    
    print(f"\\nMax Drawdown: {max_dd:.2f}%")
    
    # ===================================================================
    # DAILY PROFIT BREAKDOWN
    # ===================================================================
    print(f"\\n{'='*80}")
    print("DAILY PROFIT BREAKDOWN")
    print(f"{'='*80}\\n")
    
    sorted_dates = sorted(self.daily_profits.keys())
    for date in sorted_dates[:10]:  # Show first 10 days
        day_data = self.daily_profits[date]
        wins_today = day_data['wins']
        trades_today = day_data['trades']
        losses_today = trades_today - wins_today
        print(f"{date}: ${day_data['pnl']:+6.2f} ({trades_today} trades, {wins_today}W/{losses_today}L)")
    
    if len(sorted_dates) > 10:
        print(f"... ({len(sorted_dates) - 10} more days)")
    
    # ===================================================================
    # TRADE DURATION STATS
    # ===================================================================
    print(f"\\n{'='*80}")
    print("TRADE DURATION STATS")
    print(f"{'='*80}\\n")
    
    for tf in ['15m', '1h', '4h']:
        if self.trade_durations[tf]:
            durations = self.trade_durations[tf]
            avg_dur = sum(durations) / len(durations)
            min_dur = min(durations)
            max_dur = max(durations)
            print(f"{tf}: Avg {avg_dur:.0f}min, Min {min_dur}min, Max {max_dur}min ({len(durations)} trades)")
    
    # ===================================================================
    # PREDICTION ACCURACY
    # ===================================================================
    print(f"\\n{'='*80}")
    print("PREDICTION ACCURACY")
    print(f"{'='*80}\\n")
    
    pred_stats = self.prediction_tracker.get_statistics()
    if pred_stats and pred_stats.get('total_trades', 0) > 0:
        print(f"Total Predictions: {pred_stats['total_trades']}")
        print(f"Actual Win Rate: {pred_stats['win_rate']*100:.1f}%")
        print(f"Avg Win Prediction Error: {pred_stats['avg_win_error']:.2f}")
        print(f"Avg Duration Error: ±{pred_stats['avg_duration_error']:.0f} minutes")
        print(f"Avg PnL Error: ±${abs(pred_stats['avg_pnl_error']):.2f}")
    else:
        print("No prediction data available")
    
    # ===================================================================
    # HIGH ACCURACY FILTER REPORT
    # ===================================================================
    self.high_accuracy_filter.print_filter_report()
    
    # ===================================================================
    # CALCULATION VALIDATION SUMMARY
    # ===================================================================
    print(f"\\n{'='*80}")
    print("CALCULATION VALIDATION")
    print(f"{'='*80}\\n")
    
    if self.calculation_checks:
        valid_count = sum(1 for c in self.calculation_checks if c['valid'])
        print(f"Total Calculations Checked: {len(self.calculation_checks)}")
        print(f"Valid: {valid_count}/{len(self.calculation_checks)} ({valid_count/len(self.calculation_checks)*100:.1f}%)")
        
        invalid = [c for c in self.calculation_checks if not c['valid']]
        if invalid:
            print(f"\\n⚠️ Invalid Calculations Found: {len(invalid)}")
            for inv in invalid[:5]:
                print(f"  {inv['timestamp']}: PnL error ${inv['pnl_error']:.4f}, PnL% error {inv['pnl_pct_error']:.2f}%")
        else:
            print("\\n✅ ALL CALCULATIONS VALID")
    else:
        print("No calculation checks performed")
