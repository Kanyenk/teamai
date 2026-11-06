"""Tests unitaires de l'entité Barcode."""
import unittest
from engine.barcode import Barcode


class TestBarcodeEntity(unittest.TestCase):
    def test_creation_valide(self):
        """Création valide doit passer sans erreur."""
        obj = Barcode(**self._defaults())
        self.assertTrue(obj.id.startswith("brc"))

    def test_organisation_id_manquant(self):
        with self.assertRaises(ValueError):
            Barcode(**{**self._defaults(), "organisation_id": ""})

    def test_product_id_manquant(self):
        with self.assertRaises(ValueError):
            Barcode(**{**self._defaults(), "product_id": ""})

    def test_code_manquant(self):
        with self.assertRaises(ValueError):
            Barcode(**{**self._defaults(), "code": ""})

    def test_type_manquant(self):
        with self.assertRaises(ValueError):
            Barcode(**{**self._defaults(), "type": ""})

    def test_to_dict(self):
        obj = Barcode(**self._defaults())
        d = obj.to_dict()
        self.assertEqual(d["id"], obj.id)

    def test_repr(self):
        obj = Barcode(**self._defaults())
        self.assertIn("brc-", repr(obj))

    @staticmethod
    def _defaults():
        return {
            "organisation_id": 'org-1',
            "product_id": 'prod-1',
            "code": '3012345678900',
            "type": 'ean13',
            "label": 'Code-barres produit A',        }


if __name__ == "__main__":
    unittest.main()
