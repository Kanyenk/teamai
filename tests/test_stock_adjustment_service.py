"""Tests unitaires du service StockAdjustment."""
import os
import tempfile
import unittest
from engine.stock_adjustment_repository import StockAdjustmentRepository
from engine.stock_adjustment_service import StockAdjustmentService


class TestStockAdjustmentService(unittest.TestCase):
    """Tests du service StockAdjustment."""

    def setUp(self):
        """Crée une base temporaire et un service pour chaque test."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.repo = StockAdjustmentRepository(db_path=self.db_path)
        self.service = StockAdjustmentService(self.repo)

    def tearDown(self):
        """Supprime la base temporaire."""
        os.unlink(self.db_path)

    def test_create_adjustment(self):
        """Créer un ajustement doit fonctionner."""
        a = self.service.create_adjustment(
            organisation_id="org-1",
            warehouse_id="wh-1",
            product_id="prod-1",
            quantity=5,
            reason="correction",
        )
        self.assertEqual(a.quantity, 5)
        self.assertIsNotNone(self.service.get_adjustment(a.id))

    def test_create_adjustment_negative(self):
        """Créer un ajustement avec quantité négative doit fonctionner."""
        a = self.service.create_adjustment(
            organisation_id="org-1",
            warehouse_id="wh-1",
            product_id="prod-1",
            quantity=-3,
            reason="loss",
        )
        self.assertEqual(a.quantity, -3)

    def test_get_adjustment_inexistant(self):
        """Récupérer un ajustement inexistant doit retourner None."""
        self.assertIsNone(self.service.get_adjustment("adj-inexistant"))

    def test_list_adjustments(self):
        """Lister les ajustements d'une organisation."""
        self.service.create_adjustment("org-1", "wh-1", "prod-1", 1, "correction")
        self.service.create_adjustment("org-1", "wh-1", "prod-2", 2, "damage")
        items = self.service.list_adjustments("org-1")
        self.assertEqual(len(items), 2)

    def test_delete_adjustment(self):
        """Supprimer un ajustement."""
        a = self.service.create_adjustment("org-1", "wh-1", "prod-1", 1, "other")
        self.assertTrue(self.service.delete_adjustment(a.id))
        self.assertIsNone(self.service.get_adjustment(a.id))

    def test_delete_adjustment_inexistant(self):
        """Supprimer un ajustement inexistant doit retourner False."""
        self.assertFalse(self.service.delete_adjustment("adj-inexistant"))


if __name__ == "__main__":
    unittest.main()
