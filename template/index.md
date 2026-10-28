# Index

**Answers:** what's in this folder and what each file is for. One line per file; a path ending
in `/` covers a whole folder. It keeps no state and no numbers: those live in the files it names.

**Rule:** whoever creates, renames, deletes or retires a file updates this list in the same move.
`wikicheck lint` (check L1) flags any mismatch between this list and the folder.

**Types:** state (read at the start) · page (a topic, entity or concept) · method (how work is
done) · block (one-shot instructions, deleted once executed) · reference (read, not maintained) ·
source (ground truth, never edited) · log (append-only)

## State

| Path | Type | Answers |
|---|---|---|
| `pending.md` | state | What's left to do. Short, only what's open. Read first |
| `registry.md` | state | Only tables: each D, H, T and P with its status, evidence and page, plus superseded values |
| `registry/` | state | One small page per ID with its why. Open only the ones the work item touches |
| `log.md` | log | Who changed what and when: the chronology. Read only its last lines before writing |

## Pages

| Path | Type | Answers |
|---|---|---|
| `wiki/` | page | The wiki pages, one subject per page |

## Method

| Path | Type | Answers |
|---|---|---|
| `CLAUDE.md` | method | How this wiki is maintained: order of truth, rules, cycle, scripts, agents and workflows |
| `index.md` | method | This file |
| `roles/writer.md` | method | Instructions for an agent that writes documents from fact sheets |
| `roles/reviewer.md` | method | Instructions for an agent that reviews cold |
| `roles/TEMPLATE.md` | method | Skeleton for a new role |
| `workflows/TEMPLATE.md` | method | Skeleton for a step-by-step workflow with a check per step |

## Ground truth and records

| Path | Type | Answers |
|---|---|---|
| `raw/` | source | The ground truth. Never edited |
| `snapshots/` | log | One hash snapshot of `raw/` per verified change. Never edited or deleted |
| `reviews/` | reference | Reviewers' reports, archived as received, with a header of what was verified |
