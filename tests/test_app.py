import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/backend"))
from app import app


class AppTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_page_and_api_share_one_server(self):
        with self.client.get("/") as response:
            self.assertIn(b"Check Backend", response.data)
        self.assertEqual(self.client.get("/api/health").json["status"], "ok")
        self.assertEqual(len(self.client.get("/api/items").json), 2)

    def test_unknown_routes_and_source_are_not_served(self):
        for path in ("/app.py", "/requirements.txt", "/api/missing", "/static/../app.py"):
            self.assertEqual(self.client.get(path).status_code, 404, path)

    def test_unconfigured_storage_does_not_break_health(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(self.client.post("/api/storage/test").status_code, 503)
            self.assertEqual(self.client.get("/api/health").status_code, 200)

    @patch.dict(os.environ, {"AZURE_STORAGE_ACCOUNT_URL": "https://test.blob.core.windows.net"})
    @patch("app.storage")
    def test_storage_check_cleans_up_and_uses_unique_names(self, storage):
        blob = storage.return_value.get_blob_client.return_value
        blob.download_blob.return_value.readall.return_value = b"blob storage is working"
        for _ in range(2):
            response = self.client.post("/api/storage/test")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json["content"], "blob storage is working")
        names = [call.args[0] for call in storage.return_value.get_blob_client.call_args_list]
        self.assertEqual(len(set(names)), 2)
        self.assertEqual(blob.delete_blob.call_count, 2)

    @patch.dict(os.environ, {"AZURE_STORAGE_ACCOUNT_URL": "https://test.blob.core.windows.net"})
    @patch("app.storage")
    def test_failed_download_cleans_up_without_exposing_details(self, storage):
        blob = storage.return_value.get_blob_client.return_value
        blob.download_blob.side_effect = RuntimeError("sensitive detail")
        with self.assertLogs(app.logger, level="ERROR"):
            response = self.client.post("/api/storage/test")
        self.assertEqual(response.status_code, 502)
        self.assertNotIn(b"sensitive detail", response.data)
        blob.delete_blob.assert_called_once()
