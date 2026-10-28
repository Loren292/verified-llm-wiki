#!/usr/bin/env python3
"""wikicheck: deterministic, read-only checks for an LLM-maintained wiki.

Part of verified-llm-wiki. Standard library only, Python 3.9+.

    python wikicheck.py lint     [--root DIR]
    python wikicheck.py cite     REPORT [--root DIR] [--slack N] [--terms T1,T2]
                                 [--files F1,F2] [--expect-model NAME]
    python wikicheck.py snapshot [--root DIR] [--paths raw] [--against FILE] [--out FILE]
    python wikicheck.py hash     FILE [FILE ...]
    python wikicheck.py extract  TERM [TERM ...] [--root DIR]

lint      Seven checks over the whole folder (L1 to L7, below).
cite      Verifies every <<<CITE ... CITE>>> block of a report against the files,
          the READ ranges the report declares, and which mentions of the given
          terms no citation covers.
snapshot  Hashes the ground truth (default: raw/) and diffs it against the last
          snapshot in snapshots/. With --out, saves the new snapshot.
hash      Prints a file's sha256, for the `sources:` frontmatter of a page.
extract   Every mention of the terms in every .md file, with its paragraph, or with
          its table row and the table header.

Lint checks:
    L1 index       index.md and the folder list the same files; every entry has a type
    L2 links       [[page]] and [[page#heading]] resolve
    L3 registry    IDs (D, H, T, P) are registered once, statuses are valid,
                   "executed" has evidence, no unknown or cancelled IDs in use,
                   every page in registry/ has its row
    L4 superseded  values in an "Old value" column don't appear anywhere else
    L5 provenance  sources hashed in a page's frontmatter haven't changed
    L6 log         log.md times are clock times, in order, not in the future,
                   and every line says what was checked
    L7 rules       every rule in the schema's Rules section has an Origin

Everything it reports is a candidate, not a verdict: the agent reads each one
before telling a human. The only write is `snapshot --out`, which never
overwrites an existing file. Exit code: 0 clean, 1 candidates found, 2 usage error.

The file formats it expects are described in template/CLAUDE.md, section 11.
"""
from __future__ import annotations

import argparse
import bisect
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path

IGNORE_DIRS = {".git", ".github", ".obsidian", "__pycache__", ".venv", "node_modules"}
IGNORE_FILES = {".DS_Store", "Thumbs.db"}
TYPES = {"state", "page", "method", "block", "reference", "source", "log"}
STATUSES = {
    "D": {"proposed", "decided", "executed", "cancelled"},
    "H": {"active", "superseded"},
    "T": {"open", "answered"},
    "P": {"open", "closed"},
}
SCHEMA_FILES = ("CLAUDE.md", "AGENTS.md")
EMPTY = {"", "-", "—", "–", "n/a"}
ID_RE = re.compile(r"(?<![A-Za-z0-9_\-/.])([DHTP])(\d+)(?![A-Za-z0-9_])")
LINK_RE = re.compile(r"\[\[([^\]\n]+?)\]\]")
SEP_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
FUTURE_TOLERANCE = dt.timedelta(minutes=10)


# ---------------------------------------------------------------- helpers

def rel(root: Path, p: Path) -> str:
    return p.relative_to(root).as_posix()


def walk_files(base: Path) -> list[Path]:
    out = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if d not in IGNORE_DIRS)
        for name in sorted(filenames):
            if name not in IGNORE_FILES:
                out.append(Path(dirpath) / name)
    return out


def md_files(root: Path) -> list[Path]:
    return [p for p in walk_files(root) if p.suffix.lower() == ".md"]


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def numbered(text: str) -> list[tuple[int, str]]:
    """Lines outside code fences and HTML comments, numbered from 1."""
    text = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    out, fence = [], None
    for n, line in enumerate(text.splitlines(), 1):
        s = line.lstrip()
        if fence is None and (s.startswith("```") or s.startswith("~~~")):
            fence = s[:3]
            continue
        if fence is not None:
            if s.startswith(fence):
                fence = None
            continue
        out.append((n, line))
    return out


def split_row(line: str) -> list[str] | None:
    s = line.strip()
    if not s.startswith("|"):
        return None
    s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    cells, cur, tick, i = [], "", False, 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            cur += "\\|"
            i += 2
            continue
        if c == "`":
            tick = not tick
        if c == "|" and not tick:
            cells.append(cur.strip())
            cur = ""
        else:
            cur += c
        i += 1
    cells.append(cur.strip())
    return cells


def tables(lines: list[tuple[int, str]]):
    """Yield (header_cells, header_lineno, [(lineno, cells), ...])."""
    i = 0
    while i < len(lines) - 1:
        n, line = lines[i]
        header = split_row(line)
        if header is not None and SEP_RE.match(lines[i + 1][1]) and lines[i + 1][0] == n + 1:
            rows, j = [], i + 2
            while j < len(lines) and lines[j][0] == lines[j - 1][0] + 1:
                cells = split_row(lines[j][1])
                if cells is None:
                    break
                rows.append((lines[j][0], cells))
                j += 1
            yield header, n, rows
            i = j
        else:
            i += 1


def clean_cell(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == "`" and s[-1] == "`":
        s = s[1:-1]
    return s.strip().strip("*").strip()


def frontmatter(text: str) -> list[tuple[int, str]]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return []
    for k in range(1, len(lines)):
        if lines[k].strip() == "---":
            return [(n + 1, lines[n]) for n in range(1, k)]
    return []


def norm_heading(s: str) -> str:
    s = re.sub(r"[`*_]", "", s).strip().lower()
    return re.sub(r"\s+", " ", s)


def headings(text: str) -> set[str]:
    out = set()
    for _, line in numbered(text):
        m = re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", line)
        if m:
            out.add(norm_heading(m.group(1)))
    return out


# ---------------------------------------------------------------- lint checks

def check_index(root: Path, **_):
    tag, out = "L1 index", []
    idx = root / "index.md"
    if not idx.is_file():
        return [(tag, "index.md", "missing")]
    entries: dict[str, int] = {}
    for header, _, rows in tables(numbered(read(idx))):
        for n, cells in rows:
            m = re.fullmatch(r"`([^`]+)`", cells[0]) if cells else None
            if not m:
                continue
            path, loc = m.group(1), f"index.md:{n}"
            if path in entries:
                out.append((tag, loc, f"`{path}` is listed twice (also line {entries[path]})"))
            entries[path] = n
            typ = cells[1].strip().strip("`").lower() if len(cells) > 1 else ""
            if typ not in TYPES:
                out.append((tag, loc, f"`{path}`: type '{typ}' is not one of {', '.join(sorted(TYPES))}"))
            if len(cells) < 3 or cells[2].strip() in EMPTY:
                out.append((tag, loc, f"`{path}`: doesn't say what it answers"))
            target = root / path.rstrip("/")
            if path.endswith("/") and not target.is_dir():
                out.append((tag, loc, f"folder `{path}` is listed but doesn't exist"))
            elif not path.endswith("/") and not target.is_file():
                out.append((tag, loc, f"`{path}` is listed but doesn't exist"))
    folders = [p for p in entries if p.endswith("/")]
    for p in walk_files(root):
        r = rel(root, p)
        if r not in entries and not any(r.startswith(d) for d in folders):
            out.append((tag, r, "not in index.md"))
    return out


def check_links(root: Path, **_):
    tag, out = "L2 links", []
    files = md_files(root)
    by_stem: dict[str, list[Path]] = {}
    for p in files:
        by_stem.setdefault(p.stem.lower(), []).append(p)
    heads: dict[Path, set[str]] = {}
    for p in files:
        for n, line in numbered(read(p)):
            for m in LINK_RE.finditer(re.sub(r"`[^`]*`", "", line)):
                inner = re.split(r"\\?\|", m.group(1), maxsplit=1)[0]
                target, _, heading = inner.partition("#")
                target, loc = target.strip(), f"{rel(root, p)}:{n}"
                if not target:
                    dest = p
                elif "/" in target:
                    cand = root / (target if target.endswith(".md") else target + ".md")
                    dest = cand if cand.is_file() else None
                else:
                    stem = target[:-3] if target.lower().endswith(".md") else target
                    found = by_stem.get(stem.lower(), [])
                    if len(found) > 1:
                        out.append((tag, loc, f"[[{m.group(1)}]] is ambiguous: "
                                    + ", ".join(rel(root, f) for f in found)))
                        continue
                    dest = found[0] if found else None
                if dest is None:
                    out.append((tag, loc, f"[[{m.group(1)}]] points to a page that doesn't exist"))
                    continue
                if heading.strip():
                    if dest not in heads:
                        heads[dest] = headings(read(dest))
                    if norm_heading(heading) not in heads[dest]:
                        out.append((tag, loc, f"[[{m.group(1)}]]: no heading '{heading.strip()}' "
                                    f"in {rel(root, dest)}"))
    return out


def registry_ids(root: Path):
    """Return ({id: (status, lineno)}, findings)."""
    tag, out, ids = "L3 registry", [], {}
    reg = root / "registry.md"
    if not reg.is_file():
        return ids, [(tag, "registry.md", "missing")]
    for header, _, rows in tables(numbered(read(reg))):
        h = [c.strip().lower() for c in header]
        if "id" not in h or "status" not in h:
            continue
        i_id, i_st = h.index("id"), h.index("status")
        i_ev = h.index("evidence") if "evidence" in h else None
        for n, cells in rows:
            loc = f"registry.md:{n}"
            raw = clean_cell(cells[i_id]) if i_id < len(cells) else ""
            m = re.fullmatch(r"([DHTP])(\d+)", raw)
            if not m:
                out.append((tag, loc, f"'{raw}' is not an ID (D, H, T or P and a number)"))
                continue
            if raw in ids:
                out.append((tag, loc, f"{raw} is registered twice (also line {ids[raw][1]})"))
            st = clean_cell(cells[i_st]).lower() if i_st < len(cells) else ""
            if st not in STATUSES[m.group(1)]:
                out.append((tag, loc, f"{raw}: status '{st}' is not one of "
                            + ", ".join(sorted(STATUSES[m.group(1)]))))
            if st == "executed":
                ev = cells[i_ev].strip() if i_ev is not None and i_ev < len(cells) else ""
                if ev in EMPTY:
                    out.append((tag, loc, f"{raw} is 'executed' with no evidence"))
            ids[raw] = (st, n)
    return ids, out


def check_registry(root: Path, **_):
    tag = "L3 registry"
    ids, out = registry_ids(root)
    if not (root / "registry.md").is_file():
        return out
    pages = root / "registry"
    if pages.is_dir():
        for p in sorted(pages.glob("*.md")):
            if p.stem not in ids:
                out.append((tag, rel(root, p), f"page for {p.stem}, which has no row in registry.md"))
    for p in md_files(root):
        r = rel(root, p)
        for n, line in numbered(read(p)):
            for m in ID_RE.finditer(line):
                code = m.group(0)
                if code not in ids:
                    out.append((tag, f"{r}:{n}", f"{code} is used but not registered"))
                elif (ids[code][0] == "cancelled" and r != "registry.md"
                      and "cancel" not in line.lower()):
                    out.append((tag, f"{r}:{n}", f"{code} is cancelled but used as if it were current"))
    return out


def check_superseded(root: Path, **_):
    tag, out = "L4 superseded", []
    olds, skip = [], set()
    files = md_files(root)
    cache = {p: numbered(read(p)) for p in files}
    for p in files:
        for header, hn, rows in tables(cache[p]):
            h = [c.strip().lower() for c in header]
            if "old value" not in h or "new value" not in h:
                continue
            io = h.index("old value")
            skip.add((p, hn))
            for n, cells in rows:
                skip.add((p, n))
                val = clean_cell(cells[io]) if io < len(cells) else ""
                if val in EMPTY:
                    continue
                if len(val) < 3:
                    out.append((tag, f"{rel(root, p)}:{n}", f"old value '{val}' is too short to "
                                "search reliably: write it with its unit or context"))
                    continue
                pat = re.compile(r"(?<![0-9A-Za-z])" + re.escape(val) + r"(?![0-9A-Za-z])")
                olds.append((val, pat, f"{rel(root, p)}:{n}"))
    for p in files:
        r = rel(root, p)
        if r == "log.md":
            continue
        for n, line in cache[p]:
            if (p, n) in skip or "(old)" in line.lower():
                continue
            for val, pat, src in olds:
                if pat.search(line):
                    out.append((tag, f"{r}:{n}", f"'{val}' was superseded ({src}) and is still here"))
    return out


def check_provenance(root: Path, **_):
    tag, out = "L5 provenance", []
    line_re = re.compile(r'^\s*-\s+(?:"([^"]+)"|(\S+))\s+sha256:([0-9a-fA-F]{8,64})\s*$')
    for p in md_files(root):
        r, in_sources = rel(root, p), False
        for n, line in frontmatter(read(p)):
            if re.match(r"^sources:\s*$", line):
                in_sources = True
                continue
            if not in_sources:
                continue
            if re.match(r"^\S", line):
                in_sources = False
                continue
            if not line.strip():
                continue
            m = line_re.match(line)
            if not m:
                out.append((tag, f"{r}:{n}", "source line should be '- path sha256:<hex>'"))
                continue
            src, prefix = (m.group(1) or m.group(2)), m.group(3).lower()
            sp = root / src
            if not sp.is_file():
                out.append((tag, f"{r}:{n}", f"source `{src}` doesn't exist"))
                continue
            now = sha256(sp)
            if not now.startswith(prefix):
                out.append((tag, f"{r}:{n}", f"`{src}` changed since this page was written "
                            f"(recorded {prefix[:12]}, now {now[:12]}): the page may be stale"))
    return out


def check_log(root: Path, now: dt.datetime | None = None, **_):
    tag, out = "L6 log", []
    log = root / "log.md"
    if not log.is_file():
        return [(tag, "log.md", "missing")]
    now = now or dt.datetime.now()
    prev = None
    for header, _, rows in tables(numbered(read(log))):
        if not header or header[0].strip().lower() != "when":
            continue
        for n, cells in rows:
            loc = f"log.md:{n}"
            try:
                t = dt.datetime.strptime(cells[0].strip(), "%Y-%m-%d %H:%M")
            except ValueError:
                out.append((tag, loc, f"'{cells[0]}' is not a clock time (YYYY-MM-DD HH:MM)"))
                continue
            if prev and t < prev:
                out.append((tag, loc, "earlier than a line above it: estimated time, or written out of order"))
            if t > now + FUTURE_TOLERANCE:
                out.append((tag, loc, "in the future: the time was estimated, not read from the clock"))
            if len(cells) < 5 or cells[4].strip() in EMPTY:
                out.append((tag, loc, "doesn't say what was checked"))
            prev = max(prev, t) if prev else t
    return out


def check_rules(root: Path, **_):
    tag = "L7 rules"
    schema = next((root / s for s in SCHEMA_FILES if (root / s).is_file()), None)
    if schema is None:
        return [(tag, "CLAUDE.md", "no schema (CLAUDE.md or AGENTS.md)")]
    lines = numbered(read(schema))
    start = level = None
    for k, (n, line) in enumerate(lines):
        m = re.match(r"^(#{1,6})\s.*\brules\b", line, re.I)
        if m:
            start, level = k, len(m.group(1))
            break
    if start is None:
        return [(tag, schema.name, "no Rules section")]
    items: list[tuple[int, str]] = []
    for n, line in lines[start + 1:]:
        hm = re.match(r"^(#{1,6})\s", line)
        if hm and len(hm.group(1)) <= level:
            break
        if re.match(r"^(\d+[.)]|[-*])\s", line):
            items.append((n, line))
        elif items and line.strip():
            items[-1] = (items[-1][0], items[-1][1] + " " + line.strip())
    out = []
    for n, text in items:
        if not re.search(r"origin\s*\**\s*:", text, re.I):
            short = re.sub(r"\s+", " ", text.strip())[:70]
            out.append((tag, f"{schema.name}:{n}", f"rule without its origin: {short}…"))
    return out


CHECKS = [check_index, check_links, check_registry, check_superseded,
          check_provenance, check_log, check_rules]


def lint(root: Path, now: dt.datetime | None = None):
    out = []
    for check in CHECKS:
        out.extend(check(root, now=now))
    return out


# ---------------------------------------------------------------- cite

CITE_RE = re.compile(r'<<<CITE[ \t]+(?:"([^"]+)"|(\S+))[ \t]+(\d+)(?:-(\d+))?[ \t]*\r?\n(.*?)\r?\nCITE>>>', re.S)
READ_RE = re.compile(r'^READ[ \t]+(?:"([^"]+)"|(\S+))[ \t]+(\d+)-(\d+)[ \t]*$', re.M)
GAP = 3000


class Flat:
    """A file as one whitespace-normalized string, with line offsets."""

    def __init__(self, path: Path):
        self.lines = read(path).splitlines()
        parts, self.starts, pos = [], [], 0
        for line in self.lines:
            nl = " ".join(line.split())
            self.starts.append(pos)
            parts.append(nl)
            pos += len(nl) + 1
        self.text = " ".join(parts)

    def line_of(self, offset: int) -> int:
        return bisect.bisect_right(self.starts, offset)

    def find(self, frags: list[str], want: tuple[int, int]):
        """All matches of the fragments in order; return the one nearest `want`."""
        best, i = None, 0
        while True:
            a = self.text.find(frags[0], i)
            if a < 0:
                break
            end, ok = a + len(frags[0]), True
            for f in frags[1:]:
                q = self.text.find(f, end)
                if q < 0 or q - end > GAP:
                    ok = False
                    break
                end = q + len(f)
            if ok:
                span = (self.line_of(a), self.line_of(end - 1))
                dist = 0 if (span[0] >= want[0] and span[1] <= want[1]) else \
                    min(abs(span[0] - want[0]), abs(span[1] - want[1])) + 1
                if best is None or dist < best[0]:
                    best = (dist, span)
                if dist == 0:
                    break
            i = a + 1
        return best[1] if best else None


def cite(report: Path, root: Path, slack: int = 3, terms=None, files=None, expect_model=None):
    """Return (results, problems). results: dicts per citation."""
    text = read(report)
    results, problems, flats = [], [], {}
    if expect_model:
        # The report's first line; an archived copy may have a header above it.
        m = re.search(r"^MODEL:\s*(.+?)\s*$", text, re.M)
        if not m:
            problems.append("no 'MODEL: <model>' line")
        elif expect_model.lower() not in m.group(1).lower():
            problems.append(f"model is '{m.group(1)}', expected '{expect_model}'")
    for m in CITE_RE.finditer(text):
        path = m.group(1) or m.group(2)
        a = int(m.group(3))
        b = int(m.group(4) or a)
        quote = m.group(5)
        res = {"path": path, "lines": (a, b), "status": None, "found": None,
               "at": text.count("\n", 0, m.start()) + 1}
        fp = root / path
        if not fp.is_file():
            res["status"] = "missing file"
        elif b < a:
            res["status"] = "bad range"
        else:
            flat = flats.setdefault(path, Flat(fp))
            frags = [" ".join(f.split()) for f in re.split(r"…|\.\.\.", quote)]
            frags = [f for f in frags if f]
            if not frags:
                res["status"] = "empty quote"
            else:
                span = flat.find(frags, (a, b))
                if span is None:
                    res["status"] = "not found"
                elif span[0] >= a and span[1] <= b:
                    res["status"], res["found"] = "ok", span
                elif span[0] >= a - slack and span[1] <= b + slack:
                    res["status"], res["found"] = "shifted", span
                else:
                    res["status"], res["found"] = "wrong lines", span
        results.append(res)
        if res["status"] != "ok":
            where = f" (found at {res['found'][0]}-{res['found'][1]})" if res["found"] else ""
            problems.append(f"report line {res['at']}: CITE {path} {a}-{b}: {res['status']}{where}")
    if not results:
        problems.append("no <<<CITE blocks in the report")

    reads: dict[str, list[tuple[int, int]]] = {}
    for m in READ_RE.finditer(text):
        reads.setdefault(m.group(1) or m.group(2), []).append((int(m.group(3)), int(m.group(4))))
    for path in (files or []):
        fp = root / path
        if not fp.is_file():
            problems.append(f"--files: `{path}` doesn't exist")
            continue
        total = len(read(fp).splitlines())
        covered = set()
        for a, b in reads.get(path, []):
            covered.update(range(a, b + 1))
        gaps = [n for n in range(1, total + 1) if n not in covered]
        if gaps:
            problems.append(f"`{path}` not read in full: missing lines {ranges(gaps)}")
        if terms:
            lowered = [t.lower() for t in terms]
            spans = [r["found"] for r in results if r["path"] == path and r["found"]]
            for n, line in enumerate(read(fp).splitlines(), 1):
                if any(t in line.lower() for t in lowered) and not any(s[0] <= n <= s[1] for s in spans):
                    problems.append(f"`{path}`:{n} mentions a term and no citation covers it: "
                                    f"{line.strip()[:80]}")
    return results, problems


def ranges(nums: list[int]) -> str:
    out, start, prev = [], None, None
    for n in nums:
        if start is None:
            start = prev = n
        elif n == prev + 1:
            prev = n
        else:
            out.append(f"{start}-{prev}" if start != prev else str(start))
            start = prev = n
    if start is not None:
        out.append(f"{start}-{prev}" if start != prev else str(start))
    return ", ".join(out)


# ---------------------------------------------------------------- snapshot

def take_snapshot(root: Path, paths: list[str]) -> dict:
    files = {}
    for p in paths:
        base = root / p
        if base.is_file():
            files[rel(root, base)] = sha256(base)
        elif base.is_dir():
            for f in walk_files(base):
                files[rel(root, f)] = sha256(f)
    return {"created": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "paths": paths, "files": files}


def latest_snapshot(root: Path) -> Path | None:
    d = root / "snapshots"
    snaps = sorted(d.glob("*.json")) if d.is_dir() else []
    return snaps[-1] if snaps else None


def diff_snapshots(old: dict, new: dict) -> dict:
    a, b = old.get("files", {}), new.get("files", {})
    return {
        "added": sorted(set(b) - set(a)),
        "removed": sorted(set(a) - set(b)),
        "changed": sorted(k for k in set(a) & set(b) if a[k] != b[k]),
    }


# ---------------------------------------------------------------- extract

def blocks(lines: list[str]):
    """Yield (start, end, section, header_or_None, text)."""
    section, i, para = "", 0, []
    while i < len(lines):
        line = lines[i]
        hm = re.match(r"^#{1,6}\s+(.*)$", line)
        cells = split_row(line)
        if cells is not None and i + 1 < len(lines) and SEP_RE.match(lines[i + 1]):
            if para:
                yield para[0][0], para[-1][0], section, None, "\n".join(t for _, t in para)
                para = []
            header, j = line, i + 2
            while j < len(lines) and split_row(lines[j]) is not None:
                yield j + 1, j + 1, section, header, lines[j]
                j += 1
            i = j
            continue
        if hm or not line.strip():
            if para:
                yield para[0][0], para[-1][0], section, None, "\n".join(t for _, t in para)
                para = []
            if hm:
                section = hm.group(1).strip()
                yield i + 1, i + 1, section, None, line
        else:
            para.append((i + 1, line))
        i += 1
    if para:
        yield para[0][0], para[-1][0], section, None, "\n".join(t for _, t in para)


def extract(root: Path, terms: list[str]):
    lowered = [t.lower() for t in terms]
    hits = []
    for p in md_files(root):
        for a, b, section, header, text in blocks(read(p).splitlines()):
            if any(t in text.lower() for t in lowered):
                hits.append((rel(root, p), a, b, section, header, text))
    return hits


# ---------------------------------------------------------------- CLI

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="wikicheck", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("lint", help="run the seven checks")
    p.add_argument("--root", default=".")

    p = sub.add_parser("cite", help="verify the citations of a report")
    p.add_argument("report")
    p.add_argument("--root", default=".")
    p.add_argument("--slack", type=int, default=3, help="lines a quote may be off and count as 'shifted'")
    p.add_argument("--terms", default="", help="comma-separated: mentions no citation covers are listed")
    p.add_argument("--files", default="", help="comma-separated: files the report had to read in full")
    p.add_argument("--expect-model", default="")

    p = sub.add_parser("snapshot", help="hash the ground truth and diff against the last snapshot")
    p.add_argument("--root", default=".")
    p.add_argument("--paths", default="raw", help="comma-separated paths to hash (default: raw)")
    p.add_argument("--against", default="", help="snapshot to compare with (default: the latest)")
    p.add_argument("--out", default="", help="save the new snapshot here (never overwrites)")

    p = sub.add_parser("hash", help="print a file's sha256")
    p.add_argument("files", nargs="+")

    p = sub.add_parser("extract", help="every mention of the terms, with its paragraph or table row")
    p.add_argument("terms", nargs="+")
    p.add_argument("--root", default=".")

    a = ap.parse_args(argv)

    if a.cmd == "hash":
        for f in a.files:
            h = sha256(Path(f))
            print(f"{f}: sha256:{h[:12]}  (full: {h})")
        return 0

    root = Path(a.root).resolve()
    if not root.is_dir():
        print(f"--root {a.root}: not a folder", file=sys.stderr)
        return 2

    if a.cmd == "lint":
        found = lint(root)
        for tag, loc, msg in found:
            print(f"[{tag}] {loc}: {msg}")
        print(f"\n{len(CHECKS)} checks · {len(found)} candidate(s)" if found
              else f"{len(CHECKS)} checks · 0 candidates")
        return 1 if found else 0

    if a.cmd == "cite":
        split = lambda s: [x.strip() for x in s.split(",") if x.strip()]
        results, problems = cite(Path(a.report), root, a.slack, split(a.terms),
                                 split(a.files), a.expect_model)
        counts: dict[str, int] = {}
        for r in results:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
        for line in problems:
            print(line)
        summary = ", ".join(f"{v} {k}" for k, v in sorted(counts.items())) or "none"
        print(f"\n{len(results)} citation(s): {summary} · {len(problems)} problem(s)")
        return 1 if problems else 0

    if a.cmd == "snapshot":
        paths = [x.strip() for x in a.paths.split(",") if x.strip()]
        new = take_snapshot(root, paths)
        prev = Path(a.against) if a.against else latest_snapshot(root)
        if prev and not prev.is_absolute() and not prev.exists():
            prev = root / prev
        if prev and prev.is_file():
            d = diff_snapshots(json.loads(read(prev)), new)
            print(f"against {prev.name}:")
            for k in ("added", "removed", "changed"):
                for f in d[k]:
                    print(f"  {k:8} {f}")
            if not any(d.values()):
                print("  no changes")
        else:
            print("no previous snapshot to compare with")
        print(f"{len(new['files'])} file(s) hashed")
        if a.out:
            out = Path(a.out)
            out = out if out.is_absolute() else root / out
            if out.exists():
                print(f"{out} already exists: snapshots are never overwritten", file=sys.stderr)
                return 2
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(new, indent=1, sort_keys=True) + "\n", encoding="utf-8")
            print(f"saved {rel(root, out) if out.is_relative_to(root) else out}")
        return 0

    if a.cmd == "extract":
        hits = extract(root, a.terms)
        for path, s, e, section, header, text in hits:
            loc = f"{path}:{s}" if s == e else f"{path}:{s}-{e}"
            print(f"== {loc}" + (f" · {section}" if section else ""))
            if header:
                print(header)
            print(text + "\n")
        print(f"{len(hits)} block(s)")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
