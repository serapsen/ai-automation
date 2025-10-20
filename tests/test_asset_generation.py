import os
import tempfile
import unittest

from src.pipeline.asset_generation import generate_image, ASPECT_SIZES


class TestAssetGeneration(unittest.TestCase):
    def test_generate_placeholder_without_api(self):
        brief = {
            "brand": {"colors": {"primary": "#336699"}},
            "message": "Test msg",
            "region": "EU-DE",
            "audience": "GenZ",
        }
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, "gen.png")
            res = generate_image("Alpha", brief, "16:9", out_path)
            self.assertTrue(os.path.isfile(res))
            from PIL import Image
            with Image.open(res) as im:
                self.assertEqual(im.size, ASPECT_SIZES["16:9"])    


if __name__ == "__main__":
    unittest.main()
