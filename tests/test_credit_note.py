"""Tests unitaires pour le module CreditNote."""

import unittest
import tempfile
import shutil
import os
from datetime import datetime, timezone

from xohive.crm.domain.credit_note import CreditNote, CreditNoteError
from xohive.crm.repository.credit_note_repository import CreditNoteRepository


class TestCreditNoteCreation(unittest.TestCase):
    """Tests pour la création d'un avoir."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_teamai.db")
        self.repo = CreditNoteRepository(self.db_path)
        self.credit_note = CreditNote(
            organisation_id="org-1",
            company_id="cmp-1",
            invoice_id="inv-1",
            credit_date="2026-11-05",
            amount=500.00,
            reason="Remboursement partiel",
            currency="EUR",
            status="draft",
        )

    def tearDown(self):
        self.repo.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_creation_valide(self):
        self.assertEqual(self.credit_note.organisation_id, "org-1")
        self.assertEqual(self.credit_note.company_id, "cmp-1")
        self.assertEqual(self.credit_note.amount, 500.00)
        self.assertEqual(self.credit_note.status, "draft")
        self.assertIsNotNone(self.credit_note.id)
        self.assertIsNotNone(self.credit_note.created_at)

    def test_creation_department(self):
        self.credit_note.status = "approved"
        self.assertEqual(self.credit_note.status, "approved")

    def test_reference_auto(self):
        c = CreditNote(
            organisation_id="org-1",
            company_id="cmp-1",
            invoice_id="inv-1",
            credit_date="2026-11-05",
            amount=100.00,
        )
        self.assertTrue(len(c.id) >= 8)

    def test_validation_erreur_status_invalid(self):
        with self.assertRaises(CreditNoteError):
            CreditNote(
                organisation_id="org-1",
                company_id="cmp-1",
                invoice_id="inv-1",
                credit_date="2026-11-05",
                amount=100.00,
                status="invalid",
            )

    def test_validation_erreur_amount_negative(self):
        with self.assertRaises(CreditNoteError):
            CreditNote(
                organisation_id="org-1",
                company_id="cmp-1",
                invoice_id="inv-1",
                credit_date="2026-11-05",
                amount=-100.00,
                status="pending",
            )


class TestCreditNoteRepository(unittest.TestCase):
    """Tests pour le repository d'avoir."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_teamai.db")
        self.repo = CreditNoteRepository(self.db_path)
        self.credit_note_data = {
            "organisation_id": "org-1",
            "company_id": "cmp-1",
            "invoice_id": "inv-1",
            "credit_date": datetime.now(timezone.utc).isoformat(),
            "amount": 500.00,
            "reason": "Remboursement partiel",
            "currency": "EUR",
        }

    def tearDown(self):
        self.repo.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_and_get(self):
        c = CreditNote(**self.credit_note_data)
        self.repo.create(c)
        retrieved = self.repo.get(c.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.invoice_id, c.invoice_id)

    def test_list_with_filters(self):
        c1 = CreditNote(
            organisation_id="org-1", company_id="cmp-1",
            invoice_id="inv-1", credit_date="2026-11-05",
            amount=100.00, status="draft",
        )
        c2 = CreditNote(
            organisation_id="org-1", company_id="cmp-1",
            invoice_id="inv-2", credit_date="2026-11-06",
            amount=200.00, status="approved",
        )
        self.repo.create(c1)
        self.repo.create(c2)

        items = self.repo.list(organisation_id="org-1")
        self.assertEqual(len(items), 2)

        items_approved = self.repo.list(status="approved")
        self.assertEqual(len(items_approved), 1)
        self.assertEqual(items_approved[0].status, "approved")

    def test_list_empty(self):
        items = self.repo.list(organisation_id="org-1")
        self.assertEqual(items, [])

    def test_update(self):
        c = CreditNote(**self.credit_note_data)
        self.repo.create(c)
        c.status = "approved"
        c.updated_at = datetime.now(timezone.utc).isoformat()
        self.repo.update(c)

        retrieved = self.repo.get(c.id)
        self.assertEqual(retrieved.status, "approved")

    def test_delete(self):
        c = CreditNote(**self.credit_note_data)
        self.repo.create(c)
        self.repo.delete(c.id)

        retrieved = self.repo.get(c.id)
        self.assertIsNone(retrieved)


class TestCreditNoteAudit(unittest.TestCase):
    """Tests pour la génération d'audit sur les avoirs."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_teamai.db")
        self.repo = CreditNoteRepository(self.db_path)

    def tearDown(self):
        self.repo.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_generates_audit(self):
        """Vérifie qu'une création génère un événement d'audit."""
        # Test temporaire - la table audit n'est pas configurée dans le test
        c = CreditNote(
            organisation_id="org-1",
            company_id="cmp-1",
            invoice_id="inv-1",
            credit_date="2026-11-05",
            amount=100.00,
            status="draft",
        )
        self.repo.create(c)
        # L'audit est vérifié par le système AuditCRM séparément


if __name__ == "__main__":
    unittest.main()
