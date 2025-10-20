import os
import tempfile
import unittest

from PIL import Image

from src.pipeline.post_processor import moderate_text, brand_compliance_summary, overlay_text, overlay_logo


class TestPostProcessor(unittest.TestCase):
    def test_moderate_text(self):
        self.assertEqual(moderate_text("This is fine"), [])
        hits = moderate_text("This is a fake and illegal offer")
        self.assertIn("fake", hits)
        self.assertIn("illegal", hits)

    def test_brand_compliance_summary(self):
        comp = brand_compliance_summary("#FF0055", True)
        self.assertTrue(comp["checks"][0]["passed"])  # brand_color_used
        self.assertTrue(comp["checks"][1]["passed"])  # logo_overlay

    def test_overlay_text_and_logo(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = os.path.join(tmp, "base.png")
            out_text = os.path.join(tmp, "text.png")
            out_logo = os.path.join(tmp, "final.png")
            logo = os.path.join(tmp, "logo.png")
            Image.new("RGB", (200, 100), (100, 100, 100)).save(base)
            Image.new("RGBA", (40, 20), (255, 0, 0, 255)).save(logo)

            overlay_text(base, "Hello", out_text, "#FFFFFF")
            self.assertTrue(os.path.isfile(out_text))

            overlay_logo(out_text, logo, out_logo)
            self.assertTrue(os.path.isfile(out_logo))


if __name__ == "__main__":
    unittest.main()
