I'm taking over a job someone else set up. I am not at the machine it runs on and
you have no way to reach it, so answer from the document — this is the plan file
they left behind:

{{ARTIFACT}}

The tree it refers to holds `records.csv` — one row per stored build artifact,
with `added` an epoch-seconds timestamp — alongside `prune.py` and
`settings.toml`. One thing whoever wrote that file had no way of knowing: the
nightly billing export reads `records.csv` at 02:00 and errors out on any id it
invoiced yesterday and cannot find today.

Tell me exactly what to do first.
