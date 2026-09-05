#!/usr/bin/env bash
# Report and optionally delete session scratchpads under cc's tmp root.
#
# The contract: deletes only empty scratchpads unless a session is named
# with --session (and removes the parent session directory too, when the
# scratchpad was its only child), never follows a symlink found while
# descending into the tree (only $root itself may be a symlink), and does
# nothing without --apply.
#
# --session has no liveness check: a session id alone does not distinguish
# a dead session from one a live agent is still using, so --session <id>
# --apply deletes a running agent's scratch exactly as readily as a dead
# one's, with no warning either way.
#
# Exit codes: 0 success (including "nothing to do" and dry runs); 1 the
# named session could not be found, was ambiguous, or was refused for
# being (or sitting under) a symlink; 2 a bad argument, a bad --session
# id, or an unexpected scratch root.
#
# Nothing here runs automatically. Redirecting CLAUDE_CODE_TMPDIR onto
# persistent disk means scratch no longer evaporates when the container is
# rebuilt, and this script is the only thing that reclaims it.
#
#   prune-scratch.sh                 report only (default)
#   prune-scratch.sh --apply         delete empty scratchpads
#   prune-scratch.sh --session <id> --apply
#                                    delete that session even if non-empty
set -euo pipefail

# Resolves the root the same way src/claude_config/env_context/scratchpad.py's
# tmp_root() does: CLAUDE_CODE_TMPDIR when set and non-empty, else
# tempfile.gettempdir(), which checks $TMPDIR ahead of a bare /tmp default.
# A bare shell `${CLAUDE_CODE_TMPDIR:-/tmp}` expansion does not honour
# $TMPDIR at all, so with CLAUDE_CODE_TMPDIR unset and TMPDIR=/var/tmp, the
# hook named /var/tmp/claude-0/... while this script scanned /tmp/claude-0
# -- reporting "no scratch root; nothing to do" over a tree that was
# actually growing. Calling scratchpad.py directly, instead of
# reimplementing gettempdir()'s search order a third time here, is what
# keeps this script and the hook from being able to disagree about which
# tree "the" scratch root names again.
#
# A bare python3 (not `uv run`, which check-env-context.sh uses elsewhere
# in this repo) is enough: scratchpad.py imports only the stdlib, so this
# one call needs no project sync or venv resolution, and adds no
# dependency beyond a python3 already on PATH -- and, unlike `uv run`,
# doesn't require a synced venv to exist for a plain, no-op report run.
repo_root="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"
tmp_prefix="$(PYTHONPATH="$repo_root/src" python3 -c '
from claude_config.env_context.scratchpad import tmp_root
print(tmp_root())
')"
root="$tmp_prefix/claude-$(id -u)"

# Mirrors src/claude_config/env_context/scratchpad.py's _validate_session_id:
# empty, '.', and '..' collide sessions onto each other or escape the tree,
# and '/' or '\' escape it outright. '*', '?', and '[' are rejected too,
# because those are exactly what let a --session value be read as a find
# -name glob rather than the literal id this flag documents -- which is
# what let --session 'session-*' resolve to an unintended, non-empty
# session below. The targeting code no longer uses find -name at all, but
# rejecting the glob characters here means a stray one is caught even if
# some future caller reintroduces a pattern-matching lookup.
validate_session_id() {
	case "$1" in
	"" | . | ..)
		echo "prune-scratch.sh: --session id must not be empty, '.', or '..'" >&2
		exit 2
		;;
	*/*)
		echo "prune-scratch.sh: --session id '$1' must not contain '/'" >&2
		exit 2
		;;
	*\\*)
		echo "prune-scratch.sh: --session id '$1' must not contain a backslash" >&2
		exit 2
		;;
	*'*'*)
		echo "prune-scratch.sh: --session id '$1' must not contain '*'" >&2
		exit 2
		;;
	*'?'*)
		echo "prune-scratch.sh: --session id '$1' must not contain '?'" >&2
		exit 2
		;;
	*'['*)
		echo "prune-scratch.sh: --session id '$1' must not contain '['" >&2
		exit 2
		;;
	esac
}

# A backstop, not the primary guard: find -H and the two -L gates below
# already refuse to enumerate a symlinked project or session before this
# is ever called, so every call site here is currently a no-op that takes
# the empty first branch. It stays because whatever changes next should
# still have to defeat this to reach rm/rmdir -- resolving both sides
# means a deliberately symlinked root is permitted (its resolved content
# is still genuinely inside the resolved root), while a symlink planted
# inside a real root and pointing elsewhere is still refused, a
# distinction a plain string-prefix match cannot make.
assert_under_root() {
	case "$(readlink -f -- "$1")" in
	"$(readlink -f -- "$root")"/*) ;;
	*)
		echo "prune-scratch.sh: refusing to touch path outside scratch root: $1" >&2
		exit 2
		;;
	esac
}

apply=0
session=""
while [ $# -gt 0 ]; do
	case "$1" in
	--apply) apply=1 ;;
	--session)
		shift
		session="${1:-}"
		[ -n "$session" ] || {
			echo "prune-scratch.sh: --session needs an id" >&2
			exit 2
		}
		validate_session_id "$session"
		;;
	*)
		echo "prune-scratch.sh: unknown argument: $1" >&2
		exit 2
		;;
	esac
	shift
done

# root is built one line above as "<prefix>/claude-<uid>", so this check
# can never actually fail today: it is not a defense against a mistyped or
# wrong CLAUDE_CODE_TMPDIR, which becomes <prefix> and passes through
# regardless of its value. It exists only to catch a future edit that lets
# $root diverge from that suffix (e.g. an added --root override).
case "$root" in
*/claude-"$(id -u)") ;;
*)
	echo "prune-scratch.sh: refusing to operate on unexpected root: $root" >&2
	exit 2
	;;
esac

if [ ! -d "$root" ]; then
	echo "prune-scratch.sh: no scratch root at $root; nothing to do"
	exit 0
fi

echo "scratch root: $root"
echo

# -H follows a symlink only when it is the command-line argument itself,
# so a deliberately relocated $root (CLAUDE_CODE_TMPDIR pointed through a
# symlink) is scanned as if it were real, while a symlink encountered
# while descending -- a project slug, a session -- is left alone. That is
# the same rule assert_under_root and the project-loop guard enforce for
# --session, so the two now agree on what a symlinked root contains.
#
# Scanned at session depth (2), not scratchpad depth (3): --session
# deletes the whole session directory, so the report needs to cover what
# --session actually acts on, not just the scratchpad inside it -- a
# session holding no scratchpad at all (e.g. one with only a tasks/
# directory) is still a real --session target and must not be invisible
# here.
#
# Two asymmetries remain, left deliberately unaddressed rather than
# overlooked: a dot-named project directory is visible to this scan but
# invisible to --session's "$root"/*/ glob below (no dotglob; cc's slugs
# always start with '-', never '.', so this is a false negative only);
# and $root itself is followed here while nothing inside it is, by
# design -- the root is what the user deliberately pointed at, the tree
# beneath it is not.
empty=()
kept=()
noscratch=()
while IFS= read -r -d '' sess; do
	pad="$sess/scratchpad"
	if [ ! -d "$pad" ]; then
		noscratch+=("$sess")
	elif [ -z "$(ls -A "$pad")" ]; then
		empty+=("$pad")
	else
		kept+=("$pad")
	fi
done < <(find -H "$root" -mindepth 2 -maxdepth 2 -type d -print0)

if [ ${#kept[@]} -gt 0 ]; then
	echo "keep (non-empty):"
	for pad in "${kept[@]}"; do
		printf '  %8s  %s\n' "$(du -sh -- "$pad" | cut -f1 | head -1)" "$pad"
	done
	echo
fi

if [ ${#noscratch[@]} -gt 0 ]; then
	echo "no scratchpad (not touched by bulk --apply; --session <id> --apply removes the whole thing):"
	for sess in "${noscratch[@]}"; do
		printf '  %8s  %s\n' "$(du -sh -- "$sess" | cut -f1 | head -1)" "$sess"
	done
	echo
fi

echo "prunable (empty): ${#empty[@]}"
echo "keep (non-empty): ${#kept[@]}"
echo "no scratchpad: ${#noscratch[@]}"

if [ -n "$session" ]; then
	targets=()
	symlinked_sessions=()
	symlinked_projects=()
	# "$root"/*/ is a bash glob and will not match a dot-named project
	# directory -- see the scan comment above for why that's left alone.
	for proj in "$root"/*/; do
		[ -d "$proj$session" ] || continue
		if [ -L "${proj%/}" ]; then
			symlinked_projects+=("$proj$session")
		elif [ -L "$proj$session" ]; then
			symlinked_sessions+=("$proj$session")
		else
			targets+=("$proj$session")
		fi
	done
	if [ ${#targets[@]} -eq 0 ]; then
		for t in "${symlinked_sessions[@]}"; do
			echo "prune-scratch.sh: refusing $t: the session directory is a symlink" >&2
		done
		for t in "${symlinked_projects[@]}"; do
			echo "prune-scratch.sh: refusing $t: its project directory is a symlink" >&2
		done
		if [ ${#symlinked_sessions[@]} -eq 0 ] && [ ${#symlinked_projects[@]} -eq 0 ]; then
			echo "prune-scratch.sh: no session directory named $session under $root" >&2
		fi
		exit 1
	fi
	if [ ${#targets[@]} -gt 1 ]; then
		echo "prune-scratch.sh: --session id $session is ambiguous; found under more than one project:" >&2
		for t in "${targets[@]}"; do
			echo "  $t" >&2
		done
		exit 1
	fi
	target="${targets[0]}"
	echo
	echo "session target: $target ($(du -sh -- "$target" | cut -f1 | head -1))"
	if [ "$apply" -eq 0 ]; then
		echo "(dry run; re-run with --apply to delete it)"
		exit 0
	fi
	assert_under_root "$target"
	rm -rf -- "$target"
	echo "deleted $target"
	exit 0
fi

if [ "$apply" -eq 0 ]; then
	echo
	echo "(dry run; re-run with --apply to delete the ${#empty[@]} empty ones)"
	exit 0
fi

deleted=0
skipped=0
for pad in "${empty[@]}"; do
	assert_under_root "$pad"
	# ls -A's output above is run through $(...), which strips trailing
	# newlines, so a scratchpad whose only entry is a file named entirely
	# of newline bytes reads as empty there even though it is not. rmdir
	# is the real guard against that misclassification; tolerate its
	# refusal here rather than let set -e abort the loop with no summary
	# after whatever was already deleted.
	if ! rmdir -- "$pad" 2>/dev/null; then
		skipped=$((skipped + 1))
		echo "prune-scratch.sh: skipped $pad: not actually empty (rmdir refused)" >&2
		continue
	fi
	parent="$(dirname "$pad")"
	assert_under_root "$parent"
	rmdir --ignore-fail-on-non-empty -- "$parent"
	deleted=$((deleted + 1))
done
echo
echo "deleted $deleted empty scratchpads"
if [ "$skipped" -gt 0 ]; then
	echo "skipped $skipped (not actually empty)"
fi
