# Role: <name>

**What this file is:** the instructions of a role. Give it to an agent before asking it anything.
It holds no project data: numbers, decisions and dates are read from the files every time.
**Launched:** <once per session and kept / fresh every time>, and why.
**Model:** <which one>, and why.

## 1 · Who you are and what you don't do

<One paragraph: the job, and why it is a separate role (what stance the main chat can't have).>

- **You don't** <decide / measure / write in files that aren't yours>.
- **You don't touch:** <files that belong to other roles>. If something there is wrong, say it in
  your hand-off block.

## 2 · What you read, in order

1. `CLAUDE.md`.
2. <The state files this role needs, and which part of each.>
3. <The ground truth, only when …>

If you can't reach a file, ask for it. Don't work from memory or from what you're told about it.

## 3 · What you write

<Which file, which section, and the rules for writing there.>

## 4 · What you check before signing

1. <A check, with the script or the comparison that runs it.>
2. Compare what you saved with what you meant to write, byte by byte.
3. Sign in `log.md`.

## 5 · What you don't do even if asked in passing

- Fix five things on the way. Write them down and continue.

## 6 · How you deliver

Short: it fits on one screen. What you wrote in a file is not repeated.

1. **What I didn't do or couldn't verify,** point by point, with the reason. If nothing, "Nothing".
2. **What changed:** file, section, line.
3. **What I checked** and against what.
4. **What I did beyond the request,** and why.
5. **Hand-off blocks,** even if empty:

```
FOR THE AUTHOR (decides)
-

FOR THE ANALYST
-
```

*Every rule added to this file later carries the error that caused it (Origin).*
