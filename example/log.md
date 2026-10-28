# Log

**Answers:** who changed what, and when. One line per write, appended at the end, with the time
read from the clock (never estimated). Earlier lines are never edited. Changes made by hand by a
person are signed with their name.

| When | Who | Files | What | Checked |
|---|---|---|---|---|
| 2026-10-28 13:40 | Store owner | all | Folder created from the verified-llm-wiki template; `raw/orders.csv` added (September export) | `wikicheck lint`: 0 candidates |
| 2026-10-28 13:55 | Claude, analyst chat (model unconfirmed) | `wiki/orders-table.md`, `registry.md`, `registry/H1.md`, `registry/T1.md`, `pending.md` | Measured `raw/orders.csv`; registered H1, T1 and P1 | `wikicheck lint`: 0 candidates; byte-compare ok |
| 2026-10-28 14:15 | Claude, analyst chat (model unconfirmed) | `wiki/metrics.md`, `registry.md`, `registry/D1.md`, `pending.md`, `snapshots/2026-10-28 1415.json` | D1 executed (refunds out); D2 registered as decided; old revenue and AOV moved to superseded values | D1 checks 3 of 3 as expected; `wikicheck lint`: 0; snapshot taken; byte-compare ok |
| 2026-10-28 14:16 | Claude, analyst chat (model unconfirmed) | `reviews/reviewer - metrics - 28-10.md` | Archived the cold review of the metrics page; finding 1 classified as real, fix pending the owner's OK | `wikicheck cite`: 2 of 2 citations ok, 0 problems |
