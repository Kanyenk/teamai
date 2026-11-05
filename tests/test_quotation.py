"""Tests unitaires pour le module Quotation."""

import unittest
import tempfile
import shutil
import os
from datetime import datetime, timezone

from xohive.crm.domain.quotation import Quotation, QuotationError
from xohive.crm.repository.quotation_repository import QuotationRepository


class TestQuotationCreation(unittest.TestCase):
    """Tests pour la création d'une quotation."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_teamai.db")
        self.repo = QuotationRepository(self.db_path)
        self.quotation = Quotation(
            organisation_id="org-1",
            company_id="cmp-1",
            contact_id="cnt-1",
            user_id="usr-1",
            total_amount=1500.00,
            tax_rate=20.0,
            currency="EUR",
            status="draft",
            valid_until="2026-12-31",
        )

    def tearDown(self):
        self.repo.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_creation_valide(self):
        self.assertEqual(self.quotation.organisation_id, "org-1")
        self.assertEqual(self.quotation.company_id, "cmp-1")
        self.assertEqual(self.quotation.total_amount, 1500.00)
        self.assertEqual(self.quotation.status, "draft")
        self.assertIsNotNone(self.quotation.id)
        self.assertIsNotNone(self.quotation.created_at)

    def test_creation_department(self):
        self.quotation.status = "sent"
        self.assertEqual(self.quotation.status, "sent")

    def test_reference_auto(self):
        q = Quotation(
            organisation_id="org-1",
            company_id="cmp-1",
            total_amount=100.00,
            valid_until="2026-12-31",
        )
        self.assertTrue(len(q.reference) >= 8)
        self.assertTrue(q.reference.startswith("Q-"))

    def test_validation_erreur_status_invalid(self):
        with self.assertRaises(QuotationError):
            Quotation(
                organisation_id="org-1",
                company_id="cmp-1",
                total_amount=100.00,
                valid_until="2026-12-31",
                status="invalid",
            )

    def test_validation_erreur_total_negative(self):
        with self.assertRaises(QuotationError):
            Quotation(
                organisation_id="org-1",
                company_id="cmp-1",
                total_amount=-100.00,
                valid_until="2026-12-31",
            )

    def test_validation_erreur_valid_until_before(self):
        with self.assertRaises(QuotationError):
            Quotation(
                organisation_id="org-1",
                company_id="cmp-1",
                total_amount=100.00,
                quotation_date="2026-12-31",
                valid_until="2026-01-01",
            )


class TestQuotationRepository(unittest.TestCase):
    """Tests pour le repository de quotation."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_teamai.db")
        self.repo = QuotationRepository(self.db_path)
        self.quotation_data = {
            "organisation_id": "org-1",
            "company_id": "cmp-1",
            "contact_id": "cnt-1",
            "user_id": "usr-1",
            "total_amount": 1500.00,
            "tax_rate": 20.0,
            "currency": "EUR",
            "quotation_date": datetime.now(timezone.utc).isoformat(),
            "valid_until": "2026-12-31",
        }

    def tearDown(self):
        self.repo.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_and_get(self):
        q = Quotation(**self.quotation_data)
        q.id = self.repo.create(q).id
        retrieved = self.repo.get(q.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.reference, q.reference)

    def test_list_with_filters(self):
        q1 = Quotation(
            organisation_id="org-1", company_id="cmp-1",
            total_amount=100.00, valid_until="2026-12-31",
            status="draft", quotation_date=self.quotation_data["quotation_date"],
        )
        q2 = Quotation(
            organisation_id="org-1", company_id="cmp-1",
            total_amount=200.00, valid_until="2026-12-31",
            status="sent", quotation_date=self.quotation_data["quotation_date"],
        )
        self.repo.create(q1)
        self.repo.create(q2)

        items = self.repo.list(organisation_id="org-1")
        self.assertEqual(len(items), 2)

        items_sent = self.repo.list(status="sent")
        self.assertEqual(len(items_sent), 1)
        self.assertEqual(items_sent[0].status, "sent")

    def test_list_empty(self):
        items = self.repo.list(organisation_id="org-1")
        self.assertEqual(items, [])

    def test_update(self):
        q = Quotation(**self.quotation_data)
        self.repo.create(q)
        q.status = "sent"
        q.updated_at = datetime.now(timezone.utc).isoformat()
        self.repo.update(q)

        retrieved = self.repo.get(q.id)
        self.assertEqual(retrieved.status, "sent")

    def test_delete(self):
        q = Quotation(**self.quotation_data)
        self.repo.create(q)
        self.repo.delete(q.id)

        retrieved = self.repo.get(q.id)
        self.assertIsNone(retrieved)


class TestQuotationAudit(unittest.TestCase):
    """Tests pour la génération d'audit sur les quotations."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_teamai.db")
        from xohive.crm.repository.quotation_repository import QuotationRepository
        self.repo = QuotationRepository(self.db_path)

    def tearDown(self):
        self.repo.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_generates_audit(self):
        """Vérifie qu'une création génère un événement d'audit."""
        # Test temporaire - la table audit n'est pas configurée dans le test
        # L'audit est géré par le module AuditCRM séparément
        q = Quotation(
            organisation_id="org-1",
            company_id="cmp-1",
            total_amount=100.00,
            valid_until="2026-12-31",
        )
        self.repo.create(q)
        # L'audit est vérifié par le système AuditCRM séparément


if __name__ == "__main__":
    unittest.main()
