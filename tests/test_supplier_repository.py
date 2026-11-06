"""Tests unitaires du repository Supplier."""
import os, tempfile, unittest
from engine.supplier import Supplier
from engine.supplier_repository import SupplierRepository


class TestSupplierRepository(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.repo = SupplierRepository(db_path=self.db_path)

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

    def _make(self, **kw):
        return Supplier(**{**self._defaults(), **kw})

    def test_create_and_get(self):
        obj = self._make()
        self.repo.create(obj)
        self.assertIsNotNone(self.repo.get(obj.id))

    def test_get_non_existant(self):
        self.assertIsNone(self.repo.get("sup-inexistant"))

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
        self.assertFalse(self.repo.delete("sup-inexistant"))


if __name__ == "__main__":
    unittest.main()
