import os
import tempfile
import unittest

from src.pipeline.asset_ingestion import normalize_aspect, aspect_to_dir, get_aspect_list, list_existing_assets


class TestAssetIngestion(unittest.TestCase):
    def test_normalize_aspect(self):
        self.assertEqual(normalize_aspect("1:1"), "1:1")
        self.assertEqual(normalize_aspect("1x1"), "1:1")
        self.assertEqual(normalize_aspect("9_16"), "9:16")
        self.assertEqual(normalize_aspect("16-9"), "16:9")

    def test_aspect_to_dir(self):
        self.assertEqual(aspect_to_dir("1:1"), "1x1")
        self.assertEqual(aspect_to_dir("9:16"), "9x16")

    def test_get_aspect_list_default(self):
        aspects = get_aspect_list({})
        self.assertEqual(aspects, ["1:1", "9:16", "16:9"])

    def test_list_existing_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            assets_root = os.path.join(tmp, "assets")
            prod = "AlphaSneaker"
            aspect_dir = os.path.join(assets_root, prod, "1x1")
            os.makedirs(aspect_dir, exist_ok=True)
            # create fake images (empty files with .png extension)
            open(os.path.join(aspect_dir, "a.png"), "wb").close()
            open(os.path.join(aspect_dir, "b.jpg"), "wb").close()

            found = list_existing_assets(prod, "1:1", assets_root)
            self.assertEqual(len(found), 2)
            self.assertTrue(all(os.path.isfile(p) for p in found))


if __name__ == "__main__":
    unittest.main()
