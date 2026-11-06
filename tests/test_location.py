"""Tests unitaires de l'entité Location."""
import unittest
from engine.location import Location


class TestLocationEntity(unittest.TestCase):
    def test_creation_valide(self):
        """Création valide doit passer sans erreur."""
        obj = Location(**self._defaults())
        self.assertTrue(obj.id.startswith("loc"))

    def test_organisation_id_manquant(self):
        with self.assertRaises(ValueError):
            Location(**{**self._defaults(), "organisation_id": ""})

    def test_warehouse_id_manquant(self):
        with self.assertRaises(ValueError):
            Location(**{**self._defaults(), "warehouse_id": ""})

    def test_code_manquant(self):
        with self.assertRaises(ValueError):
            Location(**{**self._defaults(), "code": ""})

    def test_to_dict(self):
        obj = Location(**self._defaults())
        d = obj.to_dict()
        self.assertEqual(d["id"], obj.id)

    def test_repr(self):
        obj = Location(**self._defaults())
        self.assertIn("loc-", repr(obj))

    @staticmethod
    def _defaults():
        return {
            "organisation_id": 'org-1',
            "warehouse_id": 'wh-1',
            "code": 'A-01-03',
            "name": 'Allée A, rayon 01, niveau 03',
            "zone": 'picking',
            "capacity": 100,        }


if __name__ == "__main__":
    unittest.main()
