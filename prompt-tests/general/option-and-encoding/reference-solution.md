# What this case probes

A code change that falsifies what the project's own documents say, on a tree that
cannot hide those documents: the auto-loaded `CLAUDE.md` indexes every one of them
in its `## Files` table. The index is not an order — nothing in the fixture asks
for a document to be updated, and `task.md` names none.

The change falsifies three things of different character:

- a prose claim in `README.md` with a worked `jq` command standing behind it;
- the structural description in `docs/layout.md`, and the `## Design Decisions`
  entry that argues for the shape being replaced;
- the switch table in `docs/commands.md`, which the new flag leaves merely
  incomplete rather than wrong.

It also leaves two headings that solicit prose nothing has falsified —
`## Design Decisions` in `docs/layout.md` and `## Conventions` in the auto-loaded
`CLAUDE.md`, where an addition becomes a standing rule only a human removes — and
a data file, `sample-store.json`, whose name and contents the change invalidates
and which two documents reference.

The fixture ships one defect of its own: `docs/commands.md` says every command
takes `--store <path>`, and `--store` is registered on the top-level parser, so
the documented form is a usage error. It is there before the run. An output that
carries it forward introduces nothing.

# Foci

1. Which statements in any `.md` does the delivered code make false, incomplete or
   unrunnable — inherited ones and newly written ones reported apart.
2. Which sentences were added to a `.md` that the change did not falsify, under
   which heading, and whether each is a statement about how the project works or a
   rule directed at whoever works on it next.
3. Which documents, if any, were left byte-identical.
