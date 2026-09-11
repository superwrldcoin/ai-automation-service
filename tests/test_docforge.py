"""Unit tests for demo/docforge.py — the template rendering engine used for
batch document generation. These tests run with the standard library
`unittest` module so no extra package manager or install step is required.
"""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "demo" / "docforge.py"

spec = importlib.util.spec_from_file_location("docforge", MODULE_PATH)
docforge = importlib.util.module_from_spec(spec)
sys.modules["docforge"] = docforge
spec.loader.exec_module(docforge)


class MoneyFilterTests(unittest.TestCase):
    def test_formats_plain_number(self):
        self.assertEqual(docforge.money(250000), "$250,000.00")

    def test_formats_string_with_existing_symbols(self):
        self.assertEqual(docforge.money("$1,200.50"), "$1,200.50")

    def test_returns_original_value_when_not_numeric(self):
        self.assertEqual(docforge.money("n/a"), "n/a")


class DateFilterTests(unittest.TestCase):
    def test_normalizes_iso_date(self):
        self.assertEqual(docforge.normalize_date("2026-01-05"), "January 05, 2026")

    def test_normalizes_slash_date(self):
        self.assertEqual(docforge.normalize_date("01/05/2026"), "January 05, 2026")

    def test_leaves_unparseable_value_untouched(self):
        self.assertEqual(docforge.normalize_date("not-a-date"), "not-a-date")


class RenderTests(unittest.TestCase):
    def test_substitutes_plain_field(self):
        rendered, missing = docforge.render("Hello {{ name }}!", {"name": "Dana"})
        self.assertEqual(rendered, "Hello Dana!")
        self.assertEqual(missing, set())

    def test_applies_filter(self):
        rendered, missing = docforge.render("Total: {{ price | money }}", {"price": "1500"})
        self.assertEqual(rendered, "Total: $1,500.00")
        self.assertEqual(missing, set())

    def test_tracks_missing_fields(self):
        rendered, missing = docforge.render("{{ unknown_field }}", {"name": "Dana"})
        self.assertEqual(rendered, "{{ unknown_field }}")
        self.assertEqual(missing, {"unknown_field"})

    def test_conditional_block_shows_when_field_present(self):
        template = "Base{[ if repairs ]} + repairs needed{[ endif ]}."
        rendered, _ = docforge.render(template, {"repairs": "roof"})
        self.assertEqual(rendered, "Base + repairs needed.")

    def test_conditional_block_hides_when_field_empty(self):
        template = "Base{[ if repairs ]} + repairs needed{[ endif ]}."
        rendered, _ = docforge.render(template, {"repairs": ""})
        self.assertEqual(rendered, "Base.")


class SafeNameTests(unittest.TestCase):
    def test_uses_pattern_fields(self):
        name = docforge.safe_name("{property_id}_{last_name}", {"property_id": "12", "last_name": "Doe"}, 1, ".html")
        self.assertEqual(name, "12_Doe.html")

    def test_falls_back_when_pattern_field_missing(self):
        name = docforge.safe_name("{missing_field}", {"name": "Dana"}, 3, ".txt")
        self.assertEqual(name, "document_003.txt")

    def test_sanitizes_unsafe_characters(self):
        name = docforge.safe_name("{name}", {"name": "Dana / Whitmore?!"}, 1, ".html")
        self.assertNotIn("/", name)
        self.assertTrue(name.endswith(".html"))


if __name__ == "__main__":
    unittest.main()
