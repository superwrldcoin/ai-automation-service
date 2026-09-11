"""Lightweight integrity checks for the static site in docs/. These catch the
most common regressions in a static-HTML project: malformed JSON manifests
and broken same-site links, without needing a browser or JS runtime.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

LINK_RE = re.compile(r'href="([^"]+)"')
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "tel:", "#")


class ManifestJsonTests(unittest.TestCase):
    def test_all_manifest_and_config_json_files_parse(self):
        json_files = list(DOCS.rglob("manifest*.json")) + list(DOCS.rglob("config.json"))
        self.assertTrue(json_files, "expected at least one manifest/config JSON file under docs/")
        for path in json_files:
            with self.subTest(path=str(path.relative_to(ROOT))):
                json.loads(path.read_text(encoding="utf-8"))


class InternalLinkTests(unittest.TestCase):
    def test_relative_links_resolve_to_real_files(self):
        html_files = list(DOCS.rglob("*.html"))
        self.assertTrue(html_files, "expected at least one HTML file under docs/")
        broken = []
        for html_file in html_files:
            text = html_file.read_text(encoding="utf-8", errors="ignore")
            for href in LINK_RE.findall(text):
                if href.startswith(EXTERNAL_PREFIXES) or not href.strip():
                    continue
                if "${" in href or "{{" in href:
                    continue  # JS template literals / server-side placeholders, not real links
                target = (html_file.parent / href.split("#")[0].split("?")[0]).resolve()
                if not target.exists():
                    broken.append(f"{html_file.relative_to(ROOT)} -> {href}")
        self.assertEqual(broken, [], "broken internal links found:\n" + "\n".join(broken))


class ClientFolderTests(unittest.TestCase):
    def test_every_client_folder_has_a_config(self):
        clients_dir = DOCS / "clients"
        if not clients_dir.exists():
            self.skipTest("no docs/clients directory yet")
        client_dirs = [p for p in clients_dir.iterdir() if p.is_dir()]
        missing = [p.name for p in client_dirs if not (p / "config.json").exists()]
        self.assertEqual(missing, [], f"client folders missing config.json: {missing}")


if __name__ == "__main__":
    unittest.main()
