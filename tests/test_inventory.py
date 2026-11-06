"""Tests unitaires de l'entité Inventory."""
import unittest
from engine.inventory import Inventory


class TestInventoryEntity(unittest.TestCase):
    def test_creation_valide(self):
        """Création valide doit passer sans erreur."""
        obj = Inventory(**self._defaults())
        self.assertTrue(obj.id.startswith("inv"))

    def test_organisation_id_manquant(self):
        with self.assertRaises(ValueError):
            Inventory(**{**self._defaults(), "organisation_id": ""})

    def test_warehouse_id_manquant(self):
        with self.assertRaises(ValueError):
            Inventory(**{**self._defaults(), "warehouse_id": ""})

    def test_product_id_manquant(self):
        with self.assertRaises(ValueError):
            Inventory(**{**self._defaults(), "product_id": ""})

    def test_counted_quantity_invalide(self):
        with self.assertRaises(ValueError):
            Inventory(**{**self._defaults(), "counted_quantity": -1})

    def test_expected_quantity_invalide(self):
        with self.assertRaises(ValueError):
            Inventory(**{**self._defaults(), "expected_quantity": -1})

    def test_to_dict(self):
        obj = Inventory(**self._defaults())
        d = obj.to_dict()
        self.assertEqual(d["id"], obj.id)

    def test_repr(self):
        obj = Inventory(**self._defaults())
        self.assertIn("inv-", repr(obj))

    @staticmethod
    def _defaults():
        return {
            "organisation_id": "org-1",
            "warehouse_id": "wh-1",
            "product_id": "prod-1",
            "counted_quantity": 5,
            "expected_quantity": 4,
            "note": "Inventaire annuel",        }


if __name__ == "__main__":
    unittest.main()
