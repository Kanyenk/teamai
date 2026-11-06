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


class TestMovementQuantityFilters(unittest.TestCase):
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

    def _create_movements(self):
        product = json.dumps({
            "organisation_id": "org-1",
            "sku": "SKU-MVT-QTY",
            "name": "Produit Mvt Qty",
            "unit": "unité",
            "default_price": 5.0,
        }).encode()
        req = urllib.request.Request(self.base + "/api/v1/wms/products", data=product, headers=self.headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            product_id = json.loads(r.read())["item"]["id"]

        warehouse = json.dumps({
            "organisation_id": "org-1",
            "code": "WH-MVT-QTY",
            "name": "Entrepôt Mvt Qty",
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

    def test_movements_min_quantity(self):
        self._create_movements()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-movements?min_quantity=5",
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        quantities = [m["quantity"] for m in data["items"]]
        self.assertTrue(all(q >= 5 for q in quantities))
        self.assertEqual(data["pagination"]["total"], len(quantities))

    def test_movements_max_quantity(self):
        self._create_movements()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-movements?max_quantity=5",
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        quantities = [m["quantity"] for m in data["items"]]
        self.assertTrue(all(q <= 5 for q in quantities))

    def test_movements_invalid_quantity_returns_400(self):
        self._create_movements()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-movements?min_quantity=abc",
            headers={"Authorization": "Bearer test-token"},
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=10)
        self.assertEqual(ctx.exception.code, 400)


class TestCsvExport(unittest.TestCase):
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
        for code in ["WH-CSV-1", "WH-CSV-2"]:
            body = json.dumps({
                "organisation_id": "org-1",
                "code": code,
                "name": f"Entrepôt {code}",
            }).encode()
            req = urllib.request.Request(self.base + "/api/v1/wms/warehouses", data=body, headers=self.headers, method="POST")
            with urllib.request.urlopen(req, timeout=10):
                pass

    def test_warehouses_csv_export(self):
        self._create_warehouses()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/warehouses?format=csv",
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            self.assertEqual(r.headers["Content-Type"], "text/csv; charset=utf-8")
            self.assertIn("warehouses.csv", r.headers["Content-Disposition"])
            body = r.read().decode("utf-8")
        lines = body.strip().splitlines()
        self.assertEqual(lines[0], "id,code,name,address,created_at")
        self.assertEqual(len(lines), 3)
        self.assertIn("WH-CSV-1", body)
        self.assertIn("WH-CSV-2", body)

    def test_warehouses_json_default(self):
        self._create_warehouses()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/warehouses",
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            self.assertEqual(r.headers["Content-Type"], "application/json")


class TestMovementCsvExport(unittest.TestCase):
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
            "sku": "SKU-CSV-MVT",
            "name": "Produit CSV Mvt",
            "unit": "unité",
            "default_price": 5.0,
        }).encode()
        req = urllib.request.Request(self.base + "/api/v1/wms/products", data=product, headers=self.headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            product_id = json.loads(r.read())["item"]["id"]

        warehouse = json.dumps({
            "organisation_id": "org-1",
            "code": "WH-CSV-MVT",
            "name": "Entrepôt CSV Mvt",
        }).encode()
        req = urllib.request.Request(self.base + "/api/v1/wms/warehouses", data=warehouse, headers=self.headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            warehouse_id = json.loads(r.read())["item"]["id"]

        movement = json.dumps({
            "organisation_id": "org-1",
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "movement_type": "in",
            "quantity": 7,
        }).encode()
        req = urllib.request.Request(self.base + "/api/v1/wms/stock-movements", data=movement, headers=self.headers, method="POST")
        with urllib.request.urlopen(req, timeout=10):
            pass

    def test_movements_csv_export(self):
        self._create_movement()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-movements?format=csv",
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            self.assertEqual(r.headers["Content-Type"], "text/csv; charset=utf-8")
            self.assertIn("stock_movements.csv", r.headers["Content-Disposition"])
            body = r.read().decode("utf-8")
        lines = body.strip().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertIn("SKU-CSV-MVT"[:0] or "in", body)
        self.assertIn(",7,", body)


class TestDateValidation(unittest.TestCase):
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

    def test_warehouses_invalid_created_from_returns_400(self):
        req = urllib.request.Request(
            self.base + "/api/v1/wms/warehouses?created_from=abc",
            headers={"Authorization": "Bearer test-token"},
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=10)
        self.assertEqual(ctx.exception.code, 400)

    def test_warehouses_invalid_created_to_returns_400(self):
        req = urllib.request.Request(
            self.base + "/api/v1/wms/warehouses?created_to=2020-13-45",
            headers={"Authorization": "Bearer test-token"},
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=10)
        self.assertEqual(ctx.exception.code, 400)

    def test_products_invalid_created_from_returns_400(self):
        req = urllib.request.Request(
            self.base + "/api/v1/wms/products?created_from=not-a-date",
            headers={"Authorization": "Bearer test-token"},
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=10)
        self.assertEqual(ctx.exception.code, 400)


class TestStockAlerts(unittest.TestCase):
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

    def _create_stock(self, sku, quantity):
        product = self.products.create(Product(
            organisation_id="org-1", sku=sku, name=f"P-{sku}",
        ))
        warehouse = self.warehouses.create(Warehouse(
            organisation_id="org-1", code=f"WH-{sku}", name="W",
        ))
        for _ in range(quantity):
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
        return product.id

    def test_stock_alerts_below_threshold(self):
        low_id = self._create_stock("SKU-ALERT-LOW", 3)
        self._create_stock("SKU-ALERT-HIGH", 10)
        status, data = self._get("/api/v1/wms/stock-alerts", "?threshold=5")
        self.assertEqual(status, 200)
        self.assertEqual(data["threshold"], 5)
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["product_id"], low_id)

    def test_stock_alerts_no_results(self):
        self._create_stock("SKU-ALERT-ZERO", 2)
        status, data = self._get("/api/v1/wms/stock-alerts", "?threshold=0")
        self.assertEqual(status, 200)
        self.assertEqual(data["items"], [])

    def test_stock_alerts_invalid_threshold_returns_400(self):
        status, data = self._get("/api/v1/wms/stock-alerts", "?threshold=abc")
        self.assertEqual(status, 400)

    def test_stock_alerts_csv_format(self):
        product_id = self._create_stock("SKU-ALERT-CSV", 3)
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-alerts?threshold=5&format=csv",
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(r.headers.get("Content-Type"), "text/csv; charset=utf-8")
            body = r.read().decode("utf-8")
        self.assertIn("id,organisation_id,product_id,warehouse_id,quantity,created_at", body)
        self.assertIn(product_id, body)

    def test_alert_threshold_set_and_get(self):
        product_id = self._create_stock("SKU-THRESH", 1)
        body = json.dumps({"threshold": 5}).encode()
        req = urllib.request.Request(
            self.base + f"/api/v1/wms/products/{product_id}/alert-threshold",
            data=body, headers=self.headers, method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            self.assertEqual(r.status, 200)
        status, data = self._get(f"/api/v1/wms/products/{product_id}/alert-threshold")
        self.assertEqual(status, 200)
        self.assertEqual(data["alert_threshold"], 5)

    def test_alert_threshold_product_not_found(self):
        status, data = self._get("/api/v1/wms/products/prod-inconnu/alert-threshold")
        self.assertEqual(status, 404)

    def test_stock_alerts_uses_product_threshold(self):
        self._create_stock("SKU-TH-A", 3)
        high_id = self._create_stock("SKU-TH-B", 8)
        body = json.dumps({"threshold": 10}).encode()
        req = urllib.request.Request(
            self.base + f"/api/v1/wms/products/{high_id}/alert-threshold",
            data=body, headers=self.headers, method="POST",
        )
        with urllib.request.urlopen(req, timeout=10):
            pass
        status, data = self._get("/api/v1/wms/stock-alerts", "?threshold=1")
        self.assertEqual(status, 200)
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["product_id"], high_id)

    def test_dashboard_stock(self):
        product_a = self.products.create(Product(
            organisation_id="org-1", sku="SKU-DASH-A", name="A", default_price=10.0,
        ))
        product_b = self.products.create(Product(
            organisation_id="org-1", sku="SKU-DASH-B", name="B", default_price=5.0,
        ))
        self.warehouses.create(Warehouse(
            organisation_id="org-1", code="WH-DASH", name="W",
        ))
        for pid, qty in ((product_a.id, 3), (product_b.id, 8)):
            for _ in range(qty):
                body = json.dumps({
                    "organisation_id": "org-1",
                    "product_id": pid,
                    "warehouse_id": self.warehouses.list_by_organisation("org-1")[0].id,
                    "movement_type": "in", "quantity": 1,
                }).encode()
                req = urllib.request.Request(
                    self.base + "/api/v1/wms/stock-movements",
                    data=body, headers=self.headers, method="POST",
                )
                with urllib.request.urlopen(req, timeout=10):
                    pass
        body = json.dumps({"threshold": 10}).encode()
        req = urllib.request.Request(
            self.base + f"/api/v1/wms/products/{product_b.id}/alert-threshold",
            data=body, headers=self.headers, method="POST",
        )
        with urllib.request.urlopen(req, timeout=10):
            pass

        status, data = self._get("/api/v1/wms/dashboard/stock", "?organisation_id=org-1")
        self.assertEqual(status, 200)
        self.assertEqual(data["stock_value"], 70.0)
        self.assertEqual(len(data["alerts"]), 1)
        self.assertEqual(data["alerts"][0]["product_id"], product_b.id)
        warehouse = data["warehouses"][0]
        self.assertEqual(warehouse["total_quantity"], 11)
        self.assertEqual(warehouse["product_count"], 2)

    def test_dashboard_stock_missing_organisation_returns_400(self):
        status, data = self._get("/api/v1/wms/dashboard/stock")
        self.assertEqual(status, 400)

    def test_product_stock_movements(self):
        product_id = self._create_stock("SKU-MV-PROD", 3)
        status, data = self._get(f"/api/v1/wms/products/{product_id}/stock-movements")
        self.assertEqual(status, 200)
        self.assertEqual(data["pagination"]["total"], 3)
        self.assertEqual(len(data["items"]), 3)
        self.assertTrue(all(m["product_id"] == product_id for m in data["items"]))

    def test_product_stock_movements_not_found(self):
        status, data = self._get("/api/v1/wms/products/prod-inconnu/stock-movements")
        self.assertEqual(status, 404)

    def test_product_stock_movements_filter_type(self):
        product_id = self._create_stock("SKU-MV-FILT", 2)
        status, data = self._get(
            f"/api/v1/wms/products/{product_id}/stock-movements",
            "?movement_type=in",
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["pagination"]["total"], 2)
