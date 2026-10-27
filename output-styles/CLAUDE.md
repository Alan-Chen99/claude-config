# output-styles/

Output formatting styles. Since 2.1.269 a style arrives as a `role: "system"`
message in `messages[]`, not inside the system prompt; `README.md`, "Where the
style is delivered", governs.

## Files

| File                   | What                                           | When to read                                |
| ---------------------- | ---------------------------------------------- | ------------------------------------------- |
| `README.md`            | Design decisions, delivery, activation         | **Always read if working on output styles** |
| `alan-default-next.md` | Alan's style; unloaded while `outputStyle` is `default` | -                                  |
| `direct.md`            | Terse, fact-only style                         | -                                           |
