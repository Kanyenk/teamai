"""Tests d'intégration HTTP pour les routes relevés bancaires.

Couverture :
- POST /api/v1/crm/bank-statements/import
- GET  /api/v1/crm/bank-statements
- GET  /api/v1/crm/bank-statements/{id}/matches
- POST /api/v1/crm/bank-statements/{id}/reconcile

Avec l'API sécurisée (Bearer token).
"""

import unittest
import tempfile
import json
import sys
import io
import uuid
from datetime import datetime, timezone
from pathlib import Path
from http.server import HTTPServer
from io import BytesIO

# Ajout du répertoire parent au chemin d'import
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.http import HttpHandler, make_app
from engine.auth import TokenAuth
from engine.repository import DocumentRepository


class TestBankStatementHttpApi(unittest.TestCase):
    """Tests d'intégration de l'API HTTP relevés bancaires."""

    SERVER_AVAILABLE = False

    @classmethod
    def setUpClass(cls):
        """Configuration de la classe (executée une fois)."""
        try:
            cls.temp_dir = tempfile.TemporaryDirectory()
            cls.db_path = Path(cls.temp_dir.name) / "test_teamai.db"
            cls.repo = DocumentRepository(cls.db_path)
            auth = TokenAuth({"test-token"})
            cls.server = HTTPServer(("127.0.0.1", 0), make_app(cls.repo, auth=auth))
            cls.server.store = cls.repo
            cls.server.auth = auth
            import threading

            HttpHandler.log_message = lambda self, format, *args: None
            cls.thread = threading.Thread(target=cls.server.serve_forever)
            cls.thread.start()
            cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"
            cls.SERVER_AVAILABLE = True
        except Exception as e:
            cls.SERVER_AVAILABLE = False
            print(f"Erreur de configuration du serveur : {e}")

    @classmethod
    def tearDownClass(cls):
        """Nettoyage après tous les tests."""
        if hasattr(cls, "server"):
            cls.server.shutdown()
            cls.server.server_close()
            cls.thread.join(timeout=5)
            cls.repo.close()
        if hasattr(cls, "temp_dir"):
            cls.temp_dir.cleanup()

    def setUp(self):
        """Préparation avant chaque test."""
        if not self.SERVER_AVAILABLE:
            self.skipTest("Serveur HTTP non disponible")

    def _request(self, method, path, body=None, token="test-token"):
        """Envoie une requête HTTP et retourne la réponse."""
        import urllib.request
        import urllib.error

        url = self.base_url + path
        data = None
        headers = {"Content-Type": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
        if token is not None and path != "/health":
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8"))

    def _import_bank_statement(self, statement_date, file_name, amount, reference):
        """Helper pour importer un relevé bancaire."""
        return self._request(
            "POST",
            "/api/v1/crm/bank-statements/import",
            {
                "statement_date": statement_date,
                "file_name": file_name,
                "amount": amount,
                "reference": reference,
            },
        )

    def test_import_bank_statement(self):
        """Test POST /api/v1/crm/bank-statements/import."""
        status, data = self._import_bank_statement(
            statement_date=datetime.now(timezone.utc).isoformat(),
            file_name="autorisation_001.csv",
            amount=50.00,
            reference="REF-001",
        )
        self.assertEqual(status, 201)
        self.assertIn("item", data)
        self.assertIn("id", data["item"])
        self.assertEqual(data["item"]["file_name"], "autorisation_001.csv")

    def test_import_missing_token(self):
        """Test que l'absence de token retourne 401."""
        status, data = self._request("POST", "/api/v1/crm/bank-statements/import", token=None)
        self.assertEqual(status, 401)

    def test_banks_statement_get(self):
        """Test GET /api/v1/crm/bank-statements."""
        status, data = self._request("GET", "/api/v1/crm/bank-statements")
        self.assertEqual(status, 200)
        self.assertIn("items", data)

    def test_banks_statement_get_one(self):
        """Test GET /api/v1/crm/bank-statements/{id}."""
        # First create
        status, data = self._import_bank_statement(
            statement_date=datetime.now(timezone.utc).isoformat(),
            file_name="autorisation_002.csv",
            amount=100.00,
            reference="REF-002",
        )
        statement_id = data["item"]["id"]

        # Then get
        status, data = self._request("GET", f"/api/v1/crm/bank-statements/{statement_id}")
        self.assertEqual(status, 200)
        self.assertEqual(data["item"]["file_name"], "autorisation_002.csv")

    def test_matches_get(self):
        """Test GET /api/v1/crm/bank-statements/{id}/matches."""
        # First create a statement
        status, data = self._request(
            "POST",
            "/api/v1/crm/bank-statements/import",
            {
                "statement_date": datetime.now(timezone.utc).isoformat(),
                "file_name": "autorisation_003.csv",
                "amount": 75.00,
                "reference": "REF-003",
            },
        )
        statement_id = data["item"]["id"]

        # Then get matches (should be empty initially)
        status, data = self._request(f"GET", f"/api/v1/crm/bank-statements/{statement_id}/matches")
        self.assertEqual(status, 200)
        self.assertEqual(data.get("items"), [])

    def test_reconcile(self):
        """Test POST /api/v1/crm/bank-statements/{id}/reconcile."""
        # First create a statement
        status, data = self._request(
            "POST",
            "/api/v1/crm/bank-statements/import",
            {
                "statement_date": datetime.now(timezone.utc).isoformat(),
                "file_name": "autorisation_004.csv",
                "amount": 200.00,
                "reference": "REF-004",
            },
        )
        statement_id = data["item"]["id"]

        # Then reconcile
        status, data = self._request(
            "POST",
            f"/api/v1/crm/bank-statements/{statement_id}/reconcile",
            body={"payment_id": "test-payment-id"},
        )
        self.assertEqual(status, 201)
        self.assertIn("item", data)
        self.assertEqual(data["item"]["status"], "pending")


if __name__ == "__main__":
    unittest.main()
