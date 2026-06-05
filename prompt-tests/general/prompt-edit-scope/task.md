Below is a system prompt for an agent that helps users edit code:

```
You help users edit code. When the user asks you to make a change, identify the file, make the change, and report what you did.
```

When the user said "rename `foo` to `bar` in `utils.py`", the agent ran `sed -i 's/foo/bar/g' utils.py`, which also renamed `food` to `bard` and `foobar` to `barbar`.

Edit the prompt to fix this issue. Output the full edited prompt in your response.
