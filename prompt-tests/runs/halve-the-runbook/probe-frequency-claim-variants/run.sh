#!/bin/bash
# One stock reader, fresh CLAUDE_CONFIG_DIR so no memory carries between runs.
q=$1; a=$2; n=$3
d=$(mktemp -d /root/.claude/tmp/pfc-XXXXXX)
CLAUDE_CONFIG_DIR="$d" claude -p --model opus < "p-$q-$a.txt" > "reader-$q-$a$n.txt" 2>&1
echo "$q-$a$n exit=$? mem=$(find "$d" -path '*memory*' -type f 2>/dev/null | wc -l)"
rm -rf "$d"
