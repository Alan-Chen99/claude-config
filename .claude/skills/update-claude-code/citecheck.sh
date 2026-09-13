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

# `git ls-files` lists the tree below the *current* directory, so run from
# anywhere but the root and the scan quietly shrinks — from the skill's own
# directory it finds one citation, and reports that as cleanly as it reports
# all of them. Resolve the root from this script's own path instead of trusting
# the caller's cwd.
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)

mapfile -t cites < <(
    git -C "$REPO" ls-files -z \
        | (cd "$REPO" && xargs -0 grep -ohE 'chunk-[a-z0-9]+\.js:[0-9]+(-[0-9]+)?' 2>/dev/null) \
        | sort -u
)

# A floor, not a pin: citations are added and removed legitimately, so this is
# set well below the real count (137 as of 2.1.269) and exists only to catch a
# scan that collapsed. Without it, "checked one citation" and "checked every
# citation" are the same clean run.
FLOOR=100
if [ "${#cites[@]}" -lt "$FLOOR" ]; then
    echo "scan collapsed: ${#cites[@]} citations found under $REPO, expected >= $FLOOR" >&2
    exit 2
fi

fail=0
for cite in "${cites[@]}"; do
    f=${cite%%:*}; rest=${cite#*:}
    start=${rest%%-*}; end=${rest#*-}; [ "$end" = "$rest" ] && end=$start
    if [ ! -f "$D/$f" ]; then
        echo "MISSING FILE  $cite"; fail=1; continue
    fi
    # `wc -l` counts newlines, so it reports one short for a file whose last
    # line is unterminated — and then flags a citation to that real last line
    # as past EOF. `awk END{NR}` counts the line itself.
    n=$(awk 'END{print NR}' "$D/$f")
    if [ "$end" -gt "$n" ]; then
        echo "LINE PAST EOF $cite (file has $n lines)"; fail=1
    fi
done

exit "$fail"
