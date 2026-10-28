# Verified LLM Wiki

*Español: [README.es.md](README.es.md)*

An extension of Andrej Karpathy's [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
pattern. Read his idea file first: this one builds on it. Like the original, this is an idea file.
Paste it to your agent and build your own version together. The repo also ships a template, a
read-only checker (`tools/wikicheck.py`) and a small worked example.

## The short version

Karpathy's pattern: instead of retrieving from raw documents on every question, an LLM builds and
maintains a wiki of markdown files that sits between you and your sources. A schema file
(`CLAUDE.md`, `AGENTS.md`) tells it how. It ingests sources, answers questions, files good answers
back, and periodically lints the wiki. Knowledge compounds instead of being re-derived.

This document adds one thing: **a verification layer that doesn't depend on the model.**

In the original, the same LLM that writes the wiki also checks it. That works while the wiki is
small and the stakes are low. It stops working when:

- the wiki backs numbers someone has to defend;
- the sources change under it;
- several agents and people write in it at the same time.

The wiki then looks consistent while being quietly wrong.

Everything below came out of a real project that hit all three. It was a data model and its
documentation, maintained for weeks by several AI agents (Claude, Codex) and two people in one
shared folder. Every rule exists because a specific error happened. They are written here in
generic form.

## What goes wrong without it

- **Copied numbers go stale.** A figure is copied into a summary page, the source page later
  corrects it, and the copy stays. In one audit, of 12 cells that were stale or wrong in a summary
  page, 9 were numbers or counts copied from elsewhere.
- **"Decided" gets read as "done".** A page says a change was made when it was only agreed.
  Everything downstream assumes something that isn't true.
- **Citations look right but aren't.** A reviewer agent returns findings with quotes. The quotes
  are real, but some point to the wrong lines, and some relevant passages were silently skipped.
  In one test, an extraction agent's coverage varied between runs: complete twice, 82% once. Every
  quote it did return was perfect, and only a full mechanical check noticed what was missing.
- **Self-review misses what the author "already knows".** The agent that wrote a page reads what
  it meant, not what it wrote.
- **Two writers, one file.** Two chats, or a chat and a person with the file open, save over each
  other.
- **Rules decay.** A rule written without its reason starts to look like a style preference and
  stops being followed.

## Principles

1. **Mechanical work goes to scripts, judgment goes to the model.** Searching, counting, crossing
   lists and comparing values between files belong to a script: it does them the same way every
   time, with full coverage. The model decides, designs, writes, and judges whether something is
   really a contradiction. A cheap model asked for judgment makes mistakes. Asked for no judgment,
   it does what grep does, slower and with variable coverage.
2. **Order of truth: ground truth > wiki > what anyone tells the agent**, including you. Ground
   truth is whatever can be measured: the data, the code, the actual system.
   - If the wiki disagrees with the ground truth, the ground truth wins and a finding is
     registered.
   - If what you tell the agent disagrees with the wiki, the wiki wins and the agent says so. Your
     summaries will be wrong sometimes, and that's what the wiki is for.
3. **Measure before you claim.** If something can be measured, it's measured before it's written.
   "Not enough to say" beats a clean conclusion without support.
4. **Checks must fail loudly.** A check whose expected value moves with the clock (today's date,
   the latest row) always passes and checks nothing.

## Architecture

Karpathy's three layers stay, and a fourth is added.

- **Ground truth** (his raw sources). It isn't always immutable: it may be a database, a codebase,
  or a model that keeps changing. The wiki records *which version* each claim was checked against.
- **The wiki,** split into *state* (what's true now, what's open) and *pages* (topics, entities,
  concepts). One fact lives in one place. **Many small files:** no state file grows without limit
  (see 4 and 11).
- **The schema: method only, never state.** No numbers, decisions or dates go in it, because those
  go stale. A schema that holds only method doesn't expire.
- **The verification layer** (new): a read-only checker, snapshots of the ground truth, a signature
  log, and role files for independent review.

## The additions

### 1. Lint with a script, not with the model

Karpathy's lint asks the LLM to look for contradictions, stale claims, orphans and missing links.
Here, everything that can be checked mechanically is checked by a read-only script, every time,
with full coverage. The script reports **candidates, not verdicts**: the agent reads each one
before reporting it.

`wikicheck lint` runs seven checks:

| Check | Catches |
|---|---|
| L1 Index | Files nobody listed, entries pointing to deleted files, entries without a type, in the root index and in every area's index |
| L2 Links | `[[page]]` and `[[page#heading]]` that point nowhere |
| L3 Registry | IDs used but never registered, duplicates, "executed" without evidence, cancelled decisions still in use, open items in the archive, unknown areas |
| L4 Superseded values | An old value that a correction already replaced, still sitting in some page |
| L5 Provenance | Pages derived from a source that changed after they were written |
| L6 Log | Signatures out of order, in the future (estimated, not read from a clock), in the wrong month's file, or that don't say what was checked |
| L7 Rules | Rules in the schema without the error that caused them |

### 2. Decided ≠ executed

Every decision has two separate states, decided and executed. "Executed" requires evidence from
the ground truth (a diff, a measured value, a snapshot), not from the wiki itself. Confusing the
two was the most repeated error in the project this came from.

Numbering keeps things apart:

| | What it is |
|---|---|
| **D** | Decision: two defensible options, one chosen, with the reason |
| **H** | Finding: the data showed something not known before |
| **T** | Question to a third party: the answer isn't in the data, so say what's at stake, measured |
| **P** | Pending decision of yours, with what it blocks |

### 3. A ground truth that changes: snapshots and provenance

If the ground truth changes, "the wiki says X" only means something together with "checked
against version V".

- After each verified change, take a **snapshot**: a hash of every ground-truth file. The next
  session starts by diffing against the last snapshot, so it knows what changed instead of
  trusting what it's told.
- A page derived from a source records the source's **hash** in its frontmatter. If the source
  changes, the lint flags the page as possibly stale.

### 4. Small files: the registry is a table, each entry is a page

The project behind this kept decisions in one growing changelog. It reached about 700 KB and
needed scripts just to navigate. So, in Karpathy's style:

- `registry.md` holds **only tables**: one row per D, H, T and P, with status, evidence and a link
  to its page.
- **Each ID has its own small page** (`registry/D12.md`) with the what, the why, how it was done,
  where else the same thing is calculated, and the checks. The status isn't repeated in the page:
  it lives only in the table.
- **The chronology lives in `log.md`.** Like Karpathy's log, it's read by its tail, never in full.

The agent reads a short table and opens only the pages the work touches.

### 5. Point, don't copy

A number lives in one place, and other pages point to it.

- When a value is corrected, the old value goes into a **superseded values** table (old, new,
  since, why), and the lint searches every page for it. To mention an old value on purpose, as
  history, mark the line `(old)`.
- A change that alters a calculation says **where else the same thing is calculated**. Once a
  correction was applied to one view while another view computed the same metric on its own with
  the old rule. Someone outside the project caught it.

### 6. Citations a program can verify

Karpathy's query step answers "with citations", but nothing checks them. Here, any report that
cites the wiki (a reviewer's findings, an extraction) uses a fixed format:

```
<<<CITE wiki/metrics.md 12-14
the exact text, copied; "…" may cut, never rewrite
CITE>>>
```

The report also declares what it read in full (`READ wiki/metrics.md 1-120`). `wikicheck cite`
checks every quote, not a sample: whether it's at those lines, shifted, or not found. It also
flags files that weren't read in full and, given the search terms, mentions that no quote covers.
Coverage is the part that matters: a report can have perfect quotes and still have skipped half
the mentions.

### 7. Roles and cold review

One agent doing everything grades its own work. Split it:

| Role | Does | Doesn't |
|---|---|---|
| Analyst (main chat) | Measures, writes a fact sheet for each piece, decides with you, verifies every report, writes to the wiki, signs | Pass you a report it hasn't verified |
| Writer | Writes only from the fact sheet (measured facts, their base, their source, what stays out) | Measure, decide, or copy the fact sheet's wording |
| Reviewer | Reads cold and reports findings with verifiable quotes | Write anything |

- **The reviewer starts fresh every time**, ideally on a different model with different blind
  spots. It gets the request, the material and the data, **never the analyst's conclusions**. The
  writer's open questions go in a separate block, read only after the review is done.
- **The reviewer gets the data, not just the text.** A review without data leaves every number
  unverified.
- **Something the data contradicts is high severity,** even if the argument still stands.
- **The analyst classifies every finding** as real, apparent (with the reason) or not enough to
  decide, after reading its quote in context. Raw reports are archived as received.
- **Every hand-off item is answered or passed on,** one by one. An observation that never reached
  the writer was repeated three times.

### 8. Agents, workflows and scripts are part of the method, and it grows

Karpathy says you and the LLM co-evolve the schema. This turns that into a procedure, with three
kinds of tool, each with its own rules for when to create one. The details and templates are in
`template/CLAUDE.md`, section 8.

**Which tool for what.**

| Task | Tool |
|---|---|
| Search, count, compare between files, check that a number still holds | Script |
| Independent review | Fresh agent, preferably a different model, with the reviewer role |
| A heavy read that would fill the conversation | Agent, strong model |
| Repetitive, verifiable work a script can't do | Cheap model, and only then |
| Decide, design, write checks, judge contradictions | Main chat |

An agent doesn't save usage just because it runs a cheaper model. It has its own startup cost and
its output has to be verified. Use one for what it adds (a cold read, a clean main context), not
to save.

**Scripts for repetitive tasks.** A task is a candidate when it meets four signals:

- it repeats: done twice or more, and coming back;
- it's mechanical: two people would do it the same way;
- its result can be checked;
- by hand it's costly or error-prone.

Then:

1. The agent **proposes before building:** what, how often it appeared, what the script would and
   wouldn't do, how you'll know it works.
2. After your approval, the agent builds it **read-only** and tests it **with errors planted on
   purpose**.
3. The agent uses it **with distrust at first,** checking a sample by hand.

A task that needs judgment is never automated: a script that decides looks certain and isn't.

**Agents (roles).** A new role is worth creating when a kind of work keeps coming back and needs a
stance the main chat can't have: reading cold, writing only from measured facts, keeping a map
without deciding. A role file says:

- who it is and, above all, **what it doesn't do**;
- what it reads and in what order;
- what it writes;
- what it checks before signing;
- how it delivers, with hand-off blocks for the other roles;
- which model it runs on, and whether it's kept across a session or started fresh.

Roles get better through **post-mortems.** After a heavy session, the agents' transcripts are read
and each error is listed with its evidence and its cause: a missing rule, an ambiguous rule, a
rule that was ignored, or a tool problem. Then the role file is patched. The most expensive errors
are usually in what an agent *received* (a half-measured fact sheet, an incomplete brief), not in
what it did.

**Workflows (step-by-step guides).** For a task that has to be done exactly, especially one a
person carries out by hand in a tool the agent can't touch. Each step comes with **its own check
and expected value**, plus a final check table. A one-shot workflow is a *block*: it's deleted once
it's executed and verified, and the registry page keeps what it did.

**Every rule carries its origin.** Each rule in the schema and the role files carries the error
that caused it ("Origin: …"), and the lint flags any rule without one. Every work item closes with
a question: **was something done by hand a second time, or did an error repeat?** If so, the agent
proposes a rule, a check, a script, a role or a workflow, and nothing is built without your
approval.

### 9. Many writers

Karpathy's setup is one person and one agent. With several (two chats, Codex and Claude, a
co-author with the file open):

- **A signature log.** Every write appends one line to `log.md` with:
  - the time, **read from the clock** and never estimated;
  - who wrote it, with the model, or "unconfirmed";
  - the files touched;
  - what was done;
  - what was checked.
- **Before writing,** the agent reads the tail of the log. If someone touched the same file in the
  last ~30 minutes, it asks first.
- **The agent reads the file at write time** and changes only its part. A file is never rebuilt
  from an older copy.
- **After saving, the agent compares byte by byte,** not by size. A save can leave the previous version in
  place, and the same size doesn't mean the same content.
- **A file a person may have open** (a document, a spreadsheet) isn't written until they confirm
  it's closed. Their next save would overwrite yours.
- Git sits underneath for history.

### 10. An index with types and a lifecycle

Karpathy's index is a catalog. Here each entry also has a **type**: state, page, method, block,
reference, source or log. The lint keeps the index and the folder in sync. Types carry a
lifecycle:

- a *block* (one-shot instructions) is deleted once it's applied;
- a *reference* is read but not maintained;
- a *source* is never edited.

### 11. When the project grows

This is what the first question about this pattern usually is: for a big project, one wiki or
several? **One wiki, split into areas,** almost always. Splitting into separate wikis loses
exactly what makes the pattern worth it: when a source touches two areas, both get updated, and
contradictions between them get flagged. Separate wikis only make sense when the areas have nothing
to tell each other, have different readers (one private, one shared), or need schemas that don't
fit together.

**When to split:** a state file the agent can't read in full in one go, a session start that spends
more on reading than on working, an index that no longer fits on a screen or two. The split is
itself a decision, carried out with a one-shot workflow, with the lint at 0 before and after.

| What grows | How it's split |
|---|---|
| The wiki | One folder per area, `areas/<area>/`, with its own `index.md` and `pending.md`. The root index lists `areas/` and nothing inside it. Whatever several areas use goes in `shared/`, one page per thing |
| The schema | Stays one. An area that works differently gets a conventions file with only what differs |
| The registry | Stays one, with global numbering so IDs never collide, and an `Area` column. Closed rows move to `registry-archive.md`, so `registry.md` keeps only what's open |
| The log | Rotates by month: `log/YYYY-MM.md`. Before writing, read only the tail of the current month |
| Pending | One per area. The root keeps only what blocks across areas |
| Links | A page name used in two areas is linked by path: `[[areas/sales/overview]]` |

- **Reading at the start of a session:** the root index, the area's index and pending, the
  registry rows of that area, and only the pages the work touches.
- **Search.** Karpathy notes that the index is enough up to a few hundred pages, and suggests a
  search engine (qmd) beyond that. Use it to *find*. To *verify coverage* (every mention of a
  term, code or value) keep using `wikicheck extract --in <area>`: a ranked search doesn't promise
  it brought everything.
- **Checks** always run over the whole folder, because links and values cross areas.
  `wikicheck lint --only areas/<area>` shows one area's candidates while working there.
- **Review:** one reviewer per area in parallel, plus one that only checks what crosses areas
  (the same number said differently, links between areas, a term used two ways).
- **A wiki that cites another** declares it like any source, with its hash, so the lint notices
  when the other one changes.

`wikicheck` supports all of this: sub-indexes per folder, rotated logs, the registry archive and
the `Area` column are checked, and `tests/` builds a grown wiki and plants errors in it. The full
procedure is in `template/CLAUDE.md`, section 12.

## The cycle of a work item

Karpathy's ingest, query and lint become one cycle, used for any unit of work: a source to
ingest, a question, a page, a decision.

1. **Scope** in one line: what's in and what's out. If it grows, cut it.
2. **Read what's already decided.** Starting over on something resolved is the most expensive way
   to lose time.
3. **Measure the ground truth** before proposing anything.
4. **Confront the three versions:** what the wiki says, what the system does, what the data shows.
   If they don't match, *that* is the work.
5. **Decide what's missing,** numbered and with the reason. If the call is yours, the agent brings
   the options with what's gained and what's lost, measured.
6. **Execute and validate,** with checks that fail loudly. A change without a check isn't done.
7. **Register:** the row, its page with the why, `pending.md`, and the log, all in the same move.
8. **Close:** what's resolved, what's open, who it depends on, and the repeat question (8).

## Trade-offs

- **Overhead.** The full protocol pays off when the wiki backs numbers someone has to defend, or
  when several writers share it. For personal notes, Karpathy's lighter version is probably enough.
  Everything here is modular.
- **A different emphasis.** This makes the wiki more trustworthy and easier to change safely. It
  doesn't make the synthesis itself any better: that's still the model and your questions.

## In this repo

```
template/          a starting folder: copy it to begin
  CLAUDE.md        the schema (rename to AGENTS.md for Codex)
  index.md         one line per file, with its type
  registry.md      tables only: D, H, T, P and superseded values
  registry/        one page per ID
  pending.md       what's left to do
  log.md           the signature log
  roles/           writer, reviewer, and a template for new roles
  workflows/       a template for step-by-step guides with checks
  wiki/ raw/ snapshots/ reviews/
tools/wikicheck.py the read-only checker (standard library only, Python 3.9+)
example/           a tiny wiki (an online store's order metrics) that passes every check
tests/             each check tested against planted errors, also on a grown wiki with areas
```

```
python tools/wikicheck.py lint     --root my-wiki
python tools/wikicheck.py lint     --root my-wiki --only areas/sales   # one area's candidates
python tools/wikicheck.py snapshot --root my-wiki                  # diff raw/ against the last snapshot
python tools/wikicheck.py snapshot --root my-wiki --out "snapshots/2026-10-28 1415.json"
python tools/wikicheck.py cite report.md --root my-wiki --files wiki/metrics.md --terms shipping
python tools/wikicheck.py hash     my-wiki/raw/orders.csv          # for a page's sources: frontmatter
python tools/wikicheck.py extract  refund --root my-wiki           # every mention, with its paragraph or table row
python tools/wikicheck.py extract  refund --root my-wiki --in areas/sales
```

**Quick start:**

1. Copy `template/` into a new folder.
2. Give this README and `CLAUDE.md` to your agent, and fill in section 1 of `CLAUDE.md` together.
3. Run `wikicheck lint` and `wikicheck snapshot` at the start of every session.

To see every check fail on purpose, look at `tests/`.

## Credits

The LLM Wiki pattern is Andrej Karpathy's
([gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)). This repo extends it
and isn't affiliated with him. MIT license.
