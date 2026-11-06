"""Tests unitaires du modèle et du repository StockMovement."""

import tempfile
import unittest
from pathlib import Path

from xohive.wms.domain.stock_movement import StockMovement
from xohive.wms.domain.stock_level import StockLevel
from xohive.wms.repository.stock_movement_repository import StockMovementRepository
from xohive.wms.repository.stock_level_repository import StockLevelRepository


class TestStockMovementModel(unittest.TestCase):
    def test_valid_in_movement(self):
        m = StockMovement(
            organisation_id="org-1", product_id="p1", warehouse_id="w1",
            movement_type="in", quantity=10,
        )
        self.assertEqual(m.movement_type, "in")

    def test_invalid_type_raises(self):
        with self.assertRaises(ValueError):
            StockMovement(
                organisation_id="org-1", product_id="p1", warehouse_id="w1",
                movement_type="unknown", quantity=10,
            )

    def test_zero_quantity_raises(self):
        with self.assertRaises(ValueError):
            StockMovement(
                organisation_id="org-1", product_id="p1", warehouse_id="w1",
                movement_type="in", quantity=0,
            )

    def test_transfer_requires_target(self):
        with self.assertRaises(ValueError):
            StockMovement(
                organisation_id="org-1", product_id="p1", warehouse_id="w1",
                movement_type="transfer", quantity=5,
            )


class TestStockMovementRepository(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "test.db"
        self.repo = StockMovementRepository(self.db)
        self.levels = StockLevelRepository(self.db)

    def tearDown(self):
        self.repo.close()
        self.levels.close()
        self.tmp.cleanup()

    def test_in_movement_increases_stock(self):
        self.repo.create(StockMovement(
            organisation_id="org-1", product_id="p1", warehouse_id="w1",
            movement_type="in", quantity=10,
        ))
        level = self.levels.get_by_product_and_warehouse("org-1", "p1", "w1")
        self.assertEqual(level.quantity, 10)

    def test_out_movement_decreases_stock(self):
        self.repo.create(StockMovement(
            organisation_id="org-1", product_id="p1", warehouse_id="w1",
            movement_type="in", quantity=10,
        ))
        self.repo.create(StockMovement(
            organisation_id="org-1", product_id="p1", warehouse_id="w1",
            movement_type="out", quantity=4,
        ))
        level = self.levels.get_by_product_and_warehouse("org-1", "p1", "w1")
        self.assertEqual(level.quantity, 6)

    def test_out_insufficient_stock_raises(self):
        with self.assertRaises(ValueError):
            self.repo.create(StockMovement(
                organisation_id="org-1", product_id="p1", warehouse_id="w1",
                movement_type="out", quantity=5,
            ))

    def test_adjustment_sets_absolute_quantity(self):
        self.repo.create(StockMovement(
            organisation_id="org-1", product_id="p1", warehouse_id="w1",
            movement_type="in", quantity=10,
        ))
        self.repo.create(StockMovement(
            organisation_id="org-1", product_id="p1", warehouse_id="w1",
            movement_type="adjustment", quantity=3,
        ))
        level = self.levels.get_by_product_and_warehouse("org-1", "p1", "w1")
        self.assertEqual(level.quantity, 3)

    def test_transfer_moves_stock_between_warehouses(self):
        self.repo.create(StockMovement(
            organisation_id="org-1", product_id="p1", warehouse_id="w1",
            movement_type="in", quantity=10,
        ))
        self.repo.create(StockMovement(
            organisation_id="org-1", product_id="p1", warehouse_id="w1",
            movement_type="transfer", quantity=4, target_warehouse_id="w2",
        ))
        src = self.levels.get_by_product_and_warehouse("org-1", "p1", "w1")
        dst = self.levels.get_by_product_and_warehouse("org-1", "p1", "w2")
        self.assertEqual(src.quantity, 6)
        self.assertEqual(dst.quantity, 4)

    def test_get_by_id_and_list(self):
        m = self.repo.create(StockMovement(
            organisation_id="org-1", product_id="p1", warehouse_id="w1",
            movement_type="in", quantity=10,
        ))
        fetched = self.repo.get_by_id(m.id)
        self.assertEqual(fetched.quantity, 10)
        self.assertEqual(len(self.repo.list()), 1)


if __name__ == "__main__":
    unittest.main()
