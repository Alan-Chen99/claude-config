#!/bin/bash
input=$(cat)

MODEL=$(echo "$input" | jq -r '.model.display_name // "?"')
# Absent on models without reasoning effort, where the model name stands alone
EFFORT=$(echo "$input" | jq -r '.effort.level // empty')
[ -n "$EFFORT" ] && MODEL="$MODEL ($EFFORT)"
# Absent until cc auto-names the session after its first prompt, or /rename
NAME=$(echo "$input" | jq -r '.session_name // empty')
PERCENT=$(echo "$input" | jq -r '.context_window.used_percentage // 0 | round')
COST=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
TRANSCRIPT=$(echo "$input" | jq -r '.transcript_path // empty')
SESSION=$(echo "$input" | jq -r '.session_id // empty')

# Context size is the last call's prompt plus its reply: what the next call
# starts from, unlike the session totals cc also sends.
USED_K=$(echo "$input" | jq -r '.context_window.current_usage // {}
    | ((.input_tokens // 0) + (.output_tokens // 0) + (.cache_creation_input_tokens // 0)
       + (.cache_read_input_tokens // 0)) / 1000 | floor')

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

# Cost split by token category. cc sends only the total, so this re-prices the
# transcript and its subagents' with cc 2.1.289's own table (model catalog
# `pricing_tiers`, $/Mtok); per-model prices rather than ratios, because cache
# read is 0.05x input on opus-5-5 but 0.1x elsewhere, and a session mixes models.
# `traced` is this sum over cc's total, shown when they differ by over 1%: a
# resumed session's transcript holds turns cc's total does not, and calls cc
# makes outside the transcript are invisible here.
BREAKDOWN="cost split ?"
COST_WARN=""
if [ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ]; then
    # 3s: a 44 MB transcript takes 0.75s, and the `ps` above holds the rest of
    # the 5000 ms budget.
    if SPLIT=$(find "$TRANSCRIPT" "${TRANSCRIPT%.jsonl}" -name '*.jsonl' -print0 2>/dev/null \
        | xargs -0 cat | timeout 3 jq -n -r --argjson total "$COST" '
        def tier: {
            t2_10:  {in: 2,   out: 10, w5: 2.5,   w1h: 4,   rd: 0.2},
            t3_15:  {in: 3,   out: 15, w5: 3.75,  w1h: 6,   rd: 0.3},
            t5_25:  {in: 5,   out: 25, w5: 6.25,  w1h: 10,  rd: 0.5},
            t15_75: {in: 15,  out: 75, w5: 18.75, w1h: 30,  rd: 1.5},
            t10_50: {in: 10,  out: 50, w5: 12.5,  w1h: 20,  rd: 1},
            t10_50r:{in: 10,  out: 50, w5: 12.5,  w1h: 20,  rd: 0.25},
            t4_20r: {in: 4,   out: 20, w5: 5,     w1h: 8,   rd: 0.2},
            h35:    {in: 0.8, out: 4,  w5: 1,     w1h: 1.6, rd: 0.08},
            h45:    {in: 1,   out: 5,  w5: 1.25,  w1h: 2,   rd: 0.1}};
        def models: {
            "claude-3-5-haiku": "h35", "claude-haiku-4-5": "h45",
            "claude-3-5-sonnet": "t3_15", "claude-3-7-sonnet": "t3_15",
            "claude-sonnet-4-0": "t3_15", "claude-sonnet-4-5": "t3_15", "claude-sonnet-4-6": "t3_15",
            "claude-sonnet-5": "t2_10", "claude-sonnet-5-5": "t2_10",
            "claude-opus-4-0": "t15_75", "claude-opus-4-1": "t15_75",
            "claude-opus-4-5": "t5_25", "claude-opus-4-6": "t5_25", "claude-opus-4-7": "t5_25",
            "claude-opus-4-8": "t5_25", "claude-opus-5": "t5_25", "claude-opus-5-5": "t4_20r",
            "claude-fable-5": "t10_50", "claude-fable-5-1": "t10_50r",
            "claude-mythos-5": "t10_50", "claude-mythos-5-1": "t10_50r"};
        # Fast mode doubles every rate on the models that offer it
        def fast: {"claude-opus-4-8": 2, "claude-opus-5": 2, "claude-opus-5-5": 2};
        # One API response is logged once per content block, each line
        # carrying the same usage, so responses are keyed by message id.
        (reduce (inputs | select(.type == "assistant" and .message.usage and .message.id))
            as $r ({}; .[$r.message.id] = {model: $r.message.model, u: $r.message.usage}))
        | [.[] | .u as $u
            | ($u.cache_creation_input_tokens // 0) as $cw
            | ([$u.cache_creation.ephemeral_1h_input_tokens // 0, $cw] | min) as $w1h
            | select(($u.input_tokens // 0) + ($u.output_tokens // 0) + $cw
                     + ($u.cache_read_input_tokens // 0) > 0)
            | (.model | sub("-[0-9]{8}$"; "")) as $m
            # cc prices an unknown model at tier_5_25 and so does this, named
            | (models[$m] // null) as $t
            | (tier[$t // "t5_25"]) as $p
            | ((if $u.inference_geo == "us" then 1.1 else 1 end)
               * (if $u.speed == "fast" then (fast[$m] // 1) else 1 end) / 1e6) as $k
            | {unpriced: (if $t then null else $m end),
               in: (($u.input_tokens // 0) * $p.in * $k),
               out: (($u.output_tokens // 0) * $p.out * $k),
               wr: ((($cw - $w1h) * $p.w5 + $w1h * $p.w1h) * $k),
               rd: (($u.cache_read_input_tokens // 0) * $p.rd * $k),
               web: (($u.server_tool_use.web_search_requests // 0) * 0.01)}]
        | (map(.unpriced) | map(select(.)) | unique) as $unpriced
        | {in: (map(.in) | add // 0), out: (map(.out) | add // 0), wr: (map(.wr) | add // 0),
           rd: (map(.rd) | add // 0), web: (map(.web) | add // 0)} as $c
        | ($c | add) as $sum
        | if $sum == 0 then "cost split -" else
            ([["in", $c.in, 75], ["out", $c.out, 213], ["wr", $c.wr, 214], ["rd", $c.rd, 114]]
              + (if $c.web > 0 then [["web", $c.web, 250]] else [] end)) as $cats
            | ($cats | map(.[1] / $sum * 100)) as $pct
            # Cumulative rounding, so the segments always fill exactly 12 cells
            | [foreach $pct[] as $p (0; . + $p; . * 12 / 100 | round)] as $ends
            | [range($cats | length) | {c: $cats[.][2], name: $cats[.][0], p: ($pct[.] | round),
                w: ($ends[.] - (if . == 0 then 0 else $ends[. - 1] end))}] as $seg
            | ($seg | map(select(.w > 0) | "\u001b[38;5;\(.c)m" + ("█" * .w)) | join("")) + "\u001b[39m "
            + ($seg | map("\u001b[38;5;\(.c)m\(.name)\u001b[39m \u001b[22m"
                + (.p | tostring | " " * (3 - length) + .) + "%\u001b[2m") | join(" "))
            + "\t"
            + (if $total > 0 and (($sum / $total - 1) | fabs) > 0.01
               then " \u001b[38;5;203mtraced \($sum / $total * 100 | round)%\u001b[39m" else "" end)
            + (if ($unpriced | length) > 0
               then " \u001b[38;5;203munpriced: \($unpriced | join(","))\u001b[39m" else "" end)
          end'); then
        IFS=$'\t' read -r BREAKDOWN COST_WARN <<<"$SPLIT"
    else
        BREAKDOWN="cost split ?"
    fi
fi

# cc renders every row dimmed and prefixes each row with all the escape codes
# of the rows above it, so styles here only ever change the foreground (closed
# by 39, never 0) or lift a value to normal intensity (22, then back to 2):
# a full reset would undim the rest of the row and leak into the next.
E=$'\e'
hi() { printf '%s' "$E[22m$1$E[2m"; }
fg() { printf '%s' "$E[38;5;$1m$2$E[39m"; }
RED=203; YELLOW=220; GREEN=114
# A usage percentage at normal intensity, yellow from 50, red from 80
level() {
    if [ "$1" -ge 80 ]; then fg $RED "$(hi "$2")"
    elif [ "$1" -ge 50 ]; then fg $YELLOW "$(hi "$2")"
    else hi "$2"; fi
}
case "$BREAKDOWN" in *\?) BREAKDOWN=$(fg $RED "$BREAKDOWN") ;; esac
[ "$TASKS" = "▶ ?" ] && TASKS=$(fg $RED "$TASKS")

# Prompt cache, absent until the first API response. `|`-joined because read
# collapses adjacent tab separators, and a null field must stay in its slot.
CACHE="cache -"
if [ -n "$(echo "$input" | jq -r '.prompt_cache // empty | "x"')" ]; then
    IFS='|' read -r PC_WARM PC_TTL PC_EXP PC_HIT PC_MISS PC_REQ PC_CAUSE < <(echo "$input" | jq -r '.prompt_cache
        | [.warm, .ttl, .expires_at, (.hit_ratio | if . == null then null else . * 100 | round end),
           .misses, .requests, (.last_miss_cause.causes // [] | join(","))]
        | map(if . == null then "" else tostring end) | join("|")')
    if [ "$PC_WARM" = true ]; then PC_STATE=warm; PC_COLOR=$GREEN; else PC_STATE=cold; PC_COLOR=$YELLOW; fi
    # jq 1.8.1's strflocaltime prints UTC even with TZ set; date honours it
    [ -n "$PC_EXP" ] && PC_STATE="$PC_STATE until $(date -d "@$PC_EXP" '+%H:%M')"
    PC_HIT=${PC_HIT:+$PC_HIT%}
    MISS=$(printf "%5s" "$PC_MISS/$PC_REQ")
    [ "${PC_MISS:-0}" -gt 0 ] && MISS=$(fg $YELLOW "$MISS")
    CACHE="cache $(printf %-2s "$PC_TTL") $(fg $PC_COLOR "$(printf %-16s "$PC_STATE")") │ hit $(hi "$(printf %4s "${PC_HIT:--}")") │ $MISS miss"
    [ -n "$PC_CAUSE" ] && CACHE="$CACHE (last: $PC_CAUSE)"
fi

# Plan rate limits; cc omits a window it has no current reading for
LIMITS=""
while read -r LABEL PCT RESETS; do
    LIMITS="$LIMITS │ $LABEL $(level "$PCT" "$(printf "%3s%%" "$PCT")") $(date -d "@$RESETS" '+%a %H:%M')"
done < <(echo "$input" | jq -r '.rate_limits // {} | ["5h", .five_hour], ["7d", .seven_day]
    | select(.[1]) | "\(.[0]) \(.[1].used_percentage | round) \(.[1].resets_at)"')

# Fixed-width fields first and the variable-length ones last, so each item
# sits in the same column in every session; cc truncates a row at the
# terminal's width, so the name is what a narrow window loses.
printf "%s\n" "ctx $(hi "$(printf %4s "${USED_K}K")") $(level "$PERCENT" "$(printf %3s%% "$PERCENT")") │ $(hi "$(printf %-8s "\$$(printf %.4f "$COST")")") $BREAKDOWN │ $(printf %-19s "$MODEL")${NAME:+ │ $(hi "$NAME")}"
printf "%s\n" "$CACHE$LIMITS"
# Cost warnings lead this row rather than follow the split, which would push
# the model and name off their columns whenever one appears
printf "%s\n" "${COST_WARN:+${COST_WARN# } │ }${TRANSCRIPT:-$(fg $RED "transcript ?")}"
[ -n "$TASKS" ] && printf "%s\n" "$TASKS"

exit 0
