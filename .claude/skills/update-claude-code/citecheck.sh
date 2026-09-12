#!/usr/bin/env bash
# Every `chunk-<hash>.js:<line>` citation in tracked files must resolve in the
# decompiled tree. Prints one line per unresolved citation; exits 1 if any.
#
# Resolution here means the file exists and is at least that long. It does NOT
# mean the line still says what the citing text claims — chunk hashes and line
# numbers both rotate per build, so a citation can resolve and still be wrong.
set -uo pipefail
D=${1:-/repos/claude-code-decompiled/src}
[ -d "$D" ] || { echo "decompiled tree not found: $D" >&2; exit 2; }

fail=0
while IFS= read -r cite; do
    f=${cite%%:*}; rest=${cite#*:}
    start=${rest%%-*}; end=${rest#*-}; [ "$end" = "$rest" ] && end=$start
    if [ ! -f "$D/$f" ]; then
        echo "MISSING FILE  $cite"; fail=1; continue
    fi
    n=$(wc -l < "$D/$f")
    if [ "$end" -gt "$n" ]; then
        echo "LINE PAST EOF $cite (file has $n lines)"; fail=1
    fi
done < <(git ls-files -z | xargs -0 grep -ohE 'chunk-[a-z0-9]+\.js:[0-9]+(-[0-9]+)?' 2>/dev/null | sort -u)

exit "$fail"
