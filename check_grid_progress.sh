#!/bin/bash
# Monitor grid search progress

echo "🔍 Grid Search Progress Monitor"
echo "================================"
echo ""

# Check if CSV file exists
if [ -f "grid_search_results/eth_15m_complete.csv" ]; then
    LINES=$(wc -l < grid_search_results/eth_15m_complete.csv)
    STRATEGIES=$((LINES - 1))  # Subtract header
    PERCENT=$(echo "scale=1; $STRATEGIES * 100 / 121500" | bc)
    
    echo "📊 Strategies tested: $STRATEGIES / 121,500"
    echo "📈 Progress: $PERCENT%"
    echo ""
    
    if [ $STRATEGIES -gt 100 ]; then
        echo "🔝 Preview of top results so far:"
        echo "================================"
        head -1 grid_search_results/eth_15m_complete.csv
        tail -n +2 grid_search_results/eth_15m_complete.csv | \
            awk -F',' '$4 >= 3' | \
            sort -t',' -k7 -rn | \
            head -5
    fi
else
    echo "⏳ CSV file not created yet. Grid search still initializing..."
fi

echo ""
echo "💡 Tip: Run this script again in a few minutes to check progress"
echo "   Or open grid_search_results/eth_15m_complete.csv in Excel"
