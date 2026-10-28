# Workflow: <what it builds or changes>

**What it is:** <one line>.
**Applies:** <the decision it carries out, linked to its registry page>.
**Written against:** <snapshot or version of the ground truth it assumes>. If the ground truth
changed since then, check the diff before starting.
**Type:** method if it's reused, block if it's one-shot (deleted once executed and verified; the
registry page keeps what it did).

---

## Part 0 · Before starting: write down the numbers that must not move

| # | Where | What | Before | After |
|---|---|---|---|---|
| 1 | | | | |

## Part 1 · <first step>

1. <Small action.>
2. <Small action.>

**Check 1.** <What to look at>: it must show **<expected value>**. If it doesn't: <stop and undo /
tell the analyst>; don't go on.

## Part 2 · <next step>

…

**Check 2.** …

---

## Final checks

| # | Where | Expected | If it fails |
|---|---|---|---|
| C1 | <tool or file> | The numbers of Part 0 are the same before and after | Something depended on what changed: undo and report |
| C2 | `wikicheck lint` | 0 candidates | Read each one before closing |
| C3 | `wikicheck snapshot` | Only the expected files changed | Find out why before registering "executed" |

Checks must fail loudly: an expected value that moves with the clock (today's date, the last row)
always passes and checks nothing.
