"""Tests unitaires du repository Inventory."""
import os, tempfile, unittest
from engine.inventory import Inventory
from engine.inventory_repository import InventoryRepository


class TestInventoryRepository(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.repo = InventoryRepository(db_path=self.db_path)

    def tearDown(self):
        os.unlink(self.db_path)

    @staticmethod
    def _defaults():
        return {
            "organisation_id": "org-1",
            "warehouse_id": "wh-1",
            "product_id": "prod-1",
            "counted_quantity": 5,
            "expected_quantity": 4,
            "note": "Inventaire annuel",        }

    def _make(self, **kw):
        return Inventory(**{**self._defaults(), **kw})

    def test_create_and_get(self):
        obj = self._make()
        self.repo.create(obj)
        self.assertIsNotNone(self.repo.get(obj.id))

    def test_get_non_existant(self):
        self.assertIsNone(self.repo.get("inv-inexistant"))

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
        self.assertFalse(self.repo.delete("inv-inexistant"))


if __name__ == "__main__":
    unittest.main()
