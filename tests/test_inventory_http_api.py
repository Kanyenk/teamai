"""Tests HTTP des inventories (http.server)."""
import json, os, tempfile, threading, unittest, urllib.error, urllib.request
from http.server import HTTPServer
from types import SimpleNamespace
from engine.http import make_app
from engine.inventory_repository import InventoryRepository
from engine.inventory_service import InventoryService


class TestInventoryHttpApi(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.repo = InventoryRepository(db_path=self.db_path)
        self.service = InventoryService(self.repo)
        store = SimpleNamespace(db_path=self.db_path)
        handler = make_app(store, auth=None)
        self.server = HTTPServer(("127.0.0.1", 0), handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        os.unlink(self.db_path)

    def _request(self, method, path, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())

    def _create(self, **overrides):
        payload = {
            "organisation_id": "org-1",
            "warehouse_id": "wh-1",
            "product_id": "prod-1",
            "counted_quantity": 5,
            "expected_quantity": 4,
            "note": "Inventaire annuel",        }
        payload.update(overrides)
        return self._request("POST", "/api/v1/wms/inventories", payload)

    def test_create(self):
        status, body = self._create()
        self.assertEqual(status, 201)
        self.assertIn("item", body)

    def test_list(self):
        self._create()
        status, body = self._request("GET", "/api/v1/wms/inventories?organisation_id=org-1")
        self.assertEqual(status, 200)
        self.assertEqual(len(body["items"]), 1)

    def test_list_missing_org(self):
        status, _ = self._request("GET", "/api/v1/wms/inventories")
        self.assertEqual(status, 400)

    def test_get(self):
        _, body = self._create()
        obj_id = body["item"]["id"]
        status, body = self._request("GET", f"/api/v1/wms/inventories/{obj_id}")
        self.assertEqual(status, 200)

    def test_get_not_found(self):
        status, _ = self._request("GET", "/api/v1/wms/inventories/inv-inexistant")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
