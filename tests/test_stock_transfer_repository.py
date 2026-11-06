"""Tests unitaires du repository StockTransfer."""
import os, tempfile, unittest
from engine.stock_transfer import StockTransfer
from engine.stock_transfer_repository import StockTransferRepository


class TestStockTransferRepository(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.repo = StockTransferRepository(db_path=self.db_path)

    def tearDown(self):
        os.unlink(self.db_path)

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

    def _make(self, **kw):
        return StockTransfer(**{**self._defaults(), **kw})

    def test_create_and_get(self):
        obj = self._make()
        self.repo.create(obj)
        self.assertIsNotNone(self.repo.get(obj.id))

    def test_get_non_existant(self):
        self.assertIsNone(self.repo.get("trf-inexistant"))

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
        self.assertFalse(self.repo.delete("trf-inexistant"))


if __name__ == "__main__":
    unittest.main()
