---
sources:
  - raw/orders.csv sha256:5a55063575c9
---
# Order metrics

September 2026, measured on `raw/orders.csv`. Refunded orders are left out ([[D1]]).

| Metric | Definition | Value |
|---|---|---|
| Orders | Count of paid orders | 9 |
| Revenue | Sum of `amount` over paid orders | $374.60 |
| Average order value (AOV) | Revenue / Orders | $41.62 |

## Limits

- `amount` may include shipping: asked as [[T1]]. Until it's answered, AOV is reported as is.
- A partial refund has no status of its own: see [[orders-table#status]].
