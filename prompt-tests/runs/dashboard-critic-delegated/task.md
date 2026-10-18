Hand this to a general-purpose subagent (Agent tool, subagent_type general-purpose, run_in_background false) with the request below as its prompt, word for word, then relay its result.

Use the decision-critic skill on this: we're about to pick SQLite over Postgres as the session store for our internal dashboard: one VM, about 40 users, nightly backups by copying the database file.
