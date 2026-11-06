"""Tests du modèle et du repository Shipment (expéditions)."""

import tempfile
import unittest
from pathlib import Path

from xohive.wms.domain.product import Product
from xohive.wms.domain.shipment import Shipment
from xohive.wms.domain.warehouse import Warehouse
from xohive.wms.repository.product_repository import ProductRepository
from xohive.wms.repository.shipment_repository import ShipmentRepository
from xohive.wms.repository.stock_movement_repository import (
    StockMovementRepository,
)
from xohive.wms.repository.warehouse_repository import (
    WarehouseRepository,
)


class TestShipmentModel(unittest.TestCase):
    """Tests de validation du modèle Shipment."""

    def test_valid_shipment(self):
        """Une expédition valide doit passer."""
        s = Shipment(
            organisation_id="org-1", order_id="ord-1",
            warehouse_id="wh-1", product_id="prod-1", quantity=5,
        )
        self.assertEqual(s.status, "draft")

    def test_missing_fields_raise(self):
        """Champs manquants doivent lever une erreur."""
        with self.assertRaises(ValueError):
            Shipment(organisation_id="", order_id="ord-1",
                     warehouse_id="wh-1", product_id="prod-1", quantity=5)
        with self.assertRaises(ValueError):
            Shipment(organisation_id="org-1", order_id="",
                     warehouse_id="wh-1", product_id="prod-1", quantity=5)
        with self.assertRaises(ValueError):
            Shipment(organisation_id="org-1", order_id="ord-1",
                     warehouse_id="", product_id="prod-1", quantity=5)
        with self.assertRaises(ValueError):
            Shipment(organisation_id="org-1", order_id="ord-1",
                     warehouse_id="wh-1", product_id="", quantity=5)

    def test_invalid_quantity_raises(self):
        """Quantité invalide doit lever une erreur."""
        with self.assertRaises(ValueError):
            Shipment(organisation_id="org-1", order_id="ord-1",
                     warehouse_id="wh-1", product_id="prod-1", quantity=0)
        with self.assertRaises(ValueError):
            Shipment(organisation_id="org-1", order_id="ord-1",
                     warehouse_id="wh-1", product_id="prod-1", quantity=-1)

    def test_invalid_status_raises(self):
        """Statut invalide doit lever une erreur."""
        with self.assertRaises(ValueError):
            Shipment(organisation_id="org-1", order_id="ord-1",
                     warehouse_id="wh-1", product_id="prod-1",
                     quantity=5, status="invalid")


class TestShipmentRepository(unittest.TestCase):
    """Tests du repository Shipment."""

    def setUp(self):
        # Créer un dépôt temporaire.
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = ShipmentRepository(Path(self.tmp.name) / "test.db")
        self.products = ProductRepository(self.repo.db_path)
        self.warehouses = WarehouseRepository(self.repo.db_path)
        self.movements = StockMovementRepository(self.repo.db_path)

    def tearDown(self):
        # Fermer les connexions SQLite.
        self.repo.close()
        self.products.close()
        self.warehouses.close()
        self.movements.close()
        # Nettoyer le répertoire temporaire.
        self.tmp.cleanup()

    def _create_stock(self, product_id, warehouse_id, quantity):
        """Helper : crée un stock initial via un mouvement d'entrée."""
        from xohive.wms.domain.stock_movement import StockMovement
        self.movements.create(StockMovement(
            organisation_id="org-1",
            product_id=product_id,
            warehouse_id=warehouse_id,
            movement_type="in",
            quantity=quantity,
        ))

    def _create_refs(self):
        """Helper : crée un produit et un entrepôt de test."""
        product = self.products.create(Product(
            organisation_id="org-1", sku="SKU-SH", name="P",
        ))
        warehouse = self.warehouses.create(Warehouse(
            organisation_id="org-1", code="WH-SH", name="W",
        ))
        return product.id, warehouse.id

    def test_create_and_get_by_id(self):
        """Création et consultation d'une expédition."""
        product_id, warehouse_id = self._create_refs()
        s = self.repo.create(Shipment(
            organisation_id="org-1", order_id="ord-1",
            warehouse_id=warehouse_id, product_id=product_id, quantity=5,
        ))
        self.assertIsNotNone(s.id)
        self.assertEqual(s.status, "draft")
        got = self.repo.get_by_id(s.id)
        self.assertIsNotNone(got)
        self.assertEqual(got.quantity, 5)

    def test_list_by_organisation(self):
        """Liste des expéditions d'une organisation."""
        product_id, warehouse_id = self._create_refs()
        self.repo.create(Shipment(
            organisation_id="org-1", order_id="ord-1",
            warehouse_id=warehouse_id, product_id=product_id, quantity=5,
        ))
        items = self.repo.list_by_organisation("org-1")
        self.assertGreaterEqual(len(items), 1)

    def test_ship_creates_out_movement(self):
        """Expédition crée un mouvement out et passe à shipped."""
        product_id, warehouse_id = self._create_refs()
        s = self.repo.create(Shipment(
            organisation_id="org-1", order_id="ord-1",
            warehouse_id=warehouse_id, product_id=product_id, quantity=5,
        ))
        self._create_stock(product_id, warehouse_id, 10)
        result = self.repo.ship(s.id, carrier="UPS", tracking_number="TRK-1")
        self.assertEqual(result["shipment"]["status"], "shipped")
        self.assertIsNotNone(result["movement_id"])

    def test_ship_twice_raises(self):
        """Double expédition doit lever une erreur."""
        product_id, warehouse_id = self._create_refs()
        s = self.repo.create(Shipment(
            organisation_id="org-1", order_id="ord-1",
            warehouse_id=warehouse_id, product_id=product_id, quantity=5,
        ))
        self._create_stock(product_id, warehouse_id, 10)
        self.repo.ship(s.id)
        with self.assertRaises(ValueError):
            self.repo.ship(s.id)

    def test_ship_unknown_raises(self):
        """Expédition d'un id inexistant doit lever une erreur."""
        with self.assertRaises(ValueError):
            self.repo.ship("shipment-inconnu")


if __name__ == "__main__":
    unittest.main()
