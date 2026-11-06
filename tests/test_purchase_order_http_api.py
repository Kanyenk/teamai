"""Tests HTTP des endpoints purchase-orders (réceptions fournisseurs)."""

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
from xohive.wms.repository.warehouse_repository import (
    WarehouseRepository,
)


class TestPurchaseOrderHttpApi(unittest.TestCase):
    """Tests HTTP des endpoints purchase-orders."""

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
        self.warehouses = WarehouseRepository(self.repo.db_path)

    def tearDown(self):
        # Arrêter la boucle serve_forever.
        self.server.shutdown()
        # Fermer la socket d'écoute (évite les ResourceWarning).
        self.server.server_close()
        # Fermer les connexions SQLite.
        self.warehouses.close()
        # Nettoyer le répertoire temporaire.
        self.tmp.cleanup()

    def _create_warehouse(self, code="WH-PO"):
        """Helper : crée un entrepôt de test."""
        warehouse = self.warehouses.create(Warehouse(
            organisation_id="org-1", code=code, name="W",
        ))
        return warehouse.id

    def test_create_purchase_order_returns_201(self):
        """POST /api/v1/wms/purchase-orders doit renvoyer 201."""
        warehouse_id = self._create_warehouse()
        body = json.dumps({
            "organisation_id": "org-1",
            "supplier_name": "Fournisseur A",
            "warehouse_id": warehouse_id,
        }).encode()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/purchase-orders",
            data=body, headers=self.headers, method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            self.assertEqual(r.status, 201)
            data = json.loads(r.read())
            self.assertEqual(data["item"]["supplier_name"], "Fournisseur A")
            self.assertEqual(data["item"]["status"], "draft")

    def test_get_purchase_order_returns_200(self):
        """GET /api/v1/wms/purchase-orders/{id} doit renvoyer 200."""
        warehouse_id = self._create_warehouse()
        body = json.dumps({
            "organisation_id": "org-1",
            "supplier_name": "Fournisseur B",
            "warehouse_id": warehouse_id,
        }).encode()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/purchase-orders",
            data=body, headers=self.headers, method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            order_id = json.loads(r.read())["item"]["id"]
        # Consulter la commande.
        req = urllib.request.Request(
            self.base + f"/api/v1/wms/purchase-orders/{order_id}",
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            self.assertEqual(r.status, 200)
            data = json.loads(r.read())
            self.assertEqual(data["item"]["supplier_name"], "Fournisseur B")

    def test_get_purchase_orders_list_returns_200(self):
        """GET /api/v1/wms/purchase-orders doit renvoyer 200."""
        warehouse_id = self._create_warehouse()
        body = json.dumps({
            "organisation_id": "org-1",
            "supplier_name": "Fournisseur C",
            "warehouse_id": warehouse_id,
        }).encode()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/purchase-orders",
            data=body, headers=self.headers, method="POST",
        )
        urllib.request.urlopen(req, timeout=10).read()
        # Lister les commandes.
        req = urllib.request.Request(
            self.base + "/api/v1/wms/purchase-orders?organisation_id=org-1",
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            self.assertEqual(r.status, 200)
            data = json.loads(r.read())
            self.assertGreaterEqual(len(data["items"]), 1)

    def test_receive_purchase_order_returns_200(self):
        """POST /api/v1/wms/purchase-orders/{id}/receive doit renvoyer 200."""
        warehouse_id = self._create_warehouse()
        body = json.dumps({
            "organisation_id": "org-1",
            "supplier_name": "Fournisseur D",
            "warehouse_id": warehouse_id,
        }).encode()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/purchase-orders",
            data=body, headers=self.headers, method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            order_id = json.loads(r.read())["item"]["id"]
        # Réceptionner la commande.
        req = urllib.request.Request(
            self.base + f"/api/v1/wms/purchase-orders/{order_id}/receive",
            data=b"{}", headers=self.headers, method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            self.assertEqual(r.status, 200)
            data = json.loads(r.read())
            self.assertEqual(data["item"]["status"], "received")

    def test_receive_twice_returns_400(self):
        """POST /api/v1/wms/purchase-orders/{id}/receive deux fois doit renvoyer 400."""
        warehouse_id = self._create_warehouse()
        body = json.dumps({
            "organisation_id": "org-1",
            "supplier_name": "Fournisseur E",
            "warehouse_id": warehouse_id,
        }).encode()
        req = urllib.request.Request(
            self.base + "/api/v1/wms/purchase-orders",
            data=body, headers=self.headers, method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            order_id = json.loads(r.read())["item"]["id"]
        # Première réception.
        req = urllib.request.Request(
            self.base + f"/api/v1/wms/purchase-orders/{order_id}/receive",
            data=b"{}", headers=self.headers, method="POST",
        )
        urllib.request.urlopen(req, timeout=10).read()
        # Deuxième réception doit échouer (400).
        req = urllib.request.Request(
            self.base + f"/api/v1/wms/purchase-orders/{order_id}/receive",
            data=b"{}", headers=self.headers, method="POST",
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=10)
        self.assertEqual(ctx.exception.code, 400)

    def test_create_without_token_returns_401(self):
        """POST /api/v1/wms/purchase-orders sans token doit renvoyer 401."""
        req = urllib.request.Request(
            self.base + "/api/v1/wms/purchase-orders",
            data=b"{}", method="POST",
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=10)
        self.assertEqual(ctx.exception.code, 401)


if __name__ == "__main__":
    unittest.main()
