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
        self.server.server_close()
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


class TestStockMovementPaginationHttp(unittest.TestCase):
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
        self.product = self.products.create(Product(
            organisation_id="org-1", sku="SKU-PAG", name="P",
        ))
        self.warehouse = self.warehouses.create(Warehouse(
            organisation_id="org-1", code="WH-PAG", name="W",
        ))

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.products.close()
        self.warehouses.close()
        self.tmp.cleanup()

    def _create(self):
        body = json.dumps({
            "organisation_id": "org-1",
            "product_id": self.product.id,
            "warehouse_id": self.warehouse.id,
            "movement_type": "in", "quantity": 1,
        }).encode()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-movements",
            data=body, headers=self.headers, method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())

    def _get(self, query=""):
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-movements" + query,
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())

    def test_pagination_default_and_pages(self):
        for _ in range(10):
            self._create()
        status, data = self._get()
        self.assertEqual(status, 200)
        self.assertEqual(len(data["items"]), 10)

        status, page1 = self._get("?limit=4&offset=0")
        status2, page2 = self._get("?limit=4&offset=4")
        self.assertEqual(len(page1["items"]), 4)
        self.assertEqual(len(page2["items"]), 4)
        self.assertNotEqual(page1["items"][0]["id"], page2["items"][0]["id"])

    def test_pagination_invalid_limit_returns_400(self):
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-movements?limit=0",
            headers={"Authorization": "Bearer test-token"},
        )
        try:
            urllib.request.urlopen(req, timeout=10)
            self.fail("devrait lever 400")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 400)


class TestStockMovementFiltersHttp(unittest.TestCase):
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
        self.product = self.products.create(Product(
            organisation_id="org-1", sku="SKU-FILT", name="P",
        ))
        self.warehouse = self.warehouses.create(Warehouse(
            organisation_id="org-1", code="WH-FILT", name="W",
        ))

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.products.close()
        self.warehouses.close()
        self.tmp.cleanup()

    def _create(self, mtype, qty):
        body = json.dumps({
            "organisation_id": "org-1",
            "product_id": self.product.id,
            "warehouse_id": self.warehouse.id,
            "movement_type": mtype, "quantity": qty,
        }).encode()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-movements",
            data=body, headers=self.headers, method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())

    def _get(self, query=""):
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-movements" + query,
            headers={"Authorization": "Bearer test-token"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_filter_by_movement_type(self):
        self._create("in", 10)
        self._create("adjustment", 5)
        status, data = self._get("?movement_type=in")
        self.assertEqual(status, 200)
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["movement_type"], "in")

    def test_filter_by_product(self):
        self._create("in", 10)
        status, data = self._get(f"?product_id={self.product.id}")
        self.assertEqual(len(data["items"]), 1)
        status, data = self._get("?product_id=inexistant")
        self.assertEqual(len(data["items"]), 0)

    def test_filter_invalid_type_returns_400(self):
        status, _ = self._get("?movement_type=unknown")
        self.assertEqual(status, 400)

    def test_filters_with_pagination(self):
        for _ in range(6):
            self._create("in", 1)
        status, data = self._get("?movement_type=in&limit=4&offset=2")
        self.assertEqual(status, 200)
        self.assertEqual(len(data["items"]), 4)


class TestStockMovementPaginationMetadata(unittest.TestCase):
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
        self.product = self.products.create(Product(
            organisation_id="org-1", sku="SKU-META", name="P",
        ))
        self.warehouse = self.warehouses.create(Warehouse(
            organisation_id="org-1", code="WH-META", name="W",
        ))

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.products.close()
        self.warehouses.close()
        self.tmp.cleanup()

    def _create(self, mtype="in", qty=1):
        body = json.dumps({
            "organisation_id": "org-1",
            "product_id": self.product.id,
            "warehouse_id": self.warehouse.id,
            "movement_type": mtype, "quantity": qty,
        }).encode()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-movements",
            data=body, headers=self.headers, method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())

    def _get(self, query=""):
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-movements" + query,
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())

    def test_pagination_metadata_present(self):
        for _ in range(7):
            self._create()
        status, data = self._get("?limit=3&offset=2")
        self.assertEqual(status, 200)
        self.assertEqual(data["pagination"]["total"], 7)
        self.assertEqual(data["pagination"]["limit"], 3)
        self.assertEqual(data["pagination"]["offset"], 2)
        self.assertEqual(len(data["items"]), 3)

    def test_pagination_metadata_with_filter(self):
        self._create("in", 1)
        self._create("adjustment", 1)
        status, data = self._get("?movement_type=in")
        self.assertEqual(data["pagination"]["total"], 1)
        self.assertEqual(len(data["items"]), 1)
