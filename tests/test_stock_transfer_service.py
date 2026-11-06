"""Tests unitaires du service StockTransfer."""
import os, tempfile, unittest
from engine.stock_transfer_repository import StockTransferRepository
from engine.stock_transfer_service import StockTransferService


class TestStockTransferService(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.repo = StockTransferRepository(db_path=self.db_path)
        self.service = StockTransferService(self.repo)

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

    def test_create(self):
        obj = self.service.create(**self._defaults())
        self.assertIsNotNone(self.service.get(obj.id))

    def test_get_inexistant(self):
        self.assertIsNone(self.service.get("trf-inexistant"))

    def test_list(self):
        self.service.create(**self._defaults())
        self.service.create(**self._defaults())
        self.assertEqual(len(self.service.list("org-1")), 2)

    def test_delete(self):
        obj = self.service.create(**self._defaults())
        self.assertTrue(self.service.delete(obj.id))
        self.assertIsNone(self.service.get(obj.id))

    def test_delete_inexistant(self):
        self.assertFalse(self.service.delete("trf-inexistant"))


if __name__ == "__main__":
    unittest.main()
