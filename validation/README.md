# Production-Grade Validation System

Comprehensive validation framework ensuring data integrity, strategy quality, and system readiness before live trading.

## Overview

The validation system provides multiple layers of protection:

1. **Expected Values** - Pre-calculated bounds for all parameters and metrics
2. **Data Validation** - Validates downloaded candle data integrity
3. **Strategy Validation** - Validates strategy parameters and performance metrics
4. **Audit Logging** - Tracks all validation checks and system operations
5. **System Health** - Monitors overall system health and readiness
6. **Production Checklist** - Comprehensive pre-trading verification

## Quick Start

### Run System Health Check
```bash
python -m validation.system_health
```

### Run Data Validation
```bash
python -m validation.data_validator
```

### Run Production Readiness Checklist
```bash
python -m validation.production_checklist
```

## Components

### 1. Expected Values (`expected_values.py`)

Defines all acceptable ranges for:
- **Data**: Candle counts (129,000-130,000), date spans (88-92 days), price/volume ranges
- **Strategy Parameters**: Confidence (0.60-0.95), volume (1.5-6.0), trend (0.40-0.70), ADX (20-40), ATR (0.005-0.060)
- **Performance Metrics**: Win rate (0.70-0.98), trades (3-1000), P&L per trade (-10 to 100), max drawdown (0-0.35)

Functions:
- `validate_strategy_params(params)` - Returns (valid, violations)
- `validate_performance_metrics(metrics)` - Returns (valid, violations)
- `is_within_expected_range(value, min, max)` - Check if value in range

### 2. Data Validator (`data_validator.py`)

Validates downloaded candle data against expected bounds.

**What it checks:**
- Candle count matches expected range
- Date span matches expected range (88-92 days for 90-day data)
- OHLC prices are valid (no negatives, high >= low, etc.)
- Volume is valid (no negatives, meets minimums for BTC/ETH)
- No time gaps (missing candles)
- No duplicate timestamps

**Usage:**
```python
from validation.data_validator import validate_candle_data, print_validation_report

# Validate single file
passed, checks = validate_candle_data('data/BTCUSDT_1m_90d.json', 'BTCUSDT')

if not passed:
    print_validation_report('BTCUSDT', passed, checks)

# Validate all active pairs
from validation.data_validator import validate_all_active_pairs
results = validate_all_active_pairs()
```

### 3. Audit Logger (`audit_logger.py`)

Comprehensive logging system tracking all validation checks and system operations.

**Log Levels:**
- INFO - Normal operations
- WARNING - Validation warnings, recoverable issues
- ERROR - Validation failures, operation errors
- CRITICAL - System anomalies, production readiness failures

**Event Types:**
- DATA_VALIDATION - Data integrity checks
- STRATEGY_VALIDATION - Strategy parameter/performance checks
- DATA_DOWNLOAD - Download operations
- GRID_SEARCH - Grid search completion
- FALLBACK_SAVE - Strategy saving operations
- SYSTEM_CHECK - Health check results
- ANOMALY_DETECTED - Critical anomalies

**Usage:**
```python
from validation.audit_logger import log_data_validation, log_strategy_validation

# Log data validation
log_data_validation('BTCUSDT', passed=True, checks={'candle_count': 129660, ...})

# Log strategy validation
log_strategy_validation('BTCUSDT', '1m', strategy_num=1, passed=True, violations=[])

# Access global logger
from validation.audit_logger import get_audit_logger
logger = get_audit_logger()
logger.log_event('CUSTOM_EVENT', AuditLevel.INFO, 'Custom message', {'data': 'value'})
```

**Log Files:**
- `logs/audit/audit_YYYYMMDD_HHMMSS.jsonl` - Session logs (JSON lines format)
- `logs/audit/audit_summary.json` - Summary of warnings/errors/critical events

### 4. System Health Monitor (`system_health.py`)

Monitors overall system health and readiness.

**Checks:**
- **Data Freshness** - All data files exist and < 30 days old
- **Fallback Strategies** - All required strategies exist with 2+ strategies each
- **Model Files** - ML models exist for all pairs/timeframes
- **Directories** - All required directories exist (data/, ml/, logs/, validation/)
- **Dependencies** - All Python packages installed (numpy, pandas, sklearn, binance, requests)

**Usage:**
```python
from validation.system_health import run_health_check

# Run all checks and print report
passed = run_health_check()

if not passed:
    print("Fix issues before proceeding to live trading")

# Access individual checks
from validation.system_health import SystemHealth
health = SystemHealth()
checks = health.run_all_checks()
health.print_report()
```

### 5. Production Checklist (`production_checklist.py`)

Comprehensive verification before enabling live trading.

**Checks:**
1. System Health - All system health checks pass
2. Data Validation - All data validated against expected ranges
3. Grid Search Completion - Grid searches completed for all pairs/timeframes
4. Strategy Recency - All strategies < 30 days old
5. Validation Flags - All strategies have validation_passed flag
6. Audit Logging - Audit system operational
7. No Critical Events - No critical issues in audit logs
8. No Placeholders - No test/placeholder values in production config

**Usage:**
```bash
# Run checklist
python -m validation.production_checklist

# Exit code: 0 if passed, 1 if failed
```

```python
from validation.production_checklist import run_production_checklist

passed = run_production_checklist()

if passed:
    print("System ready for live trading!")
else:
    print("Fix issues before going live")
```

**Output:**
- Console report with all check results
- `production_readiness_report.json` - Detailed JSON report

## Integration with Trading System

### Auto Strategy Updater Integration

The `auto_strategy_updater.py` automatically uses validation:

1. **During Grid Search** - Logs grid search completion with audit trail
2. **Strategy Display** - Shows validation status for each strategy
3. **Before Saving** - Validates all strategies before saving to fallback file
4. **Rejects Invalid** - Skips strategies that fail validation

Example output:
```
🔍 VALIDATING STRATEGIES BEFORE SAVING
================================================================================

Validating Strategy #1...
  ✅ Strategy #1 validation PASSED
Validating Strategy #2...
  ⚠️  Strategy #2 validation FAILED
    - Parameter issue: min_confidence = 0.99 (expected 0.60-0.95)
  ❌ Skipping invalid strategy

✅ 1/2 strategies passed validation

💾 Saved 1 validated fallback strategies to ml/fallback_strategies.json
```

### Parallel Downloader Integration

The `parallel_downloader.py` includes data validation:

```python
# Download with validation
download_and_save_all(symbols=['BTCUSDT', 'ETHUSDT'], days=90, verify=True, validate=True)
```

1. Downloads data
2. Saves to file
3. Logs download to audit trail
4. Validates candle data against expected bounds
5. Runs blockchain verification
6. Returns None if validation fails

## Expected Values Reference

### Data Expectations
- Candle count: 129,000 - 130,000 (for 90 days of 1m data)
- Date span: 88 - 92 days
- BTC/ETH minimum volume: 0.001

### Strategy Parameter Bounds
- Confidence: 0.60 - 0.95
- Volume: 1.5 - 6.0
- Trend: 0.40 - 0.70
- ADX: 20 - 40
- ATR Min: 0.005 - 0.060
- ATR Max: 0.005 - 0.060

### Performance Expectations
- Win rate: 0.70 - 0.98 (70% - 98%)
- Minimum trades: 3
- Maximum trades: 1000
- P&L per trade: -10 to 100 USDT
- Maximum drawdown: 0.0 - 0.35 (0% - 35%)

### Backtest Constraints
- Maximum leverage: 25x
- Maximum risk per trade: 5%

## Audit Log Analysis

### View Recent Session Logs
```bash
tail -f logs/audit/audit_*.jsonl | jq '.'
```

### Check for Errors
```bash
cat logs/audit/audit_summary.json | jq '.errors'
```

### Check for Critical Events
```bash
cat logs/audit/audit_summary.json | jq '.critical'
```

### Count Events by Type
```bash
cat logs/audit/audit_*.jsonl | jq -r '.event_type' | sort | uniq -c
```

## Best Practices

1. **Always run production checklist before live trading**
   ```bash
   python -m validation.production_checklist
   ```

2. **Monitor audit logs regularly**
   - Check for warnings/errors after each operation
   - Review critical events immediately

3. **Validate after downloads**
   - Use `validate=True` parameter in downloader
   - Review validation reports for failures

4. **Keep strategies fresh**
   - Re-run grid search if strategies > 30 days old
   - Update fallback strategies regularly

5. **Check system health daily**
   ```bash
   python -m validation.system_health
   ```

## Troubleshooting

### Data Validation Fails
- Check candle count (should be ~129,600 for 90 days)
- Check date range (should span ~90 days)
- Look for gaps in timestamps
- Check for invalid OHLC values

### Strategy Validation Fails
- Parameters outside expected bounds → Adjust grid search ranges
- Performance metrics suspicious → Review backtest logic
- No valid strategies → Widen grid search parameters

### Production Checklist Fails
- Follow recommendations in output
- Fix issues in order shown
- Re-run checklist after fixes

### Audit Logs Show Errors
- Review error details in `audit_summary.json`
- Check recent session logs for context
- Fix underlying issues and re-validate

## Files Structure

```
validation/
├── __init__.py                  # Package init
├── expected_values.py           # Pre-calculated bounds and ranges
├── data_validator.py            # Data integrity validation
├── audit_logger.py              # Comprehensive audit logging
├── system_health.py             # System health monitoring
├── production_checklist.py      # Production readiness verification
└── README.md                    # This file

logs/
└── audit/
    ├── audit_YYYYMMDD_HHMMSS.jsonl    # Session logs
    └── audit_summary.json              # Error/warning summary
```

## Next Steps

Before moving to live trading:

1. ✅ Run production checklist
2. ✅ Review all validation reports
3. ✅ Check audit logs for critical events
4. ✅ Verify system health
5. ✅ Ensure all strategies validated
6. ✅ Confirm data is fresh (<30 days)
7. ⚠️ Perform paper trading test
8. ⚠️ Start with minimal position sizes
9. ⚠️ Monitor closely for first 24 hours

## Support

For issues or questions:
- Review audit logs for detailed error information
- Check validation reports for specific failures
- Run system health check to identify missing components
- Consult main documentation in `docs/USER_MANUAL.md`
