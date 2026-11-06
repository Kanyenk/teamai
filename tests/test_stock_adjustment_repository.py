"""Tests unitaires du repository StockAdjustment."""
import os
import tempfile
import unittest
from engine.stock_adjustment import StockAdjustment
from engine.stock_adjustment_repository import StockAdjustmentRepository


class TestStockAdjustmentRepository(unittest.TestCase):
    """Tests CRUD du repository StockAdjustment."""

    def setUp(self):
        """Crée une base temporaire pour chaque test."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.repo = StockAdjustmentRepository(db_path=self.db_path)

    def tearDown(self):
        """Supprime la base temporaire."""
        os.unlink(self.db_path)

    def _make_adjustment(self, **kwargs):
        """Crée un ajustement de test."""
        defaults = dict(
            organisation_id="org-1",
            warehouse_id="wh-1",
            product_id="prod-1",
            quantity=5,
            reason="correction",
        )
        defaults.update(kwargs)
        return StockAdjustment(**defaults)

    def test_create_and_get(self):
        """Créer puis récupérer un ajustement."""
        a = self._make_adjustment()
        self.repo.create(a)
        loaded = self.repo.get(a.id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.id, a.id)
        self.assertEqual(loaded.organisation_id, "org-1")
        self.assertEqual(loaded.quantity, 5)

    def test_get_non_existant(self):
        """Récupérer un ajustement inexistant doit retourner None."""
        self.assertIsNone(self.repo.get("adj-inexistant"))

    def test_list(self):
        """Lister les ajustements d'une organisation."""
        a1 = self._make_adjustment()
        a2 = self._make_adjustment(product_id="prod-2")
        self.repo.create(a1)
        self.repo.create(a2)
        items = self.repo.list("org-1")
        self.assertEqual(len(items), 2)

    def test_list_empty(self):
        """Lister une organisation sans ajustements."""
        items = self.repo.list("org-inconnu")
        self.assertEqual(len(items), 0)

    def test_delete(self):
        """Supprimer un ajustement."""
        a = self._make_adjustment()
        self.repo.create(a)
        self.assertTrue(self.repo.delete(a.id))
        self.assertIsNone(self.repo.get(a.id))

    def test_delete_non_existant(self):
        """Supprimer un ajustement inexistant doit retourner False."""
        self.assertFalse(self.repo.delete("adj-inexistant"))


if __name__ == "__main__":
    unittest.main()
