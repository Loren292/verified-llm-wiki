"""Each check is tested against errors planted on purpose: checks must fail loudly too.

Run from the repo root:  python -m unittest discover -s tests -v
"""
import datetime as dt
import importlib.util
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("wikicheck", REPO / "tools" / "wikicheck.py")
wc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wc)

NOW = dt.datetime(2026, 10, 28, 15, 0)


class ExampleWiki(unittest.TestCase):
    """A fresh copy of example/ for every test."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "wiki"
        shutil.copytree(REPO / "example", self.root)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def lint(self, tag=None):
        found = wc.lint(self.root, now=NOW)
        return [f for f in found if tag is None or f[0].startswith(tag)]

    def append(self, rel, text):
        p = self.root / rel
        p.write_text(p.read_text(encoding="utf-8") + text, encoding="utf-8")

    def replace(self, rel, old, new):
        p = self.root / rel
        t = p.read_text(encoding="utf-8")
        self.assertIn(old, t, f"test setup: '{old}' not in {rel}")
        p.write_text(t.replace(old, new, 1), encoding="utf-8")


class TestCleanFolders(unittest.TestCase):
    def test_example_is_clean(self):
        self.assertEqual(wc.lint(REPO / "example", now=NOW), [])

    def test_template_is_clean(self):
        self.assertEqual(wc.lint(REPO / "template", now=NOW), [])


class TestL1Index(ExampleWiki):
    def test_file_not_in_index(self):
        (self.root / "wiki" / "new-page.md").write_text("# New\n", encoding="utf-8")
        found = self.lint("L1")
        self.assertEqual(len(found), 1)
        self.assertIn("wiki/new-page.md", found[0][1])

    def test_index_points_to_deleted_file(self):
        (self.root / "wiki" / "orders-table.md").unlink()
        self.assertTrue(any("doesn't exist" in f[2] for f in self.lint("L1")))

    def test_bad_type(self):
        self.replace("index.md", "| `pending.md` | state |", "| `pending.md` | status |")
        self.assertTrue(any("type 'status'" in f[2] for f in self.lint("L1")))

    def test_folder_entry_covers_its_files(self):
        (self.root / "raw" / "october.csv").write_text("x\n", encoding="utf-8")
        self.assertEqual(self.lint("L1"), [])


class TestL2Links(ExampleWiki):
    def test_missing_page(self):
        self.append("wiki/metrics.md", "\nSee [[forecast]].\n")
        self.assertTrue(any("[[forecast]]" in f[2] for f in self.lint("L2")))

    def test_missing_heading(self):
        self.append("wiki/metrics.md", "\nSee [[orders-table#customer]].\n")
        self.assertTrue(any("no heading 'customer'" in f[2] for f in self.lint("L2")))

    def test_link_in_code_is_ignored(self):
        self.append("wiki/metrics.md", "\nWrite links as `[[page]]`.\n\n```\n[[nothing]]\n```\n")
        self.assertEqual(self.lint("L2"), [])


class TestL3Registry(ExampleWiki):
    def test_unregistered_id(self):
        self.append("wiki/metrics.md", "\nThis follows D9.\n")
        self.assertTrue(any("D9 is used but not registered" in f[2] for f in self.lint("L3")))

    def test_executed_without_evidence(self):
        self.replace("registry.md", "| decided | — | — |", "| executed | — | — |")
        self.assertTrue(any("D2 is 'executed' with no evidence" in f[2] for f in self.lint("L3")))

    def test_bad_status(self):
        self.replace("registry.md", "| H1 | 3 of the 12 September orders were refunded | active |",
                     "| H1 | 3 of the 12 September orders were refunded | done |")
        self.assertTrue(any("status 'done'" in f[2] for f in self.lint("L3")))

    def test_duplicate_id(self):
        self.replace("registry.md", "| D2 |", "| D1 |")
        self.assertTrue(any("registered twice" in f[2] for f in self.lint("L3")))

    def test_cancelled_used_as_current(self):
        self.replace("registry.md", "| D2 | Revenue and AOV are also shown by week | decided |",
                     "| D2 | Revenue and AOV are also shown by week | cancelled |")
        found = self.lint("L3")
        self.assertTrue(any("D2 is cancelled" in f[2] and f[1].startswith("pending.md") for f in found))

    def test_page_without_row(self):
        (self.root / "registry" / "H7.md").write_text("# H7\n", encoding="utf-8")
        self.assertTrue(any("registry/H7.md" == f[1] for f in self.lint("L3")))


class TestL4Superseded(ExampleWiki):
    def test_old_value_reappears(self):
        self.append("wiki/orders-table.md", "\nAverage order: $43.04.\n")
        found = self.lint("L4")
        self.assertEqual(len(found), 1)
        self.assertIn("$43.04", found[0][2])

    def test_old_value_marked_is_allowed(self):
        self.append("wiki/orders-table.md", "\nIt used to be $43.04 (old).\n")
        self.assertEqual(self.lint("L4"), [])

    def test_value_boundaries(self):
        self.append("wiki/orders-table.md", "\nA different number: $43.045 and 1$516.50.\n")
        self.assertEqual(self.lint("L4"), [])


class TestL5Provenance(ExampleWiki):
    def test_source_changed(self):
        self.append("raw/orders.csv", "1013,2026-09-30,20.00,paid\n")
        found = self.lint("L5")
        self.assertEqual(len(found), 2)  # both pages derived from it
        self.assertTrue(all("may be stale" in f[2] for f in found))

    def test_source_missing(self):
        self.replace("wiki/metrics.md", "raw/orders.csv sha256", "raw/sales.csv sha256")
        self.assertTrue(any("doesn't exist" in f[2] for f in self.lint("L5")))


class TestL6Log(ExampleWiki):
    def test_future_time(self):
        self.append("log.md", "| 2026-10-28 18:00 | me | x | y | z |\n")
        self.assertTrue(any("in the future" in f[2] for f in self.lint("L6")))

    def test_out_of_order(self):
        self.append("log.md", "| 2026-10-28 09:00 | me | x | y | z |\n")
        self.assertTrue(any("earlier than" in f[2] for f in self.lint("L6")))

    def test_not_a_clock_time(self):
        self.append("log.md", "| around 3pm | me | x | y | z |\n")
        self.assertTrue(any("not a clock time" in f[2] for f in self.lint("L6")))

    def test_nothing_checked(self):
        self.append("log.md", "| 2026-10-28 14:30 | me | x | y | — |\n")
        self.assertTrue(any("what was checked" in f[2] for f in self.lint("L6")))


class TestL7Rules(ExampleWiki):
    def test_rule_without_origin(self):
        self.replace("CLAUDE.md", "## 5 · The cycle", "8. **Always be brief.**\n\n## 5 · The cycle")
        found = self.lint("L7")
        self.assertEqual(len(found), 1)
        self.assertIn("Always be brief", found[0][2])


class TestCite(ExampleWiki):
    def report(self, body):
        p = self.tmp / "report.md"
        p.write_text("MODEL: test-model\n\n" + body, encoding="utf-8")
        return p

    def run_cite(self, body, **kw):
        return wc.cite(self.report(body), self.root, **kw)

    def test_ok(self):
        results, problems = self.run_cite(
            "<<<CITE wiki/metrics.md 13\n| Average order value (AOV) | Revenue / Orders | $41.62 |\nCITE>>>\n")
        self.assertEqual(results[0]["status"], "ok")
        self.assertEqual(problems, [])

    def test_shifted(self):
        results, _ = self.run_cite(
            "<<<CITE wiki/metrics.md 11\n| Average order value (AOV) | Revenue / Orders | $41.62 |\nCITE>>>\n")
        self.assertEqual(results[0]["status"], "shifted")
        self.assertEqual(results[0]["found"], (13, 13))

    def test_rewritten_quote_is_not_found(self):
        results, _ = self.run_cite("<<<CITE wiki/metrics.md 13\nAOV is about $42\nCITE>>>\n")
        self.assertEqual(results[0]["status"], "not found")

    def test_ellipsis_and_line_breaks(self):
        results, _ = self.run_cite(
            "<<<CITE wiki/orders-table.md 19-20\nWhether it includes shipping … in the data\nCITE>>>\n")
        self.assertEqual(results[0]["status"], "ok")

    def test_uncovered_mentions_and_unread_lines(self):
        _, problems = self.run_cite(
            "<<<CITE wiki/metrics.md 13\n| Average order value (AOV) | Revenue / Orders | $41.62 |\nCITE>>>\n"
            "READ wiki/metrics.md 1-10\n",
            files=["wiki/metrics.md"], terms=["AOV"])
        self.assertTrue(any("not read in full: missing lines 11-18" in p for p in problems))
        self.assertTrue(any(":17 mentions a term" in p for p in problems))

    def test_wrong_model(self):
        _, problems = self.run_cite(
            "<<<CITE wiki/metrics.md 13\n| Average order value (AOV) | Revenue / Orders | $41.62 |\nCITE>>>\n",
            expect_model="other-model")
        self.assertTrue(any("expected 'other-model'" in p for p in problems))


class TestSnapshotAndExtract(ExampleWiki):
    def test_snapshot_diff(self):
        old = json.loads(next((self.root / "snapshots").glob("*.json")).read_text(encoding="utf-8"))
        self.append("raw/orders.csv", "1013,2026-09-30,20.00,paid\n")
        (self.root / "raw" / "october.csv").write_text("x\n", encoding="utf-8")
        d = wc.diff_snapshots(old, wc.take_snapshot(self.root, ["raw"]))
        self.assertEqual(d, {"added": ["raw/october.csv"], "removed": [], "changed": ["raw/orders.csv"]})

    def test_snapshot_never_overwrites(self):
        name = next((self.root / "snapshots").glob("*.json")).name
        code = wc.main(["snapshot", "--root", str(self.root), "--out", f"snapshots/{name}"])
        self.assertEqual(code, 2)

    def test_extract_finds_paragraphs_and_table_rows(self):
        hits = wc.extract(self.root, ["AOV"])
        where = {(h[0], h[1]) for h in hits}
        self.assertIn(("wiki/metrics.md", 13), where)          # a table row
        row = next(h for h in hits if h[0] == "wiki/metrics.md" and h[1] == 13)
        self.assertIn("| Metric | Definition | Value |", row[4])  # with its header


class LargeWiki(ExampleWiki):
    """example/ grown the way template/CLAUDE.md section 12 says: an area with its own
    index, the log rotated by month, and closed registry rows moved to the archive."""

    D1_ROW = ("| D1 | Refunded orders are left out of orders, revenue and AOV | executed | "
              "`wiki/metrics.md` recomputed on `raw/orders.csv` (sha256 5a55063575c9), "
              "snapshot `2026-10-28 1415` | [[D1]] |")

    def setUp(self):
        super().setUp()
        r = self.root
        area = r / "areas" / "sales"
        area.mkdir(parents=True)
        (area / "index.md").write_text(
            "# Index · sales\n\n| Path | Type | Answers |\n|---|---|---|\n"
            "| `pending.md` | state | What's left in this area |\n"
            "| `channels.md` | page | AOV by sales channel |\n", encoding="utf-8")
        (area / "pending.md").write_text(
            "# Pending · sales\n\n| Task | Blocks | Depends on |\n|---|---|---|\n", encoding="utf-8")
        (area / "channels.md").write_text(
            "# Channels\n\nAOV by channel, with the definition in [[metrics]].\n", encoding="utf-8")
        row = "| `wiki/orders-table.md` | page | What each column of the orders export means, according to the data |"
        self.replace("index.md", row, row + "\n| `areas/` | page | One folder per area, each with its own index |")

        (r / "log").mkdir()
        (r / "log" / "2026-10.md").write_text((r / "log.md").read_text(encoding="utf-8"), encoding="utf-8")
        (r / "log.md").unlink()
        self.replace("index.md", "| `log.md` | log | Who changed what and when: the chronology. Read only its last lines before writing |",
                     "| `log/` | log | Who changed what and when, one file per month. Read the tail of the current month |")

        self.replace("registry.md", self.D1_ROW + "\n", "")
        (r / "registry-archive.md").write_text(
            "# Registry archive\n\nClosed items, moved out of `registry.md`.\n\n"
            "| ID | Decision | Status | Evidence | Page | Area |\n|---|---|---|---|---|---|\n"
            + self.D1_ROW + " all |\n", encoding="utf-8")
        row = "| `registry.md` | state | Only tables: each D, H, T and P with its status, evidence and page, plus superseded values |"
        self.replace("index.md", row, row + "\n| `registry-archive.md` | state | Closed items of the registry |")


class TestScale(LargeWiki):
    def test_large_is_clean(self):
        self.assertEqual(self.lint(), [])

    def test_file_missing_from_area_index(self):
        (self.root / "areas" / "sales" / "forecast.md").write_text("# Forecast\n", encoding="utf-8")
        found = self.lint("L1")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0][1], "areas/sales/forecast.md")
        self.assertIn("not in areas/sales/index.md", found[0][2])

    def test_nested_folder_belongs_to_its_area(self):
        (self.root / "areas" / "sales" / "notes").mkdir()
        (self.root / "areas" / "sales" / "notes" / "call.md").write_text("# Call\n", encoding="utf-8")
        self.assertTrue(any("not in areas/sales/index.md" in f[2] for f in self.lint("L1")))

    def test_area_index_points_to_deleted_file(self):
        (self.root / "areas" / "sales" / "channels.md").unlink()
        found = self.lint("L1")
        self.assertTrue(any(f[1].startswith("areas/sales/index.md:") and "doesn't exist" in f[2] for f in found))

    def test_area_not_listed_above(self):
        self.replace("index.md", "| `areas/` | page | One folder per area, each with its own index |\n", "")
        self.assertTrue(any("doesn't list `areas/sales/`" in f[2] for f in self.lint("L1")))

    def test_entry_outside_its_month(self):
        self.append("log/2026-10.md", "| 2026-11-02 10:00 | me | x | y | z |\n")
        self.assertTrue(any("entry in the log of 2026-10" in f[2] for f in self.lint("L6")))

    def test_rotated_logs_are_read_in_order(self):
        (self.root / "log" / "2026-09.md").write_text(
            "# Log · 2026-09\n\n| When | Who | Files | What | Checked |\n|---|---|---|---|---|\n"
            "| 2026-09-30 18:00 | me | x | y | z |\n", encoding="utf-8")
        self.assertEqual(self.lint("L6"), [])

    def test_rotated_log_badly_named(self):
        (self.root / "log" / "october.md").write_text("# Log\n", encoding="utf-8")
        self.assertTrue(any("named after its month" in f[2] for f in self.lint("L6")))

    def test_open_item_in_archive(self):
        self.replace("registry-archive.md", "| executed |", "| decided |")
        self.assertTrue(any("only closed items go to the archive" in f[2] for f in self.lint("L3")))

    def test_unknown_area(self):
        self.replace("registry-archive.md", " all |\n", " marketing |\n")
        self.assertTrue(any("area 'marketing'" in f[2] for f in self.lint("L3")))

    def test_same_id_in_registry_and_archive(self):
        self.replace("registry.md", "| D2 |", self.D1_ROW + "\n| D2 |")
        found = [f for f in self.lint("L3") if "D1 is registered twice" in f[2]]
        self.assertEqual(len(found), 1)
        self.assertTrue(found[0][1].startswith("registry-archive.md:") and "also registry.md:" in found[0][2])

    def test_only_filter(self):
        (self.root / "areas" / "sales" / "forecast.md").write_text("# Forecast\n", encoding="utf-8")
        (self.root / "wiki" / "new.md").write_text("# New\n", encoding="utf-8")
        found = wc.lint(self.root, now=NOW, only="areas/sales")
        self.assertEqual([f[1] for f in found], ["areas/sales/forecast.md"])

    def test_extract_within_an_area(self):
        hits = wc.extract(self.root, ["AOV"], "areas/sales")
        self.assertTrue(hits)
        self.assertTrue(all(h[0].startswith("areas/sales/") for h in hits))


class TestTemplateAndExampleInSync(unittest.TestCase):
    """example/ is template/ filled in: everything but section 1 of the schema must match."""

    def test_schema_differs_only_in_section_1(self):
        strip = lambda t: re.sub(r"## 1 · The project\n.*?\n## 2 · ", "## 1\n## 2 · ", t, flags=re.S)
        a = (REPO / "template" / "CLAUDE.md").read_text(encoding="utf-8")
        b = (REPO / "example" / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertEqual(strip(a), strip(b))

    def test_roles_and_workflows_are_identical(self):
        for folder in ("roles", "workflows"):
            for f in (REPO / "template" / folder).glob("*.md"):
                self.assertEqual(f.read_bytes(), (REPO / "example" / folder / f.name).read_bytes(), f.name)


if __name__ == "__main__":
    unittest.main()
