"""Tests HTTP des endpoints stock-locations."""
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
from xohive.wms.domain.warehouse import Warehouse
from xohive.wms.repository.warehouse_repository import WarehouseRepository


class TestStockLocationHttpApi(unittest.TestCase):
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
        self.warehouses = WarehouseRepository(self.repo.db_path)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.warehouses.close()
        self.tmp.cleanup()

    def _create_warehouse(self, code="WH-LOC"):
        warehouse = self.warehouses.create(Warehouse(organisation_id="org-1", code=code, name="W"))
        return warehouse.id

    def _create_location(self, warehouse_id):
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-locations",
            data=json.dumps({
                "organisation_id": "org-1",
                "warehouse_id": warehouse_id,
                "code": "A-01-01",
                "name": "Zone A",
            }).encode(),
            method="POST",
            headers=self.headers,
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())

    def test_create_location_returns_201(self):
        warehouse_id = self._create_warehouse()
        result = self._create_location(warehouse_id)
        self.assertEqual(result["item"]["code"], "A-01-01")

    def test_list_locations_returns_200(self):
        warehouse_id = self._create_warehouse()
        self._create_location(warehouse_id)
        req = urllib.request.Request(
            self.base + f"/api/v1/wms/stock-locations?organisation_id=org-1&warehouse_id={warehouse_id}",
            method="GET",
            headers=self.headers,
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read())
        self.assertEqual(len(result["items"]), 1)

    def test_get_location_returns_200(self):
        warehouse_id = self._create_warehouse()
        result = self._create_location(warehouse_id)
        loc_id = result["item"]["id"]
        req = urllib.request.Request(
            self.base + f"/api/v1/wms/stock-locations/{loc_id}",
            method="GET",
            headers=self.headers,
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read())
        self.assertEqual(result["item"]["code"], "A-01-01")

    def test_get_location_not_found(self):
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-locations/loc-inexistant",
            method="GET",
            headers=self.headers,
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=10)
        self.assertEqual(ctx.exception.code, 404)

    def test_create_location_missing_code_returns_400(self):
        warehouse_id = self._create_warehouse()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-locations",
            data=json.dumps({
                "organisation_id": "org-1",
                "warehouse_id": warehouse_id,
            }).encode(),
            method="POST",
            headers=self.headers,
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=10)
        self.assertEqual(ctx.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
