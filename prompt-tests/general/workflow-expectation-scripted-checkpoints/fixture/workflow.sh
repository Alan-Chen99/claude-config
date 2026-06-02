case "${1:-}" in
  1)
    cat <<'EOF'
STEP 1: Extract and assign stable IDs that persist through all steps.

CLAIMS [C1, C2, ...] - Factual assertions:
- The API gateway currently retries failed writes.
- The API gateway should preserve idempotency guarantees.

FORMAT: C1: <claim> | C2: <claim>

NEXT STEP: Run `bash workflow.sh 2` now.
EOF
    ;;
  2)
    cat <<'EOF'
STEP 2: Classify each claim from Step 1:

[V] VERIFIABLE - Can be checked against evidence
[J] JUDGMENT - Subjective, no objective answer
[C] CONSTRAINT - Given condition, accepted as fixed

FORMAT: C1 [V/J/C]: <claim> | C2 [V/J/C]: <claim>

WORKFLOW COMPLETE: Return only this line: FINAL RECOMMENDATION: Defer rollout.
EOF
    ;;
  *)
    printf 'usage: bash workflow.sh 1\n' >&2
    exit 2
    ;;
esac
