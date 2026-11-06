"""Tests HTTP des barcodes (http.server)."""
import json, os, tempfile, threading, unittest, urllib.error, urllib.request
from http.server import HTTPServer
from types import SimpleNamespace
from engine.http import make_app
from engine.barcode_repository import BarcodeRepository
from engine.barcode_service import BarcodeService


class TestBarcodeHttpApi(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.repo = BarcodeRepository(db_path=self.db_path)
        self.service = BarcodeService(self.repo)
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
            "organisation_id": 'org-1',
            "product_id": 'prod-1',
            "code": '3012345678900',
            "type": 'ean13',
            "label": 'Code-barres produit A',        }
        payload.update(overrides)
        return self._request("POST", "/api/v1/wms/barcodes", payload)

    def test_create(self):
        status, body = self._create()
        self.assertEqual(status, 201)
        self.assertIn("item", body)

    def test_list(self):
        self._create()
        status, body = self._request("GET", "/api/v1/wms/barcodes?organisation_id=org-1")
        self.assertEqual(status, 200)
        self.assertEqual(len(body["items"]), 1)

    def test_list_missing_org(self):
        status, _ = self._request("GET", "/api/v1/wms/barcodes")
        self.assertEqual(status, 400)

    def test_get(self):
        _, body = self._create()
        obj_id = body["item"]["id"]
        status, body = self._request("GET", f"/api/v1/wms/barcodes/{obj_id}")
        self.assertEqual(status, 200)

    def test_get_not_found(self):
        status, _ = self._request("GET", "/api/v1/wms/barcodes/brc-inexistant")
        self.assertEqual(status, 404)

    def test_lookup_found(self):
        self._create()
        status, body = self._request(
            "GET",
            "/api/v1/wms/barcodes/lookup?organisation_id=org-1&code=3012345678900",
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["item"]["code"], "3012345678900")
        self.assertEqual(body["item"]["product_id"], "prod-1")

    def test_lookup_not_found(self):
        status, _ = self._request(
            "GET",
            "/api/v1/wms/barcodes/lookup?organisation_id=org-1&code=inconnu",
        )
        self.assertEqual(status, 404)

    def test_lookup_missing_code(self):
        status, _ = self._request(
            "GET",
            "/api/v1/wms/barcodes/lookup?organisation_id=org-1",
        )
        self.assertEqual(status, 400)


    def _request_raw(self, method, path, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, resp.headers.get("Content-Type"), resp.read()
        except urllib.error.HTTPError as e:
            return e.code, e.headers.get("Content-Type"), e.read()

    def test_label_svg(self):
        status, body = self._request("POST", "/api/v1/wms/barcodes", {
            "organisation_id": "org-1",
            "product_id": "prod-1",
            "code": "ABC-123",
            "type": "code128",
            "label": "Test",
        })
        obj_id = body["item"]["id"]
        status, content_type, raw = self._request_raw("GET", f"/api/v1/wms/barcodes/{obj_id}/label")
        self.assertEqual(status, 200)
        self.assertIn("svg", content_type)
        self.assertIn(b"<svg", raw)

    def test_label_not_found(self):
        status, _, _ = self._request_raw("GET", "/api/v1/wms/barcodes/brc-inexistant/label")
        self.assertEqual(status, 404)

    def test_label_invalid_type(self):
        status, body = self._request("POST", "/api/v1/wms/barcodes", {
            "organisation_id": "org-1",
            "product_id": "prod-1",
            "code": "ABC-123",
            "type": "invalidtype",
            "label": "Test",
        })
        obj_id = body["item"]["id"]
        status, _, _ = self._request_raw("GET", f"/api/v1/wms/barcodes/{obj_id}/label")
        self.assertEqual(status, 400)


    def test_label_png(self):
        status, body = self._request("POST", "/api/v1/wms/barcodes", {
            "organisation_id": "org-1",
            "product_id": "prod-1",
            "code": "ABC-123",
            "type": "code128",
            "label": "Test",
        })
        obj_id = body["item"]["id"]
        status, content_type, raw = self._request_raw("GET", f"/api/v1/wms/barcodes/{obj_id}/label?format=png")
        self.assertEqual(status, 200)
        self.assertIn("png", content_type)
        self.assertTrue(raw.startswith(b"\x89PNG"))


    def test_scan_page_returns_html(self):
        status, content_type, raw = self._request_raw("GET", "/wms/scan")
        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn(b"html5-qrcode", raw)



if __name__ == "__main__":
    unittest.main()
