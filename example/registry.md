# Registry

**Answers:** what was decided, found, asked and left pending, with its status. This file is only
tables: one row per ID. The *why* of each one lives in its own small page, `registry/<ID>.md`
(what, why, how, where else this is calculated, validation). The status lives only here, never in
the page. The chronology lives in `log.md`.

Decided and executed are separate states: "executed" needs evidence from the ground truth.

## Decisions

| ID | Decision | Status | Evidence | Page |
|---|---|---|---|---|
| D1 | Refunded orders are left out of orders, revenue and AOV | executed | `wiki/metrics.md` recomputed on `raw/orders.csv` (sha256 5a55063575c9), snapshot `2026-10-28 1415` | [[D1]] |
| D2 | Revenue and AOV are also shown by week | decided | — | — |

## Findings

| ID | Finding | Status | Evidence | Page |
|---|---|---|---|---|
| H1 | 3 of the 12 September orders were refunded | active | Counted in `raw/orders.csv`, column `status` | [[H1]] |

## Questions to third parties

| ID | Question, and what's at stake (measured) | Status | Evidence | Page |
|---|---|---|---|---|
| T1 | Does `amount` include shipping? If it does, every AOV figure includes the shipping fee | open | — | [[T1]] |

## Pending decisions

| ID | Decision to take, and what it blocks | Status | Evidence | Page |
|---|---|---|---|---|
| P1 | Report AOV with or without shipping. Blocks the final definition of AOV; waits for T1 | open | — | — |

## Superseded values

When a value is corrected, the old one goes here. `wikicheck lint` (check L4) searches every page
for it. To mention an old value on purpose somewhere else, mark that line `(old)`.

| Where | Old value | New value | Since | Why |
|---|---|---|---|---|
| `wiki/metrics.md`, Revenue | $516.50 | $374.60 | 2026-10-28 | D1 |
| `wiki/metrics.md`, AOV | $43.04 | $41.62 | 2026-10-28 | D1 |
