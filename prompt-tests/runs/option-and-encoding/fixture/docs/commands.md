# Commands

| Command | Switch | What it does |
| --- | --- | --- |
| `add <text>` | | Appends one entry stamped with the current UTC time |
| `list` | | Prints every entry, oldest first |
| `list` | `--limit <n>` | Prints only the last `n` entries |
| `count` | | Prints how many entries the store holds |

Every command takes `--store <path>`, defaulting to `./sample-store.json`.
