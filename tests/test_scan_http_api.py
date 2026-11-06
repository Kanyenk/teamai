"""Tests HTTP du endpoint scan (barcode -> mouvement de stock)."""
import json, os, tempfile, threading, unittest, urllib.error, urllib.request
from http.server import HTTPServer
from types import SimpleNamespace
from engine.http import make_app
from engine.barcode_repository import BarcodeRepository
from engine.barcode_service import BarcodeService


class TestScanHttpApi(unittest.TestCase):
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

    def _create_barcode(self):
        status, body = self._request("POST", "/api/v1/wms/barcodes", {
            "organisation_id": "org-1",
            "product_id": "prod-1",
            "code": "3012345678900",
            "type": "ean13",
            "label": "Test",
        })
        return body["item"]["id"]

    def test_scan_unknown_barcode(self):
        status, _ = self._request("POST", "/api/v1/wms/scan", {
            "organisation_id": "org-1",
            "code": "inconnu",
            "warehouse_id": "wh-1",
            "movement_type": "in",
            "quantity": 5,
        })
        self.assertEqual(status, 404)

    def test_scan_missing_warehouse(self):
        self._create_barcode()
        status, _ = self._request("POST", "/api/v1/wms/scan", {
            "organisation_id": "org-1",
            "code": "3012345678900",
            "movement_type": "in",
            "quantity": 5,
        })
        self.assertEqual(status, 400)

    def _create_barcode_for(self, product_id):
        status, body = self._request("POST", "/api/v1/wms/barcodes", {
            "organisation_id": "org-1",
            "product_id": product_id,
            "code": "3012345678900",
            "type": "ean13",
            "label": "Test",
        })
        return body["item"]["id"]

    def _create_product_and_warehouses(self):
        from xohive.wms.domain.product import Product
        from xohive.wms.repository.product_repository import ProductRepository
        from xohive.wms.domain.warehouse import Warehouse
        from xohive.wms.repository.warehouse_repository import WarehouseRepository

        product = Product(organisation_id="org-1", sku="SKU-1", name="Produit Test")
        products = ProductRepository(self.db_path)
        try:
            product = products.create(product)
        finally:
            products.close()

        wh1 = Warehouse(organisation_id="org-1", code="WH-1", name="Entrepôt 1")
        wh2 = Warehouse(organisation_id="org-1", code="WH-2", name="Entrepôt 2")
        warehouses = WarehouseRepository(self.db_path)
        try:
            wh1 = warehouses.create(wh1)
            wh2 = warehouses.create(wh2)
        finally:
            warehouses.close()
        return product.id, wh1.id, wh2.id

    def test_scan_in(self):
        product_id, wh1_id, _ = self._create_product_and_warehouses()
        self._create_barcode_for(product_id)
        status, body = self._request("POST", "/api/v1/wms/scan", {
            "organisation_id": "org-1",
            "code": "3012345678900",
            "warehouse_id": wh1_id,
            "movement_type": "in",
            "quantity": 5,
        })
        self.assertEqual(status, 201)
        self.assertEqual(body["item"]["product_id"], product_id)
        self.assertEqual(body["item"]["movement_type"], "in")
        self.assertEqual(body["item"]["quantity"], 5)

    def test_scan_out_insufficient(self):
        product_id, wh1_id, _ = self._create_product_and_warehouses()
        self._create_barcode_for(product_id)
        status, _ = self._request("POST", "/api/v1/wms/scan", {
            "organisation_id": "org-1",
            "code": "3012345678900",
            "warehouse_id": wh1_id,
            "movement_type": "out",
            "quantity": 100,
        })
        self.assertEqual(status, 400)

    def test_scan_transfer(self):
        product_id, wh1_id, wh2_id = self._create_product_and_warehouses()
        self._create_barcode_for(product_id)
        # Entrée de 10 dans wh1.
        self._request("POST", "/api/v1/wms/scan", {
            "organisation_id": "org-1",
            "code": "3012345678900",
            "warehouse_id": wh1_id,
            "movement_type": "in",
            "quantity": 10,
        })
        # Transfert de 5 vers wh2.
        status, body = self._request("POST", "/api/v1/wms/scan", {
            "organisation_id": "org-1",
            "code": "3012345678900",
            "warehouse_id": wh1_id,
            "movement_type": "transfer",
            "quantity": 5,
            "target_warehouse_id": wh2_id,
        })
        self.assertEqual(status, 201)
        self.assertEqual(body["item"]["movement_type"], "transfer")
        self.assertEqual(body["item"]["target_warehouse_id"], wh2_id)



if __name__ == "__main__":
    unittest.main()
