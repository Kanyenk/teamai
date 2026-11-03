"""Tests unitaires pour l'entité Organization et son Repository."""

import unittest
import tempfile
import os
from pathlib import Path

from xohive.domain.organization import Organization
from xohive.domain.organization_repository import OrganizationRepository


class TestOrganizationEntity(unittest.TestCase):
    """Tests de l'entité Organization."""

    def test_creation_valide(self):
        org = Organization(name="Acme SARL")
        self.assertEqual(org.name, "Acme SARL")
        self.assertEqual(org.currency, "EUR")
        self.assertEqual(org.is_active, True)
        self.assertIsNotNone(org.id)
        self.assertGreater(len(org.id), 0)

    def test_creation_personnalisee(self):
        org = Organization(
            name="Acme SARL",
            tz="Europe/Paris",
            currency="EUR",
            fiscal_code="123456789",
            website="https://acme.com",
            phone="+3312345678",
            address="10 Rue de Rivoli",
            contact_email="contact@acme.com",
            created_by="admin",
            is_active=True,
            callback_webhook="https://acme.com/webhooks",
        )
        self.assertEqual(org.name, "Acme SARL")
        self.assertEqual(org.timezone, "Europe/Paris")
        self.assertEqual(org.currency, "EUR")
        self.assertEqual(org.fiscal_code, "123456789")
        self.assertEqual(org.is_active, True)

    def test_currency_invalide(self):
        with self.assertRaises(ValueError):
            Organization(name="Test", currency="XXX")

    def test_name_vide(self):
        with self.assertRaises(ValueError):
            Organization(name="")

    def test_to_dict(self):
        org = Organization(
            name="Acme SARL",
            tz="Europe/Paris",
            currency="EUR",
            fiscal_code="123456789",
            website="https://acme.com",
            phone="+3312345678",
            address="10 Rue de Rivoli",
            contact_email="contact@acme.com",
            created_by="admin",
            is_active=True,
            callback_webhook="https://acme.com/webhooks",
        )
        d = org.to_dict()
        self.assertEqual(d["name"], "Acme SARL")
        self.assertEqual(d["currency"], "EUR")
        self.assertTrue(d["is_active"])
        self.assertEqual(d["callback_webhook"], "https://acme.com/webhooks")

    def test_repr(self):
        org = Organization(name="Acme SARL")
        self.assertIn("Acme SARL", repr(org))
        self.assertIn("org-", repr(org))


class TestOrganizationRepository(unittest.TestCase):
    """Tests du Repository Organization."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.repo = OrganizationRepository(self.db_path)

    def tearDown(self):
        self.repo.close()
        for f in Path(self.temp_dir).glob("*.db*"):
            f.unlink()
        os.rmdir(self.temp_dir)

    def test_create(self):
        org = Organization(name="Acme SARL")
        saved = self.repo.create(org)
        self.assertIsNotNone(saved)
        self.assertEqual(saved.id, org.id)
        self.assertEqual(saved.name, "Acme SARL")

    def test_get(self):
        org = Organization(name="Acme SARL")
        self.repo.create(org)
        retrieved = self.repo.get(org.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Acme SARL")

    def test_get_non_existant(self):
        retrieved = self.repo.get("org-inconnu")
        self.assertIsNone(retrieved)

    def test_list(self):
        org1 = Organization(name="Acme SARL")
        org2 = Organization(name="Beta SARL")
        self.repo.create(org1)
        self.repo.create(org2)
        orgs = self.repo.list()
        self.assertEqual(len(orgs), 2)
        self.assertEqual(orgs[0].name, "Acme SARL")
        self.assertEqual(orgs[1].name, "Beta SARL")

    def test_update(self):
        org = Organization(name="Acme SARL")
        self.repo.create(org)
        org.name = "Acme SAS"
        org.is_active = False
        updated = self.repo.update(org)
        self.assertEqual(updated.name, "Acme SAS")
        self.assertFalse(updated.is_active)

    def test_delete(self):
        org = Organization(name="Acme SARL")
        self.repo.create(org)
        deleted = self.repo.delete(org.id)
        self.assertTrue(deleted)
        self.assertIsNone(self.repo.get(org.id))

    def test_delete_non_existant(self):
        deleted = self.repo.delete("org-inconnu")
        self.assertFalse(deleted)

    def test_list_plusieurs(self):
        for i in range(5):
            org = Organization(name=f"Organisation {i}")
            self.repo.create(org)
        orgs = self.repo.list()
        self.assertEqual(len(orgs), 5)

    def test_context_manager(self):
        with OrganizationRepository(self.db_path) as repo:
            org = Organization(name="Acme SARL")
            self.repo.create(org)
            retrieved = repo.get(org.id)
            self.assertIsNotNone(retrieved)


if __name__ == "__main__":
    unittest.main()
