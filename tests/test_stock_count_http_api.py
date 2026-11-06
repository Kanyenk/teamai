"""Tests HTTP des endpoints stock-counts (inventaires)."""

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
from xohive.wms.domain.stock_movement import StockMovement
from xohive.wms.domain.warehouse import Warehouse
from xohive.wms.repository.product_repository import ProductRepository
from xohive.wms.repository.stock_movement_repository import (
    StockMovementRepository,
)
from xohive.wms.repository.warehouse_repository import (
    WarehouseRepository,
)


class TestStockCountHttpApi(unittest.TestCase):
    """Tests HTTP des endpoints stock-counts."""

    def setUp(self):
        # Créer un dépôt temporaire et un serveur HTTP de test.
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = DocumentRepository(Path(self.tmp.name) / "test.db")
        self.auth = TokenAuth({"test-token"})
        self.server = HTTPServer(("127.0.0.1", 0), make_app(self.repo, auth=self.auth))
        self.server.store = self.repo
        self.server.auth = self.auth
        # Désactiver les logs HTTP pour garder la sortie de test propre.
        HttpHandler.log_message = lambda self, *a, **k: None
        # Démarrer le serveur dans un thread daemon.
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.headers = {"Authorization": "Bearer test-token", "Content-Type": "application/json"}
        self.products = ProductRepository(self.repo.db_path)
        self.warehouses = WarehouseRepository(self.repo.db_path)
        self.movements = StockMovementRepository(self.repo.db_path)

    def tearDown(self):
        # Arrêter la boucle serve_forever.
        self.server.shutdown()
        # Fermer la socket d'écoute (évite les ResourceWarning).
        self.server.server_close()
        # Fermer les connexions SQLite.
        self.products.close()
        self.warehouses.close()
        self.movements.close()
        # Nettoyer le répertoire temporaire.
        self.tmp.cleanup()

    def _create_product_and_warehouse(self, sku="SKU-SC", code="WH-SC"):
        """Helper : crée un produit et un entrepôt de test."""
        product = self.products.create(Product(
            organisation_id="org-1", sku=sku, name=f"P-{sku}",
        ))
        warehouse = self.warehouses.create(Warehouse(
            organisation_id="org-1", code=code, name="W",
        ))
        return product.id, warehouse.id

    def _create_stock(self, product_id, warehouse_id, quantity):
        """Helper : crée un stock initial via un mouvement d'entrée."""
        self.movements.create(StockMovement(
            organisation_id="org-1",
            product_id=product_id,
            warehouse_id=warehouse_id,
            movement_type="in",
            quantity=quantity,
        ))

    def test_create_stock_count_returns_201(self):
        """POST /api/v1/wms/stock-counts doit renvoyer 201."""
        product_id, warehouse_id = self._create_product_and_warehouse()
        body = json.dumps({
            "organisation_id": "org-1",
            "warehouse_id": warehouse_id,
            "product_id": product_id,
            "counted_quantity": 5,
        }).encode()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-counts",
            data=body, headers=self.headers, method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            self.assertEqual(r.status, 201)
            data = json.loads(r.read())
            self.assertEqual(data["item"]["counted_quantity"], 5)
            self.assertEqual(data["item"]["status"], "draft")

    def test_get_stock_count_returns_200(self):
        """GET /api/v1/wms/stock-counts/{id} doit renvoyer 200."""
        product_id, warehouse_id = self._create_product_and_warehouse()
        body = json.dumps({
            "organisation_id": "org-1",
            "warehouse_id": warehouse_id,
            "product_id": product_id,
            "counted_quantity": 3,
        }).encode()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-counts",
            data=body, headers=self.headers, method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            count_id = json.loads(r.read())["item"]["id"]
        # Consulter le comptage.
        req = urllib.request.Request(
            self.base + f"/api/v1/wms/stock-counts/{count_id}",
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            self.assertEqual(r.status, 200)
            data = json.loads(r.read())
            self.assertEqual(data["item"]["counted_quantity"], 3)

    def test_get_stock_count_not_found_returns_404(self):
        """GET /api/v1/wms/stock-counts/{id} inexistant doit renvoyer 404."""
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-counts/count-inconnu",
            headers={"Authorization": "Bearer test-token"},
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=10)
        self.assertEqual(ctx.exception.code, 404)

    def test_adjust_with_difference_returns_200(self):
        """POST /api/v1/wms/stock-counts/{id}/adjust doit renvoyer 200."""
        product_id, warehouse_id = self._create_product_and_warehouse()
        # Créer un stock théorique de 5.
        self._create_stock(product_id, warehouse_id, 5)
        # Créer un comptage de 3 (écart de -2).
        body = json.dumps({
            "organisation_id": "org-1",
            "warehouse_id": warehouse_id,
            "product_id": product_id,
            "counted_quantity": 3,
        }).encode()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-counts",
            data=body, headers=self.headers, method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            count_id = json.loads(r.read())["item"]["id"]
        # Ajuster le comptage.
        req = urllib.request.Request(
            self.base + f"/api/v1/wms/stock-counts/{count_id}/adjust",
            data=b"{}", headers=self.headers, method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            self.assertEqual(r.status, 200)
            data = json.loads(r.read())
            self.assertEqual(data["difference"], -2)
            self.assertIsNotNone(data["movement_id"])
            self.assertEqual(data["status"], "adjusted")

    def test_adjust_without_token_returns_401(self):
        """POST /api/v1/wms/stock-counts/{id}/adjust sans token doit renvoyer 401."""
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-counts/count-1/adjust",
            data=b"{}", method="POST",
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=10)
        self.assertEqual(ctx.exception.code, 401)

    def test_adjust_twice_returns_400(self):
        """POST /api/v1/wms/stock-counts/{id}/adjust deux fois doit renvoyer 400."""
        product_id, warehouse_id = self._create_product_and_warehouse()
        # Créer un comptage et l'ajuster une première fois.
        body = json.dumps({
            "organisation_id": "org-1",
            "warehouse_id": warehouse_id,
            "product_id": product_id,
            "counted_quantity": 0,
        }).encode()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/stock-counts",
            data=body, headers=self.headers, method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            count_id = json.loads(r.read())["item"]["id"]
        req = urllib.request.Request(
            self.base + f"/api/v1/wms/stock-counts/{count_id}/adjust",
            data=b"{}", headers=self.headers, method="POST",
        )
        urllib.request.urlopen(req, timeout=10).read()
        # Deuxième ajustement doit échouer (400).
        req = urllib.request.Request(
            self.base + f"/api/v1/wms/stock-counts/{count_id}/adjust",
            data=b"{}", headers=self.headers, method="POST",
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=10)
        self.assertEqual(ctx.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
