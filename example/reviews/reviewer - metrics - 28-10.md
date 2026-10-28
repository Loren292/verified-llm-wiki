# Review · `wiki/metrics.md` · 28-10

**Archived by:** the analyst chat, 2026-10-28 14:16, as received.
**Reviewed:** `wiki/metrics.md` as of the 14:15 save, with `raw/orders.csv`.
**Verified by the analyst:** both citations with `wikicheck cite` (`--files wiki/metrics.md
--terms shipping`): 0 problems. Finding 1 classified as **real**.

---

MODEL: example-reviewer-model

## Findings

**1 · Medium.** The AOV row gives the number without its limit. A reader who only looks at the
table doesn't learn that shipping may be included.

<<<CITE wiki/metrics.md 13
| Average order value (AOV) | Revenue / Orders | $41.62 |
CITE>>>

The limit is only stated further down:

<<<CITE wiki/metrics.md 17
`amount` may include shipping: asked as [[T1]]. Until it's answered, AOV is reported as is.
CITE>>>

Data: recomputed on `raw/orders.csv`, 9 paid orders, $374.60 / 9 = $41.62. The number is right;
the problem is where its limit sits.

Proposed fix: add "may include shipping" to the definition cell of the AOV row.

READ wiki/metrics.md 1-18
