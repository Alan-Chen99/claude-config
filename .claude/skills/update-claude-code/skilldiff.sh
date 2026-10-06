#!/usr/bin/env bash
# The skills vendored from the Claude Code binary must match the assets of the
# extracted build. Asset filenames are content hashes that rotate per build, so
# each is found by its `name:` frontmatter line. Prints one line per skill that
# drifted or has no asset; exits 1 if any, 2 without an extracted tree.
# `--update` replaces each tracked copy with the extract's text instead — the
# only sanctioned way to change them.
#
# Matching the asset is not matching the built-in, and only for artifact-design:
# its loader splices a dataviz callout into the asset's `<!-- dataviz-callout -->`
# line behind a server flag, then under CLAUDE_CODE_ARTIFACT_TOOLSET prefixes a
# page contract and swaps one phrase (`Est`, src/chunk-h86mqzg4.js:59, calling
# `RTo`, src/chunk-sye9h7es.js:259). artifact-diagramming is loaded verbatim, so
# its copy does say what the built-in says. This checks the body the asset holds,
# nothing else; the loader read that covers the rest is unconditional at every
# upgrade (SKILL.md, section 4).
set -uo pipefail
A=${ASSETS:-/repos/claude-code-decompiled/assets}
[ -d "$A" ] || { echo "decompiled assets not found: $A" >&2; exit 2; }
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)

# Add a name here when vendoring another built-in skill; nothing detects an
# unlisted copy.
VENDORED=(artifact-design artifact-diagramming)

update=0; [ "${1:-}" = "--update" ] && update=1
fail=0; ok=0
for name in "${VENDORED[@]}"; do
    mapfile -t hits < <(grep -l -x "name: $name" "$A"/SKILL-*.md 2>/dev/null)
    if [ "${#hits[@]}" -ne 1 ]; then
        echo "NO ASSET  $name (${#hits[@]} candidates under $A)"; fail=1; continue
    fi
    src=${hits[0]}; dst="$REPO/skills/$name/SKILL.md"
    if cmp -s "$src" "$dst"; then ok=$((ok+1)); continue; fi
    if [ "$update" = 1 ]; then
        cp "$src" "$dst" && { echo "UPDATED   $name <- ${src##*/}"; ok=$((ok+1)); }
    else
        echo "DRIFT     $name != ${src##*/}"; fail=1
    fi
done
[ "$fail" = 0 ] && echo "OK: $ok vendored skill(s) match the extract"
exit "$fail"
