"""Tests d'intégration HTTP pour StockMovement."""

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


class TestStockMovementHttpApi(unittest.TestCase):
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

        # Entités réelles pour satisfaire la validation croisée
        self.products = ProductRepository(self.repo.db_path)
        self.warehouses = WarehouseRepository(self.repo.db_path)
        self.product = self.products.create(Product(
            organisation_id="org-1", sku="SKU-1", name="Produit 1",
        ))
        self.warehouse = self.warehouses.create(Warehouse(
            organisation_id="org-1", code="WH-01", name="Entrepôt 1",
        ))
        self.target_warehouse = self.warehouses.create(Warehouse(
            organisation_id="org-1", code="WH-02", name="Entrepôt 2",
        ))

    def tearDown(self):
        self.server.shutdown()
        self.products.close()
        self.warehouses.close()
        self.tmp.cleanup()

    def _post(self, body):
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-movements",
            data=json.dumps(body).encode(), headers=self.headers, method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def _get(self, path=""):
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-movements" + path,
            headers={"Authorization": "Bearer test-token"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_create_in_movement(self):
        status, data = self._post({
            "organisation_id": "org-1",
            "product_id": self.product.id,
            "warehouse_id": self.warehouse.id,
            "movement_type": "in", "quantity": 10,
        })
        self.assertEqual(status, 201)
        self.assertEqual(data["item"]["movement_type"], "in")

    def test_create_out_insufficient_stock(self):
        status, _ = self._post({
            "organisation_id": "org-1",
            "product_id": self.product.id,
            "warehouse_id": self.warehouse.id,
            "movement_type": "out", "quantity": 5,
        })
        self.assertEqual(status, 400)

    def test_create_transfer_requires_target(self):
        status, _ = self._post({
            "organisation_id": "org-1",
            "product_id": self.product.id,
            "warehouse_id": self.warehouse.id,
            "movement_type": "transfer", "quantity": 5,
        })
        self.assertEqual(status, 400)

    def test_create_movement_with_unknown_product(self):
        status, _ = self._post({
            "organisation_id": "org-1",
            "product_id": "inexistant",
            "warehouse_id": self.warehouse.id,
            "movement_type": "in", "quantity": 5,
        })
        self.assertEqual(status, 400)

    def test_create_movement_missing_token(self):
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-movements",
            data=json.dumps({
                "organisation_id": "org-1",
                "product_id": self.product.id,
                "warehouse_id": self.warehouse.id,
                "movement_type": "in", "quantity": 5,
            }).encode(),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            urllib.request.urlopen(req, timeout=10)
            self.fail("devrait lever 401")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 401)

    def test_get_movements(self):
        self._post({
            "organisation_id": "org-1",
            "product_id": self.product.id,
            "warehouse_id": self.warehouse.id,
            "movement_type": "in", "quantity": 10,
        })
        status, data = self._get()
        self.assertEqual(status, 200)
        self.assertIsInstance(data["items"], list)

    def test_get_movement_by_id(self):
        _, created = self._post({
            "organisation_id": "org-1",
            "product_id": self.product.id,
            "warehouse_id": self.warehouse.id,
            "movement_type": "in", "quantity": 10,
        })
        mid = created["item"]["id"]
        status, data = self._get(f"/{mid}")
        self.assertEqual(status, 200)
        self.assertEqual(data["item"]["id"], mid)


if __name__ == "__main__":
    unittest.main()
