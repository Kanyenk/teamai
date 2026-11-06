"""Tests unitaires de l'entité StockTransfer."""
import unittest
from engine.stock_transfer import StockTransfer


class TestStockTransferEntity(unittest.TestCase):
    def test_creation_valide(self):
        """Création valide doit passer sans erreur."""
        obj = StockTransfer(**self._defaults())
        self.assertTrue(obj.id.startswith("trf"))

    def test_organisation_id_manquant(self):
        with self.assertRaises(ValueError):
            StockTransfer(**{**self._defaults(), "organisation_id": ""})

    def test_from_warehouse_id_manquant(self):
        with self.assertRaises(ValueError):
            StockTransfer(**{**self._defaults(), "from_warehouse_id": ""})

    def test_to_warehouse_id_manquant(self):
        with self.assertRaises(ValueError):
            StockTransfer(**{**self._defaults(), "to_warehouse_id": ""})

    def test_product_id_manquant(self):
        with self.assertRaises(ValueError):
            StockTransfer(**{**self._defaults(), "product_id": ""})

    def test_quantity_invalide(self):
        with self.assertRaises(ValueError):
            StockTransfer(**{**self._defaults(), "quantity": -1})

    def test_to_dict(self):
        obj = StockTransfer(**self._defaults())
        d = obj.to_dict()
        self.assertEqual(d["id"], obj.id)

    def test_repr(self):
        obj = StockTransfer(**self._defaults())
        self.assertIn("trf-", repr(obj))

    @staticmethod
    def _defaults():
        return {
            "organisation_id": "org-1",
            "from_warehouse_id": "wh-1",
            "to_warehouse_id": "wh-2",
            "product_id": "prod-1",
            "quantity": 10,
            "status": "draft",
            "note": "Transfert urgent",        }


if __name__ == "__main__":
    unittest.main()
