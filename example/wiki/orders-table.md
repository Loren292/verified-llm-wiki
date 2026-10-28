---
sources:
  - raw/orders.csv sha256:5a55063575c9
---
# The orders table

`raw/orders.csv`: one row per order. Each column is described from the data, not from its name.

## order_id

Unique, from 1001 to 1012, with no gaps.

## date

From 2026-09-01 to 2026-09-25, at most one order per day.

## amount

Order total in dollars, with two decimals, from $27.50 to $61.20. Whether it includes shipping
isn't in the data: [[T1]].

## status

Two values: `paid` (9 orders) and `refunded` (3), see [[H1]]. There is no value for a partial
refund.
