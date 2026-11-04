"""Tests unitaires pour Contact et ContactRepository."""

import unittest
import tempfile
import os
import shutil
from pathlib import Path

from xohive.crm.domain.contact import Contact, ContactError
from xohive.crm.repository.contact_repository import ContactRepository


class TestContactEntity(unittest.TestCase):
    """Tests de l'entité Contact."""

    def test_creation_valide(self):
        contact = Contact(
            organisation_id="org-123",
            company_id="crm-001",
            first_name="Jean",
            last_name="Dupont",
            email="jean.dupont@acme.com",
        )
        self.assertEqual(contact.first_name, "Jean")
        self.assertEqual(contact.last_name, "Dupont")
        self.assertEqual(contact.email, "jean.dupont@acme.com")
        self.assertTrue(contact.is_active)
        self.assertIsNotNone(contact.id)

    def test_creation_personnalisee(self):
        contact = Contact(
            organisation_id="org-123",
            company_id="crm-001",
            first_name="Jean",
            last_name="Dupont",
            email="jean.dupont@acme.com",
            phone="+33155555555",
            job_title="Directeur",
            is_active=True,
            created_by="admin",
        )
        self.assertEqual(contact.phone, "+33155555555")
        self.assertEqual(contact.job_title, "Directeur")

    def test_creation_nom_vide(self):
        with self.assertRaises(ContactError):
            Contact(
                organisation_id="org-123",
                company_id="crm-001",
                first_name="",
                last_name="Dupont",
                email="jean@acme.com",
            )

    def test_creation_prenom_vide(self):
        with self.assertRaises(ContactError):
            Contact(
                organisation_id="org-123",
                company_id="crm-001",
                first_name="Jean",
                last_name="",
                email="jean@acme.com",
            )

    def test_creation_email_invalide(self):
        with self.assertRaises(ContactError):
            Contact(
                organisation_id="org-123",
                company_id="crm-001",
                first_name="Jean",
                last_name="Dupont",
                email="invalide",
            )

    def test_creation_company_id_manquant(self):
        with self.assertRaises(ContactError):
            Contact(
                organisation_id="org-123",
                company_id="",
                first_name="Jean",
                last_name="Dupont",
                email="jean@acme.com",
            )

    def test_email_trie(self):
        contact = Contact(
            organisation_id="org-123",
            company_id="crm-001",
            first_name="Jean",
            last_name="Dupont",
            email="Jean@ACME.com",
        )
        self.assertEqual(contact.email, "jean@acme.com")

    def test_deactivate(self):
        contact = Contact(
            organisation_id="org-123",
            company_id="crm-001",
            first_name="Jean",
            last_name="Dupont",
            email="jean@acme.com",
        )
        self.assertTrue(contact.is_active)
        contact.deactivate()
        self.assertFalse(contact.is_active)

    def test_to_dict(self):
        contact = Contact(
            organisation_id="org-123",
            company_id="crm-001",
            first_name="Jean",
            last_name="Dupont",
            email="jean@acme.com",
            is_active=False,
        )
        d = contact.to_dict()
        self.assertEqual(d["first_name"], "Jean")
        self.assertFalse(d["is_active"])

    def test_repr(self):
        contact = Contact(
            organisation_id="org-123",
            company_id="crm-001",
            first_name="Jean",
            last_name="Dupont",
            email="jean@acme.com",
        )
        self.assertIn("Contact", repr(contact))


class TestContactRepository(unittest.TestCase):
    """Tests du repository Contact."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.repo = ContactRepository(self.db_path)

    def tearDown(self):
        self.repo.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create(self):
        company = Contact(
            organisation_id="org-123",
            company_id="crm-001",
            first_name="Jean",
            last_name="Dupont",
            email="jean@acme.com",
        )
        saved = self.repo.create(company)
        self.assertIsNotNone(saved)
        self.assertEqual(saved.first_name, "Jean")

    def test_get(self):
        contact = Contact(
            organisation_id="org-123",
            company_id="crm-001",
            first_name="Jean",
            last_name="Dupont",
            email="jean@acme.com",
        )
        self.repo.create(contact)
        retrieved = self.repo.get(contact.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.email, "jean@acme.com")

    def test_get_non_existant(self):
        retrieved = self.repo.get("crm-inconnu")
        self.assertIsNone(retrieved)

    def test_list(self):
        for i in range(3):
            contact = Contact(
                organisation_id="org-123",
                company_id="crm-001",
                first_name=f"Jean{i}",
                last_name=f"Dupont{i}",
                email=f"jean{i}@acme.com",
            )
            self.repo.create(contact)
        contacts = self.repo.list()
        self.assertEqual(len(contacts), 3)

    def test_list_empty(self):
        contacts = self.repo.list()
        self.assertEqual(len(contacts), 0)

    def test_update(self):
        contact = Contact(
            organisation_id="org-123",
            company_id="crm-001",
            first_name="Jean",
            last_name="Dupont",
            email="jean@acme.com",
        )
        self.repo.create(contact)
        contact.first_name = "Jeanpierre"
        contact.updated_at = contact._now_iso()
        updated = self.repo.update(contact)
        self.assertEqual(updated.first_name, "Jeanpierre")

    def test_delete(self):
        contact = Contact(
            organisation_id="org-123",
            company_id="crm-001",
            first_name="Jean",
            last_name="Dupont",
            email="jean@acme.com",
        )
        self.repo.create(contact)
        result = self.repo.delete(contact.id)
        self.assertTrue(result)
        retrieved = self.repo.get(contact.id)
        self.assertIsNone(retrieved)

    def test_delete_non_existant(self):
        result = self.repo.delete("crm-inconnu")
        self.assertFalse(result)

    def test_unique_email(self):
        contact1 = Contact(
            organisation_id="org-123",
            company_id="crm-001",
            first_name="Jean",
            last_name="Dupont",
            email="jean@acme.com",
        )
        self.repo.create(contact1)
        contact2 = Contact(
            organisation_id="org-123",
            company_id="crm-002",
            first_name="Pierre",
            last_name="Dupont",
            email="jean@acme.com",
        )
        with self.assertRaises(ContactError):
            self.repo.create(contact2)

    def test_context_manager(self):
        with ContactRepository(self.db_path) as repo:
            contact = Contact(
                organisation_id="org-123",
                company_id="crm-001",
                first_name="Jean",
                last_name="Dupont",
                email="jean@acme.com",
            )
            repo.create(contact)
            retrieved = repo.get(contact.id)
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.first_name, "Jean")


if __name__ == "__main__":
    unittest.main()
