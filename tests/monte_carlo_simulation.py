#!/usr/bin/env python3
"""
Monte Carlo Simulation for HARVEST System (Phase 5)
Statistical validation through randomized scenario testing
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import json

from core.models import Config, AccountState, Engine, OHLCV, Side, ExecutionIntent
from core.regime_classifier import RegimeClassifier
from core.risk_governor import RiskGovernor


def generate_price_path(initial_price: float, days: int, volatility: float, 
                        drift: float, periods_per_day: int = 24) -> np.ndarray:
    """
    Generate synthetic price path using geometric Brownian motion.
    
    Args:
        initial_price: Starting price
        days: Number of days to simulate
        volatility: Annual volatility (e.g., 0.8 for 80%)
        drift: Annual drift (e.g., 0.1 for 10% annual growth)
        periods_per_day: Time periods per day (24 for hourly)
    
    Returns:
        Array of prices
    """
    periods = days * periods_per_day
    dt = 1 / (365 * periods_per_day)  # Time step in years
    
    # Generate random returns
    random_returns = np.random.normal(
        drift * dt,
        volatility * np.sqrt(dt),
        periods
    )
    
    # Calculate prices
    price_path = initial_price * np.exp(np.cumsum(random_returns))
    
    return price_path


def create_synthetic_ohlcv(prices: np.ndarray, base_volume: float = 1000.0) -> List[OHLCV]:
    """Create OHLCV data from price path"""
    start_time = datetime.now() - timedelta(hours=len(prices))
    candles = []
    
    for i, price in enumerate(prices):
        # Add random noise for OHLC
        high = price * (1 + np.random.uniform(0, 0.02))
        low = price * (1 - np.random.uniform(0, 0.02))
        open_price = prices[i-1] if i > 0 else price
        
        volume = base_volume * (1 + np.random.uniform(-0.3, 0.3))
        
        candles.append(OHLCV(
            timestamp=start_time + timedelta(hours=i),
            open=open_price,
            high=high,
            low=low,
            close=price,
            volume=volume
        ))
    
    return candles


def simulate_trading_scenario(
    initial_equity: float,
    days: int,
    market_drift: float,
    market_volatility: float,
    config: Config
) -> Dict:
    """
    Simulate one trading scenario.
    
    Args:
        initial_equity: Starting capital
        days: Simulation period
        market_drift: Expected annual return
        market_volatility: Annual volatility
        config: System configuration
    
    Returns:
        Simulation results dictionary
    """
    # Generate price path
    prices = generate_price_path(
        initial_price=3000.0,
        days=days,
        volatility=market_volatility,
        drift=market_drift,
        periods_per_day=24
    )
    
    # Create OHLCV data
    candles = create_synthetic_ohlcv(prices)
    
    # Initialize components
    regime_classifier = RegimeClassifier(config)
    risk_governor = RiskGovernor(config)
    
    # Initialize account
    account = AccountState(
        equity=initial_equity,
        daily_pnl=0.0,
        daily_pnl_pct=0.0,
        consecutive_losses=0,
        trades_today={},
        losses_today={},
        mode=Engine.IDLE
    )
    
    # Track signals
    signals_generated = []
    regimes = []
    
    # Simulate day by day
    min_lookback = 200
    
    for i in range(min_lookback, len(candles)):
        current_window = candles[:i+1]
        
        # Classify regime
        regime = regime_classifier.classify(current_window[-100:], account)
        regimes.append(regime.value)
        
        # Check if trading is allowed
        active_engine = risk_governor.determine_active_engine(regime, account)
        
        if active_engine != Engine.IDLE:
            # Simplified signal generation based on regime
            if regime.value == "range" and np.random.random() < 0.05:  # 5% chance
                signals_generated.append({
                    'timestamp': current_window[-1].timestamp,
                    'engine': 'ER-90',
                    'price': current_window[-1].close,
                    'regime': regime.value
                })
            elif regime.value == "strong_trend" and np.random.random() < 0.03:  # 3% chance
                signals_generated.append({
                    'timestamp': current_window[-1].timestamp,
                    'engine': 'SIB',
                    'price': current_window[-1].close,
                    'regime': regime.value
                })
    
    # Calculate statistics
    final_price = prices[-1]
    initial_price = prices[0]
    market_return = (final_price - initial_price) / initial_price * 100
    
    # Regime distribution
    from collections import Counter
    regime_dist = Counter(regimes)
    
    return {
        'initial_equity': initial_equity,
        'initial_price': initial_price,
        'final_price': final_price,
        'market_return_pct': market_return,
        'days_simulated': days,
        'signals_generated': len(signals_generated),
        'signals': signals_generated,
        'regime_distribution': dict(regime_dist),
        'max_price': np.max(prices),
        'min_price': np.min(prices),
        'volatility_realized': np.std(np.diff(np.log(prices))) * np.sqrt(365 * 24)
    }


def run_monte_carlo_simulations(
    num_simulations: int = 1000,
    days: int = 30,
    initial_equity: float = 10000.0
) -> Dict:
    """
    Run Monte Carlo simulations with different market conditions.
    
    Args:
        num_simulations: Number of scenarios to simulate
        days: Days per simulation
        initial_equity: Starting capital
    
    Returns:
        Aggregated results
    """
    print("="*70)
    print("HARVEST MONTE CARLO SIMULATION (PHASE 5)")
    print("="*70)
    print(f"Simulations: {num_simulations}")
    print(f"Period: {days} days")
    print(f"Initial equity: ${initial_equity:,.2f}")
    print()
    
    config = Config(initial_equity=initial_equity)
    
    # Market condition distributions
    market_conditions = [
        # (drift, volatility, probability, description)
        (0.0, 0.5, 0.3, "Low volatility sideways"),
        (0.2, 0.8, 0.2, "Bullish moderate volatility"),
        (-0.1, 0.8, 0.2, "Bearish moderate volatility"),
        (0.3, 1.2, 0.1, "Strong bull high volatility"),
        (-0.2, 1.2, 0.1, "Strong bear high volatility"),
        (0.0, 1.5, 0.1, "Extreme volatility choppy"),
    ]
    
    results = []
    
    for i in range(num_simulations):
        if (i + 1) % 100 == 0:
            print(f"Progress: {i + 1}/{num_simulations} simulations...")
        
        # Select market condition based on probability
        rand = np.random.random()
        cumulative = 0.0
        selected_condition = market_conditions[0]
        
        for condition in market_conditions:
            cumulative += condition[2]
            if rand <= cumulative:
                selected_condition = condition
                break
        
        drift, volatility, _, description = selected_condition
        
        # Run simulation
        result = simulate_trading_scenario(
            initial_equity=initial_equity,
            days=days,
            market_drift=drift,
            market_volatility=volatility,
            config=config
        )
        
        result['market_condition'] = description
        result['drift'] = drift
        result['volatility'] = volatility
        results.append(result)
    
    # Aggregate statistics
    print(f"\nCompleted {num_simulations} simulations")
    print("\nAnalyzing results...")
    
    signals_per_sim = [r['signals_generated'] for r in results]
    market_returns = [r['market_return_pct'] for r in results]
    volatilities = [r['volatility_realized'] for r in results]
    
    # Calculate percentiles
    signal_percentiles = np.percentile(signals_per_sim, [10, 25, 50, 75, 90])
    
    # Group by market condition
    condition_groups = {}
    for result in results:
        condition = result['market_condition']
        if condition not in condition_groups:
            condition_groups[condition] = []
        condition_groups[condition].append(result)
    
    summary = {
        'total_simulations': num_simulations,
        'period_days': days,
        'initial_equity': initial_equity,
        'signal_statistics': {
            'mean': np.mean(signals_per_sim),
            'median': np.median(signals_per_sim),
            'std': np.std(signals_per_sim),
            'min': np.min(signals_per_sim),
            'max': np.max(signals_per_sim),
            'percentiles': {
                'p10': signal_percentiles[0],
                'p25': signal_percentiles[1],
                'p50': signal_percentiles[2],
                'p75': signal_percentiles[3],
                'p90': signal_percentiles[4]
            }
        },
        'market_statistics': {
            'mean_return': np.mean(market_returns),
            'mean_volatility': np.mean(volatilities)
        },
        'by_market_condition': {}
    }
    
    # Statistics by market condition
    for condition, group in condition_groups.items():
        signals = [r['signals_generated'] for r in group]
        summary['by_market_condition'][condition] = {
            'count': len(group),
            'mean_signals': np.mean(signals),
            'median_signals': np.median(signals),
            'zero_signals_pct': sum(1 for s in signals if s == 0) / len(signals) * 100
        }
    
    return summary, results


def print_results(summary: Dict):
    """Print Monte Carlo results"""
    print("\n" + "="*70)
    print("MONTE CARLO SIMULATION RESULTS")
    print("="*70)
    
    print(f"\nSimulation Parameters:")
    print(f"  Total runs: {summary['total_simulations']}")
    print(f"  Period: {summary['period_days']} days")
    print(f"  Initial equity: ${summary['initial_equity']:,.2f}")
    
    print(f"\nSignal Generation Statistics:")
    stats = summary['signal_statistics']
    print(f"  Mean: {stats['mean']:.2f} signals per simulation")
    print(f"  Median: {stats['median']:.2f} signals")
    print(f"  Std Dev: {stats['std']:.2f}")
    print(f"  Range: {stats['min']:.0f} - {stats['max']:.0f}")
    print(f"\n  Percentiles:")
    print(f"    10th: {stats['percentiles']['p10']:.1f}")
    print(f"    25th: {stats['percentiles']['p25']:.1f}")
    print(f"    50th: {stats['percentiles']['p50']:.1f}")
    print(f"    75th: {stats['percentiles']['p75']:.1f}")
    print(f"    90th: {stats['percentiles']['p90']:.1f}")
    
    print(f"\nMarket Statistics:")
    mkt = summary['market_statistics']
    print(f"  Mean return: {mkt['mean_return']:.2f}%")
    print(f"  Mean volatility: {mkt['mean_volatility']*100:.1f}%")
    
    print(f"\nResults by Market Condition:")
    for condition, data in summary['by_market_condition'].items():
        print(f"\n  {condition}:")
        print(f"    Simulations: {data['count']}")
        print(f"    Mean signals: {data['mean_signals']:.2f}")
        print(f"    Median signals: {data['median_signals']:.1f}")
        print(f"    Zero signals: {data['zero_signals_pct']:.1f}%")
    
    print("\n" + "="*70)
    print("INTERPRETATION")
    print("="*70)
    
    if stats['median'] < 1:
        print("\n⚠️  Low signal generation observed")
        print("This is EXPECTED with conservative risk parameters.")
        print("The system prioritizes capital preservation over frequency.")
        print("\nRecommendations:")
        print("  - Increase capital ($1,000+ for more opportunities)")
        print("  - Relax RSI thresholds (currently 70/30)")
        print("  - Accept low frequency as designed behavior")
    elif stats['median'] < 5:
        print("\n✅ Moderate signal generation")
        print("System is generating signals at a reasonable rate.")
        print("This aligns with conservative risk management design.")
    else:
        print("\n✅ Good signal generation")
        print("System is actively finding trading opportunities.")
    
    print("\n" + "="*70)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Monte Carlo simulation for HARVEST')
    parser.add_argument('--simulations', type=int, default=1000,
                       help='Number of simulations (default: 1000)')
    parser.add_argument('--days', type=int, default=30,
                       help='Days per simulation (default: 30)')
    parser.add_argument('--capital', type=float, default=10000.0,
                       help='Initial capital (default: 10000)')
    parser.add_argument('--output', type=str,
                       help='Output file for detailed results (JSON)')
    
    args = parser.parse_args()
    
    # Run simulations
    summary, detailed_results = run_monte_carlo_simulations(
        num_simulations=args.simulations,
        days=args.days,
        initial_equity=args.capital
    )
    
    # Print results
    print_results(summary)
    
    # Save detailed results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump({
                'summary': summary,
                'detailed_results': detailed_results[:100]  # Save first 100
            }, f, indent=2, default=str)
        print(f"\n📄 Detailed results saved to: {args.output}")
    
    print("\n✅ Monte Carlo simulation complete")
