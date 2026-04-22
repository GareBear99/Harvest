# Validation System Quick Reference

## Essential Commands

### Check System Health
```bash
python -m validation.system_health
```
Checks data freshness, fallback strategies, model files, directories, and dependencies.

### Run Production Checklist
```bash
python -m validation.production_checklist
```
**⚠️ RUN THIS BEFORE LIVE TRADING**  
Comprehensive 8-check verification including data validation, system health, and audit logs.

### Validate Data Files
```bash
python -m validation.data_validator
```
Validates all downloaded data files against expected ranges (candle counts, date spans, OHLC integrity, volume).

### Test Validation Functions
```bash
python -m validation.expected_values
```
Tests validation functions with sample data to verify they're working correctly.

### Run Complete Test Suite
```bash
python test_validation_system.py
```
Comprehensive tests of all validation components (7 tests).

## Daily Operations

### Morning Checklist
```bash
# 1. Check system health
python -m validation.system_health

# 2. Check for stale data
python pre_trading_check.py --check-only

# 3. Review audit logs
ls -lh logs/audit/
```

### Before Strategy Updates
```bash
# 1. Check system health
python -m validation.system_health

# 2. Download fresh data (if needed)
python parallel_downloader.py

# 3. Update strategies (includes validation)
python auto_strategy_updater.py
```

### Before Live Trading
```bash
# MANDATORY: Run production checklist
python -m validation.production_checklist

# Review the report
cat production_readiness_report.json

# Check for critical events
cat logs/audit/audit_summary.json | grep -i critical
```

## Audit Log Analysis

### View Recent Events
```bash
# View last 10 events
tail -10 logs/audit/audit_*.jsonl

# Pretty print last event
tail -1 logs/audit/audit_*.jsonl | python -m json.tool
```

### Check for Errors
```bash
# View error summary
cat logs/audit/audit_summary.json | python -m json.tool

# Count events by type
cat logs/audit/audit_*.jsonl | grep -o '"event_type":"[^"]*"' | sort | uniq -c
```

### Search for Specific Events
```bash
# Find all data validations
grep 'DATA_VALIDATION' logs/audit/audit_*.jsonl

# Find failed validations
grep -i 'failed' logs/audit/audit_*.jsonl

# Find critical events
grep 'CRITICAL' logs/audit/audit_*.jsonl
```

## Troubleshooting Commands

### Fix Missing Directories
```bash
mkdir -p logs/audit validation ml/models ml/metadata data
```

### Check Data Files
```bash
ls -lh data/*.json
```

### Verify Strategy File
```bash
cat ml/fallback_strategies.json | python -m json.tool | grep -E "(validation_passed|updated_at)"
```

### Clean Old Audit Logs (optional)
```bash
# Keep only last 7 days
find logs/audit -name "audit_*.jsonl" -mtime +7 -delete
```

## Integration Testing

### Test Download with Validation
```bash
python parallel_downloader.py
# Validates data automatically after download
```

### Test Strategy Update with Validation
```bash
python auto_strategy_updater.py
# Validates strategies before saving
```

### Test Pre-Trading Check
```bash
# Check only (no updates)
python pre_trading_check.py --check-only

# Auto-update if needed
python pre_trading_check.py --non-interactive
```

## Expected Output Examples

### Healthy System
```
🏥 SYSTEM HEALTH REPORT
================================================================================

✅ Overall Status: HEALTHY

✅ Data Freshness: FRESH
✅ Fallback Strategies: All required strategies exist with 2+ strategies each
✅ Model Files: All models exist
✅ Directories: All required directories exist
✅ Dependencies: All required packages installed
```

### Production Ready
```
🚀 PRODUCTION READINESS CHECKLIST
================================================================================

[1/8] System Health... ✅ System health check passed
[2/8] Data Validation... ✅ All 2 active pairs validated successfully
[3/8] Grid Search Completion... ✅ Grid search completed for all 4 required pairs
[4/8] Strategy Recency... ✅ All strategies are recent (<30 days)
[5/8] Validation Flags... ✅ All strategies have passed validation
[6/8] Audit Logging... ✅ Audit logging operational (2 log files)
[7/8] No Critical Events... ✅ No critical audit events
[8/8] No Placeholders... ✅ No placeholder values detected

================================================================================
✅ ALL CHECKS PASSED - SYSTEM READY FOR PRODUCTION
================================================================================
```

### Data Validation Passed
```
📊 DATA VALIDATION REPORT: BTCUSDT
================================================================================

✅ Overall Status: PASSED

✅ Candle Count: 129660 (expected: 129000-130000)
✅ Date Range: 90 days (2024-09-17 to 2024-12-16) (expected: 88-92 days)
✅ Price Data: Valid
✅ Volume Data: Valid
✅ Time Gaps: None detected
✅ Duplicates: None detected
```

## Common Issues and Solutions

### Issue: "No audit logs found"
**Solution:** Audit logger hasn't been used yet. Run any validation command to create logs.

### Issue: "Data validation failed"
**Solution:** 
1. Check candle count (should be ~129,600 for 90 days)
2. Check for gaps in timestamps
3. Re-download data if corruption detected

### Issue: "Strategy validation failed"
**Solution:**
1. Review parameter violations in output
2. Adjust grid search ranges if needed
3. Re-run grid search

### Issue: "Production checklist failed"
**Solution:**
1. Read the failure details carefully
2. Follow recommendations in output
3. Fix issues one by one
4. Re-run checklist

## File Locations

### Configuration
- `validation/expected_values.py` - All validation bounds
- `validation/README.md` - Detailed documentation

### Logs
- `logs/audit/audit_YYYYMMDD_HHMMSS.jsonl` - Session logs
- `logs/audit/audit_summary.json` - Error/warning summary

### Strategies
- `ml/fallback_strategies.json` - Validated fallback strategies

### Reports
- `production_readiness_report.json` - Latest production check

### Tests
- `test_validation_system.py` - Comprehensive test suite
- `TEST_RESULTS.md` - Latest test results

## Validation Bounds Reference

### Strategy Parameters
- Confidence: 0.60 - 0.95
- Volume: 1.5 - 6.0
- Trend: 0.40 - 0.70
- ADX: 20 - 40
- ATR: 0.005 - 0.060

### Performance Metrics
- Win Rate: 70% - 98%
- Trades: 3 - 1000
- P&L per Trade: -$10 to $100
- Max Drawdown: 0% - 35%

### Data Requirements
- Candle Count: 129,000 - 130,000 (for 90 days)
- Date Span: 88 - 92 days
- No gaps > 5 minutes
- No duplicate timestamps

## Support

For detailed information:
- `validation/README.md` - Complete documentation
- `TEST_RESULTS.md` - Test results and verification
- `docs/USER_MANUAL.md` - Full system manual

For issues:
1. Check audit logs: `logs/audit/audit_summary.json`
2. Run health check: `python -m validation.system_health`
3. Review validation reports in output
