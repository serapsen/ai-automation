import os
import tempfile
import unittest

from src.utils.hash import sha1_file


class TestHash(unittest.TestCase):
    def test_sha1_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"hello world")
            tmp_path = tmp.name
        try:
            h = sha1_file(tmp_path)
            self.assertEqual(h, "2aae6c35c94fcfb415dbe95f408b9ce91ee846ed")
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()
