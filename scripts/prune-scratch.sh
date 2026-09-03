#!/usr/bin/env bash
# Report and optionally delete session scratchpads under cc's tmp root.
#
# The contract: deletes only empty scratchpads unless a session is named
# with --session, never follows a symlink found while descending into the
# tree (only $root itself may be a symlink), and does nothing without
# --apply.
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

root="${CLAUDE_CODE_TMPDIR:-/tmp}/claude-$(id -u)"

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
	esac
	case "$1" in
	*/*)
		echo "prune-scratch.sh: --session id '$1' must not contain '/'" >&2
		exit 2
		;;
	esac
	case "$1" in
	*\\*)
		echo "prune-scratch.sh: --session id '$1' must not contain a backslash" >&2
		exit 2
		;;
	esac
	case "$1" in
	*'*'*)
		echo "prune-scratch.sh: --session id '$1' must not contain '*'" >&2
		exit 2
		;;
	esac
	case "$1" in
	*'?'*)
		echo "prune-scratch.sh: --session id '$1' must not contain '?'" >&2
		exit 2
		;;
	esac
	case "$1" in
	*'['*)
		echo "prune-scratch.sh: --session id '$1' must not contain '['" >&2
		exit 2
		;;
	esac
}

# Establishes that the target *resolves* to a path inside the *resolved*
# root -- not that its literal string is prefixed by $root's literal
# string, which any symlinked component (a project slug, or $root itself)
# defeats trivially, and not "the value is safe" in any broader sense.
# Resolving both sides also means a deliberately symlinked root is
# permitted (its resolved content is still genuinely inside the resolved
# root), while a symlink planted inside a real root and pointing
# elsewhere is still refused -- a distinction a plain string-prefix match
# cannot make.
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
# --session, so the two now agree on what a symlinked root contains,
# which they did not before -H replaced the previous bare find "$root".
#
# Two asymmetries remain, left deliberately unaddressed rather than
# overlooked: a dot-named project directory is visible to this scan but
# invisible to --session's "$root"/*/ glob (no dotglob) -- cc's slugs
# always start with '-', never '.', so this is a false negative only; and
# $root itself is followed here while nothing inside it is, an asymmetry
# by design: the root is what the user deliberately pointed at, the tree
# beneath it is not.
empty=()
kept=()
while IFS= read -r -d '' pad; do
	if [ -z "$(ls -A "$pad")" ]; then
		empty+=("$pad")
	else
		kept+=("$pad")
	fi
done < <(find -H "$root" -mindepth 3 -maxdepth 3 -type d -name scratchpad -print0)

if [ ${#kept[@]} -gt 0 ]; then
	echo "keep (non-empty):"
	for pad in "${kept[@]}"; do
		printf '  %8s  %s\n' "$(du -sh -- "$pad" | cut -f1 | head -1)" "$pad"
	done
	echo
fi

echo "prunable (empty): ${#empty[@]}"
echo "keep (non-empty): ${#kept[@]}"

if [ -n "$session" ]; then
	targets=()
	# "$root"/*/ is a bash glob, not find: it will not match a dot-named
	# project directory (no dotglob), so a session under one would be
	# invisible here even though the find-based scan above has no such
	# exclusion. False negative only -- cc's slugs always start with '-',
	# never '.' -- so this is left deliberately unaddressed.
	for proj in "$root"/*/; do
		[ ! -L "${proj%/}" ] && [ -d "$proj$session" ] && [ ! -L "$proj$session" ] && targets+=("$proj$session")
	done
	if [ ${#targets[@]} -eq 0 ]; then
		echo "prune-scratch.sh: no session directory named $session under $root" >&2
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
