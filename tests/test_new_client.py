"""Tests for tools/new-client.py — the client app generator. These exercise the
real stamping logic against a temporary output directory so the suite never
writes into the tracked docs/clients folder.
"""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "new-client.py"

spec = importlib.util.spec_from_file_location("new_client", MODULE_PATH)
new_client = importlib.util.module_from_spec(spec)
sys.modules["new_client"] = new_client
spec.loader.exec_module(new_client)


class StampFilesTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dest = Path(self._tmp.name) / "acme-hvac"

    def test_stamps_expected_client_files(self):
        new_client.stamp_files(
            self.dest, "acme-hvac", "Acme HVAC", "#d35400", "hvac",
            "support@example.com", "https://example.com/clients/acme-hvac/",
        )
        expected = {"crm.html", "manifest-crm.json", "sw.js", "index.html",
                    "how-to.html", "client-handoff.html", "README.md", "icons"}
        actual = {p.name for p in self.dest.iterdir()}
        self.assertTrue(expected.issubset(actual))

    def test_handoff_page_contains_business_and_support_details(self):
        new_client.stamp_files(
            self.dest, "acme-hvac", "Acme HVAC", "#d35400", "hvac",
            "support@example.com", "https://example.com/clients/acme-hvac/",
        )
        handoff = (self.dest / "client-handoff.html").read_text(encoding="utf-8")
        self.assertIn("Acme HVAC", handoff)
        self.assertIn("support@example.com", handoff)
        self.assertIn("https://example.com/clients/acme-hvac/", handoff)

    def test_client_guide_has_link_and_support_filled_in(self):
        new_client.stamp_files(
            self.dest, "acme-hvac", "Acme HVAC", "#d35400", "hvac",
            "support@example.com", "https://example.com/clients/acme-hvac/",
        )
        guide = (self.dest / "how-to.html").read_text(encoding="utf-8")
        self.assertNotIn("[YOUR TOOL LINK GOES HERE]", guide)
        self.assertIn("https://example.com/clients/acme-hvac/", guide)
        self.assertIn("support@example.com", guide)

    def test_manifest_uses_theme_color(self):
        new_client.stamp_files(
            self.dest, "acme-hvac", "Acme HVAC", "#d35400", "hvac",
            "support@example.com", "https://example.com/clients/acme-hvac/",
        )
        manifest = json.loads((self.dest / "manifest-crm.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["theme_color"], "#d35400")
        self.assertEqual(manifest["name"], "Acme HVAC — Hub")


class ClientDirectoryTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.clients_dir = Path(self._tmp.name)
        self._orig_clients = new_client.CLIENTS
        new_client.CLIENTS = self.clients_dir
        self.addCleanup(setattr, new_client, "CLIENTS", self._orig_clients)

    def test_directory_lists_generated_clients(self):
        dest = self.clients_dir / "acme-hvac"
        new_client.stamp_files(
            dest, "acme-hvac", "Acme HVAC", "#d35400", "hvac",
            "support@example.com", "https://example.com/clients/acme-hvac/",
        )
        (dest / "config.json").write_text(json.dumps({
            "clientId": "acme-hvac", "business": "Acme HVAC", "trade": "hvac",
            "handoff": {"url": "https://example.com/clients/acme-hvac/",
                        "supportEmail": "support@example.com"},
        }), encoding="utf-8")

        new_client.write_client_directory()

        index_html = (self.clients_dir / "index.html").read_text(encoding="utf-8")
        self.assertIn("Acme HVAC", index_html)
        self.assertIn("support@example.com", index_html)

    def test_directory_handles_no_clients_yet(self):
        new_client.write_client_directory()
        index_html = (self.clients_dir / "index.html").read_text(encoding="utf-8")
        self.assertIn("No client apps have been generated yet.", index_html)


if __name__ == "__main__":
    unittest.main()
