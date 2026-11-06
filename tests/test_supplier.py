"""Tests unitaires de l'entité Supplier."""
import unittest
from engine.supplier import Supplier


class TestSupplierEntity(unittest.TestCase):
    def test_creation_valide(self):
        """Création valide doit passer sans erreur."""
        obj = Supplier(**self._defaults())
        self.assertTrue(obj.id.startswith("sup"))

    def test_organisation_id_manquant(self):
        with self.assertRaises(ValueError):
            Supplier(**{**self._defaults(), "organisation_id": ""})

    def test_name_manquant(self):
        with self.assertRaises(ValueError):
            Supplier(**{**self._defaults(), "name": ""})

    def test_to_dict(self):
        obj = Supplier(**self._defaults())
        d = obj.to_dict()
        self.assertEqual(d["id"], obj.id)

    def test_repr(self):
        obj = Supplier(**self._defaults())
        self.assertIn("sup-", repr(obj))

    @staticmethod
    def _defaults():
        return {
            "organisation_id": "org-1",
            "name": "Fournisseur Test",
            "email": "contact@fournisseur.fr",
            "phone": "+33123456789",
            "address": "12 rue du Commerce",        }


if __name__ == "__main__":
    unittest.main()
