"""Tests unitaires pour Company et CompanyRepository."""

import unittest
import tempfile
import os
import shutil
from pathlib import Path

from xohive.crm.domain.company import Company, CompanyError
from xohive.crm.repository.company_repository import CompanyRepository


class TestCompanyEntity(unittest.TestCase):
    """Tests de l'entité Company."""

    def test_creation_valide(self):
        company = Company(
            organisation_id="org-123",
            name="Acme SARL",
            siret="12345678901234",
        )
        self.assertEqual(company.name, "Acme SARL")
        self.assertEqual(company.siret, "12345678901234")
        self.assertTrue(company.is_active)
        self.assertIsNotNone(company.id)
        self.assertTrue(company.is_active)
        self.assertIsNotNone(company.created_at)

    def test_creation_personnalisee(self):
        company = Company(
            organisation_id="org-123",
            name="Acme SARL",
            siret="12345678901234",
            address="10 Rue de Rivoli",
            city="Paris",
            zip_code="75001",
            country="FR",
            website="https://acme.com",
            phone="+33155555555",
            email="contact@acme.com",
            contact_person="Jean Dupont",
            is_active=True,
            created_by="admin",
        )
        self.assertEqual(company.address, "10 Rue de Rivoli")
        self.assertEqual(company.city, "Paris")
        self.assertEqual(company.zip_code, "75001")
        self.assertEqual(company.country, "FR")
        self.assertEqual(company.contact_person, "Jean Dupont")
        self.assertTrue(company.is_active)

    def test_creation_siret_invalide(self):
        with self.assertRaises(CompanyError):
            Company(
                organisation_id="org-123",
                name="Acme SARL",
                siret="123456789",  # 9 chiffres
            )

    def test_creation_siret_trop_long(self):
        with self.assertRaises(CompanyError):
            Company(
                organisation_id="org-123",
                name="Acme SARL",
                siret="123456789012345",  # 15 chiffres
            )

    def test_creation_siret_non_digit(self):
        with self.assertRaises(CompanyError):
            Company(
                organisation_id="org-123",
                name="Acme SARL",
                siret="ABCDEFGHIJKLMN",
            )

    def test_creation_email_invalide(self):
        with self.assertRaises(CompanyError):
            Company(
                organisation_id="org-123",
                name="Acme SARL",
                siret="12345678901234",
                email="invalide",
            )

    def test_creation_pays_invalide(self):
        with self.assertRaises(CompanyError):
            Company(
                organisation_id="org-123",
                name="Acme SARL",
                siret="12345678901234",
                country="XX",
            )

    def test_creation_nom_vide(self):
        with self.assertRaises(CompanyError):
            Company(
                organisation_id="org-123",
                name="",
                siret="12345678901234",
            )

    def test_deactivate(self):
        company = Company(
            organisation_id="org-123",
            name="Acme SARL",
            siret="12345678901234",
        )
        self.assertTrue(company.is_active)
        company.deactivate()
        self.assertFalse(company.is_active)
        self.assertIsNotNone(company.updated_at)

    def test_to_dict(self):
        company = Company(
            organisation_id="org-123",
            name="Acme SARL",
            siret="12345678901234",
            is_active=False,
        )
        d = company.to_dict()
        self.assertEqual(d["name"], "Acme SARL")
        self.assertEqual(d["siret"], "12345678901234")
        self.assertFalse(d["is_active"])

    def test_repr(self):
        company = Company(
            organisation_id="org-123",
            name="Acme SARL",
            siret="12345678901234",
        )
        self.assertIn("Company", repr(company))
        self.assertIn(company.id, repr(company))


class TestCompanyRepository(unittest.TestCase):
    """Tests du repository Company."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.repo = CompanyRepository(self.db_path)

    def tearDown(self):
        self.repo.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create(self):
        company = Company(
            organisation_id="org-123",
            name="Acme SARL",
            siret="12345678901234",
        )
        saved = self.repo.create(company)
        self.assertIsNotNone(saved)
        self.assertEqual(saved.name, "Acme SARL")

    def test_get(self):
        company = Company(
            organisation_id="org-123",
            name="Acme SARL",
            siret="12345678901234",
        )
        self.repo.create(company)
        retrieved = self.repo.get(company.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Acme SARL")

    def test_get_non_existant(self):
        retrieved = self.repo.get("crm-inconnu")
        self.assertIsNone(retrieved)

    def test_list(self):
        for i in range(3):
            company = Company(
                organisation_id="org-123",
                name=f"Acme {i}",
                siret="12345678901234",
            )
            self.repo.create(company)
        companies = self.repo.list()
        self.assertEqual(len(companies), 3)

    def test_list_empty(self):
        companies = self.repo.list()
        self.assertEqual(len(companies), 0)

    def test_update(self):
        company = Company(
            organisation_id="org-123",
            name="Acme SARL",
            siret="12345678901234",
        )
        self.repo.create(company)
        company.name = "Acme SAS"
        company.updated_at = company._now_iso()
        updated = self.repo.update(company)
        self.assertEqual(updated.name, "Acme SAS")

    def test_delete(self):
        company = Company(
            organisation_id="org-123",
            name="Acme SARL",
            siret="12345678901234",
        )
        self.repo.create(company)
        result = self.repo.delete(company.id)
        self.assertTrue(result)
        retrieved = self.repo.get(company.id)
        self.assertIsNone(retrieved)

    def test_delete_non_existant(self):
        result = self.repo.delete("crm-inconnu")
        self.assertFalse(result)

    def test_context_manager(self):
        with CompanyRepository(self.db_path) as repo:
            company = Company(
                organisation_id="org-123",
                name="Acme SARL",
                siret="12345678901234",
            )
            repo.create(company)
            retrieved = repo.get(company.id)
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.name, "Acme SARL")


if __name__ == "__main__":
    unittest.main()
