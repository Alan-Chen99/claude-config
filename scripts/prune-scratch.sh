#!/usr/bin/env bash
# Report and optionally delete session scratchpads under cc's tmp root.
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

# The check that actually earns its place: no path reaches rm/rmdir without
# first being proven a descendant of $root, regardless of how it was
# enumerated -- a real invariant about the value being deleted, unlike the
# claude-<uid> suffix check below, which is about how $root was assembled.
assert_under_root() {
	case "$1" in
	"$root"/*) ;;
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

empty=()
kept=()
while IFS= read -r -d '' pad; do
	if [ -z "$(ls -A "$pad")" ]; then
		empty+=("$pad")
	else
		kept+=("$pad")
	fi
done < <(find "$root" -mindepth 3 -maxdepth 3 -type d -name scratchpad -print0)

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
	for proj in "$root"/*/; do
		[ -d "$proj$session" ] && targets+=("$proj$session")
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

for pad in "${empty[@]}"; do
	assert_under_root "$pad"
	rmdir -- "$pad"
	parent="$(dirname "$pad")"
	assert_under_root "$parent"
	rmdir --ignore-fail-on-non-empty -- "$parent"
done
echo
echo "deleted ${#empty[@]} empty scratchpads"
