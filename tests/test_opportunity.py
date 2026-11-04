"""Tests unitaires pour Opportunity et OpportunityRepository."""

import unittest
import tempfile
import shutil
from pathlib import Path

from xohive.crm.domain.opportunity import Opportunity, OpportunityError
from xohive.crm.repository.opportunity_repository import OpportunityRepository


class TestOpportunityEntity(unittest.TestCase):
    """Tests de l'entité Opportunity."""

    def test_creation_valide(self):
        opp = Opportunity(
            organisation_id="org-123",
            company_id="crm-001",
            title="Achat logiciel",
            amount=50000.0,
        )
        self.assertEqual(opp.title, "Achat logiciel")
        self.assertEqual(opp.amount, 50000.0)
        self.assertEqual(opp.stage, Opportunity.STAGE_PROSPECTING)
        self.assertIsNotNone(opp.id)

    def test_creation_personnalisee(self):
        opp = Opportunity(
            organisation_id="org-123",
            company_id="crm-001",
            contact_id="crm-002",
            title="Achat logiciel",
            amount=50000.0,
            stage=Opportunity.STAGE_QUALIFYING,
            probability=75.0,
            close_date="2026-12-31",
            is_active=True,
            created_by="admin",
        )
        self.assertEqual(opp.stage, Opportunity.STAGE_QUALIFYING)
        self.assertEqual(opp.probability, 75.0)

    def test_creation_amount_negatif(self):
        with self.assertRaises(OpportunityError):
            Opportunity(
                organisation_id="org-123",
                company_id="crm-001",
                title="Test",
                amount=-100.0,
            )

    def test_creation_amount_nul(self):
        with self.assertRaises(OpportunityError):
            Opportunity(
                organisation_id="org-123",
                company_id="crm-001",
                title="Test",
                amount=0.0,
            )

    def test_creation_stage_invalide(self):
        with self.assertRaises(OpportunityError):
            Opportunity(
                organisation_id="org-123",
                company_id="crm-001",
                title="Test",
                amount=100.0,
                stage="invalide",
            )

    def test_probability_invalide(self):
        with self.assertRaises(OpportunityError):
            Opportunity(
                organisation_id="org-123",
                company_id="crm-001",
                title="Test",
                amount=100.0,
                probability=150.0,
            )

    def test_title_vide(self):
        with self.assertRaises(OpportunityError):
            Opportunity(
                organisation_id="org-123",
                company_id="crm-001",
                title="",
                amount=100.0,
            )

    def test_advance_stage(self):
        opp = Opportunity(
            organisation_id="org-123",
            company_id="crm-001",
            title="Test",
            amount=100.0,
        )
        self.assertEqual(opp.stage, Opportunity.STAGE_PROSPECTING)
        opp.advance()
        self.assertEqual(opp.stage, Opportunity.STAGE_QUALIFYING)
        opp.advance()
        self.assertEqual(opp.stage, Opportunity.STAGE_PROPOSITION)

    def test_advance_to_closed(self):
        stages = [
            Opportunity.STAGE_PROSPECTING,
            Opportunity.STAGE_QUALIFYING,
            Opportunity.STAGE_PROPOSITION,
            Opportunity.STAGE_NEGOTIATION,
            Opportunity.STAGE_CLOSED,
        ]
        opp = Opportunity(
            organisation_id="org-123",
            company_id="crm-001",
            title="Test",
            amount=100.0,
            stage=stages[0],
        )
        for s in stages[1:]:
            opp.advance()
            self.assertEqual(opp.stage, s)
        self.assertTrue(opp.is_closed())

    def test_to_dict(self):
        opp = Opportunity(
            organisation_id="org-123",
            company_id="crm-001",
            title="Achat",
            amount=50000.0,
            stage=Opportunity.STAGE_CLOSED,
        )
        d = opp.to_dict()
        self.assertEqual(d["title"], "Achat")
        self.assertEqual(d["amount"], 50000.0)

    def test_repr(self):
        opp = Opportunity(
            organisation_id="org-123",
            company_id="crm-001",
            title="Test",
            amount=100.0,
        )
        self.assertIn("Opportunity", repr(opp))


class TestOpportunityRepository(unittest.TestCase):
    """Tests du repository Opportunity."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.repo = OpportunityRepository(self.db_path)

    def tearDown(self):
        self.repo.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create(self):
        opp = Opportunity(
            organisation_id="org-123",
            company_id="crm-001",
            title="Achat logiciel",
            amount=50000.0,
        )
        saved = self.repo.create(opp)
        self.assertIsNotNone(saved)
        self.assertEqual(saved.title, "Achat logiciel")

    def test_get(self):
        opp = Opportunity(
            organisation_id="org-123",
            company_id="crm-001",
            title="Achat logiciel",
            amount=50000.0,
        )
        self.repo.create(opp)
        retrieved = self.repo.get(opp.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.amount, 50000.0)

    def test_get_non_existant(self):
        with self.assertRaises(OpportunityError):
            self.repo.get("crm-inconnu")

    def test_update(self):
        opp = Opportunity(
            organisation_id="org-123",
            company_id="crm-001",
            title="Achat logiciel",
            amount=50000.0,
        )
        self.repo.create(opp)
        opp.title = "Achat serveur"
        opp.amount = 75000.0
        opp.updated_at = opp._now_iso()
        updated = self.repo.update(opp)
        self.assertEqual(updated.title, "Achat serveur")
        self.assertEqual(updated.amount, 75000.0)

    def test_delete(self):
        opp = Opportunity(
            organisation_id="org-123",
            company_id="crm-001",
            title="Achat",
            amount=100.0,
        )
        self.repo.create(opp)
        result = self.repo.delete(opp.id)
        self.assertTrue(result)
        with self.assertRaises(OpportunityError):
            self.repo.get(opp.id)

    def test_list_ordered_by_amount(self):
        self.repo.create(
            Opportunity(
                organisation_id="org-123",
                company_id="crm-001",
                title="Petit",
                amount=100.0,
            )
        )
        self.repo.create(
            Opportunity(
                organisation_id="org-123",
                company_id="crm-001",
                title="Grand",
                amount=100000.0,
            )
        )
        results = self.repo.list()
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].title, "Grand")

    def test_list_empty(self):
        results = self.repo.list()
        self.assertEqual(len(results), 0)


if __name__ == "__main__":
    unittest.main()
