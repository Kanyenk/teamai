"""Tests unitaires du service Supplier."""
import os, tempfile, unittest
from engine.supplier_repository import SupplierRepository
from engine.supplier_service import SupplierService


class TestSupplierService(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.repo = SupplierRepository(db_path=self.db_path)
        self.service = SupplierService(self.repo)

    def tearDown(self):
        os.unlink(self.db_path)

    @staticmethod
    def _defaults():
        return {
            "organisation_id": "org-1",
            "name": "Fournisseur Test",
            "email": "contact@fournisseur.fr",
            "phone": "+33123456789",
            "address": "12 rue du Commerce",        }

    def test_create(self):
        obj = self.service.create(**self._defaults())
        self.assertIsNotNone(self.service.get(obj.id))

    def test_get_inexistant(self):
        self.assertIsNone(self.service.get("sup-inexistant"))

    def test_list(self):
        self.service.create(**self._defaults())
        self.service.create(**self._defaults())
        self.assertEqual(len(self.service.list("org-1")), 2)

    def test_delete(self):
        obj = self.service.create(**self._defaults())
        self.assertTrue(self.service.delete(obj.id))
        self.assertIsNone(self.service.get(obj.id))

    def test_delete_inexistant(self):
        self.assertFalse(self.service.delete("sup-inexistant"))


if __name__ == "__main__":
    unittest.main()
