"""Tests de pagination pour products, warehouses et stock-levels."""

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
from xohive.wms.domain.product import Product
from xohive.wms.domain.warehouse import Warehouse
from xohive.wms.repository.product_repository import ProductRepository
from xohive.wms.repository.warehouse_repository import WarehouseRepository


class TestPaginationHttp(unittest.TestCase):
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
        self.products = ProductRepository(self.repo.db_path)
        self.warehouses = WarehouseRepository(self.repo.db_path)

    def tearDown(self):
        self.server.shutdown()
        self.products.close()
        self.warehouses.close()
        self.tmp.cleanup()

    def _get(self, endpoint, query=""):
        req = urllib.request.Request(
            self.base + endpoint + query,
            headers={"Authorization": "Bearer test-token"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_products_pagination(self):
        for i in range(10):
            body = json.dumps({
                "organisation_id": "org-1",
                "sku": f"SKU-PAG-{i:03d}",
                "name": f"Produit {i}",
                "default_price": 10.0,
            }).encode()
            req = urllib.request.Request(
                self.base + "/api/v1/wms/products",
                data=body, headers=self.headers, method="POST",
            )
            with urllib.request.urlopen(req, timeout=10):
                pass

        status, data = self._get("/api/v1/wms/products", "?limit=4&offset=0")
        self.assertEqual(status, 200)
        self.assertEqual(len(data["items"]), 4)

        status, page2 = self._get("/api/v1/wms/products", "?limit=4&offset=4")
        self.assertEqual(len(page2["items"]), 4)
        self.assertNotEqual(data["items"][0]["id"], page2["items"][0]["id"])

    def test_products_invalid_limit_returns_400(self):
        status, _ = self._get("/api/v1/wms/products", "?limit=0")
        self.assertEqual(status, 400)

    def test_warehouses_pagination(self):
        for i in range(6):
            body = json.dumps({
                "organisation_id": "org-1",
                "code": f"WH-PG-{i:03d}",
                "name": f"Entrepôt {i}",
            }).encode()
            req = urllib.request.Request(
                self.base + "/api/v1/wms/warehouses",
                data=body, headers=self.headers, method="POST",
            )
            with urllib.request.urlopen(req, timeout=10):
                pass

        status, data = self._get("/api/v1/wms/warehouses", "?limit=3&offset=2")
        self.assertEqual(status, 200)
        self.assertEqual(len(data["items"]), 3)

    def test_stock_levels_pagination(self):
        # Créer un produit et un entrepôt
        product = self.products.create(Product(
            organisation_id="org-1", sku="SKU-SL", name="P",
        ))
        warehouse = self.warehouses.create(Warehouse(
            organisation_id="org-1", code="WH-SL", name="W",
        ))
        # Créer 5 niveaux via des entrées de stock
        for _ in range(5):
            body = json.dumps({
                "organisation_id": "org-1",
                "product_id": product.id,
                "warehouse_id": warehouse.id,
                "movement_type": "in", "quantity": 1,
            }).encode()
            req = urllib.request.Request(
                self.base + "/api/v1/wms/stock-movements",
                data=body, headers=self.headers, method="POST",
            )
            with urllib.request.urlopen(req, timeout=10):
                pass

        status, data = self._get("/api/v1/wms/stock-levels", "?limit=2&offset=0")
        self.assertEqual(status, 200)
        self.assertEqual(len(data["items"]), 1)  # une seule paire produit/entrepôt

    def test_stock_levels_invalid_offset_returns_400(self):
        status, _ = self._get("/api/v1/wms/stock-levels", "?offset=-1")
        self.assertEqual(status, 400)


if __name__ == "__main__":
    unittest.main()
