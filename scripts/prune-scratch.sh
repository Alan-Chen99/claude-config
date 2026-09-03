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
		;;
	*)
		echo "prune-scratch.sh: unknown argument: $1" >&2
		exit 2
		;;
	esac
	shift
done

# The root is derived, not supplied, but a wrong one would be deleted from just
# as happily. Refuse anything that is not the claude-<uid> directory this
# script constructs.
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
		printf '  %8s  %s\n' "$(du -sh "$pad" | cut -f1)" "$pad"
	done
	echo
fi

echo "prunable (empty): ${#empty[@]}"
echo "keep (non-empty): ${#kept[@]}"

if [ -n "$session" ]; then
	target="$(find "$root" -mindepth 2 -maxdepth 2 -type d -name "$session" -print -quit)"
	if [ -z "$target" ]; then
		echo "prune-scratch.sh: no session directory named $session under $root" >&2
		exit 1
	fi
	echo
	echo "session target: $target ($(du -sh "$target" | cut -f1))"
	if [ "$apply" -eq 0 ]; then
		echo "(dry run; re-run with --apply to delete it)"
		exit 0
	fi
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
	rmdir -- "$pad"
	rmdir --ignore-fail-on-non-empty -- "$(dirname "$pad")"
done
echo
echo "deleted ${#empty[@]} empty scratchpads"
