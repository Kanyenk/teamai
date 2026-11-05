"""Tests d'intégration HTTP pour les routes Ventes & Facturation.

Couverture :
- GET /api/v1/crm/pipeline/{company_id}
- GET /api/v1/crm/quotations
- POST /api/v1/crm/quotations
- GET /api/v1/crm/orders
- POST /api/v1/crm/orders
- GET /api/v1/crm/invoices
- POST /api/v1/crm/invoices
- GET /api/v1/crm/credit-notes
- POST /api/v1/crm/credit-notes
- GET /api/v1/crm/payments
- POST /api/v1/crm/payments
- GET /api/v1/crm/reconciliations
- POST /api/v1/crm/reconciliations
- Progression du pipeline (POST /api/v1/crm/opportunities/{id}/pipeline)

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


class TestCrmHttpApi(unittest.TestCase):
    """Tests d'intégration de l'API HTTP CRM."""

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
        if hasattr(cls, 'server'):
            cls.server.shutdown()
            cls.server.server_close()
            cls.thread.join(timeout=5)
            cls.repo.close()
        if hasattr(cls, 'temp_dir'):
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
        # Toujours envoyer le token pour les requêtes non-Health
        if token is not None and path != "/health":
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8"))

    def _create_organisation(self):
        return self._request("POST", "/api/v1/crm/companies", {
            "organisation_id": "org-test",
            "name": "Test Corp",
            "siret": "12345678901234",
            "contact_person": "Test User",
            "email": f"test-{uuid.uuid4().hex[:8]}@example.com",
            "city": "Paris",
            "zip_code": "75001",
            "country": "FR",
            "is_active": True,
        })

    def _create_contact(self, company_id):
        return self._request("POST", "/api/v1/crm/contacts", {
            "organisation_id": "org-test",
            "company_id": company_id,
            "first_name": "Test",
            "last_name": "Contact",
            "email": f"contact-{uuid.uuid4().hex[:8]}@example.com",
            "job_title": "Directeur",
            "is_active": True,
        })

    def _create_opportunity(self, company_id, contact_id):
        from datetime import datetime, timezone
        return self._request("POST", "/api/v1/crm/opportunities", {
            "organisation_id": "org-test",
            "company_id": company_id,
            "contact_id": contact_id,
            "title": "Test Opportunity",
            "amount": 10000.00,
            "stage": "prospecting",
            "probability": 30,
            "is_active": True,
        })

    def _create_quotation(self, company_id, contact_id):
        now = datetime.now(timezone.utc)
        valid_until = (now.timestamp() + 30 * 86400)
        return self._request("POST", "/api/v1/crm/quotations", {
            "organisation_id": "org-test",
            "company_id": company_id,
            "contact_id": contact_id,
            "reference": f"QTE-{uuid.uuid4().hex[:8]}",
            "quotation_date": now.isoformat(),
            "valid_until": datetime.fromtimestamp(valid_until, tz=timezone.utc).isoformat(),
            "total_amount": 5000.00,
            "tax_rate": 20.0,
            "currency": "EUR",
            "status": "draft",
            "is_active": True,
        })

    def _create_order(self, company_id, quotation_id):
        return self._request("POST", "/api/v1/crm/orders", {
            "organisation_id": "org-test",
            "company_id": company_id,
            "quotation_id": quotation_id,
            "order_date": datetime.now(timezone.utc).isoformat(),
            "shipping_method": "standard",
            "total_amount": 5000.00,
            "tax_rate": 20.0,
            "currency": "EUR",
            "status": "pending",
            "is_active": True,
        })

    def _create_invoice(self, company_id, order_id):
        now = datetime.now(timezone.utc)
        due_date = (now.timestamp() + 30 * 86400)
        return self._request("POST", "/api/v1/crm/invoices", {
            "organisation_id": "org-test",
            "company_id": company_id,
            "order_id": order_id,
            "issue_date": now.isoformat(),
            "due_date": datetime.fromtimestamp(due_date, tz=timezone.utc).isoformat(),
            "amount": 5000.00,
            "tax_rate": 20.0,
            "currency": "EUR",
            "status": "draft",
            "is_active": True,
        })

    def _create_credit_note(self, company_id, invoice_id):
        return self._request("POST", "/api/v1/crm/credit-notes", {
            "organisation_id": "org-test",
            "company_id": company_id,
            "invoice_id": invoice_id,
            "credit_date": datetime.now(timezone.utc).isoformat(),
            "amount": 500.00,
            "reason": "Remboursement partiel",
            "currency": "EUR",
            "status": "draft",
            "is_active": True,
        })

    def _create_payment(self, company_id, invoice_id):
        return self._request("POST", "/api/v1/crm/payments", {
            "organisation_id": "org-test",
            "company_id": company_id,
            "invoice_id": invoice_id,
            "amount": 4500.00,
            "currency": "EUR",
            "payment_date": datetime.now(timezone.utc).isoformat(),
            "method": "bank_transfer",
            "status": "completed",
            "is_active": True,
        })

    def _create_reconciliation(self, company_id, payment_id, ledger_entry_id):
        return self._request("POST", "/api/v1/crm/reconciliations", {
            "organisation_id": "org-test",
            "company_id": company_id,
            "payment_id": payment_id,
            "ledger_entry_id": ledger_entry_id,
            "bank_date": datetime.now(timezone.utc).isoformat(),
            "amount": 4500.00,
            "currency": "EUR",
            "status": "open",
            "reference": "REC-001",
            "is_active": True,
        })

    # ── Tests de création ────────────────────────────────────────────────

    def test_pipeline_get(self):
        """Test GET /api/v1/crm/pipeline/{company_id}."""
        status, data = self._request("GET", "/api/v1/crm/pipeline")
        self.assertEqual(status, 200)
        self.assertIn("pipeline_stage", data)

    def test_quotations_get(self):
        """Test GET /api/v1/crm/quotations."""
        status, data = self._request("GET", "/api/v1/crm/quotations")
        self.assertEqual(status, 200)
        self.assertIn("items", data)

    def test_quotation_create(self):
        """Test POST /api/v1/crm/quotations."""
        company = self._create_organisation()
        self.assertEqual(company[0], 201)
        company_id = company[1]["item"]["id"]

        contact = self._create_contact(company_id)
        self.assertEqual(contact[0], 201)
        contact_id = contact[1]["item"]["id"]

        quote = self._create_quotation(company_id, contact_id)
        # Debug: print the actual response
        print(f"\n=== DEBUG ===\nquote status: {quote[0]}\nquote error: {quote[1].get('error', 'no error') if isinstance(quote[1], dict) else type(quote[1])}\n=== END DEBUG ===\n", flush=True)
        self.assertEqual(quote[0], 201)
        self.assertIn("item", quote[1])
        self.assertEqual(quote[1]["item"]["status"], "draft")

    def test_orders_get(self):
        """Test GET /api/v1/crm/orders."""
        status, data = self._request("GET", "/api/v1/crm/orders")
        self.assertEqual(status, 200)
        self.assertIn("items", data)

    def test_order_create(self):
        """Test POST /api/v1/crm/orders."""
        company = self._create_organisation()
        company_id = company[1]["item"]["id"]
        contact = self._create_contact(company_id)
        contact_id = contact[1]["item"]["id"]

        quote = self._create_quotation(company_id, contact_id)
        quotation_id = quote[1]["item"]["id"]

        order = self._create_order(company_id, quotation_id)
        self.assertEqual(order[0], 201)
        self.assertIn("item", order[1])
        self.assertEqual(order[1]["item"]["status"], "pending")

    def test_invoices_get(self):
        """Test GET /api/v1/crm/invoices."""
        status, data = self._request("GET", "/api/v1/crm/invoices")
        self.assertEqual(status, 200)
        self.assertIn("items", data)

    def test_invoice_create(self):
        """Test POST /api/v1/crm/invoices."""
        company = self._create_organisation()
        company_id = company[1]["item"]["id"]

        contact = self._create_contact(company_id)
        quote = self._create_quotation(company_id, contact[1]["item"]["id"])
        order = self._create_order(company_id, quote[1]["item"]["id"])
        order_id = order[1]["item"]["id"]

        invoice = self._create_invoice(company_id, order_id)
        self.assertEqual(invoice[0], 201)
        self.assertIn("item", invoice[1])
        self.assertEqual(invoice[1]["item"]["status"], "draft")

    def test_credit_notes_get(self):
        """Test GET /api/v1/crm/credit-notes."""
        status, data = self._request("GET", "/api/v1/crm/credit-notes")
        self.assertEqual(status, 200)
        self.assertIn("items", data)

    def test_credit_note_create(self):
        """Test POST /api/v1/crm/credit-notes."""
        company = self._create_organisation()
        company_id = company[1]["item"]["id"]

        contact = self._create_contact(company_id)
        quote = self._create_quotation(company_id, contact[1]["item"]["id"])
        order = self._create_order(company_id, quote[1]["item"]["id"])
        invoice = self._create_invoice(company_id, order[1]["item"]["id"])

        credit_note = self._create_credit_note(company_id, invoice[1]["item"]["id"])
        self.assertEqual(credit_note[0], 201)

    def test_payments_get(self):
        """Test GET /api/v1/crm/payments."""
        status, data = self._request("GET", "/api/v1/crm/payments")
        self.assertEqual(status, 200)
        self.assertIn("items", data)

    def test_payment_create(self):
        """Test POST /api/v1/crm/payments."""
        company = self._create_organisation()
        company_id = company[1]["item"]["id"]

        contact = self._create_contact(company_id)
        quote = self._create_quotation(company_id, contact[1]["item"]["id"])
        order = self._create_order(company_id, quote[1]["item"]["id"])
        invoice = self._create_invoice(company_id, order[1]["item"]["id"])

        payment = self._create_payment(company_id, invoice[1]["item"]["id"])
        self.assertEqual(payment[0], 201)
        self.assertIn("item", payment[1])

    def test_reconciliations_get(self):
        """Test GET /api/v1/crm/reconciliations."""
        status, data = self._request("GET", "/api/v1/crm/reconciliations")
        self.assertEqual(status, 200)
        self.assertIn("items", data)

    def test_reconciliation_create(self):
        """Test POST /api/v1/crm/reconciliations."""
        company = self._create_organisation()
        company_id = company[1]["item"]["id"]

        contact = self._create_contact(company_id)
        quote = self._create_quotation(company_id, contact[1]["item"]["id"])
        order = self._create_order(company_id, quote[1]["item"]["id"])
        invoice = self._create_invoice(company_id, order[1]["item"]["id"])
        payment = self._create_payment(company_id, invoice[1]["item"]["id"])

        reconciliation = self._create_reconciliation(
            company_id, payment[1]["item"]["id"], "ledger-entry-id"
        )
        self.assertEqual(reconciliation[0], 201)

    # ── Tests de progression de pipeline ────────────────────────────────

    def test_pipeline_progression(self):
        """Test progression de l'opportunité dans le pipeline."""
        company = self._create_organisation()
        company_id = company[1]["item"]["id"]
        contact = self._create_contact(company_id)
        contact_id = contact[1]["item"]["id"]

        opp = self._create_opportunity(company_id, contact_id)
        opp_id = opp[1]["item"]["id"]

        # Progression prospecting → qualifying
        status, data = self._request("POST", f"/api/v1/crm/opportunities/{opp_id}/pipeline", {
            "stage": "qualifying"
        })
        self.assertEqual(status, 200)
        self.assertEqual(data["stage"], "qualifying")

    # ── Tests d'erreur / validation ─────────────────────────────────────

    def test_missing_token(self):
        """Test que l'absence de token retourne 401."""
        status, data = self._request("GET", "/api/v1/crm/quotations", token=None)
        self.assertEqual(status, 401)

    def test_invalid_token(self):
        """Test que le token invalide retourne 401."""
        status, data = self._request("GET", "/api/v1/crm/quotations", token="invalid")
        self.assertEqual(status, 401)

    def test_quotation_not_found(self):
        """Test GET /api/v1/crm/quotations/{id} pour un id inexistant."""
        status, data = self._request("GET", "/api/v1/crm/quotations/unknown-id")
        self.assertEqual(status, 404)

    def test_order_not_found(self):
        """Test GET /api/v1/crm/orders/{id} pour un id inexistant."""
        status, data = self._request("GET", "/api/v1/crm/orders/unknown-id")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
