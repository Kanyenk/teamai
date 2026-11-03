"""Tests d'authentification token pour l'API HTTP."""

import unittest
import tempfile
import json
from datetime import datetime, timezone
from pathlib import Path
from http.server import HTTPServer
from engine import Document, DocumentError
from engine.http import HttpHandler, make_app
from engine.repository import DocumentRepository
from engine.auth import TokenAuth

VALID_TOKENS = {"tok_valid", "tok_456"}


class TestApiAuth(unittest.TestCase):
    """Tests d'authentification pour l'API HTTP."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.repo = DocumentRepository(self.db_path)
        self.auth = TokenAuth(VALID_TOKENS)

        self.server = HTTPServer(("127.0.0.1", 0), make_app(self.repo, self.auth))
        self.server.store = self.repo
        self.server.auth = self.auth
        import threading
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()

        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.repo.close()
        self.temp_dir.cleanup()

    def _request(self, method, path, body=None, token=None):
        """Envoie une requête HTTP avec un token optionnel."""
        import urllib.request
        url = self.base_url + path
        data = None
        headers = {"Content-Type": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8"))

    # ── Tests de /health ────────────────────────────────────────────────

    def test_health_without_token(self):
        status, data = self._request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(data, {"status": "ok"})

    # ── Tests de création (POST /documents) ──────────────────────────────

    def test_create_without_token(self):
        status, data = self._request("POST", "/documents", {
            "doc_type": "FACT",
            "numero_serie": 1,
            "org_id": 1,
            "date_creation": datetime.now(timezone.utc).isoformat(),
        })
        self.assertEqual(status, 401)

    def test_create_with_invalid_token(self):
        status, data = self._request("POST", "/documents", {
            "doc_type": "FACT",
            "numero_serie": 1,
            "org_id": 1,
            "date_creation": datetime.now(timezone.utc).isoformat(),
        }, token="invalid")
        self.assertEqual(status, 401)

    def test_create_with_valid_token(self):
        status, data = self._request("POST", "/documents", {
            "doc_type": "FACT",
            "numero_serie": 1,
            "org_id": 1,
            "date_creation": datetime.now(timezone.utc).isoformat(),
        }, token="tok_valid")
        self.assertEqual(status, 201)
        self.assertEqual(data["item"]["doc_type"], "FACT")

    # ── Tests de lecture (GET /documents/{id}) ───────────────────────────

    def test_read_without_token(self):
        status, _ = self._request("GET", "/documents/123")
        self.assertEqual(status, 401)

    def test_read_with_invalid_token(self):
        status, _ = self._request("GET", "/documents/123", token="invalid")
        self.assertEqual(status, 401)

    def test_read_with_valid_token(self):
        # Créer d'abord un document
        status, data = self._request("POST", "/documents", {
            "doc_type": "FACT",
            "numero_serie": 9,
            "org_id": 1,
            "date_creation": datetime.now(timezone.utc).isoformat(),
        }, token="tok_valid")
        self.assertEqual(status, 201)
        doc_id = data["item"]["id"]

        # Lire le document
        status, data = self._request("GET", f"/documents/{doc_id}", token="tok_valid")
        self.assertEqual(status, 200)
        self.assertEqual(data["item"]["doc_type"], "FACT")

    # ── Tests de transition (POST /documents/{id}/transition) ────────────

    def test_transition_without_token(self):
        status, _ = self._request("POST", "/documents/123/transition", {
            "etat": "brouillon_pdf",
        })
        self.assertEqual(status, 401)

    def test_transition_with_invalid_token(self):
        status, _ = self._request("POST", "/documents/123/transition", {
            "etat": "brouillon_pdf",
        }, token="invalid")
        self.assertEqual(status, 401)

    def test_transition_with_valid_token(self):
        # Créer un document
        status, data = self._request("POST", "/documents", {
            "doc_type": "FACT",
            "numero_serie": 5,
            "org_id": 1,
            "date_creation": datetime.now(timezone.utc).isoformat(),
        }, token="tok_valid")
        self.assertEqual(status, 201)
        doc_id = data["item"]["id"]

        # Faire une transition valide
        status, data = self._request("POST", f"/documents/{doc_id}/transition", {
            "etat": "brouillon_pdf",
        }, token="tok_valid")
        self.assertEqual(status, 200)
        self.assertEqual(data["item"]["etat"], "brouillon_pdf")

    def test_transition_invalid_state_returns_400(self):
        # Créer un document
        status, data = self._request("POST", "/documents", {
            "doc_type": "FACT",
            "numero_serie": 7,
            "org_id": 1,
            "date_creation": datetime.now(timezone.utc).isoformat(),
        }, token="tok_valid")
        self.assertEqual(status, 201)
        doc_id = data["item"]["id"]

        # Faire une transition invalide (brouillon -> envoye n'est pas autorisé)
        status, data = self._request("POST", f"/documents/{doc_id}/transition", {
            "etat": "envoye",
        }, token="tok_valid")
        self.assertEqual(status, 400)
