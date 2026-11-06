"""Tests unitaires du service Inventory."""
import os, tempfile, unittest
from engine.inventory_repository import InventoryRepository
from engine.inventory_service import InventoryService


class TestInventoryService(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.repo = InventoryRepository(db_path=self.db_path)
        self.service = InventoryService(self.repo)

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

    def test_create(self):
        obj = self.service.create(**self._defaults())
        self.assertIsNotNone(self.service.get(obj.id))

    def test_get_inexistant(self):
        self.assertIsNone(self.service.get("inv-inexistant"))

    def test_list(self):
        self.service.create(**self._defaults())
        self.service.create(**self._defaults())
        self.assertEqual(len(self.service.list("org-1")), 2)

    def test_delete(self):
        obj = self.service.create(**self._defaults())
        self.assertTrue(self.service.delete(obj.id))
        self.assertIsNone(self.service.get(obj.id))

    def test_delete_inexistant(self):
        self.assertFalse(self.service.delete("inv-inexistant"))


if __name__ == "__main__":
    unittest.main()
