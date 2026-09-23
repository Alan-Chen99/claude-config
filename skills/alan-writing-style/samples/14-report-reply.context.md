Piece: a reply to a colleague, sent in a chat (a message to a person). Under 150 words.

Situation:
- The writer fixed the nightly supplier import on 2026-09-23 (the day in `10-12-import-day.log.md`) and posted the team status `11-team-status.human.md` that evening. Both are the material, and the writer knows both; nothing after 17:38 that day is known.
- Mira runs the weekly stock-age report off the same Postgres table the import upserts into. She read the status. She has not seen the branch or the log. Thursday morning, 2026-09-24, she writes in the team chat:

> Read your status, thanks. The weekly stock-age report runs off the same table and flags every SKU whose timestamp is older than 48 hours. Your note says SKUs that dropped out of the export keep the old naive value -- how many are those, and do they get fixed at some point? I would rather not filter them by hand every Monday.

- Nobody has counted the SKUs that are in the table but no longer in Norvell's export.
- A one-off migration shifting the old rows by the Berlin offset was proposed at 10:36 in the log and skipped at 10:38 ("every row gets overwritten tonight anyway"). That the upsert does not delete, so dropped SKUs keep the old value, was noticed only when the status was written.
- The import and its repo are the writer's; Tomas reviews the PR. A migration or a delete would be the writer's to write.
