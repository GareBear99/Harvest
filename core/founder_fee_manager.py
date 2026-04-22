#!/usr/bin/env python3
"""
Founder Fee Manager
Handles 10% founder fee collection on profits after reaching $100

Logic:
- Only activates when account reaches $100 AND full system is active
- Collects $10 fee for every $100 in total profit
- Only collects when account has $10+ profit above last baseline
- Does not collect if account dropped below baseline
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger("harvest.founder_fee")


class FounderFeeManager:
    """
    Manages founder fee collection (10% on profits after $100)
    
    Rules:
    1. Must reach $100+ balance first
    2. Must have full system active (both assets, all 5 timeframes)
    3. Collects $10 for every $100 profit made
    4. First $10 profit at $100 → founder fee → unlocks 2nd position set
    5. Next $100 profit ($200 total) → founder fee → unlocks 3rd position set
    6. At $300+ → fully maxed (3 positions per timeframe), positions grow in size
    7. Does not collect if account dropped below previous baseline
    
    Position Scaling (2 assets: ETH + BTC):
    - $100: Baseline set, 1 pos/TF/asset (10 total: 5 TFs × 2 assets × 1)
    - $110: Fee #1 → 2 pos/TF/asset (20 total: 5 TFs × 2 assets × 2)
    - $210: Fee #2 → 3 pos/TF/asset (30 total: 5 TFs × 2 assets × 3 - MAXED)
    - $310: Fee #3 → Still maxed, positions grow in size
    - $410: Fee #4 → Every $100 from baseline ($100), collect $10
    
    Baseline never resets - always $100. Fees at: $110, $210, $310, $410, $510...
    """
    
    ACTIVATION_THRESHOLD = 100.0  # $100 to activate founder fees
    FEE_AMOUNT = 10.0             # $10 per collection
    FEE_INTERVAL = 100.0          # Collect every $100 profit from baseline
    FIRST_FEE_AT = 110.0          # First fee at $110 (first $10 profit)
    SECOND_FEE_AT = 210.0         # Second fee at $210 (unlocks 3rd position set)
    # After that: $310, $410, $510... (every $100 from baseline)
    
    NUM_ASSETS = 2                # ETH + BTC
    NUM_TIMEFRAMES = 5            # 1m, 5m, 15m, 1h, 4h
    
    # Position limits per fee tier (positions per timeframe per asset)
    POSITIONS_PER_TF_PER_ASSET = {
        0: 1,  # Before any fees: 1 position per TF per asset (10 total)
        1: 2,  # After 1st fee: 2 positions per TF per asset (20 total)
        2: 3,  # After 2nd fee: 3 positions per TF per asset (30 total - maxed)
    }
    
    # Founder wallet address
    FOUNDER_ADDRESS = "0xdFb64E012525214d87238c60ce92C8b3721E1420"
    
    def __init__(self, data_dir: str = "data", client_id: Optional[str] = None, metamask_address: Optional[str] = None, mode: str = 'LIVE'):
        """
        Initialize founder fee manager.
        
        Args:
            data_dir: Directory to store fee tracking data
            client_id: User's unique client ID
            metamask_address: Connected MetaMask wallet address
            mode: Trading mode - 'LIVE', 'PAPER', or 'BACKTEST'
        """
        self.mode = mode
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.config_path = self.data_dir / "founder_fee_config.json"
        
        # In backtest mode, always start fresh and simulate activation
        if mode == 'BACKTEST':
            self.config = self._create_backtest_config()
        else:
            self.config = self._load_config()
        
        # Update wallet info if provided
        if client_id:
            self.config['client_id'] = client_id
        if metamask_address:
            self.config['metamask_address'] = metamask_address
            self._save_config()
        
        logger.info(f"FounderFeeManager initialized (Client: {self.config.get('client_id', 'unknown')[:8]}...)")
    
    def _load_config(self) -> Dict:
        """Load founder fee configuration from disk."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            logger.info("Loaded existing founder fee config")
            return config
        else:
            return {
                'activated': False,
                'activation_date': None,
                'baseline_balance': 0.0,
                'total_fees_collected': 0.0,
                'fee_count': 0,
                'last_collection': None,
                'collection_history': [],
                'position_tier': 0,  # 0 = 1 pos/tf, 1 = 2 pos/tf, 2 = 3 pos/tf (maxed)
                'pending_fee': None,  # Fee awaiting blockchain confirmation
                'metamask_address': None,  # Connected wallet address
                'client_id': None,  # User's unique client ID
            }
    
    def _create_backtest_config(self) -> Dict:
        """Create backtest-specific config that simulates position tier progression."""
        return {
            'activated': True,  # Always activated in backtest
            'activation_date': datetime.now().isoformat(),
            'baseline_balance': 100.0,  # Backtest baseline
            'total_fees_collected': 0.0,
            'fee_count': 0,
            'last_collection': None,
            'collection_history': [],
            'position_tier': 0,  # Start at tier 0 (1 pos per TF per asset)
            'pending_fee': None,
            'metamask_address': None,
            'client_id': 'backtest',
        }
    
    def _save_config(self):
        """Save founder fee configuration to disk."""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
        logger.debug("Saved founder fee config")
    
    def check_full_system_active(
        self, 
        active_timeframes: list, 
        active_assets: list
    ) -> bool:
        """
        Check if full trading system is active.
        
        Args:
            active_timeframes: List of active timeframes (e.g., ['1m', '5m', '15m', '1h', '4h'])
            active_assets: List of active assets (e.g., ['ETH', 'BTC'])
            
        Returns:
            True if full system (2 assets, 5 timeframes) is active
        """
        required_timeframes = ['1m', '5m', '15m', '1h', '4h']
        required_assets = ['ETH', 'BTC']
        
        has_all_timeframes = all(tf in active_timeframes for tf in required_timeframes)
        has_all_assets = all(asset in active_assets for asset in required_assets)
        
        return has_all_timeframes and has_all_assets
    
    def activate(self, current_balance: float) -> bool:
        """
        Activate founder fee system when balance reaches $100.
        
        Args:
            current_balance: Current account balance
            
        Returns:
            True if activated successfully
        """
        if self.config['activated']:
            logger.debug("Founder fee already activated")
            return False
        
        if current_balance < self.ACTIVATION_THRESHOLD:
            logger.debug(f"Balance ${current_balance:.2f} below activation threshold ${self.ACTIVATION_THRESHOLD:.2f}")
            return False
        
        # Activate!
        self.config['activated'] = True
        self.config['activation_date'] = datetime.now().isoformat()
        self.config['baseline_balance'] = current_balance
        self._save_config()
        
        logger.info("=" * 70)
        logger.info("🎉 FOUNDER FEE SYSTEM ACTIVATED")
        logger.info("=" * 70)
        logger.info(f"Activation Balance: ${current_balance:.2f}")
        logger.info(f"Baseline: ${current_balance:.2f} (never resets)")
        logger.info(f"Position Tier: 1 pos/TF/asset (10 total: 5 TFs × 2 assets × 1)")
        logger.info(f"")
        logger.info(f"💰 Founder Fee System:")
        logger.info(f"  • Next $10 profit will be collected for founder fee")
        logger.info(f"  • At $110: Send $10 to founder address")
        logger.info(f"  • At $210: Send $10 to founder address")
        logger.info(f"  • Pattern continues: $310, $410, $510...")
        logger.info(f"")
        logger.info(f"🔓 Position Unlocks:")
        logger.info(f"  • $110: Unlocks 2nd position set (20 total)")
        logger.info(f"  • $210: Unlocks 3rd position set (30 total - MAXED)")
        logger.info(f"")
        logger.info(f"Founder Address: {self.FOUNDER_ADDRESS}")
        logger.info("=" * 70)
        
        return True
    
    def check_and_collect(
        self,
        current_balance: float,
        active_timeframes: list,
        active_assets: list,
        mode: str = 'LIVE'
    ) -> Optional[Dict]:
        """
        Check if founder fee should be collected and return collection info.
        
        Args:
            current_balance: Current account balance
            active_timeframes: List of active timeframes
            active_assets: List of active assets
            mode: Trading mode - 'LIVE', 'PAPER', or 'BACKTEST' (only LIVE charges fees)
            
        Returns:
            Dict with collection info if fee should be collected, None otherwise
        """
        # In backtest mode, don't collect fees but do simulate tier progression
        if mode == 'BACKTEST':
            # Update tier based on balance milestones (but don't collect fees)
            self._update_backtest_tier(current_balance)
            return None
        # Check if system is activated
        if not self.config['activated']:
            # Try to activate if balance is high enough
            if current_balance >= self.ACTIVATION_THRESHOLD:
                # Check if full system is active
                if self.check_full_system_active(active_timeframes, active_assets):
                    self.activate(current_balance)
                else:
                    logger.debug("Full system not active yet, waiting to activate founder fees")
            return None
        
        # Check if full system is still active
        if not self.check_full_system_active(active_timeframes, active_assets):
            logger.warning("Full system not active - founder fees paused")
            return None
        
        baseline = self.config['baseline_balance']
        fee_tier = self.config.get('position_tier', 0)
        
        # Calculate next fee threshold
        # Fees collected at: baseline + ($10 + n*$100) where n = fee_count
        # Example: baseline=$100, fees at $110, $210, $310, $410...
        next_fee_threshold = baseline + 10.0 + (self.config['fee_count'] * self.FEE_INTERVAL)
        
        # Check if we've reached the next fee threshold
        if current_balance < next_fee_threshold:
            remaining = next_fee_threshold - current_balance
            logger.debug(f"Balance ${current_balance:.2f} below next fee threshold ${next_fee_threshold:.2f} (${remaining:.2f} away)")
            return None
        
        # Check if there's already a pending fee awaiting confirmation
        if self.config.get('pending_fee'):
            pending = self.config['pending_fee']
            logger.warning("=" * 70)
            logger.warning("⚠️  PENDING FEE - POSITION UNLOCK BLOCKED")
            logger.warning("=" * 70)
            logger.warning(f"Fee Amount: ${pending['amount']:.2f}")
            logger.warning(f"Must Send To: {self.FOUNDER_ADDRESS}")
            logger.warning(f"From Wallet: {self.config.get('metamask_address', 'Not connected')}")
            logger.warning(f"Next Position Tier: {pending['new_position_tier']} ({pending['new_positions']} total)")
            logger.warning(f"")
            logger.warning(f"🔒 Position unlock is BLOCKED until fee is confirmed on blockchain")
            logger.warning(f"Call confirm_fee_sent(tx_hash) after sending transaction")
            logger.warning("=" * 70)
            return None
        
        # Check if balance hasn't dropped below baseline
        if current_balance < baseline:
            logger.warning(f"Balance ${current_balance:.2f} below baseline ${baseline:.2f} - no fee collection")
            return None
        
        # Calculate profit for this fee
        profit = current_balance - baseline
        
        # Determine position unlock
        old_tier = fee_tier
        new_tier = min(fee_tier + 1, 2)  # Max tier is 2 (3 positions per timeframe per asset)
        old_positions = self.POSITIONS_PER_TF_PER_ASSET[old_tier] * self.NUM_TIMEFRAMES * self.NUM_ASSETS
        new_positions = self.POSITIONS_PER_TF_PER_ASSET[new_tier] * self.NUM_TIMEFRAMES * self.NUM_ASSETS if new_tier <= 2 else old_positions
        
        # Create pending fee (requires blockchain confirmation before unlocking positions)
        pending_fee_info = {
            'amount': self.FEE_AMOUNT,
            'from_balance': current_balance,
            'baseline': baseline,
            'profit': profit,
            'timestamp': datetime.now().isoformat(),
            'founder_address': self.FOUNDER_ADDRESS,
            'metamask_address': self.config.get('metamask_address'),
            'client_id': self.config.get('client_id'),
            'old_position_tier': old_tier,
            'new_position_tier': new_tier,
            'old_positions': old_positions,
            'new_positions': new_positions,
            'positions_unlocked': new_positions - old_positions if new_tier > old_tier else 0,
            'confirmed': False,
            'tx_hash': None
        }
        
        # Set as pending (does NOT update tier or count yet)
        self.config['pending_fee'] = pending_fee_info
        self._save_config()
        
        # Return pending fee info (not a confirmed collection)
        pending_fee_info['pending'] = True
        return pending_fee_info
        
        logger.info("=" * 70)
        logger.info("⚠️  FOUNDER FEE DUE - AWAITING PAYMENT")
        logger.info("=" * 70)
        logger.info(f"Fee Amount: ${self.FEE_AMOUNT:.2f}")
        logger.info(f"Current Balance: ${current_balance:.2f}")
        logger.info(f"Profit: ${profit:.2f}")
        logger.info(f"")
        logger.info(f"💸 Payment Required:")
        logger.info(f"  Send: ${self.FEE_AMOUNT:.2f}")
        logger.info(f"  To: {self.FOUNDER_ADDRESS}")
        logger.info(f"  From: {self.config.get('metamask_address', 'MetaMask not connected')}")
        logger.info(f"")
        logger.info(f"🔒 Position Unlock Pending:")
        if pending_fee_info['positions_unlocked'] > 0:
            logger.info(f"  Old: {old_positions} positions ({old_tier + 1} per TF per asset)")
            logger.info(f"  New: {new_positions} positions ({new_tier + 1} per TF per asset) - LOCKED")
            logger.info(f"  Waiting: {pending_fee_info['positions_unlocked']} new position slots")
            
            if new_tier == 2:
                logger.info(f"  🏆 Will unlock MAXED system: 3 pos/TF/asset (30 total)")
        
        logger.info(f"")
        logger.info(f"⏳ After sending transaction:")
        logger.info(f"  1. Copy transaction hash from MetaMask")
        logger.info(f"  2. Call: manager.confirm_fee_sent(tx_hash)")
        logger.info(f"  3. System will verify on blockchain")
        logger.info(f"  4. Positions will unlock automatically")
        logger.info("=" * 70)
        
        return collection_info
    
    def _update_backtest_tier(self, current_balance: float):
        """Update position tier for backtest mode based on balance milestones.
        
        IMPORTANT: Tiers can go UP or DOWN based on balance changes.
        - Upgrade when balance crosses thresholds going up
        - Downgrade when balance drops below thresholds
        """
        old_tier = self.config.get('position_tier', 0)
        
        # Update tier based on CURRENT balance (can downgrade from losses)
        if current_balance >= 210.0:
            self.config['position_tier'] = 2  # Maxed at 3 per TF per asset
        elif current_balance >= 110.0:
            self.config['position_tier'] = 1  # 2 per TF per asset
        elif current_balance >= 100.0:
            self.config['position_tier'] = 0  # 1 per TF per asset (baseline)
        else:
            # Below $100 - severely limited (still allow 1 position per TF per asset)
            # This allows recovery trading but with restricted capacity
            self.config['position_tier'] = 0  # Stay at baseline tier
        
        # Don't save config in backtest mode (no persistence needed)
    
    def get_status(self, current_balance: float, mode: str = 'LIVE') -> Dict:
        """
        Get comprehensive founder fee status.
        
        Args:
            current_balance: Current account balance
            mode: Trading mode - only shows status for LIVE/PAPER modes
            
        Returns:
            Dict with status information
        """
        # Don't show fee status in backtest mode
        if mode == 'BACKTEST':
            return {
                'activated': False,
                'mode': 'BACKTEST',
                'message': 'Founder fees only apply to live trading'
            }
        if not self.config['activated']:
            return {
                'activated': False,
                'activation_threshold': self.ACTIVATION_THRESHOLD,
                'current_balance': current_balance,
                'distance_to_activation': max(0, self.ACTIVATION_THRESHOLD - current_balance)
            }
        
        baseline = self.config['baseline_balance']
        profit_above_baseline = current_balance - baseline
        
        # Calculate next fee threshold: baseline + $10 + (fee_count * $100)
        # Examples: $100 baseline → fees at $110, $210, $310, $410...
        next_fee_at = baseline + 10.0 + (self.config['fee_count'] * self.FEE_INTERVAL)
        
        progress_to_next = current_balance - baseline
        target_profit = next_fee_at - baseline
        progress_pct = (progress_to_next / target_profit * 100) if target_profit > 0 else 0
        
        return {
            'activated': True,
            'activation_date': self.config['activation_date'],
            'baseline_balance': baseline,
            'current_balance': current_balance,
            'profit_above_baseline': profit_above_baseline,
            'next_fee_amount': self.FEE_AMOUNT,
            'next_fee_at': next_fee_at,
            'distance_to_next_fee': max(0, next_fee_at - current_balance),
            'progress_to_next_fee_pct': min(100, progress_pct),
            'total_fees_collected': self.config['total_fees_collected'],
            'fee_count': self.config['fee_count'],
            'last_collection': self.config['last_collection'],
            'founder_address': self.FOUNDER_ADDRESS
        }
    
    def get_collection_history(self) -> list:
        """
        Get history of all fee collections.
        
        Returns:
            List of collection records
        """
        return self.config['collection_history']
    
    def get_position_limit(self) -> int:
        """
        Get current maximum positions per timeframe per asset based on fee tier.
        
        Returns:
            Number of positions allowed per timeframe per asset (1, 2, or 3)
        """
        if not self.config['activated']:
            return 1  # Default: 1 position per timeframe per asset until activated
        
        tier = self.config.get('position_tier', 0)
        return self.POSITIONS_PER_TF_PER_ASSET.get(tier, 1)
    
    def get_total_position_limit(self) -> int:
        """
        Get total maximum positions across all timeframes and assets.
        
        Returns:
            Total number of position slots (10, 20, or 30)
        """
        return self.get_position_limit() * self.NUM_TIMEFRAMES * self.NUM_ASSETS
    
    def reset(self):
        """Reset founder fee system (for testing only)."""
        self.config = {
            'activated': False,
            'activation_date': None,
            'baseline_balance': 0.0,
            'total_fees_collected': 0.0,
            'fee_count': 0,
            'last_collection': None,
            'collection_history': []
        }
        self._save_config()
        logger.info("⚠️ Founder fee system reset")


def get_founder_fee_manager() -> FounderFeeManager:
    """Get singleton instance of founder fee manager."""
    global _founder_fee_manager_instance
    if '_founder_fee_manager_instance' not in globals():
        _founder_fee_manager_instance = FounderFeeManager()
    return _founder_fee_manager_instance


if __name__ == '__main__':
    # Demo usage
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s'
    )
    
    print("=" * 70)
    print("FOUNDER FEE MANAGER - DEMO")
    print("=" * 70)
    
    manager = FounderFeeManager()
    
    # Simulate balance growth
    test_scenarios = [
        # (balance, timeframes, assets, description)
        (50.0, ['1m', '5m', '15m'], ['ETH'], "Growing to $50 - not activated yet"),
        (100.0, ['1m', '5m', '15m', '1h', '4h'], ['ETH', 'BTC'], "$100 - ACTIVATE (baseline=$100, 10 positions)"),
        (105.0, ['1m', '5m', '15m', '1h', '4h'], ['ETH', 'BTC'], "$105 - waiting for $110"),
        (110.0, ['1m', '5m', '15m', '1h', '4h'], ['ETH', 'BTC'], "$110 - FEE #1 → 20 positions (next: $210)"),
        (150.0, ['1m', '5m', '15m', '1h', '4h'], ['ETH', 'BTC'], "$150 - waiting for $210"),
        (210.0, ['1m', '5m', '15m', '1h', '4h'], ['ETH', 'BTC'], "$210 - FEE #2 → 30 positions MAXED (next: $310)"),
        (250.0, ['1m', '5m', '15m', '1h', '4h'], ['ETH', 'BTC'], "$250 - waiting for $310"),
        (180.0, ['1m', '5m', '15m', '1h', '4h'], ['ETH', 'BTC'], "Drop to $180 - below $210, no fee"),
        (310.0, ['1m', '5m', '15m', '1h', '4h'], ['ETH', 'BTC'], "$310 - FEE #3 (maxed, next: $410)"),
        (410.0, ['1m', '5m', '15m', '1h', '4h'], ['ETH', 'BTC'], "$410 - FEE #4 (next: $510)"),
    ]
    
    for balance, timeframes, assets, description in test_scenarios:
        print(f"\n📊 Scenario: {description}")
        print(f"   Balance: ${balance:.2f}")
        print(f"   Timeframes: {', '.join(timeframes)}")
        print(f"   Assets: {', '.join(assets)}")
        
        # Check for collection
        collection = manager.check_and_collect(balance, timeframes, assets)
        
        # Show status
        status = manager.get_status(balance)
        positions_per_tf = manager.get_position_limit()
        total_positions = manager.get_total_position_limit()
        
        if status['activated']:
            print(f"   Status: Activated (baseline: ${status['baseline_balance']:.2f})")
            print(f"   Positions: {positions_per_tf} per timeframe ({total_positions} total)")
            print(f"   Profit Above Baseline: ${status['profit_above_baseline']:.2f}")
            print(f"   Next Fee At: ${status['next_fee_at']:.2f} (${status['distance_to_next_fee']:.2f} away)")
            print(f"   Total Collected: ${status['total_fees_collected']:.2f} ({status['fee_count']} fees)")
        else:
            print(f"   Status: Not activated (need ${status['distance_to_activation']:.2f} more)")
            print(f"   Positions: {positions_per_tf} per timeframe ({total_positions} total)")
    
    print("\n" + "=" * 70)
    print("COLLECTION HISTORY")
    print("=" * 70)
    history = manager.get_collection_history()
    for i, record in enumerate(history, 1):
        print(f"\n{i}. Fee Collection")
        print(f"   Amount: ${record['amount']:.2f}")
        print(f"   From Balance: ${record['from_balance']:.2f}")
        print(f"   Profit: ${record['profit']:.2f}")
        print(f"   Time: {record['timestamp']}")
    
    if not history:
        print("\nNo fees collected yet")
