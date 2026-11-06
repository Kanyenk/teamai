"""Tests HTTP des ajustements de stock (http.server)."""
import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import HTTPServer
from types import SimpleNamespace

from engine.http import make_app
from engine.stock_adjustment_repository import StockAdjustmentRepository
from engine.stock_adjustment_service import StockAdjustmentService


class TestStockAdjustmentHttpApi(unittest.TestCase):
    """Tests HTTP des endpoints ajustements."""

    def setUp(self):
        """Démarre un serveur HTTP sur un port éphémère."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.repo = StockAdjustmentRepository(db_path=self.db_path)
        self.service = StockAdjustmentService(self.repo)
        store = SimpleNamespace(db_path=self.db_path)
        handler = make_app(store, auth=None)
        self.server = HTTPServer(("127.0.0.1", 0), handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.port}"

    def tearDown(self):
        """Arrête le serveur et supprime la base."""
        self.server.shutdown()
        self.server.server_close()
        os.unlink(self.db_path)

    def _request(self, method, path, payload=None):
        """Envoie une requête HTTP et retourne (status, body)."""
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(
            self.base + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())

    def _create_adjustment(self, **overrides):
        """Crée un ajustement de test via l'API."""
        payload = {
            "organisation_id": "org-1",
            "warehouse_id": "wh-1",
            "product_id": "prod-1",
            "quantity": 5,
            "reason": "correction",
        }
        payload.update(overrides)
        status, body = self._request("POST", "/api/v1/wms/stock-adjustments", payload)
        return status, body

    def test_create_adjustment(self):
        """POST /api/v1/wms/stock-adjustments doit créer un ajustement (201)."""
        status, body = self._create_adjustment()
        self.assertEqual(status, 201)
        self.assertIn("item", body)
        self.assertEqual(body["item"]["quantity"], 5)

    def test_create_adjustment_negative(self):
        """POST avec quantité négative doit créer un ajustement (201)."""
        status, body = self._create_adjustment(quantity=-3, reason="loss")
        self.assertEqual(status, 201)
        self.assertEqual(body["item"]["quantity"], -3)

    def test_create_adjustment_invalid_reason(self):
        """POST avec raison invalide doit retourner 400."""
        status, _ = self._create_adjustment(reason="inconnu")
        self.assertEqual(status, 400)

    def test_list_adjustments(self):
        """GET /api/v1/wms/stock-adjustments doit lister les ajustements (200)."""
        self._create_adjustment()
        status, body = self._request("GET", "/api/v1/wms/stock-adjustments?organisation_id=org-1")
        self.assertEqual(status, 200)
        self.assertEqual(len(body["items"]), 1)

    def test_list_adjustments_missing_org(self):
        """GET sans organisation_id doit retourner 400."""
        status, _ = self._request("GET", "/api/v1/wms/stock-adjustments")
        self.assertEqual(status, 400)

    def test_get_adjustment(self):
        """GET /api/v1/wms/stock-adjustments/{id} doit retourner l'ajustement (200)."""
        _, body = self._create_adjustment()
        adj_id = body["item"]["id"]
        status, body = self._request("GET", f"/api/v1/wms/stock-adjustments/{adj_id}")
        self.assertEqual(status, 200)
        self.assertEqual(body["item"]["id"], adj_id)

    def test_get_adjustment_not_found(self):
        """GET sur un ajustement inexistant doit retourner 404."""
        status, _ = self._request("GET", "/api/v1/wms/stock-adjustments/adj-inexistant")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
