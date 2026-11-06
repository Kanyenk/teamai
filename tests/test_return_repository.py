"""Tests unitaires du repository Return."""
import os
import tempfile
import unittest
from engine.returns import Return
from engine.return_repository import ReturnRepository


class TestReturnRepository(unittest.TestCase):
    """Tests CRUD du repository Return."""

    def setUp(self):
        """Crée une base temporaire pour chaque test."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.repo = ReturnRepository(db_path=self.db_path)

    def tearDown(self):
        """Supprime la base temporaire."""
        os.unlink(self.db_path)

    def _make_return(self, **kwargs):
        """Crée un retour de test."""
        defaults = dict(
            organisation_id="org-1",
            order_id="ord-1",
            product_id="prod-1",
            quantity=2,
            reason="Produit défectueux",
        )
        defaults.update(kwargs)
        return Return(**defaults)

    def test_create_and_get(self):
        """Créer puis récupérer un retour."""
        r = self._make_return()
        self.repo.create(r)
        loaded = self.repo.get(r.id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.id, r.id)
        self.assertEqual(loaded.organisation_id, "org-1")
        self.assertEqual(loaded.quantity, 2)

    def test_get_non_existant(self):
        """Récupérer un retour inexistant doit retourner None."""
        self.assertIsNone(self.repo.get("ret-inexistant"))

    def test_list(self):
        """Lister les retours d'une organisation."""
        r1 = self._make_return()
        r2 = self._make_return(order_id="ord-2")
        self.repo.create(r1)
        self.repo.create(r2)
        items = self.repo.list("org-1")
        self.assertEqual(len(items), 2)

    def test_list_empty(self):
        """Lister une organisation sans retours."""
        items = self.repo.list("org-inconnu")
        self.assertEqual(len(items), 0)

    def test_update(self):
        """Mettre à jour le statut d'un retour."""
        r = self._make_return()
        self.repo.create(r)
        r.mark_requested()
        self.repo.update(r)
        loaded = self.repo.get(r.id)
        self.assertEqual(loaded.status, "requested")

    def test_delete(self):
        """Supprimer un retour."""
        r = self._make_return()
        self.repo.create(r)
        self.assertTrue(self.repo.delete(r.id))
        self.assertIsNone(self.repo.get(r.id))

    def test_delete_non_existant(self):
        """Supprimer un retour inexistant doit retourner False."""
        self.assertFalse(self.repo.delete("ret-inexistant"))


if __name__ == "__main__":
    unittest.main()
