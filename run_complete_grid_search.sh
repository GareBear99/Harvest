#!/bin/bash
#
# Complete Grid Search - Test ALL Strategies Across ALL Timeframes and Assets
#
# This will generate 6 comprehensive CSV files:
#   - ETH 15m, 1h, 4h
#   - BTC 15m, 1h, 4h
#
# Each file contains EVERY possible parameter combination tested.
#

echo "================================================================================"
echo "🔬 COMPLETE GRID SEARCH - ALL POSSIBLE STRATEGIES"
echo "================================================================================"
echo ""
echo "This will systematically test EVERY parameter combination across:"
echo "  - Assets: ETH, BTC"
echo "  - Timeframes: 15m, 1h, 4h"
echo "  - Total combinations per run: ~121,500"
echo "  - Total runs: 6"
echo "  - Total strategies tested: ~729,000"
echo ""
echo "Estimated time: 2-4 hours (depending on your machine)"
echo ""
read -p "Press ENTER to start or Ctrl+C to cancel..."
echo ""

# Create output directory
mkdir -p grid_search_results
cd "$(dirname "$0")"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Function to run search
run_search() {
    ASSET=$1
    TF=$2
    OUTPUT="grid_search_results/grid_${ASSET}_${TF}_${TIMESTAMP}.csv"
    
    echo "================================================================================"
    echo "Testing: $ASSET $TF"
    echo "Output: $OUTPUT"
    echo "================================================================================"
    
    python grid_search_all_strategies.py -a $ASSET -t $TF -o $OUTPUT
    
    echo ""
    echo "✅ $ASSET $TF complete!"
    echo ""
}

# Run all combinations
echo "🚀 Starting grid search..."
echo ""

run_search "ETH" "15m"
run_search "ETH" "1h"
run_search "ETH" "4h"

run_search "BTC" "15m"
run_search "BTC" "1h"
run_search "BTC" "4h"

# Summary
echo "================================================================================"
echo "✅ COMPLETE GRID SEARCH FINISHED"
echo "================================================================================"
echo ""
echo "Results saved in: grid_search_results/"
echo ""
echo "Files generated:"
ls -lh grid_search_results/*${TIMESTAMP}*.csv
echo ""
echo "📊 Analysis:"
echo "  1. Open CSV files in Excel/Numbers/Google Sheets"
echo "  2. Sort by 'win_rate' column to find best WR strategies"
echo "  3. Sort by 'total_pnl' column to find most profitable"
echo "  4. Filter 'trades' >= 3 for statistically valid strategies"
echo ""
echo "💡 Quick command line analysis:"
echo "  # View best WR strategies for ETH 15m:"
echo "  head -1 grid_search_results/grid_ETH_15m_${TIMESTAMP}.csv && \\"
echo "    tail -n +2 grid_search_results/grid_ETH_15m_${TIMESTAMP}.csv | sort -t',' -k7 -rn | head -20"
echo ""
echo "🎯 Next steps:"
echo "  1. Find strategies with 90%+ WR in the CSV files"
echo "  2. Update ml/base_strategy.py with best parameters"
echo "  3. Run: python optimize_base_strategy.py --quick-test"
echo ""
