"""Tests unitaires du service Barcode."""
import os, tempfile, unittest
from engine.barcode_repository import BarcodeRepository
from engine.barcode_service import BarcodeService


class TestBarcodeService(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.repo = BarcodeRepository(db_path=self.db_path)
        self.service = BarcodeService(self.repo)

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

    def test_create(self):
        obj = self.service.create(**self._defaults())
        self.assertIsNotNone(self.service.get(obj.id))

    def test_get_inexistant(self):
        self.assertIsNone(self.service.get("brc-inexistant"))

    def test_list(self):
        self.service.create(**self._defaults())
        self.service.create(**self._defaults())
        self.assertEqual(len(self.service.list("org-1")), 2)

    def test_delete(self):
        obj = self.service.create(**self._defaults())
        self.assertTrue(self.service.delete(obj.id))
        self.assertIsNone(self.service.get(obj.id))

    def test_delete_inexistant(self):
        self.assertFalse(self.service.delete("brc-inexistant"))


if __name__ == "__main__":
    unittest.main()
