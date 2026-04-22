#!/usr/bin/env python3
"""
Enhanced Backtest Results Formatter
Provides comprehensive statistics including seed info, strategy details, and dashboard metrics
"""

from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import json


class BacktestResultsFormatter:
    """Format backtest results with comprehensive statistics"""
    
    def __init__(self):
        self.results = {}
    
    def format_comprehensive_results(
        self,
        backtest_data: Dict,
        strategy_info: Dict,
        seed_info: Dict,
        slot_allocation: Dict,
        mode: str = 'BACKTEST'
    ) -> str:
        """
        Generate comprehensive backtest results report
        
        Args:
            backtest_data: Core backtest results (balance, trades, P&L)
            strategy_info: Strategy configuration and seeds
            seed_info: Seed testing statistics
            slot_allocation: Slot allocation details
            mode: Trading mode (BACKTEST, PAPER, LIVE)
        """
        
        output = []
        
        # Header
        output.append("=" * 90)
        output.append("HARVEST BACKTEST RESULTS - COMPREHENSIVE REPORT")
        output.append("=" * 90)
        output.append("")
        
        # 1. EXECUTIVE SUMMARY
        output.append(self._format_executive_summary(backtest_data, mode))
        
        # 2. STRATEGY & SEED INFORMATION
        output.append(self._format_strategy_info(strategy_info, seed_info))
        
        # 3. SLOT ALLOCATION STATUS
        output.append(self._format_slot_allocation(slot_allocation, backtest_data.get('balance', {})))
        
        # 4. PERFORMANCE METRICS
        output.append(self._format_performance_metrics(backtest_data))
        
        # 5. TIMEFRAME BREAKDOWN
        output.append(self._format_timeframe_breakdown(backtest_data.get('by_timeframe', {})))
        
        # 6. ASSET BREAKDOWN
        output.append(self._format_asset_breakdown(backtest_data.get('by_asset', {})))
        
        # 7. TRADE QUALITY ANALYSIS
        output.append(self._format_trade_quality(backtest_data.get('trades', [])))
        
        # 8. RISK METRICS
        output.append(self._format_risk_metrics(backtest_data))
        
        # 9. ML/STRATEGY STATS
        output.append(self._format_ml_stats(strategy_info))
        
        # 10. RECOMMENDATIONS
        output.append(self._format_recommendations(backtest_data, seed_info))
        
        output.append("=" * 90)
        output.append("END OF REPORT")
        output.append("=" * 90)
        
        return "\n".join(output)
    
    def _format_executive_summary(self, data: Dict, mode: str) -> str:
        """Executive summary section"""
        lines = []
        lines.append("┌─ EXECUTIVE SUMMARY ─" + "─" * 66 + "┐")
        
        balance = data.get('balance', {})
        trades = data.get('trades', [])
        
        initial = balance.get('initial', 0)
        final = balance.get('final', 0)
        profit = final - initial
        roi = (profit / initial * 100) if initial > 0 else 0
        
        wins = len([t for t in trades if t.get('pnl', 0) > 0])
        losses = len(trades) - wins
        win_rate = (wins / len(trades) * 100) if trades else 0
        
        lines.append(f"│")
        lines.append(f"│  Mode: {mode:20s}  Duration: {data.get('duration_days', 0)} days")
        lines.append(f"│  Date Range: {data.get('start_date', 'N/A')} to {data.get('end_date', 'N/A')}")
        lines.append(f"│")
        lines.append(f"│  💰 FINANCIAL SUMMARY:")
        lines.append(f"│     Starting Balance: ${initial:>10.2f}")
        lines.append(f"│     Final Balance:    ${final:>10.2f}")
        lines.append(f"│     Total Profit:     ${profit:>10.2f}  ({roi:+.2f}%)")
        lines.append(f"│")
        lines.append(f"│  📊 TRADING SUMMARY:")
        lines.append(f"│     Total Trades:     {len(trades):>10}")
        lines.append(f"│     Wins / Losses:    {wins:>4} / {losses:<4}")
        lines.append(f"│     Win Rate:         {win_rate:>9.1f}%")
        lines.append(f"│     Avg Trade P&L:    ${(profit/len(trades)) if trades else 0:>9.2f}")
        lines.append(f"│")
        
        lines.append("└" + "─" * 88 + "┘")
        lines.append("")
        return "\n".join(lines)
    
    def _format_strategy_info(self, strategy: Dict, seeds: Dict) -> str:
        """Strategy and seed information"""
        lines = []
        lines.append("┌─ STRATEGY & SEED INFORMATION ─" + "─" * 56 + "┐")
        lines.append("│")
        
        # Strategy Seeds by Timeframe
        lines.append("│  🎲 STRATEGY SEEDS BY TIMEFRAME:")
        for tf, seed_data in strategy.get('seeds_by_timeframe', {}).items():
            seed = seed_data.get('seed', 'N/A')
            input_seed = seed_data.get('input_seed', 'N/A')
            lines.append(f"│     {tf:>4s}: Seed={seed:>10}  (Input: {input_seed})")
        
        lines.append("│")
        
        # Seed Testing Statistics
        lines.append("│  📈 SEED TESTING STATS:")
        lines.append(f"│     Total Tested:     {seeds.get('total_tested', 0):>10}")
        lines.append(f"│     Whitelisted:      {seeds.get('whitelisted', 0):>10}  ({seeds.get('whitelist_pct', 0):.1f}%)")
        lines.append(f"│     Blacklisted:      {seeds.get('blacklisted', 0):>10}  ({seeds.get('blacklist_pct', 0):.1f}%)")
        
        if seeds.get('top_performer'):
            top = seeds['top_performer']
            lines.append("│")
            lines.append(f"│  ⭐ TOP PERFORMER:")
            lines.append(f"│     Seed:             {top.get('seed', 'N/A'):>10}")
            lines.append(f"│     Win Rate:         {top.get('win_rate', 0)*100:>9.1f}%")
            lines.append(f"│     P&L:              ${top.get('pnl', 0):>9.2f}")
        
        lines.append("│")
        lines.append("└" + "─" * 88 + "┘")
        lines.append("")
        return "\n".join(lines)
    
    def _format_slot_allocation(self, slots: Dict, balance: Dict) -> str:
        """Slot allocation status"""
        lines = []
        lines.append("┌─ SLOT ALLOCATION STATUS ─" + "─" * 61 + "┐")
        lines.append("│")
        
        current_balance = balance.get('final', 0)
        active_slots = slots.get('active_slots', 0)
        total_slots = slots.get('total_slots', 10)
        
        lines.append(f"│  💎 CURRENT ALLOCATION:")
        lines.append(f"│     Balance:          ${current_balance:>10.2f}")
        lines.append(f"│     Active Slots:     {active_slots:>3}/{total_slots}")
        lines.append(f"│     ETH Slots:        {slots.get('eth_slots', [])}")
        lines.append(f"│     BTC Slots:        {slots.get('btc_slots', [])}")
        lines.append(f"│     Timeframes:       {', '.join(slots.get('timeframes', []))}")
        
        if slots.get('next_unlock'):
            lines.append("│")
            lines.append(f"│  ⬆️  NEXT UNLOCK:")
            lines.append(f"│     {slots['next_unlock']}")
        
        if slots.get('position_tier'):
            tier = slots['position_tier']
            lines.append("│")
            lines.append(f"│  🏆 POSITION TIER:")
            lines.append(f"│     Current Tier:     {tier.get('current', 0)}")
            lines.append(f"│     Positions/TF:     {tier.get('positions_per_tf', 1)}")
            lines.append(f"│     Total Positions:  {tier.get('total_positions', 10)}")
        
        lines.append("│")
        lines.append("└" + "─" * 88 + "┘")
        lines.append("")
        return "\n".join(lines)
    
    def _format_performance_metrics(self, data: Dict) -> str:
        """Performance metrics"""
        lines = []
        lines.append("┌─ PERFORMANCE METRICS ─" + "─" * 64 + "┐")
        lines.append("│")
        
        trades = data.get('trades', [])
        if not trades:
            lines.append("│  No trades to analyze")
            lines.append("│")
            lines.append("└" + "─" * 88 + "┘")
            return "\n".join(lines)
        
        wins = [t for t in trades if t.get('pnl', 0) > 0]
        losses = [t for t in trades if t.get('pnl', 0) <= 0]
        
        total_pnl = sum(t.get('pnl', 0) for t in trades)
        avg_win = sum(t.get('pnl', 0) for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t.get('pnl', 0) for t in losses) / len(losses) if losses else 0
        
        win_rate = len(wins) / len(trades) * 100
        profit_factor = abs(sum(t.get('pnl', 0) for t in wins) / sum(t.get('pnl', 0) for t in losses)) if losses and sum(t.get('pnl', 0) for t in losses) != 0 else float('inf')
        
        lines.append(f"│  📊 WIN/LOSS ANALYSIS:")
        lines.append(f"│     Win Rate:         {win_rate:>9.1f}%")
        lines.append(f"│     Profit Factor:    {profit_factor:>10.2f}")
        lines.append(f"│     Average Win:      ${avg_win:>9.2f}")
        lines.append(f"│     Average Loss:     ${avg_loss:>9.2f}")
        lines.append(f"│     Win/Loss Ratio:   {abs(avg_win/avg_loss) if avg_loss != 0 else 0:>10.2f}")
        
        lines.append("│")
        lines.append(f"│  💵 P&L BREAKDOWN:")
        lines.append(f"│     Total P&L:        ${total_pnl:>9.2f}")
        lines.append(f"│     Gross Profit:     ${sum(t.get('pnl', 0) for t in wins):>9.2f}")
        lines.append(f"│     Gross Loss:       ${sum(t.get('pnl', 0) for t in losses):>9.2f}")
        
        # Drawdown
        max_dd = data.get('max_drawdown', 0)
        lines.append("│")
        lines.append(f"│  📉 RISK METRICS:")
        lines.append(f"│     Max Drawdown:     ${max_dd:>9.2f}")
        lines.append(f"│     Max DD %:         {(max_dd/data.get('balance', {}).get('initial', 1)*100):>9.2f}%")
        
        lines.append("│")
        lines.append("└" + "─" * 88 + "┘")
        lines.append("")
        return "\n".join(lines)
    
    def _format_timeframe_breakdown(self, tf_data: Dict) -> str:
        """Timeframe breakdown"""
        lines = []
        lines.append("┌─ TIMEFRAME BREAKDOWN ─" + "─" * 64 + "┐")
        lines.append("│")
        
        if not tf_data:
            lines.append("│  No timeframe data available")
            lines.append("│")
            lines.append("└" + "─" * 88 + "┘")
            return "\n".join(lines)
        
        lines.append("│  TF    Trades    Wins  Losses   Win%      P&L      Avg P&L   Avg Size")
        lines.append("│  " + "─" * 84)
        
        for tf in ['1m', '5m', '15m', '1h', '4h']:
            if tf not in tf_data:
                continue
            
            data = tf_data[tf]
            trades = data.get('trades', 0)
            wins = data.get('wins', 0)
            losses = data.get('losses', 0)
            win_rate = (wins / trades * 100) if trades > 0 else 0
            pnl = data.get('pnl', 0)
            avg_pnl = pnl / trades if trades > 0 else 0
            avg_size = data.get('avg_position_size', 0)
            
            lines.append(f"│  {tf:>4s}  {trades:>6}   {wins:>5} {losses:>6}  {win_rate:>5.1f}%  ${pnl:>8.2f}  ${avg_pnl:>7.2f}  ${avg_size:>7.2f}")
        
        lines.append("│")
        lines.append("└" + "─" * 88 + "┘")
        lines.append("")
        return "\n".join(lines)
    
    def _format_asset_breakdown(self, asset_data: Dict) -> str:
        """Asset breakdown"""
        lines = []
        lines.append("┌─ ASSET BREAKDOWN ─" + "─" * 68 + "┐")
        lines.append("│")
        
        if not asset_data:
            lines.append("│  No asset data available")
            lines.append("│")
            lines.append("└" + "─" * 88 + "┘")
            return "\n".join(lines)
        
        lines.append("│  Asset    Trades    Wins  Losses   Win%      P&L      Avg P&L")
        lines.append("│  " + "─" * 84)
        
        for asset in ['ETHUSDT', 'BTCUSDT']:
            if asset not in asset_data:
                continue
            
            data = asset_data[asset]
            trades = data.get('trades', 0)
            wins = data.get('wins', 0)
            losses = trades - wins
            win_rate = (wins / trades * 100) if trades > 0 else 0
            pnl = data.get('pnl', 0)
            avg_pnl = pnl / trades if trades > 0 else 0
            
            asset_short = asset.replace('USDT', '')
            lines.append(f"│  {asset_short:>7}  {trades:>6}   {wins:>5} {losses:>6}  {win_rate:>5.1f}%  ${pnl:>8.2f}  ${avg_pnl:>7.2f}")
        
        lines.append("│")
        lines.append("└" + "─" * 88 + "┘")
        lines.append("")
        return "\n".join(lines)
    
    def _format_trade_quality(self, trades: List[Dict]) -> str:
        """Trade quality analysis"""
        lines = []
        lines.append("┌─ TRADE QUALITY ANALYSIS ─" + "─" * 60 + "┐")
        lines.append("│")
        
        if not trades:
            lines.append("│  No trades to analyze")
            lines.append("│")
            lines.append("└" + "─" * 88 + "┘")
            return "\n".join(lines)
        
        # Quality tier breakdown
        tier_counts = {'A': 0, 'B': 0, 'C': 0, 'Unknown': 0}
        for trade in trades:
            tier = trade.get('quality_tier', 'Unknown')
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
        
        lines.append(f"│  🎯 QUALITY TIER DISTRIBUTION:")
        total = len(trades)
        for tier in ['A', 'B', 'C', 'Unknown']:
            count = tier_counts.get(tier, 0)
            pct = (count / total * 100) if total > 0 else 0
            lines.append(f"│     Tier {tier:7s}:  {count:>6}  ({pct:>5.1f}%)")
        
        # Confidence distribution
        avg_confidence = sum(t.get('confidence', 0) for t in trades) / len(trades) if trades else 0
        lines.append("│")
        lines.append(f"│  📈 CONFIDENCE METRICS:")
        lines.append(f"│     Avg Confidence:   {avg_confidence:>9.2f}")
        lines.append(f"│     Min Confidence:   {min(t.get('confidence', 0) for t in trades):>9.2f}")
        lines.append(f"│     Max Confidence:   {max(t.get('confidence', 0) for t in trades):>9.2f}")
        
        lines.append("│")
        lines.append("└" + "─" * 88 + "┘")
        lines.append("")
        return "\n".join(lines)
    
    def _format_risk_metrics(self, data: Dict) -> str:
        """Risk metrics"""
        lines = []
        lines.append("┌─ RISK METRICS ─" + "─" * 71 + "┐")
        lines.append("│")
        
        trades = data.get('trades', [])
        balance = data.get('balance', {})
        
        if trades:
            # Consecutive wins/losses
            max_consec_wins = 0
            max_consec_losses = 0
            current_wins = 0
            current_losses = 0
            
            for trade in trades:
                if trade.get('pnl', 0) > 0:
                    current_wins += 1
                    current_losses = 0
                    max_consec_wins = max(max_consec_wins, current_wins)
                else:
                    current_losses += 1
                    current_wins = 0
                    max_consec_losses = max(max_consec_losses, current_losses)
            
            lines.append(f"│  🎲 STREAK ANALYSIS:")
            lines.append(f"│     Max Consecutive Wins:     {max_consec_wins:>6}")
            lines.append(f"│     Max Consecutive Losses:   {max_consec_losses:>6}")
            
            # Average trade duration
            avg_duration = sum(t.get('duration_min', 0) for t in trades) / len(trades) if trades else 0
            lines.append("│")
            lines.append(f"│  ⏱️  TIMING METRICS:")
            lines.append(f"│     Avg Trade Duration:       {avg_duration:>6.0f} minutes")
            lines.append(f"│     Total Trading Time:       {sum(t.get('duration_min', 0) for t in trades):>6.0f} minutes")
        
        lines.append("│")
        lines.append("└" + "─" * 88 + "┘")
        lines.append("")
        return "\n".join(lines)
    
    def _format_ml_stats(self, strategy: Dict) -> str:
        """ML/Strategy statistics"""
        lines = []
        lines.append("┌─ ML & STRATEGY STATISTICS ─" + "─" * 58 + "┐")
        lines.append("│")
        
        ml_enabled = strategy.get('ml_enabled', False)
        adaptive_enabled = strategy.get('adaptive_thresholds', False)
        
        lines.append(f"│  🤖 ML FEATURES:")
        lines.append(f"│     ML Predictions:           {'Enabled' if ml_enabled else 'Disabled':>10}")
        lines.append(f"│     Adaptive Thresholds:      {'Enabled' if adaptive_enabled else 'Disabled':>10}")
        lines.append(f"│     Intelligent Learning:     {strategy.get('intelligent_learning', 'Disabled'):>10}")
        
        if strategy.get('strategy_switches'):
            lines.append("│")
            lines.append(f"│  🔄 STRATEGY SWITCHES:")
            lines.append(f"│     Total Switches:           {strategy.get('strategy_switches', 0):>10}")
        
        lines.append("│")
        lines.append("└" + "─" * 88 + "┘")
        lines.append("")
        return "\n".join(lines)
    
    def _format_recommendations(self, data: Dict, seeds: Dict) -> str:
        """Recommendations based on results"""
        lines = []
        lines.append("┌─ RECOMMENDATIONS ─" + "─" * 68 + "┐")
        lines.append("│")
        
        trades = data.get('trades', [])
        balance = data.get('balance', {})
        
        if not trades:
            lines.append("│  ⚠️  No trades executed - check entry criteria")
            lines.append("│")
            lines.append("└" + "─" * 88 + "┘")
            return "\n".join(lines)
        
        win_rate = len([t for t in trades if t.get('pnl', 0) > 0]) / len(trades) * 100
        profit = balance.get('final', 0) - balance.get('initial', 0)
        
        # Generate recommendations
        recommendations = []
        
        if win_rate < 50:
            recommendations.append("Win rate below 50% - consider adjusting entry criteria")
        elif win_rate > 80:
            recommendations.append("Excellent win rate! Consider increasing position sizes")
        
        if profit < 0:
            recommendations.append("Net loss - review strategy parameters and risk management")
        elif profit > balance.get('initial', 0):
            recommendations.append("Excellent returns! Strategy performing well")
        
        if len(trades) < 10:
            recommendations.append("Limited trade count - consider longer backtest period")
        
        whitelist_pct = seeds.get('whitelist_pct', 0)
        if whitelist_pct < 10:
            recommendations.append("Low seed whitelist rate - continue seed discovery")
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                lines.append(f"│  {i}. {rec}")
        else:
            lines.append("│  ✅ Strategy performing within normal parameters")
        
        lines.append("│")
        lines.append("└" + "─" * 88 + "┘")
        lines.append("")
        return "\n".join(lines)


def save_results_to_file(results: str, output_dir: str = "results"):
    """Save results to timestamped file"""
    Path(output_dir).mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/backtest_results_{timestamp}.txt"
    
    with open(filename, 'w') as f:
        f.write(results)
    
    return filename


if __name__ == "__main__":
    # Demo
    formatter = BacktestResultsFormatter()
    
    # Mock data
    demo_data = {
        'balance': {'initial': 10.0, 'final': 34.75},
        'duration_days': 90,
        'start_date': '2024-09-17',
        'end_date': '2024-12-16',
        'trades': [{'pnl': 2.5, 'confidence': 0.85, 'quality_tier': 'A', 'duration_min': 120}] * 35,
        'max_drawdown': 4.8,
        'by_timeframe': {
            '1m': {'trades': 11, 'wins': 8, 'losses': 3, 'pnl': 5.40, 'avg_position_size': 85.50},
            '5m': {'trades': 8, 'wins': 6, 'losses': 2, 'pnl': 3.65, 'avg_position_size': 92.30}
        },
        'by_asset': {
            'ETHUSDT': {'trades': 18, 'wins': 14, 'pnl': 12.30},
            'BTCUSDT': {'trades': 17, 'wins': 13, 'pnl': 12.45}
        }
    }
    
    strategy_data = {
        'seeds_by_timeframe': {
            '1m': {'seed': 1829669, 'input_seed': 555},
            '5m': {'seed': 5659348, 'input_seed': 666}
        },
        'ml_enabled': True,
        'adaptive_thresholds': True
    }
    
    seed_data = {
        'total_tested': 258,
        'whitelisted': 47,
        'blacklisted': 89,
        'whitelist_pct': 18.2,
        'blacklist_pct': 34.5,
        'top_performer': {'seed': 15913535, 'win_rate': 0.82, 'pnl': 24.75}
    }
    
    slot_data = {
        'active_slots': 3,
        'total_slots': 10,
        'eth_slots': [1, 3],
        'btc_slots': [2],
        'timeframes': ['1m', '5m'],
        'next_unlock': 'Slot 4 (BTC) @ $40 ($5 away)'
    }
    
    results = formatter.format_comprehensive_results(
        demo_data, strategy_data, seed_data, slot_data
    )
    
    print(results)
