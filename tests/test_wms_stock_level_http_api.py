"""Tests d'intégration HTTP pour StockLevel."""

import json
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from http.server import HTTPServer
from pathlib import Path

from engine.http import HttpHandler, make_app
from engine.auth import TokenAuth
from engine.repository import DocumentRepository


class TestStockLevelHttpApi(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = DocumentRepository(Path(self.tmp.name) / "test.db")
        self.auth = TokenAuth({"test-token"})
        self.server = HTTPServer(("127.0.0.1", 0), make_app(self.repo, auth=self.auth))
        self.server.store = self.repo
        self.server.auth = self.auth
        HttpHandler.log_message = lambda self, *a, **k: None
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.headers = {"Authorization": "Bearer test-token", "Content-Type": "application/json"}

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def _post(self, body):
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-levels",
            data=json.dumps(body).encode(), headers=self.headers, method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def _get(self, path=""):
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-levels" + path,
            headers={"Authorization": "Bearer test-token"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_create_stock_level(self):
        status, data = self._post({
            "organisation_id": "org-1", "product_id": "p1",
            "warehouse_id": "w1", "quantity": 10,
        })
        self.assertEqual(status, 201)
        self.assertEqual(data["item"]["quantity"], 10)

    def test_create_stock_level_negative_quantity(self):
        status, _ = self._post({
            "organisation_id": "org-1", "product_id": "p1",
            "warehouse_id": "w1", "quantity": -1,
        })
        self.assertEqual(status, 400)

    def test_create_stock_level_missing_token(self):
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-levels",
            data=json.dumps({
                "organisation_id": "org-1", "product_id": "p1",
                "warehouse_id": "w1", "quantity": 5,
            }).encode(),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            urllib.request.urlopen(req, timeout=10)
            self.fail("devrait lever 401")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 401)

    def test_get_stock_levels(self):
        self._post({
            "organisation_id": "org-1", "product_id": "p1",
            "warehouse_id": "w1", "quantity": 5,
        })
        status, data = self._get()
        self.assertEqual(status, 200)
        self.assertIsInstance(data["items"], list)

    def test_get_stock_level_by_id(self):
        _, created = self._post({
            "organisation_id": "org-1", "product_id": "p1",
            "warehouse_id": "w1", "quantity": 5,
        })
        lid = created["item"]["id"]
        status, data = self._get(f"/{lid}")
        self.assertEqual(status, 200)
        self.assertEqual(data["item"]["id"], lid)

    def test_get_stock_level_not_found(self):
        status, _ = self._get("/inexistant")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
