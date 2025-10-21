import unittest

from src.pipeline.brief import validate_and_normalize


class TestBrief(unittest.TestCase):
    def test_validate_and_normalize_defaults(self):
        brief = {"products": ["A"], "message": "hi"}
        out = validate_and_normalize(brief.copy())
        self.assertIn("aspect_ratios", out)
        self.assertEqual(out["aspect_ratios"], ["1:1", "9:16", "16:9"])

    def test_validate_requires_products(self):
        with self.assertRaises(SystemExit):
            validate_and_normalize({"message": "hi"})

    def test_region_audience_passthrough(self):
        b = {"products": ["A"], "message": "m", "region": "EMEA", "audience": "Gen Z"}
        out = validate_and_normalize(b.copy())
        self.assertEqual(out.get("region"), "EMEA")
        self.assertEqual(out.get("audience"), "Gen Z")


if __name__ == "__main__":
    unittest.main()
