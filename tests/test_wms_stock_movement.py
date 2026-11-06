"""Tests unitaires du modèle et du repository StockMovement."""

import tempfile
import unittest
from pathlib import Path

from xohive.wms.domain.stock_movement import StockMovement
from xohive.wms.domain.stock_level import StockLevel
from xohive.wms.domain.product import Product
from xohive.wms.domain.warehouse import Warehouse
from xohive.wms.repository.stock_movement_repository import StockMovementRepository
from xohive.wms.repository.stock_level_repository import StockLevelRepository
from xohive.wms.repository.product_repository import ProductRepository
from xohive.wms.repository.warehouse_repository import WarehouseRepository


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
        self.products = ProductRepository(self.db)
        self.warehouses = WarehouseRepository(self.db)
        # Entités réelles pour satisfaire la validation croisée
        self.product = self.products.create(Product(
            organisation_id="org-1", sku="SKU-1", name="Produit 1",
        ))
        self.warehouse = self.warehouses.create(Warehouse(
            organisation_id="org-1", code="WH-01", name="Entrepôt 1",
        ))
        self.target_warehouse = self.warehouses.create(Warehouse(
            organisation_id="org-1", code="WH-02", name="Entrepôt 2",
        ))

    def tearDown(self):
        self.repo.close()
        self.levels.close()
        self.products.close()
        self.warehouses.close()
        self.tmp.cleanup()

    def _movement(self, movement_type, quantity, target=None):
        return StockMovement(
            organisation_id="org-1",
            product_id=self.product.id,
            warehouse_id=self.warehouse.id,
            movement_type=movement_type,
            quantity=quantity,
            target_warehouse_id=target,
        )

    def test_in_movement_increases_stock(self):
        self.repo.create(self._movement("in", 10))
        level = self.levels.get_by_product_and_warehouse(
            "org-1", self.product.id, self.warehouse.id
        )
        self.assertEqual(level.quantity, 10)

    def test_out_movement_decreases_stock(self):
        self.repo.create(self._movement("in", 10))
        self.repo.create(self._movement("out", 4))
        level = self.levels.get_by_product_and_warehouse(
            "org-1", self.product.id, self.warehouse.id
        )
        self.assertEqual(level.quantity, 6)

    def test_out_insufficient_stock_raises(self):
        with self.assertRaises(ValueError):
            self.repo.create(self._movement("out", 5))

    def test_adjustment_sets_absolute_quantity(self):
        self.repo.create(self._movement("in", 10))
        self.repo.create(self._movement("adjustment", 3))
        level = self.levels.get_by_product_and_warehouse(
            "org-1", self.product.id, self.warehouse.id
        )
        self.assertEqual(level.quantity, 3)

    def test_transfer_moves_stock_between_warehouses(self):
        self.repo.create(self._movement("in", 10))
        self.repo.create(self._movement(
            "transfer", 4, target=self.target_warehouse.id
        ))
        src = self.levels.get_by_product_and_warehouse(
            "org-1", self.product.id, self.warehouse.id
        )
        dst = self.levels.get_by_product_and_warehouse(
            "org-1", self.product.id, self.target_warehouse.id
        )
        self.assertEqual(src.quantity, 6)
        self.assertEqual(dst.quantity, 4)

    def test_get_by_id_and_list(self):
        m = self.repo.create(self._movement("in", 10))
        fetched = self.repo.get_by_id(m.id)
        self.assertEqual(fetched.quantity, 10)
        self.assertEqual(len(self.repo.list()), 1)


class TestStockMovementValidation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "test.db"
        self.repo = StockMovementRepository(self.db)
        self.levels = StockLevelRepository(self.db)
        self.products = ProductRepository(self.db)
        self.warehouses = WarehouseRepository(self.db)

    def tearDown(self):
        self.repo.close()
        self.levels.close()
        self.products.close()
        self.warehouses.close()
        self.tmp.cleanup()

    def test_movement_with_unknown_product_raises(self):
        warehouse = self.warehouses.create(Warehouse(
            organisation_id="org-1", code="WH-01", name="A",
        ))
        with self.assertRaises(ValueError):
            self.repo.create(StockMovement(
                organisation_id="org-1", product_id="inexistant",
                warehouse_id=warehouse.id, movement_type="in", quantity=5,
            ))

    def test_movement_with_unknown_warehouse_raises(self):
        product = self.products.create(Product(
            organisation_id="org-1", sku="SKU-1", name="P",
        ))
        with self.assertRaises(ValueError):
            self.repo.create(StockMovement(
                organisation_id="org-1", product_id=product.id,
                warehouse_id="inexistant", movement_type="in", quantity=5,
            ))

    def test_transfer_with_unknown_target_raises(self):
        product = self.products.create(Product(
            organisation_id="org-1", sku="SKU-1", name="P",
        ))
        warehouse = self.warehouses.create(Warehouse(
            organisation_id="org-1", code="WH-01", name="A",
        ))
        with self.assertRaises(ValueError):
            self.repo.create(StockMovement(
                organisation_id="org-1", product_id=product.id,
                warehouse_id=warehouse.id, movement_type="transfer",
                quantity=5, target_warehouse_id="inexistant",
            ))

    def test_valid_movement_with_existing_refs_passes(self):
        product = self.products.create(Product(
            organisation_id="org-1", sku="SKU-1", name="P",
        ))
        warehouse = self.warehouses.create(Warehouse(
            organisation_id="org-1", code="WH-01", name="A",
        ))
        m = self.repo.create(StockMovement(
            organisation_id="org-1", product_id=product.id,
            warehouse_id=warehouse.id, movement_type="in", quantity=5,
        ))
        self.assertIsNotNone(m.id)


if __name__ == "__main__":
    unittest.main()


class TestStockMovementPagination(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "test.db"
        self.repo = StockMovementRepository(self.db)
        self.products = ProductRepository(self.db)
        self.warehouses = WarehouseRepository(self.db)
        self.product = self.products.create(Product(
            organisation_id="org-1", sku="SKU-PAG", name="P",
        ))
        self.warehouse = self.warehouses.create(Warehouse(
            organisation_id="org-1", code="WH-PAG", name="W",
        ))

    def tearDown(self):
        self.repo.close()
        self.products.close()
        self.warehouses.close()
        self.tmp.cleanup()

    def _create(self, qty):
        return self.repo.create(StockMovement(
            organisation_id="org-1",
            product_id=self.product.id,
            warehouse_id=self.warehouse.id,
            movement_type="in", quantity=qty,
        ))

    def test_list_default_limit(self):
        for i in range(60):
            self._create(1)
        self.assertEqual(len(self.repo.list()), 50)

    def test_list_with_limit_and_offset(self):
        for i in range(10):
            self._create(1)
        page1 = self.repo.list(limit=4, offset=0)
        page2 = self.repo.list(limit=4, offset=4)
        self.assertEqual(len(page1), 4)
        self.assertEqual(len(page2), 4)
        self.assertNotEqual(page1[0].id, page2[0].id)

    def test_list_invalid_limit_raises(self):
        with self.assertRaises(ValueError):
            self.repo.list(limit=0)
        with self.assertRaises(ValueError):
            self.repo.list(limit=101)

    def test_list_negative_offset_raises(self):
        with self.assertRaises(ValueError):
            self.repo.list(offset=-1)


class TestStockMovementFilters(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "test.db"
        self.repo = StockMovementRepository(self.db)
        self.products = ProductRepository(self.db)
        self.warehouses = WarehouseRepository(self.db)
        self.product = self.products.create(Product(
            organisation_id="org-1", sku="SKU-FILT", name="P",
        ))
        self.warehouse = self.warehouses.create(Warehouse(
            organisation_id="org-1", code="WH-FILT", name="W",
        ))

    def tearDown(self):
        self.repo.close()
        self.products.close()
        self.warehouses.close()
        self.tmp.cleanup()

    def _movement(self, mtype, qty):
        return StockMovement(
            organisation_id="org-1",
            product_id=self.product.id,
            warehouse_id=self.warehouse.id,
            movement_type=mtype, quantity=qty,
        )

    def test_filter_by_movement_type(self):
        self.repo.create(self._movement("in", 10))
        self.repo.create(self._movement("adjustment", 5))
        result = self.repo.list(movement_type="in")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].movement_type, "in")

    def test_filter_by_product(self):
        self.repo.create(self._movement("in", 10))
        result = self.repo.list(product_id=self.product.id)
        self.assertEqual(len(result), 1)
        result = self.repo.list(product_id="inexistant")
        self.assertEqual(len(result), 0)

    def test_filter_by_warehouse(self):
        self.repo.create(self._movement("in", 10))
        result = self.repo.list(warehouse_id=self.warehouse.id)
        self.assertEqual(len(result), 1)

    def test_invalid_movement_type_filter_raises(self):
        with self.assertRaises(ValueError):
            self.repo.list(movement_type="unknown")

    def test_filters_combined_with_pagination(self):
        for _ in range(6):
            self.repo.create(self._movement("in", 1))
        result = self.repo.list(
            movement_type="in", limit=4, offset=2
        )
        self.assertEqual(len(result), 4)
