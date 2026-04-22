# Validation Test Suite

Comprehensive validation tests for the trading system to ensure correctness, determinism, and production readiness.

## Quick Start

```bash
# Run all validation tests
python validation/run_all_tests.py

# Or run individually
python validation/test_determinism.py
python validation/test_base_strategy.py
```

## Test Suite

### 1. Determinism Test (`test_determinism.py`)

**Purpose**: Verify the system produces identical results across multiple runs with the same seed.

**What it tests**:
- Runs backtest 3 times with seed=42
- Compares trade signatures, PnL, balances
- Tests both ETH and BTC assets
- Validates random number generation is properly seeded

**Pass criteria**: All 3 runs must produce byte-for-byte identical results.

**Current status**: ✅ PASSING

```bash
$ python validation/test_determinism.py

ETH: 3 runs → IDENTICAL results (6 trades, $9.78)
BTC: 3 runs → IDENTICAL results (7 trades, $9.63)
✅ DETERMINISM TEST PASSED
```

### 2. Base Strategy Test (`test_base_strategy.py`)

**Purpose**: Verify base strategy produces known baseline results.

**What it tests**:
- Runs backtest with BASE_STRATEGY thresholds
- Compares against BASELINE_RESULTS (seed=42)
- Validates trade count, win rate, final balance
- Tests both ETH and BTC assets

**Pass criteria**: 
- Trade count must match exactly
- Win rate within 5% tolerance
- Balance within 5% tolerance

**Current status**: ✅ PASSING

```bash
$ python validation/test_base_strategy.py

ETH: 6 trades, 50.0% WR, $9.78 ✓
BTC: 7 trades, 28.6% WR, $9.63 ✓
✅ BASE STRATEGY TEST PASSED
```

### 3. Master Suite (`run_all_tests.py`)

**Purpose**: Run all validation tests and generate comprehensive report.

**Features**:
- Runs all tests sequentially
- Catches and reports crashes
- Summary report at end
- Exit code 0 if all pass, 1 if any fail

**Current status**: ✅ ALL TESTS PASSING

```bash
$ python validation/run_all_tests.py

Test Results:
  1. Determinism:    ✅ PASS
  2. Base Strategy:  ✅ PASS

✅ ALL TESTS PASSED
The trading system is validated and ready for production.
```

## Baseline Results

With seed=42, base strategy produces:

### ETH (data/eth_21days.json)
- **Trades**: 6
- **Win Rate**: 50.0% (3 wins, 3 losses)
- **Final Balance**: $9.78 (from $10.00)
- **Return**: -2.23%

### BTC (data/btc_21days.json)
- **Trades**: 7
- **Win Rate**: 28.6% (2 wins, 5 losses)
- **Final Balance**: $9.63 (from $10.00)
- **Return**: -3.73%

### Combined Portfolio
- **Total Trades**: 13
- **Combined Win Rate**: 38.5%
- **Final Balance**: $19.40 (from $20.00)
- **Return**: -2.98%

*Note: These are baseline results with conservative settings. The adaptive learning system improves performance over time.*

## When to Run Tests

### Always run before:
- Deploying to production
- Making strategy changes
- Modifying core logic
- Changing random number usage

### Run after:
- Fixing bugs
- Refactoring code
- Adding new features
- Updating dependencies

## Adding New Tests

To add a new validation test:

1. Create test file in `validation/`
2. Implement test function that returns bool
3. Add to `run_all_tests.py`
4. Update this README

Example structure:
```python
#!/usr/bin/env python3
"""Test description"""

def test_something():
    """Test function"""
    # Run test
    passed = True  # or False
    
    # Print results
    if passed:
        print("✅ TEST PASSED")
    else:
        print("❌ TEST FAILED")
    
    return passed

if __name__ == "__main__":
    import sys
    passed = test_something()
    sys.exit(0 if passed else 1)
```

## CI/CD Integration

To integrate with CI/CD:

```bash
# Run tests and exit with proper code
python validation/run_all_tests.py
exit $?
```

## Troubleshooting

### Tests fail after code changes
- Review changes that could affect determinism
- Check if random number generation was added without seeding
- Verify no unintended strategy modifications

### Tests pass locally but fail in CI
- Check environment differences (Python version, numpy version)
- Verify data files are identical
- Check random seed consistency

### Determinism test fails
- Something is non-deterministic (time-based, unsorted dict iteration, etc.)
- Review recent changes for sources of randomness
- Ensure all random operations use the seeded generator

### Base strategy test fails
- Strategy constants may have changed
- Update BASELINE_RESULTS if intentional change
- Verify no breaking changes in calculation logic

## Performance

Test suite execution time:
- Determinism test: ~30 seconds (3 runs per asset)
- Base strategy test: ~20 seconds (1 run per asset)
- **Total**: ~50 seconds

## Related Files

- `ml/base_strategy.py` - Base strategy constants and baseline results
- `ml/strategy_pool.py` - Strategy pool management
- `backtest_90_complete.py` - Main backtest with seed parameter
- `PRODUCTION_VALIDATION_COMPLETE.md` - Complete validation documentation

---

**Last Updated**: 2024-12-16
**Status**: ✅ ALL TESTS PASSING
