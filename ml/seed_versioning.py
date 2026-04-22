"""
Versioned Seed System - Bulletproof parameter evolution

Ensures old seeds remain valid when new parameters are added.

Version History:
- v1: Initial parameters (min_confidence, min_volume, min_trend, min_adx, min_roc, atr_min, atr_max)
- v2+: Future parameters added without breaking v1 seeds

Key principle: Seeds include version number, parameters always hashed in same order
"""

from typing import Dict, List, Optional
import hashlib


# Define parameter versions (order matters for hashing!)
PARAMETER_VERSIONS = {
    'v1': [
        'min_confidence',
        'min_volume',
        'min_trend',
        'min_adx',
        'min_roc',
        'atr_min',
        'atr_max'
    ],
    # Future versions - add new params at end, never reorder v1
    'v2': [
        'min_confidence',
        'min_volume',
        'min_trend',
        'min_adx',
        'min_roc',
        'atr_min',
        'atr_max',
        # New params for v2 would go here
        # 'rsi_threshold',
        # 'macd_threshold',
    ],
}

# Current version
CURRENT_VERSION = 'v1'


def get_parameter_version(params: Dict) -> str:
    """
    Determine which version a parameter set uses
    
    Args:
        params: Strategy parameters
        
    Returns:
        Version string (e.g., 'v1', 'v2')
    """
    param_keys = set(params.keys())
    
    # First: Check for exact matches (most specific)
    for version in sorted(PARAMETER_VERSIONS.keys(), reverse=True):
        version_params = set(PARAMETER_VERSIONS[version])
        if param_keys == version_params:
            return version
    
    # Second: Check if params is subset of any version (compatibility mode)
    for version in sorted(PARAMETER_VERSIONS.keys(), reverse=True):
        version_params = set(PARAMETER_VERSIONS[version])
        if param_keys.issubset(version_params):
            return version
    
    # Default to current version
    return CURRENT_VERSION


def generate_versioned_seed(timeframe: str, params: Dict, version: Optional[str] = None) -> Dict:
    """
    Generate seed with version information
    
    Args:
        timeframe: '15m', '1h', '4h'
        params: Strategy parameters
        version: Optional version override (auto-detected if None)
        
    Returns:
        Dict with seed, version, and metadata
        
    Example:
        >>> result = generate_versioned_seed('15m', params)
        >>> result
        {
            'seed': 15542880,
            'version': 'v1',
            'timeframe': '15m',
            'parameters_hash': 'a1b2c3...',
            'parameters': {...}
        }
    """
    # Auto-detect version if not provided
    if version is None:
        version = get_parameter_version(params)
    
    # Get parameter order for this version
    param_order = PARAMETER_VERSIONS[version]
    
    # Build canonical string (version-specific parameter order)
    canonical_parts = [f"{timeframe}:{version}"]
    
    for param_name in param_order:
        if param_name in params:
            value = round(float(params[param_name]), 2)
            canonical_parts.append(f"{param_name}={value}")
    
    canonical_string = "|".join(canonical_parts)
    
    # Hash to get seed
    hash_obj = hashlib.sha256(canonical_string.encode())
    hash_hex = hash_obj.hexdigest()
    hash_int = int(hash_hex[:12], 16)
    
    # Timeframe prefix
    prefix_map = {'15m': 15, '1h': 60, '4h': 240}
    prefix = prefix_map.get(timeframe, 999)
    
    seed = (prefix * 1_000_000) + (hash_int % 1_000_000)
    
    return {
        'seed': seed,
        'version': version,
        'timeframe': timeframe,
        'parameters_hash': hash_hex[:16],
        'parameters': {k: params[k] for k in param_order if k in params},
        'canonical_string': canonical_string
    }


def validate_version_compatibility(old_seed_info: Dict, new_params: Dict) -> bool:
    """
    Check if new parameters are compatible with old seed
    
    Args:
        old_seed_info: Seed info from generate_versioned_seed()
        new_params: New parameters to test
        
    Returns:
        True if compatible (would generate same seed)
    """
    # Generate new seed with same version
    new_seed_info = generate_versioned_seed(
        old_seed_info['timeframe'],
        new_params,
        version=old_seed_info['version']
    )
    
    return new_seed_info['seed'] == old_seed_info['seed']


def migrate_seed_to_new_version(old_seed_info: Dict, new_params: Dict) -> Dict:
    """
    Migrate seed to new version when parameters are added
    
    Args:
        old_seed_info: Original seed info
        new_params: New parameters (includes old + new)
        
    Returns:
        New seed info with updated version
    """
    # Determine new version
    new_version = get_parameter_version(new_params)
    
    # Generate new seed with new version
    new_seed_info = generate_versioned_seed(
        old_seed_info['timeframe'],
        new_params,
        version=new_version
    )
    
    # Add migration metadata
    new_seed_info['migrated_from'] = {
        'old_seed': old_seed_info['seed'],
        'old_version': old_seed_info['version']
    }
    
    return new_seed_info


if __name__ == "__main__":
    print("="*80)
    print("VERSIONED SEED SYSTEM - Bulletproof Parameter Evolution")
    print("="*80)
    
    # Test v1 parameters
    print("\n1. Testing v1 parameters (current)")
    print("-"*80)
    
    v1_params = {
        'min_confidence': 0.78,
        'min_volume': 1.30,
        'min_trend': 0.65,
        'min_adx': 30,
        'min_roc': 0.15,
        'atr_min': 0.80,
        'atr_max': 2.00
    }
    
    v1_seed = generate_versioned_seed('15m', v1_params)
    print(f"Version: {v1_seed['version']}")
    print(f"Seed: {v1_seed['seed']}")
    print(f"Hash: {v1_seed['parameters_hash']}")
    
    # Test determinism
    print("\n2. Testing v1 determinism")
    print("-"*80)
    
    v1_seed_2 = generate_versioned_seed('15m', v1_params)
    if v1_seed['seed'] == v1_seed_2['seed']:
        print(f"✅ v1 seed is deterministic: {v1_seed['seed']}")
    else:
        print(f"❌ v1 seed changed!")
    
    # Simulate adding new parameters in v2
    print("\n3. Simulating future v2 (with new parameters)")
    print("-"*80)
    print("Scenario: We add 'rsi_threshold' and 'macd_threshold' in the future")
    
    # Add v2 to parameter versions temporarily for demo
    PARAMETER_VERSIONS['v2'] = PARAMETER_VERSIONS['v1'] + ['rsi_threshold', 'macd_threshold']
    
    v2_params = v1_params.copy()
    v2_params['rsi_threshold'] = 70.0
    v2_params['macd_threshold'] = 0.05
    
    v2_seed = generate_versioned_seed('15m', v2_params, version='v2')
    print(f"Version: {v2_seed['version']}")
    print(f"Seed: {v2_seed['seed']}")
    print(f"Hash: {v2_seed['parameters_hash']}")
    
    # Verify v1 seed unchanged
    print("\n4. Verifying v1 seeds remain unchanged")
    print("-"*80)
    
    v1_seed_after = generate_versioned_seed('15m', v1_params, version='v1')
    if v1_seed['seed'] == v1_seed_after['seed']:
        print(f"✅ v1 seed unchanged after v2 addition: {v1_seed['seed']}")
        print(f"   Old: {v1_seed['seed']}")
        print(f"   New: {v1_seed_after['seed']}")
    else:
        print(f"❌ v1 seed changed! This should never happen!")
        print(f"   Old: {v1_seed['seed']}")
        print(f"   New: {v1_seed_after['seed']}")
    
    # Test migration
    print("\n5. Testing seed migration (v1 → v2)")
    print("-"*80)
    
    migrated = migrate_seed_to_new_version(v1_seed, v2_params)
    print(f"Original v1 seed: {v1_seed['seed']}")
    print(f"Migrated v2 seed: {migrated['seed']}")
    print(f"Migration tracked: {migrated.get('migrated_from')}")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("\n✅ Versioned seed system operational!")
    print("\nKey features:")
    print("  • Seeds include version number")
    print("  • Old seeds remain valid when new parameters added")
    print("  • Parameter order locked per version")
    print("  • Migration tracked from old to new version")
    print("\nWhen adding new parameters:")
    print("  1. Create new version in PARAMETER_VERSIONS")
    print("  2. Add new params at END of list")
    print("  3. Never reorder existing params")
    print("  4. Old seeds continue to work with old version")
