"""Tests for the minimal HTTP API.

Couverture :
- création
- lecture
- liste
- transition valide
- transition invalide
- document inexistant
"""

import unittest
import tempfile
import json
import sys
import io
from datetime import datetime, timezone
from pathlib import Path
from http.server import HTTPServer
from io import BytesIO

from engine import Document, DocumentError
from engine.http import HttpHandler, make_app
from engine.repository import DocumentRepository


class TestHttpApi(unittest.TestCase):
    """Tests de l'API HTTP minimale."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.repo = DocumentRepository(self.db_path)

        self.server = HTTPServer(("127.0.0.1", 0), make_app(self.repo))
        self.server.store = self.repo

        import threading
        # Supprime les logs du serveur HTTP pendant les tests
        HttpHandler.log_message = lambda self, format, *args: None
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()

        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.repo.close()
        self.temp_dir.cleanup()

    def _request(self, method, path, body=None):
        """Envoie une requête HTTP et retourne la réponse."""
        import urllib.request
        url = self.base_url + path
        data = None
        headers = {"Content-Type": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8"))

    def _create_document(self, doc_type="FACT", numero_serie=1, org_id=1):
        return self._request("POST", "/documents", {
            "doc_type": doc_type,
            "numero_serie": numero_serie,
            "org_id": org_id,
            "date_creation": datetime.now(timezone.utc).isoformat(),
        })

    def _get_document(self, doc_id):
        return self._request("GET", f"/documents/{doc_id}")

    def _list_documents(self):
        return self._request("GET", "/documents")

    def _transition(self, doc_id, etat, acteur="system"):
        return self._request("POST", f"/documents/{doc_id}/transition", {
            "etat": etat,
            "acteur": acteur,
        })

    # ── Tests de création ────────────────────────────────────────────────

    def test_create_document(self):
        status, data = self._create_document()
        self.assertEqual(status, 201)
        self.assertIn("item", data)
        self.assertEqual(data["item"]["doc_type"], "FACT")
        self.assertEqual(data["item"]["numero_serie"], 1)

    def test_create_document_invalid_type(self):
        status, data = self._create_document(doc_type="INVALID")
        self.assertEqual(status, 400)
        self.assertIn("error", data)

    def test_create_document_missing_fields(self):
        status, data = self._create_document(numero_serie=0)
        self.assertEqual(status, 400)

    # ── Tests de lecture ─────────────────────────────────────────────────

    def test_get_document(self):
        status, data = self._create_document()
        self.assertEqual(status, 201)
        doc_id = data["item"]["id"]

        status, data = self._get_document(doc_id)
        self.assertEqual(status, 200)
        self.assertEqual(data["item"]["doc_type"], "FACT")

    def test_get_nonexistent_document(self):
        status, data = self._get_document("inexistant")
        self.assertEqual(status, 404)
        self.assertIn("error", data)

    # ── Tests de liste ───────────────────────────────────────────────────

    def test_list_documents(self):
        self._create_document()
        self._create_document(doc_type="BC", numero_serie=2)

        status, data = self._list_documents()
        self.assertEqual(status, 200)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 2)

    def test_list_empty(self):
        status, data = self._list_documents()
        self.assertEqual(status, 200)
        self.assertEqual(data["items"], [])

    # ── Tests de transition ──────────────────────────────────────────────

    def test_valid_transition(self):
        status, data = self._create_document()
        self.assertEqual(status, 201)
        doc_id = data["item"]["id"]

        status, data = self._transition(doc_id, "brouillon_pdf")
        self.assertEqual(status, 200)
        self.assertEqual(data["item"]["etat"], "brouillon_pdf")

    def test_invalid_transition(self):
        status, data = self._create_document()
        self.assertEqual(status, 201)
        doc_id = data["item"]["id"]

        status, data = self._transition(doc_id, "envoye")
        self.assertEqual(status, 400)
        self.assertIn("error", data)

    def test_transition_nonexistent_document(self):
        status, data = self._transition("inexistant", "brouillon_pdf")
        self.assertEqual(status, 404)
        self.assertIn("error", data)

    def test_transition_invalid_state(self):
        status, data = self._create_document()
        self.assertEqual(status, 201)
        doc_id = data["item"]["id"]

        status, data = self._transition(doc_id, "inconnu")
        self.assertEqual(status, 400)
        self.assertIn("error", data)


if __name__ == "__main__":
    unittest.main()
