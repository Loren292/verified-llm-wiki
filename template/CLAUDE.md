# Schema: how this wiki is maintained

> **This file is method, not state.** It holds no numbers, decisions or dates of the project:
> those go stale. They live in the files of section 3 and are read from there every time.
> Paste or attach this file when you open a new chat. Rename it `AGENTS.md` for Codex.

---

## 1 · The project

Fill this in with your agent: a few lines, no more.

- **Topic:** what this wiki is about and who reads it.
- **Ground truth:** the data, code or system the wiki describes, where it is, and whether it changes.
- **Constraints:** what can't be modified, and what is out of scope.

## 2 · Order of truth

**Ground truth > wiki files > what anyone tells you**, including me.

- Ground truth is what can be measured: the files in `raw/`, or the system they come from. If a
  wiki file disagrees with it, the ground truth wins and you register a finding.
- If what I tell you disagrees with a wiki file, the file wins and you tell me. My summaries are
  wrong sometimes; that's why the registry exists.
- Don't work from memory, from what I tell you, or from another chat's summary.

## 3 · Where the state is

Read these before answering anything.

| File | Answers |
|---|---|
| `pending.md` | What's left to do. Short, only what's open. Read first, in full |
| `registry.md` | Only tables: every decision, finding, question and pending decision with its status and evidence, plus the superseded values. Read in full: it stays short |
| `registry/` | One small page per ID with its *why*: what, why, how, where else this is calculated, validation. Open only the ones the work item touches |
| `wiki/` | The pages. Start from `index.md` |
| `index.md` | One line per file: its type and what it answers |
| `log.md` | Who changed what and when: the chronology. Not state: written after every write; before writing, read only its last lines |

**Small files, many of them.** No state file is read in full if it can grow: a large file is
split into pages and kept as a table that points to them.

Anything about how work is done (roles, workflows, scripts) is **method** and lives in `roles/`,
`workflows/` and the tools, never in a state file.

## 4 · Rules

Each rule came from a concrete error. A rule without its reason turns into a preference and
stops being followed, so a new rule is added only with the error that caused it.

1. **Measure before you claim.** If something can be measured, measure it before writing it.
   "There isn't enough to say" beats a clean conclusion without support.
   *Origin: criteria chosen "by analogy" were contradicted by the data more than once.*
2. **Don't quote a list or a value from the wiki without checking it against the ground truth.**
   *Origin: a list in the registry was out of date with the registry's own later entries, and a
   wrong figure was computed from it.*
3. **Decided is not executed.** They are two states. A decision that hasn't been applied changed
   no number. "Executed" needs evidence from the ground truth, not from the wiki.
   *Origin: the most repeated error of the project this template comes from.*
4. **Point, don't copy.** A number lives in one place; other pages point to it. When a value is
   corrected, the old one goes to the superseded values table in the same move.
   *Origin: of twelve cells found stale or wrong in a summary page, nine were numbers or counts
   copied from elsewhere.*
5. **A change that alters a calculation says where else the same thing is calculated,** and
   whether those places were checked.
   *Origin: a correction was applied to one view while another view computed the same metric on
   its own with the old rule. Someone outside the project caught it.*
6. **Every percentage says what it is a percentage of, and every general claim is measured over
   the whole range.** Claims with "since", "all", "none", "only", "always" are measured by every
   segment (date, category, channel) before they are written.
   *Origin: a percentage of lines was written as a percentage of sales, and "empty since a date"
   was true for one channel only. Both reached the document.*
7. **Every item one role leaves for another is answered or passed on, one by one.**
   *Origin: a reviewer's observation never reached the writer and the same mistake was repeated
   three times; a writer's warning about an ambiguous word got no answer and the word stayed.*

## 5 · The cycle of a work item

A work item can be a source to ingest, a question, a page, a metric or a decision. I say which
one when I open it. The cycle is always the same.

1. **Scope.** One line: what's in and what's out. If it starts growing, cut it and register the
   rest as a separate item.
2. **Read what's already decided** in the registry about this item. Starting over on something
   already resolved is the most expensive way to lose time.
3. **Measure the ground truth** before proposing: volume, distinct values, nulls, ranges, odd cases.
4. **Confront the three versions:** what the wiki says, what the system does, what the data shows.
   Name the differences. If they don't match, that *is* the work.
5. **Decide what's missing.** Every difference closes with a numbered decision and its reason. If
   the call is mine, bring me the options with what is gained and lost, measured. If it depends on
   a third party, register the question and continue with a plan B.
6. **Execute and validate.** Every change comes with its checks, and **checks must fail loudly:**
   an expected value that moves with the clock (today's date, the last row) always passes and
   checks nothing. A change without a check isn't done. After a change to the ground truth, take a
   snapshot (`wikicheck snapshot --out`).
7. **Register.** The row in `registry.md` and its page in `registry/` with the *why* (the *what*
   can be read from the ground truth), `pending.md` updated, and a line in `log.md`, all in the
   same move.
8. **Close.** Two lines: what's resolved, what's open, and who it depends on. Then one question:
   **was something done by hand a second time, or did an error repeat?** If yes, propose in one
   line how to avoid it: a rule here (with its origin), a check, a script, a role or a workflow
   (section 8). Nothing is built without my approval.

## 6 · Numbering and statuses

| Prefix | What it is | Statuses |
|---|---|---|
| **D** | Decision: two defensible options, one chosen, with its reason | proposed, decided, executed, cancelled |
| **H** | Finding: the data showed something not known before | active, superseded |
| **T** | Question to a third party: the answer isn't in the data. Say what's at stake, measured | open, answered |
| **P** | Pending decision of mine, with what it blocks | open, closed |

A task that is decided and only needs doing is not a P: it goes to `pending.md`.

## 7 · Writing: one writer at a time

Another chat (another Claude, Codex, a person) may be working on this same folder.

1. **Read the last lines of `log.md`.** If someone signed in the last 30 minutes on a file you are
   about to write, ask me before writing. *Origin: two chats wrote at the same time.*
2. **Read the file at that moment** and change only your part. Never rebuild a file from an older copy.
3. **If the file changed since you read it,** don't force the write: read it again, merge, then save.
4. **Changes signed by someone else are kept.** If they contradict yours, tell me; I decide.
5. **After saving, compare byte by byte** (not the size) with what you meant to write.
   *Origin: twice, an older version of a file stayed after a save; comparing sizes can't catch
   that when both versions have the same length.*
6. **A file a person may have open** (a document, a spreadsheet) isn't written until they confirm
   it's closed. *Origin: a co-author saved with the file open and overwrote two rounds of edits.*
7. **Sign every write** with one line at the end of `log.md`: time **read from the clock**, never
   estimated; who you are (and your model, or "model unconfirmed"); files; what you did; what you
   checked. Earlier lines are never edited. *Origin: estimated times left three signatures out of
   order or in the future.*

## 8 · Scripts, agents and workflows

Method grows with the project. This section says which tool for which job and how a new one is
created.

### 8.1 · Which tool for what

| Task | Tool | Why |
|---|---|---|
| Search, count, compare values between files, check links, check that a number still holds | **Script** (`wikicheck` or a new mode) | Same result every time, full coverage, seconds |
| Find every mention of a term, code or value | **Script**, `wikicheck extract` | Finds 100 % of literal mentions, with the paragraph or table row |
| Verify a report from another agent | **Script**, `wikicheck cite` | Checks every citation, not a sample, and what was left out |
| Independent review | **Fresh agent**, ideally another model, with `roles/reviewer.md` | Finds what the author doesn't see because it "knows what it meant" |
| A heavy read that would fill the conversation | **Agent** (strong model) | The main chat keeps only the result |
| Lots of repetitive, verifiable work that a script can't do | **Cheap model**, only if such a case appears | The only thing a cheap model does well |
| Decide, design, write checks, say whether something is a contradiction | **Main chat** | It's judgment |

**Golden rule: mechanical work goes to a script, judgment to the main chat.** A cheap model asked
for judgment makes mistakes. Asked for no judgment, it does what a search does, slower, and with
coverage that varies between runs.

An agent doesn't save usage because it runs a cheaper model: it starts with its own context and
what it returns has to be verified. Use one for what it adds (reading cold, keeping the main
context clean), not to save. No agent is launched without my approval. Read-only scripts can be
run without asking.

### 8.2 · Scripts for repetitive tasks

**Signals.** A task is a candidate when it meets all four:
- **It repeats:** it was done twice or more (here, or according to `log.md` and the registry) and will come back.
- **It's mechanical:** it needs no decision; two people would do it the same way.
- **The result can be checked:** there's a way to know whether it came out right.
- **By hand it's costly or error-prone:** counting, copying numbers, crossing lists, searching long files.

**Propose, don't build.** Tell me in a few lines: the task, how many times it appeared and where,
what the script would do and wouldn't, how we'll know it works, and whether it fits as a new mode
of an existing script (preferred) or needs its own.

**Build and test, if I approve.**
- Read-only over the project. It never writes state files and never decides.
- Tested **before** it's used: with cases whose right answer is known, and **with errors planted on
  purpose**, to see that it catches them.
- The *how to use it* goes in the script's header; the *when* goes in the table of 8.1. Never both in the same place.

**Use it with distrust at first.** The first runs are checked by hand on a sample. If it fails,
fix the script, and if the same mistake could happen in another script, write it down.

**When not.** A one-off task, or one that needs judgment. A script that decides is worse than no
script: its results look certain and aren't.

### 8.3 · Agents (roles)

**When a new role is worth it:** a kind of work comes back often and needs a stance the main chat
can't have: reading cold (reviewer), writing only from measured facts (writer), keeping a map
without deciding or measuring, drawing figures to an approved style. A one-off task doesn't need
a role; a brief is enough (8.5).

**What a role file has** (`roles/TEMPLATE.md`):
1. **Who you are and what you don't do.** The "don't" list matters most: don't decide, don't measure, don't touch other roles' files.
2. **What you read and in what order.** This schema first. Read from the files, never from what you're told.
3. **What you write,** and the rules for writing it.
4. **What you check before signing.**
5. **How you deliver:** short, plus hand-off blocks for each other role and for me (rule 7).
6. **Which model,** and whether it is launched once and kept, or fresh every time. A reviewer is
   always fresh: its value is reading without what it saw before.

**A role is improved from its errors.** After a heavy session, read the agents' transcripts, list
each error with its evidence and its cause (missing rule? ambiguous rule? rule ignored? tool
problem?), and propose the change to the role file with the error as its origin. The most
expensive errors are usually in what the agent *received*, not in what it did.

### 8.4 · Workflows (step-by-step guides)

**When:** a task with several steps that has to be done exactly, especially one a person carries
out by hand (applying changes in a tool the agent can't touch) or one that repeats.

**What a workflow file has** (`workflows/TEMPLATE.md`):
- what it builds or changes, the decision it applies, and what it was written against (a snapshot or a version);
- numbered steps, each one small enough to check;
- **a check after each step, with its expected value,** and what to do if it doesn't match;
- a final check table: what, where, expected value, what to do if it fails.

**Lifecycle.** A reusable workflow is type *method*. A one-shot workflow is type *block*: once it's
executed and verified, it's deleted and the registry entry keeps what it did. If a step's check can
be read by a script, put it in a fenced block a script can parse.

### 8.5 · Briefing an agent

The brief has to stand on its own: the agent didn't see the conversation.

```
READ-ONLY TASK. Don't create, edit or delete any file.

FIRST LINE OF YOUR ANSWER: "MODEL: <exact identifier from your system instructions>",
or "MODEL: not stated".

Files (read ONLY these; don't search other folders):
A. <path> (<what it is, one line>)

<What is asked, concretely.>

Read the files in full, in parts of at most 300 lines. At the end, list the line ranges you read
in full, one per line: READ <path> <start>-<end>

Every citation in this exact format, because a program checks it:
<<<CITE <path> <start>-<end>
exact text from the file; you may cut with "…", never rewrite
CITE>>>

Statuses (decided, executed, cancelled…) ONLY if the text says them; otherwise "not stated".
```

For a review, add the role file and **nothing** of the conversation, and none of the main chat's
conclusions. Give it the data, not only the text: a review without data leaves every number
unverified. Open questions from the writer go in a separate block, to read after the review.

### 8.6 · Before an agent's report reaches me

1. Run `wikicheck cite` on it. Citations not found are dropped; shifted ones are fixed; uncovered mentions are read by hand.
2. Check the MODEL line.
3. Any status taken from a table is read with its column header. Anything "executed" is checked against the ground truth.
4. Classify each finding as **real**, **apparent** (with the reason) or **not enough to decide**, after reading its quote in context.
5. Archive the report as received in `reviews/`, with a header: when, on what, what was verified.

Then tell me what was found, what was verified, what was dropped and what's left for me to decide.
Never paste the raw report.

## 9 · Starting a session

Run `wikicheck lint` and `wikicheck snapshot` (it diffs the ground truth against the last
snapshot), read the files of section 3, and tell me what you found that differs from what I
expected, including which lint candidates turned out to be real. Then I tell you the work item.
In a project split into areas, what to read is in section 12.

## 10 · How you deliver

- **The result in the chat, the detail in the file.** Don't repeat in the message what you just wrote in a file.
- **Always say what changed** and where. Never hand over a file without that.
- **One file at a time.** If something fits in an existing file, it goes there.
- **Don't fix five things in passing.** Write them down and continue.
- Short answers: what was done, what changed, what's left to decide.

## 11 · File formats (what `wikicheck lint` expects)

| File | Format |
|---|---|
| `index.md` | Table rows with three cells: the path in backticks, its type, and what it answers. A path ending in `/` covers a whole folder. Types: state, page, method, block, reference, source, log. Any folder may have its own `index.md` listing its own files, with paths relative to it; the index above lists that folder |
| `registry.md` | Tables with `ID`, `Status`, `Evidence` and `Page` columns, and an optional `Area` column (an area folder name, `all` or `shared`). An "executed" row needs evidence. Closed rows can move to `registry-archive.md`, same format, closed statuses only. Superseded values go in a table with `Old value` and `New value` columns; to mention an old value on purpose elsewhere, mark the line `(old)` |
| `registry/` | One page per ID, named after it (`registry/<ID>.md`), linked from its row as `[[<ID>]]`. Every page needs its row. The status is not repeated in the page |
| `log.md` | A table whose first column is `When` (`YYYY-MM-DD HH:MM`, read from the clock) and whose fifth says what was checked. Once rotated, one file per month in `log/` (`log/YYYY-MM.md`), each with only its month |
| Pages | Links as `[[page]]` or `[[page#Heading]]` (in a table, escape the alias bar: `[[page#Heading\|text]]`). A page derived from a source declares it in frontmatter: `sources:` then `- raw/file.csv sha256:<first 12 hex>` (`wikicheck hash` prints it) |
| This file | Every item of the Rules section carries `Origin:` |

## 12 · When the project grows

**Signals.** Any of these means it's time to split:
- a state file you can no longer read in full in one go, or a session start that spends more on
  reading than on working;
- an index that no longer fits on a screen or two;
- groups of pages that rarely link to each other.

**How.** The split is a decision (a D, with its why), carried out with a one-shot workflow, with
`wikicheck lint` at 0 before and after, and a snapshot.

| What grows | How it's split |
|---|---|
| The wiki | One folder per area, `areas/<area>/`, with its own `index.md` (paths relative to the area) and `pending.md`. The root `index.md` lists `areas/` and nothing inside it. Whatever more than one area uses goes in `shared/`, one page per thing, so there are never two versions of it |
| The schema | Stays one. An area that works differently gets `areas/<area>/CONVENTIONS.md`: method only, and only what differs from this file |
| The registry | Stays one, with global numbering (no per-area prefixes, so IDs never collide) and an `Area` column: the area's folder name, or `all` / `shared` for what crosses areas. Closed rows (executed, cancelled, superseded, answered, closed) move to `registry-archive.md`; `registry.md` keeps what's still open |
| The log | Rotates by month: `log/YYYY-MM.md`. Before writing, read only the tail of the current month |
| Pending | One per area. The root `pending.md` keeps only what blocks across areas |
| Links | A page name used in two areas is ambiguous: link it by path, `[[areas/sales/overview]]` |

**What to read at the start of a session:** the root index; the index and pending of the area of
the work item; the registry rows of that area and of `all` and `shared`; and only the pages the
work touches.

**Search.** The indexes are enough up to a few hundred pages. Beyond that, add a search engine
(Karpathy suggests qmd) to *find* pages. To *verify coverage* (every mention of a term, a code or
a value) keep using `wikicheck extract`, with `--in` for one area: a ranked search doesn't promise
it brought everything.

**Checks.** `wikicheck lint` always runs over the whole folder, because links and values cross
areas. `--only areas/<area>` shows only that area's candidates while you work there. Before
closing anything that touches more than one area, look at all of them.

**Review.** One reviewer per area, in parallel, and one more that only checks what crosses areas:
the same number said differently, links between areas, the same term used two ways.

**Separate wikis** only when the areas have nothing to tell each other, when they have different
readers (one private, one shared), or when they need schemas that don't fit together. A wiki that
cites another declares it like any source, in `sources:` with its path and hash, so the lint
notices when the other one changes.
