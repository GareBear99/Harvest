"""
Seed Configuration Snapshot System

Stores EXACT configuration for every seed tested, including:
- All parameters (even unused ones)
- Parameter version
- Hash of configuration
- Backtest stats

Purpose: Verify that same seed always produces same configuration,
even after system changes (new parameters, etc.)
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Dict, Optional


class SeedSnapshot:
    """
    Stores exact configuration snapshot for each seed
    
    Ensures reproducibility by comparing:
    - Parameter values
    - Configuration hash
    - Expected vs actual outputs
    """
    
    def __init__(self, snapshot_file: str = "ml/seed_snapshots.json"):
        self.snapshot_file = snapshot_file
        self.snapshots = {}
        self.load()
    
    def load(self):
        """Load snapshots from file"""
        if os.path.exists(self.snapshot_file):
            with open(self.snapshot_file, 'r') as f:
                data = json.load(f)
                self.snapshots = data.get('snapshots', {})
            print(f"📸 Loaded {len(self.snapshots)} seed snapshots")
        else:
            print(f"📸 Creating new seed snapshot database")
            self.snapshots = {}
    
    def save(self):
        """Save snapshots to file"""
        data = {
            'snapshots': self.snapshots,
            'last_updated': datetime.now().isoformat(),
            'total_snapshots': len(self.snapshots)
        }
        
        os.makedirs(os.path.dirname(self.snapshot_file), exist_ok=True)
        with open(self.snapshot_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _hash_config(self, config: Dict) -> str:
        """Generate hash of configuration for comparison"""
        # Sort keys for deterministic hashing
        sorted_config = dict(sorted(config.items()))
        config_str = json.dumps(sorted_config, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]
    
    def create_snapshot(
        self,
        seed: int,
        timeframe: str,
        parameters: Dict,
        version: str,
        input_seed: Optional[int] = None,
        backtest_stats: Optional[Dict] = None
    ) -> Dict:
        """
        Create configuration snapshot for a seed
        
        Args:
            seed: Strategy seed
            timeframe: '15m', '1h', '4h'
            parameters: ALL parameters (complete config)
            version: Parameter version (v1, v2, etc.)
            input_seed: Optional input seed used
            backtest_stats: Optional backtest results
            
        Returns:
            Snapshot dict
        """
        seed_key = str(seed)
        
        config_hash = self._hash_config(parameters)
        
        snapshot = {
            'seed': seed,
            'timeframe': timeframe,
            'version': version,
            'input_seed': input_seed,
            'parameters': parameters.copy(),
            'config_hash': config_hash,
            'created_at': datetime.now().isoformat(),
            'backtest_stats': backtest_stats or {},
            'verification_history': []
        }
        
        # Check if seed already exists
        if seed_key in self.snapshots:
            # Compare with existing
            existing = self.snapshots[seed_key]
            if existing['config_hash'] != config_hash:
                print(f"⚠️  WARNING: Seed {seed} config changed!")
                print(f"   Old hash: {existing['config_hash']}")
                print(f"   New hash: {config_hash}")
                print(f"   This should NEVER happen for same seed!")
                
                # Log the discrepancy
                snapshot['config_changed'] = True
                snapshot['previous_hash'] = existing['config_hash']
        
        self.snapshots[seed_key] = snapshot
        self.save()
        
        return snapshot
    
    def verify_seed(
        self,
        seed: int,
        parameters: Dict,
        backtest_stats: Optional[Dict] = None
    ) -> Dict:
        """
        Verify that seed produces expected configuration
        
        Args:
            seed: Strategy seed to verify
            parameters: Current parameters generated
            backtest_stats: Optional current backtest stats
            
        Returns:
            Verification result dict
        """
        seed_key = str(seed)
        
        if seed_key not in self.snapshots:
            return {
                'verified': False,
                'reason': 'no_snapshot',
                'message': f'No snapshot exists for seed {seed}'
            }
        
        snapshot = self.snapshots[seed_key]
        current_hash = self._hash_config(parameters)
        expected_hash = snapshot['config_hash']
        
        result = {
            'seed': seed,
            'verified': current_hash == expected_hash,
            'expected_hash': expected_hash,
            'actual_hash': current_hash,
            'timestamp': datetime.now().isoformat()
        }
        
        if result['verified']:
            result['message'] = f'✅ Seed {seed} produces exact same configuration'
            
            # Compare stats if provided
            if backtest_stats and snapshot['backtest_stats']:
                stats_match = self._compare_stats(
                    snapshot['backtest_stats'],
                    backtest_stats
                )
                result['stats_match'] = stats_match
                
                if not stats_match:
                    result['message'] = f'✅ Config matches, ⚠️  stats differ (expected with different data)'
        else:
            result['message'] = f'❌ Seed {seed} configuration CHANGED!'
            result['expected_params'] = snapshot['parameters']
            result['actual_params'] = parameters
            result['differences'] = self._find_differences(
                snapshot['parameters'],
                parameters
            )
        
        # Log verification
        snapshot['verification_history'].append(result)
        self.save()
        
        return result
    
    def _compare_stats(self, expected: Dict, actual: Dict) -> bool:
        """Compare backtest stats (allowing some tolerance)"""
        # For deterministic backtests with same data, stats should match exactly
        key_stats = ['win_rate', 'trades', 'wins', 'losses']
        
        for key in key_stats:
            if key not in expected or key not in actual:
                continue
            if expected[key] != actual[key]:
                return False
        
        return True
    
    def _find_differences(self, expected: Dict, actual: Dict) -> Dict:
        """Find differences between parameter sets"""
        differences = {
            'changed': {},
            'added': {},
            'removed': {}
        }
        
        all_keys = set(expected.keys()) | set(actual.keys())
        
        for key in all_keys:
            if key not in expected:
                differences['added'][key] = actual[key]
            elif key not in actual:
                differences['removed'][key] = expected[key]
            elif expected[key] != actual[key]:
                differences['changed'][key] = {
                    'expected': expected[key],
                    'actual': actual[key]
                }
        
        return differences
    
    def get_snapshot(self, seed: int) -> Optional[Dict]:
        """Get snapshot for a seed"""
        return self.snapshots.get(str(seed))
    
    def print_verification_report(self):
        """Print verification status for all seeds"""
        print("\n" + "="*80)
        print("SEED VERIFICATION REPORT")
        print("="*80 + "\n")
        
        if not self.snapshots:
            print("No snapshots to verify")
            return
        
        verified_count = 0
        total_verifications = 0
        
        for seed_key, snapshot in self.snapshots.items():
            seed = snapshot['seed']
            tf = snapshot.get('timeframe', '?')
            version = snapshot.get('version', '?')
            
            history = snapshot.get('verification_history', [])
            if history:
                last_verification = history[-1]
                verified = last_verification.get('verified', False)
                
                if verified:
                    verified_count += 1
                    status = "✅"
                else:
                    status = "❌"
                
                total_verifications += 1
                
                print(f"{status} Seed {seed} ({tf}, {version})")
                print(f"   Verifications: {len(history)}")
                print(f"   Last: {last_verification.get('message', 'Unknown')}")
            else:
                print(f"⚪ Seed {seed} ({tf}, {version}): Never verified")
        
        if total_verifications > 0:
            pass_rate = (verified_count / total_verifications) * 100
            print(f"\n📊 Pass Rate: {verified_count}/{total_verifications} ({pass_rate:.1f}%)")


if __name__ == "__main__":
    print("="*80)
    print("SEED CONFIGURATION SNAPSHOT SYSTEM")
    print("="*80)
    
    # Demo: Create snapshots
    print("\n1. Creating seed snapshots...")
    print("-"*80)
    
    snapshot_mgr = SeedSnapshot("ml/seed_snapshots_demo.json")
    
    # Snapshot 1: Seed 42
    params_42 = {
        'min_confidence': 0.73,
        'min_volume': 1.22,
        'min_trend': 0.51,
        'min_adx': 29,
        'min_roc': 0.22,
        'atr_min': 0.82,
        'atr_max': 1.83
    }
    
    snapshot_mgr.create_snapshot(
        seed=15913535,
        timeframe='15m',
        parameters=params_42,
        version='v1',
        input_seed=777,
        backtest_stats={'win_rate': 0.82, 'trades': 18, 'wins': 15, 'losses': 3}
    )
    print(f"✓ Created snapshot for seed 15913535")
    
    # Demo: Verify with same parameters
    print("\n2. Verifying seed with same parameters...")
    print("-"*80)
    
    result = snapshot_mgr.verify_seed(15913535, params_42, {
        'win_rate': 0.82,
        'trades': 18,
        'wins': 15,
        'losses': 3
    })
    print(f"{result['message']}")
    print(f"   Expected hash: {result['expected_hash']}")
    print(f"   Actual hash: {result['actual_hash']}")
    if 'stats_match' in result:
        print(f"   Stats match: {result['stats_match']}")
    
    # Demo: Verify with changed parameters (should fail)
    print("\n3. Testing with CHANGED parameters (should detect)...")
    print("-"*80)
    
    params_changed = params_42.copy()
    params_changed['min_confidence'] = 0.74  # Changed!
    
    result_changed = snapshot_mgr.verify_seed(15913535, params_changed)
    print(f"{result_changed['message']}")
    if not result_changed['verified']:
        print(f"   Differences detected:")
        for key, val in result_changed['differences']['changed'].items():
            print(f"     {key}: {val['expected']} → {val['actual']}")
    
    # Demo: Verify with new parameters added (v2)
    print("\n4. Testing with NEW parameters added (v2)...")
    print("-"*80)
    
    params_v2 = params_42.copy()
    params_v2['rsi_threshold'] = 70.0  # New parameter
    
    result_v2 = snapshot_mgr.verify_seed(15913535, params_v2)
    print(f"{result_v2['message']}")
    if not result_v2['verified']:
        print(f"   New parameters added:")
        for key, val in result_v2['differences']['added'].items():
            print(f"     {key}: {val}")
    
    # Print report
    snapshot_mgr.print_verification_report()
    
    print("\n" + "="*80)
    print("USAGE")
    print("="*80)
    print("""
Integration with backtests:

1. Create snapshot BEFORE first backtest:
   snapshot_mgr = SeedSnapshot()
   snapshot_mgr.create_snapshot(
       seed=strategy_seed,
       timeframe='15m',
       parameters=params,
       version='v1',
       input_seed=input_seed,
       backtest_stats={'win_rate': 0.75, 'trades': 20, ...}
   )

2. Verify BEFORE every subsequent backtest:
   result = snapshot_mgr.verify_seed(strategy_seed, params)
   if not result['verified']:
       print(f"WARNING: Configuration changed!")
       print(f"Differences: {result['differences']}")

3. Check verification report:
   snapshot_mgr.print_verification_report()
""")
