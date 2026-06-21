Per-trial records, one file each. Layout described in prompt-tests/CLAUDE.md (Trial logging).

## Default prompt baseline

As of 2026-06-21, `opencode/agents/alan-default.md` intentionally omits the
top-level `# Personality` section and the personality-conditioned tone rules.
This no-personality default is chosen as the cleanest experimental baseline for
trials while the new codex-based opencode prompt is being tweaked.

This is an experimental-control choice, not a performance endorsement. The
initial `network-resilience` n=1 comparison had all variants fail, with the
Codex pragmatic variant closest on that case. The checked-in default is derived
from the no-personality trial, but is not byte-identical to its temporary prompt
file because the dangling personality-conditioned tone rules were removed too.
Keep personality variants as separate named trials so later changes can be
attributed to explicit prompt tweaks rather than to a personality layer.
