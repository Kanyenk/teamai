"""Tests unitaires du repository Barcode."""
import os, tempfile, unittest
from engine.barcode import Barcode
from engine.barcode_repository import BarcodeRepository


class TestBarcodeRepository(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.repo = BarcodeRepository(db_path=self.db_path)

    def tearDown(self):
        os.unlink(self.db_path)

    @staticmethod
    def _defaults():
        return {
            "organisation_id": 'org-1',
            "product_id": 'prod-1',
            "code": '3012345678900',
            "type": 'ean13',
            "label": 'Code-barres produit A',        }

    def _make(self, **kw):
        return Barcode(**{**self._defaults(), **kw})

    def test_create_and_get(self):
        obj = self._make()
        self.repo.create(obj)
        self.assertIsNotNone(self.repo.get(obj.id))

    def test_get_non_existant(self):
        self.assertIsNone(self.repo.get("brc-inexistant"))

    def test_list(self):
        self.repo.create(self._make())
        self.repo.create(self._make())
        self.assertEqual(len(self.repo.list("org-1")), 2)

    def test_list_empty(self):
        self.assertEqual(len(self.repo.list("inconnu")), 0)

    def test_delete(self):
        obj = self._make()
        self.repo.create(obj)
        self.assertTrue(self.repo.delete(obj.id))
        self.assertIsNone(self.repo.get(obj.id))

    def test_delete_non_existant(self):
        self.assertFalse(self.repo.delete("brc-inexistant"))


if __name__ == "__main__":
    unittest.main()
