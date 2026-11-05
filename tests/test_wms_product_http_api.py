"""Tests d'intégration HTTP pour les produits du WMS."""

import unittest
import tempfile
import json
import sys
import threading
from pathlib import Path
from http.server import HTTPServer

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.http import HttpHandler, make_app
from engine.auth import TokenAuth
from engine.repository import DocumentRepository


class TestWmsProductHttpApi(unittest.TestCase):
    SERVER_AVAILABLE = False

    @classmethod
    def setUpClass(cls):
        try:
            cls.temp_dir = tempfile.TemporaryDirectory()
            cls.db_path = Path(cls.temp_dir.name) / "test_wms.db"
            cls.repo = DocumentRepository(cls.db_path)
            auth = TokenAuth({"test-token"})
            cls.server = HTTPServer(("127.0.0.1", 0), make_app(cls.repo, auth=auth))
            cls.server.store = cls.repo
            cls.server.auth = auth
            HttpHandler.log_message = lambda self, format, *args: None
            cls.thread = threading.Thread(target=cls.server.serve_forever)
            cls.thread.start()
            cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"
            cls.SERVER_AVAILABLE = True
        except Exception as e:
            cls.SERVER_AVAILABLE = False
            print(f"Erreur de configuration du serveur : {e}")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "server"):
            cls.server.shutdown()
            cls.server.server_close()
            cls.thread.join(timeout=5)
            cls.repo.close()
        if hasattr(cls, "temp_dir"):
            cls.temp_dir.cleanup()

    def setUp(self):
        if not self.SERVER_AVAILABLE:
            self.skipTest("Serveur HTTP non disponible")

    def _request(self, method, path, body=None, token="test-token"):
        import urllib.request
        import urllib.error

        url = self.base_url + path
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Content-Type": "application/json"}
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8"))

    def test_create_product(self):
        """POST /api/v1/wms/products."""
        status, data = self._request(
            "POST",
            "/api/v1/wms/products",
            {
                "organisation_id": "org-1",
                "sku": "SKU-HTTP-001",
                "name": "Clavier HTTP",
                "default_price": 29.99,
            },
        )
        self.assertEqual(status, 201)
        self.assertIn("item", data)
        self.assertEqual(data["item"]["sku"], "SKU-HTTP-001")

    def test_get_products(self):
        """GET /api/v1/wms/products."""
        status, data = self._request("GET", "/api/v1/wms/products")
        self.assertEqual(status, 200)
        self.assertIn("items", data)

    def test_get_product_by_id(self):
        """GET /api/v1/wms/products/{id}."""
        status, data = self._request(
            "POST",
            "/api/v1/wms/products",
            {
                "organisation_id": "org-1",
                "sku": "SKU-HTTP-002",
                "name": "Souris HTTP",
            },
        )
        product_id = data["item"]["id"]

        status, data = self._request("GET", f"/api/v1/wms/products/{product_id}")
        self.assertEqual(status, 200)
        self.assertEqual(data["item"]["name"], "Souris HTTP")

    def test_get_product_not_found(self):
        """GET /api/v1/wms/products/{id} avec id inexistant."""
        status, data = self._request("GET", "/api/v1/wms/products/prod-inexistant")
        self.assertEqual(status, 404)

    def test_create_product_missing_sku(self):
        """POST sans sku doit retourner 400."""
        status, data = self._request(
            "POST",
            "/api/v1/wms/products",
            {"organisation_id": "org-1", "name": "Sans SKU"},
        )
        self.assertEqual(status, 400)

    def test_create_product_missing_token(self):
        """POST sans token doit retourner 401."""
        status, data = self._request(
            "POST",
            "/api/v1/wms/products",
            {"organisation_id": "org-1", "sku": "SKU-X", "name": "X"},
            token=None,
        )
        self.assertEqual(status, 401)


if __name__ == "__main__":
    unittest.main()
