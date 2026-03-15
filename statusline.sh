#\!/bin/bash
input=$(cat)

# Extract all values
MODEL=$(echo "$input" | jq -r '.model.display_name // "?"')
PERCENT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' 2>/dev/null)
COST=$(echo "$input" | jq -r '.cost.total_cost_usd // 0' 2>/dev/null)
DIR=$(echo "$input" | jq -r '.workspace.current_dir // "?"')

# Token metrics
TOTAL_IN=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0' 2>/dev/null)
TOTAL_OUT=$(echo "$input" | jq -r '.context_window.total_output_tokens // 0' 2>/dev/null)
CURR_IN=$(echo "$input" | jq -r '.context_window.current_usage.input_tokens // 0' 2>/dev/null)
CURR_OUT=$(echo "$input" | jq -r '.context_window.current_usage.output_tokens // 0' 2>/dev/null)
CACHE_WR=$(echo "$input" | jq -r '.context_window.current_usage.cache_creation_input_tokens // 0' 2>/dev/null)
CACHE_RD=$(echo "$input" | jq -r '.context_window.current_usage.cache_read_input_tokens // 0' 2>/dev/null)
TRANSCRIPT=$(echo "$input" | jq -r '.transcript_path // "N/A"' 2>/dev/null)

COST_FMT=$(printf "%.4f" "$COST" 2>/dev/null || echo "0.0000")

# Context window capacity and absolute usage in K
CAPACITY=$(echo "$input" | jq -r '.context_window.capacity // 0' 2>/dev/null)
CAPACITY_K=$((CAPACITY / 1000))
USED_TOKENS=$((CURR_IN + CURR_OUT + CACHE_WR + CACHE_RD))
USED_K=$((USED_TOKENS / 1000))

# Shorten dir: replace $HOME with ~
DIR_SHORT=$(echo "$DIR" | sed "s|^$HOME|~|")

# Format output
printf "%s\n" "Context: ${USED_K}K | \$${COST_FMT} | ${MODEL}"
# printf "%s\n"
# printf "%s\n"
# printf "%s\n" "${DIR_SHORT}"
printf "%s\n" "Session: ${TOTAL_IN} in / ${TOTAL_OUT} out | Last: ${CURR_IN} in / ${CURR_OUT} out"
printf "%s\n" "Cache: ${CACHE_WR} write / ${CACHE_RD} read"
printf "%s\n" "${TRANSCRIPT}"
