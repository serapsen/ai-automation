import os
import unittest
from unittest import mock

from src.storage.azure_storage import AzureBlobStorage


class TestAzureStoragePaths(unittest.TestCase):
    @mock.patch.dict(os.environ, {"AZURE_BLOB_PREFIX": "images/prefix"}, clear=False)
    def test_blob_path_with_prefix(self):
        st = AzureBlobStorage()
        p = st._blob_path("Alpha/1x1/final.png")
        self.assertEqual(p, "images/prefix/Alpha/1x1/final.png")

    @mock.patch.dict(os.environ, {"AZURE_BLOB_PREFIX": ""}, clear=False)
    def test_blob_path_without_prefix(self):
        st = AzureBlobStorage()
        p = st._blob_path("/Alpha/1x1/final.png")
        self.assertEqual(p, "Alpha/1x1/final.png")

    @mock.patch.dict(os.environ, {"AZURE_BLOB_PREFIX": "folder\\sub"}, clear=False)
    def test_blob_path_backslash_normalization(self):
        st = AzureBlobStorage()
        p = st._blob_path("Beta\\9x16\\file.png")
        self.assertEqual(p, "folder/sub/Beta/9x16/file.png")


if __name__ == "__main__":
    unittest.main()
