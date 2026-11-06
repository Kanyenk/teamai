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


class TestPaginationMetadata(unittest.TestCase):
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
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())

    def test_products_metadata(self):
        for i in range(7):
            body = json.dumps({
                "organisation_id": "org-1",
                "sku": f"SKU-META-{i:03d}",
                "name": f"Produit {i}",
                "default_price": 10.0,
            }).encode()
            req = urllib.request.Request(
                self.base + "/api/v1/wms/products",
                data=body, headers=self.headers, method="POST",
            )
            with urllib.request.urlopen(req, timeout=10):
                pass
        status, data = self._get("/api/v1/wms/products", "?limit=3&offset=2")
        self.assertEqual(status, 200)
        self.assertEqual(data["pagination"]["total"], 7)
        self.assertEqual(data["pagination"]["limit"], 3)
        self.assertEqual(data["pagination"]["offset"], 2)
        self.assertEqual(len(data["items"]), 3)

    def test_warehouses_metadata(self):
        for i in range(4):
            body = json.dumps({
                "organisation_id": "org-1",
                "code": f"WH-META-{i:03d}",
                "name": f"Entrepôt {i}",
            }).encode()
            req = urllib.request.Request(
                self.base + "/api/v1/wms/warehouses",
                data=body, headers=self.headers, method="POST",
            )
            with urllib.request.urlopen(req, timeout=10):
                pass
        status, data = self._get("/api/v1/wms/warehouses", "?limit=2&offset=1")
        self.assertEqual(status, 200)
        self.assertEqual(data["pagination"]["total"], 4)
        self.assertEqual(len(data["items"]), 2)

    def test_stock_levels_metadata(self):
        product = self.products.create(Product(
            organisation_id="org-1", sku="SKU-SLM", name="P",
        ))
        warehouse = self.warehouses.create(Warehouse(
            organisation_id="org-1", code="WH-SLM", name="W",
        ))
        for _ in range(3):
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
        status, data = self._get("/api/v1/wms/stock-levels", "?limit=1&offset=0")
        self.assertEqual(status, 200)
        self.assertEqual(data["pagination"]["total"], 1)
        self.assertEqual(len(data["items"]), 1)


class TestOrganisationFilter(unittest.TestCase):
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

    def _post(self, endpoint, body):
        req = urllib.request.Request(
            self.base + endpoint,
            data=json.dumps(body).encode(), headers=self.headers, method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())

    def _get(self, endpoint, query=""):
        req = urllib.request.Request(
            self.base + endpoint + query,
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())

    def test_products_filter_by_organisation(self):
        self._post("/api/v1/wms/products", {
            "organisation_id": "org-1", "sku": "SKU-A", "name": "A", "default_price": 1,
        })
        self._post("/api/v1/wms/products", {
            "organisation_id": "org-2", "sku": "SKU-B", "name": "B", "default_price": 1,
        })
        status, data = self._get("/api/v1/wms/products", "?organisation_id=org-1")
        self.assertEqual(status, 200)
        self.assertEqual(data["pagination"]["total"], 1)
        self.assertEqual(data["items"][0]["organisation_id"], "org-1")

    def test_warehouses_filter_by_organisation(self):
        self._post("/api/v1/wms/warehouses", {
            "organisation_id": "org-1", "code": "WH-A", "name": "A",
        })
        self._post("/api/v1/wms/warehouses", {
            "organisation_id": "org-2", "code": "WH-B", "name": "B",
        })
        status, data = self._get("/api/v1/wms/warehouses", "?organisation_id=org-2")
        self.assertEqual(status, 200)
        self.assertEqual(data["pagination"]["total"], 1)
        self.assertEqual(data["items"][0]["organisation_id"], "org-2")

    def test_stock_levels_filter_by_organisation(self):
        product = self.products.create(Product(
            organisation_id="org-1", sku="SKU-ORG", name="P",
        ))
        warehouse = self.warehouses.create(Warehouse(
            organisation_id="org-1", code="WH-ORG", name="W",
        ))
        self._post("/api/v1/wms/stock-movements", {
            "organisation_id": "org-1", "product_id": product.id,
            "warehouse_id": warehouse.id, "movement_type": "in", "quantity": 5,
        })
        status, data = self._get("/api/v1/wms/stock-levels", "?organisation_id=org-1")
        self.assertEqual(status, 200)
        self.assertEqual(data["pagination"]["total"], 1)
        status, data = self._get("/api/v1/wms/stock-levels", "?organisation_id=org-9")
        self.assertEqual(data["pagination"]["total"], 0)


class TestSorting(unittest.TestCase):
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

    def tearDown(self):
        self.server.shutdown()
        self.products.close()
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

    def test_products_sort_by_name_desc(self):
        for name in ["Cerise", "Amande", "Banane"]:
            body = json.dumps({
                "organisation_id": "org-1",
                "sku": f"SKU-{name}",
                "name": name,
                "default_price": 10.0,
            }).encode()
            req = urllib.request.Request(
                self.base + "/api/v1/wms/products",
                data=body, headers=self.headers, method="POST",
            )
            with urllib.request.urlopen(req, timeout=10):
                pass
        status, data = self._get(
            "/api/v1/wms/products", "?order_by=name&direction=desc"
        )
        self.assertEqual(status, 200)
        names = [p["name"] for p in data["items"]]
        self.assertEqual(names, sorted(names, reverse=True))

    def test_products_invalid_order_by_returns_400(self):
        status, _ = self._get("/api/v1/wms/products", "?order_by=malicious")
        self.assertEqual(status, 400)

    def test_products_invalid_direction_returns_400(self):
        status, _ = self._get("/api/v1/wms/products", "?direction=sideways")
        self.assertEqual(status, 400)


class TestSortMetadata(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = DocumentRepository(Path(self._tmp.name) / "test.db")
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
        self._tmp.cleanup()

    def _create_warehouses(self):
        for i in range(3):
            body = json.dumps({
                "organisation_id": "org-1",
                "code": f"WH-SORT-{i}",
                "name": f"Entrepôt {i}",
            }).encode()
            req = urllib.request.Request(self.base + "/api/v1/wms/warehouses", data=body, headers=self.headers, method="POST")
            with urllib.request.urlopen(req, timeout=10):
                pass

    def test_warehouses_sort_metadata(self):
        self._create_warehouses()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/warehouses?limit=2&offset=1&order_by=name&direction=desc",
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        self.assertEqual(data["sort"]["order_by"], "name")
        self.assertEqual(data["sort"]["direction"], "desc")

    def test_warehouses_sort_metadata_default(self):
        self._create_warehouses()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/warehouses?limit=2&offset=0",
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        self.assertEqual(data["sort"]["order_by"], "created_at")
        self.assertEqual(data["sort"]["direction"], "asc")


class TestSearch(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = DocumentRepository(Path(self._tmp.name) / "test.db")
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
        self._tmp.cleanup()

    def _create_warehouses(self):
        for code, name in [("WH-ALPHA", "Entrepôt Alpha"), ("WH-BETA", "Entrepôt Beta")]:
            body = json.dumps({
                "organisation_id": "org-1",
                "code": code,
                "name": name,
            }).encode()
            req = urllib.request.Request(self.base + "/api/v1/wms/warehouses", data=body, headers=self.headers, method="POST")
            with urllib.request.urlopen(req, timeout=10):
                pass

    def test_warehouses_search_by_code(self):
        self._create_warehouses()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/warehouses?search=ALPHA",
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        codes = [w["code"] for w in data["items"]]
        self.assertEqual(codes, ["WH-ALPHA"])

    def test_warehouses_search_by_name(self):
        self._create_warehouses()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/warehouses?search=Beta",
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        codes = [w["code"] for w in data["items"]]
        self.assertEqual(codes, ["WH-BETA"])

    def test_warehouses_search_no_match(self):
        self._create_warehouses()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/warehouses?search=INEXISTANT",
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        self.assertEqual(data["items"], [])
        self.assertEqual(data["pagination"]["total"], 0)


class TestDateFilters(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = DocumentRepository(Path(self._tmp.name) / "test.db")
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
        self._tmp.cleanup()

    def _create_warehouses(self):
        for i in range(2):
            body = json.dumps({
                "organisation_id": "org-1",
                "code": f"WH-DATE-{i}",
                "name": f"Entrepôt Date {i}",
            }).encode()
            req = urllib.request.Request(self.base + "/api/v1/wms/warehouses", data=body, headers=self.headers, method="POST")
            with urllib.request.urlopen(req, timeout=10):
                pass

    def test_warehouses_created_from_past(self):
        self._create_warehouses()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/warehouses?created_from=2020-01-01",
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        self.assertEqual(data["pagination"]["total"], 2)
        self.assertEqual(len(data["items"]), 2)

    def test_warehouses_created_to_past(self):
        self._create_warehouses()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/warehouses?created_to=2000-01-01",
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        self.assertEqual(data["pagination"]["total"], 0)
        self.assertEqual(data["items"], [])

    def test_warehouses_date_range_combined_with_search(self):
        self._create_warehouses()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/warehouses?search=DATE-0&created_from=2020-01-01",
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        codes = [w["code"] for w in data["items"]]
        self.assertEqual(codes, ["WH-DATE-0"])


class TestProductDateFilters(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = DocumentRepository(Path(self._tmp.name) / "test.db")
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
        self._tmp.cleanup()

    def _create_products(self):
        for i in range(2):
            body = json.dumps({
                "organisation_id": "org-1",
                "sku": f"SKU-DATE-{i}",
                "name": f"Produit Date {i}",
                "unit": "unité",
                "default_price": 10.0 + i,
            }).encode()
            req = urllib.request.Request(self.base + "/api/v1/wms/products", data=body, headers=self.headers, method="POST")
            with urllib.request.urlopen(req, timeout=10):
                pass

    def test_products_created_from_past(self):
        self._create_products()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/products?created_from=2020-01-01",
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        self.assertEqual(data["pagination"]["total"], 2)

    def test_products_created_to_past(self):
        self._create_products()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/products?created_to=2000-01-01",
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        self.assertEqual(data["pagination"]["total"], 0)
        self.assertEqual(data["items"], [])


class TestMovementDateFilters(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = DocumentRepository(Path(self._tmp.name) / "test.db")
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
        self._tmp.cleanup()

    def _create_movement(self):
        product = json.dumps({
            "organisation_id": "org-1",
            "sku": "SKU-MVT-DATE",
            "name": "Produit Mvt",
            "unit": "unité",
            "default_price": 5.0,
        }).encode()
        req = urllib.request.Request(self.base + "/api/v1/wms/products", data=product, headers=self.headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            product_id = json.loads(r.read())["item"]["id"]

        warehouse = json.dumps({
            "organisation_id": "org-1",
            "code": "WH-MVT-DATE",
            "name": "Entrepôt Mvt",
        }).encode()
        req = urllib.request.Request(self.base + "/api/v1/wms/warehouses", data=warehouse, headers=self.headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            warehouse_id = json.loads(r.read())["item"]["id"]

        movement = json.dumps({
            "organisation_id": "org-1",
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "movement_type": "in",
            "quantity": 10,
        }).encode()
        req = urllib.request.Request(self.base + "/api/v1/wms/stock-movements", data=movement, headers=self.headers, method="POST")
        with urllib.request.urlopen(req, timeout=10):
            pass

    def test_movements_created_from_past(self):
        self._create_movement()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-movements?created_from=2020-01-01",
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        self.assertEqual(data["pagination"]["total"], 1)

    def test_movements_created_to_past(self):
        self._create_movement()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-movements?created_to=2000-01-01",
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        self.assertEqual(data["pagination"]["total"], 0)
        self.assertEqual(data["items"], [])


class TestQuantityFilters(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = DocumentRepository(Path(self._tmp.name) / "test.db")
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
        self._tmp.cleanup()

    def _create_levels(self):
        product = json.dumps({
            "organisation_id": "org-1",
            "sku": "SKU-QTY",
            "name": "Produit Qty",
            "unit": "unité",
            "default_price": 5.0,
        }).encode()
        req = urllib.request.Request(self.base + "/api/v1/wms/products", data=product, headers=self.headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            product_id = json.loads(r.read())["item"]["id"]

        warehouse = json.dumps({
            "organisation_id": "org-1",
            "code": "WH-QTY",
            "name": "Entrepôt Qty",
        }).encode()
        req = urllib.request.Request(self.base + "/api/v1/wms/warehouses", data=warehouse, headers=self.headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            warehouse_id = json.loads(r.read())["item"]["id"]

        for qty in [3, 10]:
            movement = json.dumps({
                "organisation_id": "org-1",
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "movement_type": "in",
                "quantity": qty,
            }).encode()
            req = urllib.request.Request(self.base + "/api/v1/wms/stock-movements", data=movement, headers=self.headers, method="POST")
            with urllib.request.urlopen(req, timeout=10):
                pass

    def test_levels_min_quantity(self):
        self._create_levels()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-levels?min_quantity=5",
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        quantities = [l["quantity"] for l in data["items"]]
        self.assertTrue(all(q >= 5 for q in quantities))
        self.assertEqual(data["pagination"]["total"], len(quantities))

    def test_levels_max_quantity(self):
        self._create_levels()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-levels?max_quantity=5",
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        quantities = [l["quantity"] for l in data["items"]]
        self.assertTrue(all(q <= 5 for q in quantities))

    def test_levels_invalid_quantity_returns_400(self):
        self._create_levels()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-levels?min_quantity=abc",
            headers={"Authorization": "Bearer test-token"},
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=10)
        self.assertEqual(ctx.exception.code, 400)
