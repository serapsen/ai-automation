import os
import tempfile
import unittest

from src.reporting.summary import compute_uniqueness


class TestSummary(unittest.TestCase):
    def test_compute_uniqueness(self):
        with tempfile.TemporaryDirectory() as td:
            p1 = os.path.join(td, "a.png")
            p2 = os.path.join(td, "b.png")
            p3 = os.path.join(td, "c.png")
            with open(p1, "wb") as f: f.write(b"same")
            with open(p2, "wb") as f: f.write(b"same")
            with open(p3, "wb") as f: f.write(b"different")
            res = compute_uniqueness([p1, p2, p3])
            self.assertEqual(res["count"], 2)
            self.assertEqual(len(res["hashes"]), 3)


if __name__ == "__main__":
    unittest.main()
