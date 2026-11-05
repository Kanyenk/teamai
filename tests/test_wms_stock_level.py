"""Tests unitaires du modèle et du repository StockLevel."""

import tempfile
import unittest
from pathlib import Path

from xohive.wms.domain.stock_level import StockLevel
from xohive.wms.repository.stock_level_repository import StockLevelRepository


class TestStockLevelModel(unittest.TestCase):
    def test_valid_level(self):
        sl = StockLevel(organisation_id="org-1", product_id="p1", warehouse_id="w1", quantity=10)
        self.assertEqual(sl.quantity, 10)

    def test_negative_quantity_raises(self):
        with self.assertRaises(ValueError):
            StockLevel(organisation_id="org-1", product_id="p1", warehouse_id="w1", quantity=-1)

    def test_missing_product_raises(self):
        with self.assertRaises(ValueError):
            StockLevel(organisation_id="org-1", product_id="", warehouse_id="w1")


class TestStockLevelRepository(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = StockLevelRepository(Path(self.tmp.name) / "test.db")

    def tearDown(self):
        self.repo.close()
        self.tmp.cleanup()

    def test_create_and_get_by_id(self):
        sl = StockLevel(organisation_id="org-1", product_id="p1", warehouse_id="w1", quantity=5)
        created = self.repo.create(sl)
        self.assertIsNotNone(created.id)
        fetched = self.repo.get_by_id(created.id)
        self.assertEqual(fetched.quantity, 5)

    def test_unique_product_warehouse_pair(self):
        self.repo.create(StockLevel(organisation_id="org-1", product_id="p1", warehouse_id="w1"))
        with self.assertRaises(Exception):
            self.repo.create(StockLevel(organisation_id="org-1", product_id="p1", warehouse_id="w1"))

    def test_same_pair_different_orgs_allowed(self):
        self.repo.create(StockLevel(organisation_id="org-1", product_id="p1", warehouse_id="w1"))
        sl2 = self.repo.create(StockLevel(organisation_id="org-2", product_id="p1", warehouse_id="w1"))
        self.assertIsNotNone(sl2.id)

    def test_update_quantity(self):
        sl = self.repo.create(StockLevel(organisation_id="org-1", product_id="p1", warehouse_id="w1", quantity=5))
        updated = self.repo.update_quantity(sl.id, 12)
        self.assertEqual(updated.quantity, 12)

    def test_update_negative_quantity_raises(self):
        sl = self.repo.create(StockLevel(organisation_id="org-1", product_id="p1", warehouse_id="w1"))
        with self.assertRaises(ValueError):
            self.repo.update_quantity(sl.id, -5)

    def test_delete(self):
        sl = self.repo.create(StockLevel(organisation_id="org-1", product_id="p1", warehouse_id="w1"))
        self.assertTrue(self.repo.delete(sl.id))
        self.assertIsNone(self.repo.get_by_id(sl.id))


if __name__ == "__main__":
    unittest.main()
