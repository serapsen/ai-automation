import os
import tempfile
import unittest
import yaml

from main import run_pipeline


class TestPipelineE2E(unittest.TestCase):
    def test_run_pipeline_with_temp_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            assets_root = os.path.join(tmp, "assets")
            output_root = os.path.join(tmp, "out")
            os.makedirs(assets_root, exist_ok=True)
            brief_path = os.path.join(tmp, "brief.yaml")
            brief = {
                "products": ["AlphaSneaker"],
                "assets_root": assets_root,
                "output_root": output_root,
                "aspect_ratios": ["1:1"],
                "message": "Hello",
                "brand": {"colors": {"primary": "#FF0055"}},
            }
            with open(brief_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(brief, f)

            summary = run_pipeline(brief_path)
            self.assertIn("AlphaSneaker", summary["products"]) 
            out_dir = os.path.join(output_root, "AlphaSneaker", "1x1")
            self.assertTrue(os.path.isdir(out_dir))
            finals = [fn for fn in os.listdir(out_dir) if fn.endswith("_final.png")] 
            self.assertGreaterEqual(len(finals), 1)


if __name__ == "__main__":
    unittest.main()
