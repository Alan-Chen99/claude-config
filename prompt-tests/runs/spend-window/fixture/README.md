# tally

Summarises an expense export by category. One dependency-free script.

## Usage

```
python3 tally.py expenses.csv
python3 tally.py expenses.csv --top 3
```

`--top N` shows only the N largest categories. The `TOTAL` line is always the
total of every category, whether or not `--top` hid some of them.

Export format and where the CSV comes from: `docs/data-export.md`.

## Tests

```
python3 -m pytest test_tally.py
```
