#!/bin/bash
# Live progress bar for grid search

TOTAL=121500
CSV_FILE="grid_search_results/eth_15m_complete.csv"

clear
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                    🔬 GRID SEARCH LIVE PROGRESS TRACKER                    ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Function to draw progress bar
draw_progress_bar() {
    local current=$1
    local total=$2
    local width=50
    
    local percent=$(echo "scale=1; $current * 100 / $total" | bc)
    local filled=$(echo "scale=0; $current * $width / $total" | bc)
    local empty=$((width - filled))
    
    # Build bar
    printf "["
    for ((i=0; i<filled; i++)); do printf "█"; done
    for ((i=0; i<empty; i++)); do printf "░"; done
    printf "] %6.1f%% (%'d / %'d)\n" "$percent" "$current" "$total"
}

# Function to estimate time remaining
estimate_time() {
    local current=$1
    local total=$2
    local elapsed=$3
    
    if [ $current -eq 0 ]; then
        echo "Calculating..."
        return
    fi
    
    local rate=$(echo "scale=2; $current / $elapsed" | bc)
    local remaining=$((total - current))
    local eta=$(echo "scale=0; $remaining / $rate" | bc)
    
    local hours=$((eta / 3600))
    local mins=$(( (eta % 3600) / 60 ))
    local secs=$((eta % 60))
    
    if [ $hours -gt 0 ]; then
        printf "%dh %dm %ds" $hours $mins $secs
    elif [ $mins -gt 0 ]; then
        printf "%dm %ds" $mins $secs
    else
        printf "%ds" $secs
    fi
}

START_TIME=$(date +%s)

# Main loop
while true; do
    # Move cursor to top
    tput cup 4 0
    
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    
    if [ -f "$CSV_FILE" ]; then
        LINES=$(wc -l < "$CSV_FILE" 2>/dev/null || echo "1")
        STRATEGIES=$((LINES - 1))  # Subtract header
        
        if [ $STRATEGIES -lt 0 ]; then
            STRATEGIES=0
        fi
        
        # Clear previous content
        for i in {1..20}; do
            echo "                                                                                "
        done
        
        # Move back up
        tput cup 4 0
        
        echo "📊 Strategies Tested:"
        draw_progress_bar $STRATEGIES $TOTAL
        echo ""
        
        RATE=$(echo "scale=1; $STRATEGIES / $ELAPSED" | bc 2>/dev/null || echo "0")
        ETA=$(estimate_time $STRATEGIES $TOTAL $ELAPSED)
        
        echo "⚡ Speed: $RATE strategies/sec"
        echo "⏱️  Elapsed: $(date -u -r $ELAPSED +"%H:%M:%S" 2>/dev/null || echo "${ELAPSED}s")"
        echo "🕐 ETA: $ETA"
        echo ""
        
        # Show preview of results if we have enough data
        if [ $STRATEGIES -gt 100 ]; then
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "🏆 Top Strategies So Far (with 3+ trades):"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            
            # Get top 3 by win rate
            tail -n +2 "$CSV_FILE" | \
                awk -F',' '$4 >= 3 {printf "%5.1f%% WR | %2d trades | $%+6.2f PnL | Conf: %.2f | Vol: %.2f | Trend: %.2f | ADX: %d\n", $7*100, $4, $8, $14, $15, $16, $17}' | \
                sort -rn | \
                head -3 | \
                nl -w2 -s'. '
            
            echo ""
        fi
        
        # Check if complete
        if [ $STRATEGIES -ge $TOTAL ]; then
            echo ""
            echo "╔════════════════════════════════════════════════════════════════════════════╗"
            echo "║                            ✅ SEARCH COMPLETE!                             ║"
            echo "╚════════════════════════════════════════════════════════════════════════════╝"
            echo ""
            echo "📁 Results: $CSV_FILE"
            echo "📋 Summary: grid_search_results/eth_15m_complete_summary.json"
            echo ""
            echo "🎯 Next: Open CSV in Excel and sort by 'win_rate' to find 90%+ WR strategies"
            exit 0
        fi
    else
        echo "⏳ Initializing grid search..."
        echo ""
        echo "Waiting for CSV file to be created..."
    fi
    
    echo ""
    echo "💡 Press Ctrl+C to exit (search will continue in background)"
    
    sleep 2
done
