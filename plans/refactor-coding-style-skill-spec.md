`alan-coding-style` skill is supposed to mirrored after `/repos/claude-config/skills/scripts/skills/leon_writing_style/writing_style.py`.

Currently, this failed to be the case, did not follow "best practices" of agent instrutions, and have problems "duplicate content" reported by executing agnets.

We will refactor to fix this. Requirements:

MUST: **script output** matches `leon_writing_style` in organization. `leon_writing_style` uses XML tags -> use XML tags. `leon_writing_style` does not reference file paths -> do not reference file paths
MUST: the **implmentation** is still markdown-file based. Optimized for maintainability and cleaness rather than to match `leon_writing_style`
MUST: the bulk of the style text/instruction lives in committed markdown files
MUST: **implmentation** does not leak into **runtime behavior** experienced by executing agents

**change scope**
Current script, style ref markdowns, shared skill infra (if suitable), all related documentation in this project
out of scope: `leon_writing_style`
