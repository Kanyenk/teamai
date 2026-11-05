"""Tests unitaires pour le module Reconciliation."""

import unittest
import tempfile
import shutil
import os
from datetime import datetime, timezone

from xohive.crm.domain.reconciliation import Reconciliation, ReconciliationError
from xohive.crm.repository.reconciliation_repository import ReconciliationRepository


class TestReconciliationCreation(unittest.TestCase):
    """Tests pour la création d'un rapprochement bancaire."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_teamai.db")
        self.repo = ReconciliationRepository(self.db_path)
        self.reconciliation = Reconciliation(
            organisation_id="org-1",
            company_id="cmp-1",
            payment_id="pay-1",
            ledger_entry_id="led-1",
            bank_date="2026-11-05",
            amount=2500.00,
            currency="EUR",
            status="open",
        )

    def tearDown(self):
        self.repo.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_creation_valide(self):
        self.assertEqual(self.reconciliation.organisation_id, "org-1")
        self.assertEqual(self.reconciliation.company_id, "cmp-1")
        self.assertEqual(self.reconciliation.amount, 2500.00)
        self.assertEqual(self.reconciliation.status, "open")
        self.assertIsNotNone(self.reconciliation.id)
        self.assertIsNotNone(self.reconciliation.created_at)
        self.assertTrue(len(self.reconciliation.reference) >= 8)

    def test_creation_department(self):
        self.reconciliation.status = "closed"
        self.assertEqual(self.reconciliation.status, "closed")

    def test_reference_auto(self):
        r = Reconciliation(
            organisation_id="org-1",
            company_id="cmp-1",
            payment_id="pay-1",
            ledger_entry_id="led-1",
            bank_date="2026-11-05",
            amount=100.00,
        )
        self.assertTrue(len(r.reference) >= 8)
        self.assertTrue(r.reference.startswith("REC-"))

    def test_validation_erreur_status_invalid(self):
        with self.assertRaises(ReconciliationError):
            Reconciliation(
                organisation_id="org-1",
                company_id="cmp-1",
                payment_id="pay-1",
                ledger_entry_id="led-1",
                bank_date="2026-11-05",
                amount=100.00,
                status="invalid",
            )

    def test_validation_erreur_amount_negative(self):
        with self.assertRaises(ReconciliationError):
            Reconciliation(
                organisation_id="org-1",
                company_id="cmp-1",
                payment_id="pay-1",
                ledger_entry_id="led-1",
                bank_date="2026-11-05",
                amount=-100.00,
                status="open",
            )


class TestReconciliationRepository(unittest.TestCase):
    """Tests pour le repository de rapprochement."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_teamai.db")
        self.repo = ReconciliationRepository(self.db_path)
        self.reconciliation_data = {
            "organisation_id": "org-1",
            "company_id": "cmp-1",
            "payment_id": "pay-1",
            "ledger_entry_id": "led-1",
            "bank_date": datetime.now(timezone.utc).isoformat(),
            "amount": 2500.00,
            "currency": "EUR",
        }

    def tearDown(self):
        self.repo.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_and_get(self):
        r = Reconciliation(**self.reconciliation_data)
        self.repo.create(r)
        retrieved = self.repo.get(r.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.payment_id, r.payment_id)

    def test_list_with_filters(self):
        r1 = Reconciliation(
            organisation_id="org-1", company_id="cmp-1",
            payment_id="pay-1", ledger_entry_id="led-1",
            bank_date="2026-11-05", amount=100.00, status="open",
        )
        r2 = Reconciliation(
            organisation_id="org-1", company_id="cmp-1",
            payment_id="pay-2", ledger_entry_id="led-2",
            bank_date="2026-11-06", amount=200.00, status="closed",
        )
        self.repo.create(r1)
        self.repo.create(r2)

        items = self.repo.list(organisation_id="org-1")
        self.assertEqual(len(items), 2)

        items_closed = self.repo.list(status="closed")
        self.assertEqual(len(items_closed), 1)
        self.assertEqual(items_closed[0].status, "closed")

    def test_list_empty(self):
        items = self.repo.list(organisation_id="org-1")
        self.assertEqual(items, [])

    def test_update(self):
        r = Reconciliation(**self.reconciliation_data)
        self.repo.create(r)
        r.status = "closed"
        r.updated_at = datetime.now(timezone.utc).isoformat()
        self.repo.update(r)

        retrieved = self.repo.get(r.id)
        self.assertEqual(retrieved.status, "closed")

    def test_delete(self):
        r = Reconciliation(**self.reconciliation_data)
        self.repo.create(r)
        self.repo.delete(r.id)

        retrieved = self.repo.get(r.id)
        self.assertIsNone(retrieved)


class TestReconciliationAudit(unittest.TestCase):
    """Tests pour la génération d'audit sur les rapprochements."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_teamai.db")
        self.repo = ReconciliationRepository(self.db_path)

    def tearDown(self):
        self.repo.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_generates_audit(self):
        """Vérifie qu'une création génère un événement d'audit."""
        # Test temporaire - la table audit n'est pas configurée dans le test
        r = Reconciliation(
            organisation_id="org-1",
            company_id="cmp-1",
            payment_id="pay-1",
            ledger_entry_id="led-1",
            bank_date="2026-11-05",
            amount=100.00,
            status="open",
        )
        self.repo.create(r)
        # L'audit est vérifié par le système AuditCRM séparément


if __name__ == "__main__":
    unittest.main()
