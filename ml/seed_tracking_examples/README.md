# Seed Tracking System - Example Files

## Purpose
These files are **examples and demonstrations** of the 4-layer seed tracking system. They show the proper structure and format for each tracking layer.

## ⚠️ NOT Production Data
These files contain **test/demo data** created during development to demonstrate system functionality. They are NOT actively used by the trading system.

## Files Included

### Layer 1 Example: `seed_registry_demo.json`
**Purpose**: Demonstrates performance database structure

**Contains**:
- 3 example seeds (15542880, 15913535, 60507652)
- Example test history and statistics
- Shows how win rates, trades, and P&L are tracked

**Key Features Demonstrated**:
- Seed registration with input seed tracking
- Test history with multiple backtest runs
- Aggregate statistics (total_trades, avg_wr, best/worst_wr)
- Performance tracking over time

### Layer 2 Example: `seed_snapshots_test.json` & `seed_snapshots_workflow.json`
**Purpose**: Demonstrates SHA-256 verification snapshot structure

**Contains**:
- Immutable configuration snapshots
- Config hash calculations
- Verification history

**Key Features Demonstrated**:
- Configuration drift detection
- SHA-256 hash verification
- Snapshot creation workflow
- Verification tracking

### Layer 3 Example: `seed_catalog_demo.json`
**Purpose**: Demonstrates complete backtest catalog structure

**Contains**:
- 2 complete backtest run entries
- Trade-by-trade records
- Full metadata (data files, errors, warnings)
- Performance tier categorization

**Key Features Demonstrated**:
- Entry structure with all fields
- Trade logging format
- Daily stats tracking
- Performance metrics (max_drawdown, sharpe_ratio, etc.)
- Error and warning tracking

### Layer 4 Example: `seed_performance_tracker_demo.json`
**Purpose**: Demonstrates whitelist/blacklist tracking structure

**Contains**:
- 3 example seeds with performance history
- Whitelist: 1 seed (15913535, 80%+ WR)
- Blacklist: 2 seeds (60507652, 24012345, low WR)
- Statistics by timeframe

**Key Features Demonstrated**:
- Performance-based categorization
- Whitelist criteria (75%+ WR, 20+ trades)
- Blacklist criteria (<50% WR)
- Historical performance tracking
- Per-timeframe statistics

## Example Seeds Used

| Seed | Input Seed | Timeframe | Win Rate | Trades | Status |
|------|-----------|-----------|----------|--------|--------|
| 15542880 | 42 | 15m | 75% | 20 | Example good |
| 15913535 | 777 | 15m | 82% | 38 | Whitelisted |
| 60507652 | 100 | 1h | 45% | 15 | Blacklisted |
| 24012345 | - | 4h | 52% | 18 | Blacklisted |

## How to Use These Examples

### For Learning
1. **Study the structure**: Understand how each layer stores data
2. **Check the schemas**: See what fields are required
3. **Reference the examples**: Use when building your own tracking

### For Testing
1. **Copy structure**: Use as templates for test cases
2. **Validate format**: Ensure your production data matches format
3. **Reference values**: Use for unit test assertions

### For Documentation
1. **Show examples**: Reference in documentation
2. **Explain concepts**: Use to demonstrate seed tracking
3. **Training material**: Help new developers understand system

## Production Files (Not in This Directory)

The actual production tracking files are in the parent `ml/` directory:
- `ml/seed_registry.json` - Layer 1 (production)
- `ml/seed_snapshots.json` - Layer 2 (production)
- `ml/seed_catalog.json` - Layer 3 (production, will be created)
- `ml/seed_performance_tracker.json` - Layer 4 (production, will be created)
- `ml/seed_whitelist.json` - Layer 4 subset (production)
- `ml/seed_blacklist.json` - Layer 4 subset (production)

## Differences from Production

| Aspect | Examples | Production |
|--------|----------|------------|
| **Seeds** | Fake test seeds | Real SHA-256 strategy seeds |
| **Data** | Made-up test results | Actual backtest results |
| **Usage** | Reference only | Actively used by system |
| **Updates** | Static | Updated after each backtest |

## When to Update Examples

Update these example files when:
- Adding new fields to tracking system
- Changing JSON schema
- Adding new tracking features
- Documenting edge cases

**Last Updated**: December 26, 2024  
**Purpose**: Development reference and documentation examples
