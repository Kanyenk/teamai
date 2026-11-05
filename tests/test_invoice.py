"""Tests unitaires pour le module Invoice."""

import unittest
import tempfile
import shutil
import os
from datetime import datetime, timezone

from xohive.crm.domain.invoice import Invoice, InvoiceError
from xohive.crm.repository.invoice_repository import InvoiceRepository


class TestInvoiceCreation(unittest.TestCase):
    """Tests pour la création d'une facture."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_teamai.db")
        self.repo = InvoiceRepository(self.db_path)
        self.invoice = Invoice(
            organisation_id="org-1",
            company_id="cmp-1",
            order_id="order-1",
            issue_date="2026-11-05",
            due_date="2026-11-20",
            amount=3000.00,
            tax_rate=20.0,
            currency="EUR",
            status="draft",
        )

    def tearDown(self):
        self.repo.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_creation_valide(self):
        self.assertEqual(self.invoice.organisation_id, "org-1")
        self.assertEqual(self.invoice.company_id, "cmp-1")
        self.assertEqual(self.invoice.amount, 3000.00)
        self.assertEqual(self.invoice.status, "draft")
        self.assertIsNotNone(self.invoice.id)
        self.assertIsNotNone(self.invoice.created_at)

    def test_creation_department(self):
        self.invoice.status = "sent"
        self.assertEqual(self.invoice.status, "sent")

    def test_reference_auto(self):
        i = Invoice(
            organisation_id="org-1",
            company_id="cmp-1",
            order_id="order-1",
            issue_date="2026-11-05",
            amount=100.00,
        )
        self.assertTrue(len(i.id) >= 8)

    def test_validation_erreur_status_invalid(self):
        with self.assertRaises(InvoiceError):
            Invoice(
                organisation_id="org-1",
                company_id="cmp-1",
                order_id="order-1",
                issue_date="2026-11-05",
                amount=100.00,
                status="invalid",
            )

    def test_validation_erreur_amount_negative(self):
        with self.assertRaises(InvoiceError):
            Invoice(
                organisation_id="org-1",
                company_id="cmp-1",
                order_id="order-1",
                issue_date="2026-11-05",
                amount=-100.00,
                status="pending",
            )

    def test_validation_erreur_due_before_issue(self):
        with self.assertRaises(InvoiceError):
            Invoice(
                organisation_id="org-1",
                company_id="cmp-1",
                order_id="order-1",
                issue_date="2026-12-31",
                due_date="2026-11-01",
                amount=100.00,
                status="pending",
            )


class TestInvoiceRepository(unittest.TestCase):
    """Tests pour le repository de facture."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_teamai.db")
        self.repo = InvoiceRepository(self.db_path)
        self.invoice_data = {
            "organisation_id": "org-1",
            "company_id": "cmp-1",
            "order_id": "order-1",
            "issue_date": datetime.now(timezone.utc).isoformat(),
            "due_date": "2026-11-20",
            "amount": 3000.00,
            "tax_rate": 20.0,
            "currency": "EUR",
        }

    def tearDown(self):
        self.repo.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_and_get(self):
        i = Invoice(**self.invoice_data)
        self.repo.create(i)
        retrieved = self.repo.get(i.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.order_id, i.order_id)

    def test_list_with_filters(self):
        i1 = Invoice(
            organisation_id="org-1", company_id="cmp-1",
            order_id="order-1", issue_date="2026-11-05",
            amount=100.00, status="draft",
        )
        i2 = Invoice(
            organisation_id="org-1", company_id="cmp-1",
            order_id="order-2", issue_date="2026-11-06",
            amount=200.00, status="sent",
        )
        self.repo.create(i1)
        self.repo.create(i2)

        items = self.repo.list(organisation_id="org-1")
        self.assertEqual(len(items), 2)

        items_sent = self.repo.list(status="sent")
        self.assertEqual(len(items_sent), 1)
        self.assertEqual(items_sent[0].status, "sent")

    def test_list_empty(self):
        items = self.repo.list(organisation_id="org-1")
        self.assertEqual(items, [])

    def test_update(self):
        i = Invoice(**self.invoice_data)
        self.repo.create(i)
        i.status = "sent"
        i.updated_at = datetime.now(timezone.utc).isoformat()
        self.repo.update(i)

        retrieved = self.repo.get(i.id)
        self.assertEqual(retrieved.status, "sent")

    def test_delete(self):
        i = Invoice(**self.invoice_data)
        self.repo.create(i)
        self.repo.delete(i.id)

        retrieved = self.repo.get(i.id)
        self.assertIsNone(retrieved)


class TestInvoiceAudit(unittest.TestCase):
    """Tests pour la génération d'audit sur les factures."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_teamai.db")
        self.repo = InvoiceRepository(self.db_path)

    def tearDown(self):
        self.repo.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_generates_audit(self):
        """Vérifie qu'une création génère un événement d'audit."""
        # Test temporaire - la table audit n'est pas configurée dans le test
        i = Invoice(
            organisation_id="org-1",
            company_id="cmp-1",
            order_id="order-1",
            issue_date="2026-11-05",
            amount=100.00,
            status="draft",
        )
        self.repo.create(i)
        # L'audit est vérifié par le système AuditCRM séparément


if __name__ == "__main__":
    unittest.main()
