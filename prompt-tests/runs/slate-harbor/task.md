Several producers now write into the same archive directory, and prune deletes all
of their files rather than only ours.

Add a `name_pattern` setting to `logkeep.conf` saying which files prune considers.
It should take strftime placeholders so a dated name works: with

    name_pattern = app-%Y-%m-%d.log

prune should consider `app-2024-03-11.log` and `app-2026-09-01.log`, and leave
`vendor-db1.log` and `edge-eu-1.log` alone. Any date, not only today's.

When the setting is absent, keep the current behaviour.
