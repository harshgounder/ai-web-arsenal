#!/usr/bin/env python3
"""
test-regressions.py: the defects in RECHECK.md section 8, as executable tests.

Every one of those defects was a plausible wrong answer that nothing caught. A note in a document does
not stop it coming back. A test does.

Run: python3 scripts/test-regressions.py
No network, no writes outside a temp directory. Standard library only.
"""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent


def load(name, filename):
    """Scripts have hyphens in their names, so they cannot be imported conventionally."""
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bc = load("build_corpus", "build-corpus.py")
vt = load("verify_tools", "verify-tools.py")


class TestBadgeFilter(unittest.TestCase):
    """Defect 10: the image filter matched file extensions, so 13 shields.io badges shipped as tools."""

    def test_shields_language_badge_is_a_badge(self):
        self.assertTrue(bc.is_badge_url("https://img.shields.io/badge/English-Click-yellow"))
        self.assertTrue(bc.is_badge_url("https://img.shields.io/badge/日本語-クリック-青"))

    def test_extension_still_caught(self):
        self.assertTrue(bc.is_badge_url("https://example.com/a/score.svg"))

    def test_glama_badge_path_is_a_badge(self):
        self.assertTrue(bc.is_badge_url("https://glama.ai/mcp/servers/owner/repo/badges/score.svg"))

    def test_a_real_tool_page_is_not_a_badge(self):
        self.assertFalse(bc.is_badge_url("https://github.com/projectdiscovery/nuclei"))
        self.assertFalse(bc.is_badge_url("https://glama.ai/mcp/servers/owner/repo"))
        self.assertFalse(bc.is_badge_url(""))


class TestBadgeRepair(unittest.TestCase):
    """Defect 10b: three real MCP servers were stored as badge URLs and nearly deleted as cleanup."""

    def test_leading_badge_form(self):
        self.assertEqual(bc.repair_badge_url("https://glama.ai/mcp/servers/badge/@x/y"),
                         "https://glama.ai/mcp/servers/@x/y")

    def test_trailing_badge_form(self):
        self.assertEqual(bc.repair_badge_url("https://glama.ai/mcp/servers/cdeust/Cortex/badge"),
                         "https://glama.ai/mcp/servers/cdeust/Cortex")

    def test_no_repair_for_ordinary_badges(self):
        self.assertIsNone(bc.repair_badge_url("https://img.shields.io/badge/English-Click-yellow"))

    def test_repaired_url_is_not_itself_a_badge(self):
        fixed = bc.repair_badge_url("https://glama.ai/mcp/servers/cdeust/Cortex/badge")
        self.assertFalse(bc.is_badge_url(fixed))


class TestUrlNormalisation(unittest.TestCase):
    """Defect 13: 687 rows held an owner/repo identifier in their url field."""

    def test_owner_repo_becomes_a_github_url(self):
        self.assertEqual(bc.normalize_url("nasa/spacewasm"), "https://github.com/nasa/spacewasm")

    def test_absolute_urls_untouched(self):
        for u in ("https://github.com/a/b", "http://x.y/z", ""):
            self.assertEqual(bc.normalize_url(u), u)

    def test_odd_slug_is_not_invented(self):
        # A space means the shape is not unambiguous, so guessing a URL would be inventing one.
        self.assertEqual(bc.normalize_url("skt elecom/bomlens"), "skt elecom/bomlens")

    def test_single_word_is_not_a_slug(self):
        self.assertEqual(bc.normalize_url("nuclei"), "nuclei")


class TestJunkNames(unittest.TestCase):
    """Defect 9-adjacent: a badge row named "badge" must be treated as junk and renamed from its URL."""

    def test_badge_names_are_junk(self):
        for n in ("badge", "Badges", "shield", "shields"):
            self.assertTrue(bc.JUNK_NAME.match(n), n)

    def test_real_names_are_not_junk(self):
        for n in ("nuclei", "mitmproxy", "Burp Suite"):
            self.assertFalse(bc.JUNK_NAME.match(n), n)

    def test_slug_has_no_path_separators(self):
        self.assertNotIn("/", bc.slug("CI/CD tools, 2026"))


class TestPacmanFallback(unittest.TestCase):
    """Defect 11: one broken repo made `pacman -Si` fail globally and 16 tools looked missing."""

    def test_falls_back_to_the_arch_api(self):
        vt._archweb_cache.clear()
        vt._RESOLVED_VIA.clear()
        with mock.patch.object(vt.subprocess, "run", side_effect=Exception("db invalid")), \
             mock.patch.object(vt, "http_json",
                               return_value={"results": [{"pkgname": "nmap", "repo": "extra",
                                                          "pkgver": "7.95", "pkgrel": "1"}]}):
            self.assertEqual(vt.pacman_has("nmap"), "7.95-1")
        self.assertEqual(vt._RESOLVED_VIA.get("nmap"), "archweb")

    def test_pacman_answer_wins_when_it_works(self):
        vt._archweb_cache.clear()
        vt._RESOLVED_VIA.clear()
        fake = mock.Mock(returncode=0, stdout="Name : nmap\nVersion : 7.95-1\n")
        with mock.patch.object(vt.subprocess, "run", return_value=fake):
            self.assertEqual(vt.pacman_has("nmap"), "7.95-1")
        self.assertEqual(vt._RESOLVED_VIA.get("nmap"), "pacman")

    def test_non_official_repo_does_not_count(self):
        vt._archweb_cache.clear()
        vt._RESOLVED_VIA.clear()
        with mock.patch.object(vt.subprocess, "run", side_effect=Exception("db invalid")), \
             mock.patch.object(vt, "http_json",
                               return_value={"results": [{"pkgname": "httpx", "repo": "chaotic-aur",
                                                          "pkgver": "1.0"}]}):
            self.assertIsNone(vt.pacman_has("httpx"))


class TestBootstrapOwnership(unittest.TestCase):
    """Defect 16: three orphaned scripts from an earlier numbering sat in a generated directory."""

    def test_numeric_script_pattern(self):
        import re
        pat = re.compile(r"^\d{2}-.*\.sh$")
        self.assertTrue(pat.match("40-install-mobile.sh"))
        self.assertFalse(pat.match("lib.sh"))
        self.assertFalse(pat.match("logs"))

    def test_generated_set_is_exactly_eleven(self):
        scripts = sorted(p.name for p in (ROOT / "bootstrap").glob("*.sh"))
        self.assertEqual(len(scripts), 11, scripts)


class TestCorpusInvariants(unittest.TestCase):
    """Defect 9: the corpus held tools and taxonomy nodes in one file and the total was quoted as tools."""

    def test_split_partitions_the_corpus(self):
        def n(f):
            return sum(1 for l in (ROOT / "data" / f).read_text(encoding="utf-8").splitlines() if l.strip())
        parts = n("corpus.tools.jsonl") + n("corpus.taxonomy.jsonl") + n("corpus.other.jsonl")
        self.assertEqual(parts, n("corpus.jsonl"))

    def test_tools_file_holds_only_tools(self):
        for line in (ROOT / "data" / "corpus.tools.jsonl").read_text(encoding="utf-8").splitlines():
            if line.strip():
                self.assertEqual(json.loads(line)["kind"], "tool")

    def test_no_image_urls_in_tools(self):
        import re
        for line in (ROOT / "data" / "corpus.tools.jsonl").read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            u = json.loads(line).get("url") or ""
            self.assertIsNone(re.search(r"img\.shields\.io|badgen\.net|/badges?/", u), u)


class TestReconciliationIdentity(unittest.TestCase):
    """Defect 12: the identity line printed "+ residue" and hid 75 orphan rows inside a word."""

    def test_every_term_sums_to_the_total(self):
        s = json.loads((ROOT / "data" / "reconcile" / "SUMMARY.json").read_text(encoding="utf-8"))
        terms = sum(int(s.get(k) or 0) for k in
                    ("admitted", "excluded", "held", "orphan", "unresolved", "unparsed"))
        self.assertEqual(terms, s["rows_total"])
        self.assertTrue(s["identity_holds"])

    def test_orphans_are_named_not_hidden(self):
        s = json.loads((ROOT / "data" / "reconcile" / "SUMMARY.json").read_text(encoding="utf-8"))
        self.assertIn("orphan", s)
        self.assertIn("not_in_corpus", s.get("exclusion_reasons", {}))


class TestAtomsAreLists(unittest.TestCase):
    """Defect: atoms written as a string shipped three times and rendered as garbage."""

    def test_no_domain_stores_atoms_as_a_string(self):
        for f in sorted((ROOT / "data" / "domains").glob("D*.json")):
            if f.stem.endswith(".index"):
                continue
            d = json.loads(f.read_text(encoding="utf-8"))
            self.assertIsInstance(d.get("atoms"), list, f.name)
            for e in d.get("entries", []):
                self.assertIsInstance(e.get("atom"), list, f"{f.name}:{e.get('id')}")


class TestIndexStaging(unittest.TestCase):
    """Defect 14: a pre-dedupe figure was printed as the promotable total."""

    def test_label_names_the_stage(self):
        text = (ROOT / "scripts" / "build-indexes.py").read_text(encoding="utf-8")
        self.assertIn("before cross-domain dedupe", text)

    def test_dedupe_runs_after_index_build(self):
        order = (ROOT / "AUTHORING.md").read_text(encoding="utf-8")
        self.assertLess(order.index("build-indexes"), order.index("dedupe-names"))


class TestDocsAndClaims(unittest.TestCase):
    """Defects 1-8 territory: claims with no check are the mechanism that let all of it happen."""

    def test_claims_file_has_checks(self):
        text = (ROOT / "data" / "claims.yaml").read_text(encoding="utf-8")
        self.assertGreater(text.count("check:"), 20)
        self.assertGreater(text.count("statement:"), 20)

    def test_no_em_dashes_in_authored_docs(self):
        for name in ("README.md", "RECHECK.md", "PLAN.md", "AUTHORING.md", "RESUME.md"):
            p = ROOT / name
            if p.exists():
                t = p.read_text(encoding="utf-8")
                self.assertNotIn("\u2014", t, name)
                self.assertNotIn("\u2013", t, name)


def main():
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    print(f"\nregression tests: {result.testsRun} run, "
          f"{len(result.failures)} failed, {len(result.errors)} errored")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
