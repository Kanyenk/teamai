"""Tests unitaires du modèle et du repository StockCount."""

import tempfile
import unittest
from pathlib import Path

from xohive.wms.domain.product import Product
from xohive.wms.domain.stock_count import StockCount
from xohive.wms.domain.stock_movement import StockMovement
from xohive.wms.domain.warehouse import Warehouse
from xohive.wms.repository.product_repository import ProductRepository
from xohive.wms.repository.stock_count_repository import (
    StockCountRepository,
)
from xohive.wms.repository.stock_movement_repository import (
    StockMovementRepository,
)
from xohive.wms.repository.warehouse_repository import (
    WarehouseRepository,
)


class TestStockCount(unittest.TestCase):
    """Tests du modèle et du repository StockCount."""

    def setUp(self):
        # Créer un dépôt temporaire partagé par tous les repositories.
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "test.db"
        self.counts = StockCountRepository(self.db_path)
        self.products = ProductRepository(self.db_path)
        self.warehouses = WarehouseRepository(self.db_path)
        self.movements = StockMovementRepository(self.db_path)

    def tearDown(self):
        # Fermer toutes les connexions SQLite.
        self.counts.close()
        self.products.close()
        self.warehouses.close()
        self.movements.close()
        self.tmp.cleanup()

    def _create_product_and_warehouse(self, sku="SKU-1", code="WH-1"):
        """Helper : crée un produit et un entrepôt de test."""
        product = self.products.create(Product(
            organisation_id="org-1", sku=sku, name=f"P-{sku}",
        ))
        warehouse = self.warehouses.create(Warehouse(
            organisation_id="org-1", code=code, name="W",
        ))
        return product.id, warehouse.id

    def test_create_valid(self):
        """Création d'un comptage valide."""
        product_id, warehouse_id = self._create_product_and_warehouse()
        count = self.counts.create(StockCount(
            organisation_id="org-1",
            warehouse_id=warehouse_id,
            product_id=product_id,
            counted_quantity=5,
        ))
        self.assertEqual(count.counted_quantity, 5)
        self.assertEqual(count.status, "draft")
        self.assertIsNotNone(count.id)

    def test_create_negative_quantity_raises(self):
        """Quantité négative doit lever une erreur."""
        product_id, warehouse_id = self._create_product_and_warehouse()
        with self.assertRaises(ValueError):
            StockCount(
                organisation_id="org-1",
                warehouse_id=warehouse_id,
                product_id=product_id,
                counted_quantity=-1,
            )

    def test_get(self):
        """Récupération d'un comptage par son id."""
        product_id, warehouse_id = self._create_product_and_warehouse()
        count = self.counts.create(StockCount(
            organisation_id="org-1",
            warehouse_id=warehouse_id,
            product_id=product_id,
            counted_quantity=3,
        ))
        fetched = self.counts.get(count.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.counted_quantity, 3)

    def test_adjust_with_difference_creates_movement(self):
        """Ajustement avec écart crée un mouvement correctif."""
        product_id, warehouse_id = self._create_product_and_warehouse()
        # Créer un stock théorique de 5 (entrée de 5).
        self.movements.create(StockMovement(
            organisation_id="org-1",
            product_id=product_id,
            warehouse_id=warehouse_id,
            movement_type="in",
            quantity=5,
        ))
        # Compter 3 (écart de -2).
        count = self.counts.create(StockCount(
            organisation_id="org-1",
            warehouse_id=warehouse_id,
            product_id=product_id,
            counted_quantity=3,
        ))
        result = self.counts.adjust(count.id)
        self.assertEqual(result["difference"], -2)
        self.assertIsNotNone(result["movement_id"])
        # Le stock doit maintenant être à 3.
        levels = __import__(
            "xohive.wms.repository.stock_level_repository",
            fromlist=["StockLevelRepository"],
        ).StockLevelRepository(self.db_path)
        try:
            level = levels.get_by_product_and_warehouse(
                "org-1", product_id, warehouse_id
            )
            self.assertEqual(level.quantity, 3)
        finally:
            levels.close()

    def test_adjust_no_difference(self):
        """Ajustement sans écart ne crée pas de mouvement."""
        product_id, warehouse_id = self._create_product_and_warehouse()
        self.movements.create(StockMovement(
            organisation_id="org-1",
            product_id=product_id,
            warehouse_id=warehouse_id,
            movement_type="in",
            quantity=5,
        ))
        count = self.counts.create(StockCount(
            organisation_id="org-1",
            warehouse_id=warehouse_id,
            product_id=product_id,
            counted_quantity=5,
        ))
        result = self.counts.adjust(count.id)
        self.assertEqual(result["difference"], 0)
        self.assertIsNone(result["movement_id"])
        self.assertEqual(result["status"], "adjusted")

    def test_adjust_twice_raises(self):
        """Ajustement double doit lever une erreur."""
        product_id, warehouse_id = self._create_product_and_warehouse()
        count = self.counts.create(StockCount(
            organisation_id="org-1",
            warehouse_id=warehouse_id,
            product_id=product_id,
            counted_quantity=0,
        ))
        self.counts.adjust(count.id)
        with self.assertRaises(ValueError):
            self.counts.adjust(count.id)


if __name__ == "__main__":
    unittest.main()
