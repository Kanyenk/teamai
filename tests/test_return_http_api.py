"""Tests HTTP des retours clients (http.server)."""
import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import HTTPServer
from types import SimpleNamespace

from engine.http import make_app
from engine.return_repository import ReturnRepository
from engine.return_service import ReturnService


class TestReturnHttpApi(unittest.TestCase):
    """Tests HTTP des endpoints retours."""

    def setUp(self):
        """Démarre un serveur HTTP sur un port éphémère."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.repo = ReturnRepository(db_path=self.db_path)
        self.service = ReturnService(self.repo)
        store = SimpleNamespace(db_path=self.db_path)
        handler = make_app(store, auth=None)
        self.server = HTTPServer(("127.0.0.1", 0), handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.port}"

    def tearDown(self):
        """Arrête le serveur et supprime la base."""
        self.server.shutdown()
        self.server.server_close()
        os.unlink(self.db_path)

    def _request(self, method, path, payload=None):
        """Envoie une requête HTTP et retourne (status, body)."""
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(
            self.base + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())

    def _create_return(self, **overrides):
        """Crée un retour de test via l'API."""
        payload = {
            "organisation_id": "org-1",
            "order_id": "ord-1",
            "product_id": "prod-1",
            "quantity": 2,
            "reason": "Produit défectueux",
        }
        payload.update(overrides)
        status, body = self._request("POST", "/api/v1/wms/returns", payload)
        return status, body

    def test_create_return(self):
        """POST /api/v1/wms/returns doit créer un retour (201)."""
        status, body = self._create_return()
        self.assertEqual(status, 201)
        self.assertIn("item", body)
        self.assertEqual(body["item"]["status"], "draft")

    def test_create_return_missing_field(self):
        """POST sans champ requis doit retourner 400."""
        status, _ = self._create_return(organisation_id="")
        self.assertEqual(status, 400)

    def test_list_returns(self):
        """GET /api/v1/wms/returns doit lister les retours (200)."""
        self._create_return()
        status, body = self._request("GET", "/api/v1/wms/returns?organisation_id=org-1")
        self.assertEqual(status, 200)
        self.assertEqual(len(body["items"]), 1)

    def test_list_returns_missing_org(self):
        """GET sans organisation_id doit retourner 400."""
        status, _ = self._request("GET", "/api/v1/wms/returns")
        self.assertEqual(status, 400)

    def test_get_return(self):
        """GET /api/v1/wms/returns/{id} doit retourner le retour (200)."""
        _, body = self._create_return()
        ret_id = body["item"]["id"]
        status, body = self._request("GET", f"/api/v1/wms/returns/{ret_id}")
        self.assertEqual(status, 200)
        self.assertEqual(body["item"]["id"], ret_id)

    def test_get_return_not_found(self):
        """GET sur un retour inexistant doit retourner 404."""
        status, _ = self._request("GET", "/api/v1/wms/returns/ret-inexistant")
        self.assertEqual(status, 404)

    def test_request_return(self):
        """POST /request doit passer le retour en requested (200)."""
        _, body = self._create_return()
        ret_id = body["item"]["id"]
        status, body = self._request("POST", f"/api/v1/wms/returns/{ret_id}/request")
        self.assertEqual(status, 200)
        self.assertEqual(body["item"]["status"], "requested")

    def test_receive_return(self):
        """POST /receive doit passer le retour en received (200)."""
        _, body = self._create_return()
        ret_id = body["item"]["id"]
        self._request("POST", f"/api/v1/wms/returns/{ret_id}/request")
        status, body = self._request("POST", f"/api/v1/wms/returns/{ret_id}/receive")
        self.assertEqual(status, 200)
        self.assertEqual(body["item"]["status"], "received")

    def test_refund_return(self):
        """POST /refund doit passer le retour en refunded (200)."""
        _, body = self._create_return()
        ret_id = body["item"]["id"]
        self._request("POST", f"/api/v1/wms/returns/{ret_id}/request")
        self._request("POST", f"/api/v1/wms/returns/{ret_id}/receive")
        status, body = self._request("POST", f"/api/v1/wms/returns/{ret_id}/refund", {"amount": 50.0})
        self.assertEqual(status, 200)
        self.assertEqual(body["item"]["status"], "refunded")
        self.assertEqual(body["item"]["refund_amount"], 50.0)

    def test_cancel_return(self):
        """POST /cancel doit annuler le retour (200)."""
        _, body = self._create_return()
        ret_id = body["item"]["id"]
        status, body = self._request("POST", f"/api/v1/wms/returns/{ret_id}/cancel")
        self.assertEqual(status, 200)
        self.assertEqual(body["item"]["status"], "cancelled")


if __name__ == "__main__":
    unittest.main()
