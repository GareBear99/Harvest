#!/usr/bin/env python3
"""
Balance-Aware Strategy Activation System
Dynamically enables timeframes and assets based on account balance
"""

from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from enum import Enum


class Asset(Enum):
    """Supported trading assets"""
    ETH = "ETHUSDT"
    BTC = "BTCUSDT"


@dataclass
class ActivationTier:
    """Configuration for a balance tier"""
    min_balance: float
    max_balance: float
    active_timeframes: List[str]
    active_assets: List[Asset]
    max_position_per_asset: float
    description: str
    btc_wallet_required: bool = False


class BalanceAwareStrategy:
    """
    Manages timeframe and asset activation based on account balance.
    
    Activation Strategy:
    - $10-20: 1m ETH only ($10 max position)
    - $20-30: 1m ETH+BTC ($10 each) + BTC wallet funded
    - $30-40: 1m+5m ETH+BTC
    - $40-50: 1m+5m+15m ETH+BTC
    - $50-75: 1m+5m+15m+1h ETH+BTC
    - $75-100: All timeframes ETH+BTC
    - $100+: Full system with dynamic position sizing
    """
    
    def __init__(self):
        self.tiers = self._initialize_tiers()
    
    def _initialize_tiers(self) -> List[ActivationTier]:
        """Define balance tiers and their activations"""
        return [
            # Tier 1: Bare minimum - 1m ETH only
            ActivationTier(
                min_balance=10.0,
                max_balance=20.0,
                active_timeframes=['1m'],
                active_assets=[Asset.ETH],
                max_position_per_asset=10.0,
                description="Ultra-Fast ETH Scalping Only",
                btc_wallet_required=False
            ),
            
            # Tier 2: Add BTC + Fund BTC wallet
            ActivationTier(
                min_balance=20.0,
                max_balance=30.0,
                active_timeframes=['1m'],
                active_assets=[Asset.ETH, Asset.BTC],
                max_position_per_asset=10.0,
                description="1m Both Assets + BTC Wallet Funded",
                btc_wallet_required=True
            ),
            
            # Tier 3: Add 5m timeframe
            ActivationTier(
                min_balance=30.0,
                max_balance=40.0,
                active_timeframes=['1m', '5m'],
                active_assets=[Asset.ETH, Asset.BTC],
                max_position_per_asset=15.0,
                description="1m + 5m Both Assets",
                btc_wallet_required=True
            ),
            
            # Tier 4: Add 15m timeframe
            ActivationTier(
                min_balance=40.0,
                max_balance=50.0,
                active_timeframes=['1m', '5m', '15m'],
                active_assets=[Asset.ETH, Asset.BTC],
                max_position_per_asset=16.0,
                description="1m + 5m + 15m Both Assets",
                btc_wallet_required=True
            ),
            
            # Tier 5: Add 1h timeframe
            ActivationTier(
                min_balance=50.0,
                max_balance=75.0,
                active_timeframes=['1m', '5m', '15m', '1h'],
                active_assets=[Asset.ETH, Asset.BTC],
                max_position_per_asset=18.0,
                description="1m + 5m + 15m + 1h Both Assets",
                btc_wallet_required=True
            ),
            
            # Tier 6: Add 4h timeframe
            ActivationTier(
                min_balance=75.0,
                max_balance=100.0,
                active_timeframes=['1m', '5m', '15m', '1h', '4h'],
                active_assets=[Asset.ETH, Asset.BTC],
                max_position_per_asset=20.0,
                description="All Timeframes Both Assets",
                btc_wallet_required=True
            ),
            
            # Tier 7: Full system with dynamic sizing
            ActivationTier(
                min_balance=100.0,
                max_balance=float('inf'),
                active_timeframes=['1m', '5m', '15m', '1h', '4h'],
                active_assets=[Asset.ETH, Asset.BTC],
                max_position_per_asset=100.0,  # Will use position_size_limiter
                description="Full System - Dynamic Position Sizing",
                btc_wallet_required=True
            )
        ]
    
    def get_tier(self, balance: float) -> Optional[ActivationTier]:
        """
        Get the activation tier for a given balance.
        
        Args:
            balance: Current account balance in USD
            
        Returns:
            ActivationTier configuration, or None if balance too low
        """
        # Below minimum balance - no trading possible
        if balance < 10.0:
            return None
        
        for tier in self.tiers:
            if tier.min_balance <= balance < tier.max_balance:
                return tier
        
        # Default to highest tier if balance exceeds all tiers
        return self.tiers[-1]
    
    def get_active_timeframes(self, balance: float) -> List[str]:
        """Get list of active timeframes for balance"""
        tier = self.get_tier(balance)
        return tier.active_timeframes if tier else []
    
    def get_active_assets(self, balance: float) -> List[Asset]:
        """Get list of active assets for balance"""
        tier = self.get_tier(balance)
        return tier.active_assets if tier else []
    
    def is_timeframe_active(self, balance: float, timeframe: str) -> bool:
        """Check if a specific timeframe is active"""
        return timeframe in self.get_active_timeframes(balance)
    
    def is_asset_active(self, balance: float, asset: Asset) -> bool:
        """Check if a specific asset is active"""
        return asset in self.get_active_assets(balance)
    
    def get_max_position_size(self, balance: float, asset: Asset) -> float:
        """
        Get max position size for an asset at current balance.
        
        Args:
            balance: Current account balance
            asset: Trading asset
            
        Returns:
            Maximum position size in USD
        """
        tier = self.get_tier(balance)
        
        if asset not in tier.active_assets:
            return 0.0
        
        return tier.max_position_per_asset
    
    def requires_btc_wallet(self, balance: float) -> bool:
        """Check if BTC wallet is required at this balance"""
        tier = self.get_tier(balance)
        return tier.btc_wallet_required
    
    def validate_trading_requirements(self, balance: float, 
                                     has_btc_wallet: bool,
                                     connected_metamask: bool = False) -> Dict:
        """
        Validate all requirements are met for trading at this balance.
        
        Args:
            balance: Current account balance
            has_btc_wallet: Whether BTC wallet exists
            connected_metamask: Whether MetaMask is connected (optional)
            
        Returns:
            {
                'can_trade': bool,
                'tier': ActivationTier,
                'issues': List[str],
                'recommendations': List[str]
            }
        """
        tier = self.get_tier(balance)
        issues = []
        recommendations = []
        
        # Check minimum balance
        if balance < 10.0:
            issues.append(f"Insufficient balance: ${balance:.2f} (minimum: $10.00)")
            recommendations.append("Deposit at least $10 to start trading")
        
        # Check BTC wallet requirement
        if tier.btc_wallet_required and not has_btc_wallet:
            issues.append("BTC wallet required for this tier but not found")
            recommendations.append("BTC wallet will be auto-created on dashboard startup")
        
        # Check for tier-appropriate warnings
        if balance >= 20.0 and not has_btc_wallet:
            recommendations.append("Consider running dashboard to auto-create BTC wallet")
        
        if balance >= 100.0:
            recommendations.append("Full system active - all timeframes and assets enabled")
        
        can_trade = len(issues) == 0
        
        return {
            'can_trade': can_trade,
            'tier': tier,
            'issues': issues,
            'recommendations': recommendations,
            'active_timeframes': tier.active_timeframes,
            'active_assets': [a.value for a in tier.active_assets],
            'max_position_per_asset': tier.max_position_per_asset
        }
    
    def get_tier_summary(self, balance: float) -> str:
        """Get human-readable summary of current tier"""
        tier = self.get_tier(balance)
        
        timeframes_str = ', '.join(tier.active_timeframes)
        assets_str = ' + '.join([a.name for a in tier.active_assets])
        
        lines = [
            f"Balance: ${balance:.2f}",
            f"Tier: {tier.description}",
            f"Active Timeframes: {timeframes_str}",
            f"Active Assets: {assets_str}",
            f"Max Position/Asset: ${tier.max_position_per_asset:.0f}",
            f"BTC Wallet Required: {'Yes' if tier.btc_wallet_required else 'No'}"
        ]
        
        return '\n'.join(lines)
    
    def get_all_tiers_info(self) -> str:
        """Get formatted info about all tiers"""
        lines = ["BALANCE-AWARE ACTIVATION TIERS", "=" * 50]
        
        for i, tier in enumerate(self.tiers, 1):
            lines.append(f"\nTier {i}: ${tier.min_balance:.0f}-${tier.max_balance:.0f}")
            lines.append(f"  {tier.description}")
            lines.append(f"  Timeframes: {', '.join(tier.active_timeframes)}")
            lines.append(f"  Assets: {' + '.join([a.name for a in tier.active_assets])}")
            lines.append(f"  Max Position: ${tier.max_position_per_asset:.0f}/asset")
            lines.append(f"  BTC Wallet: {'Required' if tier.btc_wallet_required else 'Not Required'}")
        
        return '\n'.join(lines)


# Singleton instance
_strategy_instance = None


def get_balance_aware_strategy() -> BalanceAwareStrategy:
    """Get or create balance-aware strategy singleton"""
    global _strategy_instance
    if _strategy_instance is None:
        _strategy_instance = BalanceAwareStrategy()
    return _strategy_instance


# Testing
if __name__ == '__main__':
    strategy = BalanceAwareStrategy()
    
    print(strategy.get_all_tiers_info())
    print("\n" + "=" * 50)
    print("TESTING SPECIFIC BALANCES")
    print("=" * 50)
    
    test_balances = [10, 15, 25, 35, 45, 60, 85, 150]
    
    for balance in test_balances:
        print(f"\n--- Testing Balance: ${balance} ---")
        print(strategy.get_tier_summary(balance))
        
        # Test validation
        validation = strategy.validate_trading_requirements(
            balance=balance,
            has_btc_wallet=balance >= 20,  # Simulate wallet created at $20
            connected_metamask=balance >= 20
        )
        
        print(f"\nCan Trade: {'✅ Yes' if validation['can_trade'] else '❌ No'}")
        if validation['issues']:
            print("Issues:")
            for issue in validation['issues']:
                print(f"  - {issue}")
        if validation['recommendations']:
            print("Recommendations:")
            for rec in validation['recommendations']:
                print(f"  - {rec}")
