#!/bin/bash
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

SESSION=$(echo "$input" | jq -r '.session_id // empty' 2>/dev/null)

# Open tasks. `ps` prints nothing when nothing is running, so the row appears
# only when there is something to say. A failure must be visible: an empty line
# and a broken one are otherwise identical, and silence reads as "nothing is
# running".
TASKS=""
if [ -n "$SESSION" ]; then
    # `timeout`, because every row below shares one 5000 ms budget: a `ps`
    # that hangs takes the whole status line down with it, which is a louder
    # version of the same failure the fallback below exists to prevent. 2s is
    # comfortably inside the budget and far above what this costs even on a
    # session with a hundred captures. A timeout exits 124, so it lands in the
    # same branch every other failure does.
    if TASKS=$(timeout 2 agent-tools ps --format statusline --session-id "$SESSION" 2>/dev/null); then
        :
    else
        TASKS="▶ ?"
    fi
fi

COST_FMT=$(printf "%.4f" "$COST" 2>/dev/null || echo "0.0000")

# Absolute context usage in K
USED_TOKENS=$((CURR_IN + CURR_OUT + CACHE_WR + CACHE_RD))
USED_K=$((USED_TOKENS / 1000))

# Prompt cache, absent until the first API response. `|`-joined because read
# collapses adjacent tab separators, and a null field must stay in its slot.
CACHE_DETAIL=""
if [ -n "$(echo "$input" | jq -r '.prompt_cache // empty | "x"')" ]; then
    IFS='|' read -r PC_WARM PC_TTL PC_EXP PC_HIT PC_MISS PC_REQ PC_CAUSE < <(echo "$input" | jq -r '.prompt_cache
        | [.warm, .ttl, .expires_at, (.hit_ratio | if . == null then null else . * 100 | round end),
           .misses, .requests, (.last_miss_cause.causes // [] | join(","))]
        | map(if . == null then "" else tostring end) | join("|")')
    if [ "$PC_WARM" = true ]; then PC_STATE=warm; else PC_STATE=cold; fi
    # jq 1.8.1's strflocaltime prints UTC even with TZ set; date honours it
    [ -n "$PC_EXP" ] && PC_STATE="$PC_STATE until $(date -d "@$PC_EXP" '+%H:%M')"
    PC_HIT=${PC_HIT:+$PC_HIT%}
    CACHE_DETAIL=" | ${PC_TTL} ${PC_STATE} | hit ${PC_HIT:--} | ${PC_MISS}/${PC_REQ} miss"
    [ -n "$PC_CAUSE" ] && CACHE_DETAIL="$CACHE_DETAIL (last: $PC_CAUSE)"
fi

# Plan rate limits; cc omits a window it has no current reading for
LIMITS=""
while read -r LABEL PCT RESETS; do
    LIMITS="${LIMITS:+$LIMITS | }${LABEL} ${PCT}% (resets $(date -d "@$RESETS" '+%a %H:%M'))"
done < <(echo "$input" | jq -r '.rate_limits // {} | ["5h", .five_hour], ["7d", .seven_day]
    | select(.[1]) | "\(.[0]) \(.[1].used_percentage | round) \(.[1].resets_at)"')

# Shorten dir: replace $HOME with ~
DIR_SHORT=$(echo "$DIR" | sed "s|^$HOME|~|")

# Format output
printf "%s\n" "Context: ${USED_K}K | \$${COST_FMT} | ${MODEL}"
# printf "%s\n"
# printf "%s\n"
# printf "%s\n" "${DIR_SHORT}"
printf "%s\n" "Session: ${TOTAL_IN} in / ${TOTAL_OUT} out | Last: ${CURR_IN} in / ${CURR_OUT} out"
printf "%s\n" "Cache: ${CACHE_WR} write / ${CACHE_RD} read${CACHE_DETAIL}"
[ -n "$LIMITS" ] && printf "%s\n" "Limits: $LIMITS"
printf "%s\n" "${TRANSCRIPT}"
[ -n "$TASKS" ] && printf "%s\n" "$TASKS"

exit 0
