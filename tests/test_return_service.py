"""Tests unitaires du service Return."""
import os
import tempfile
import unittest
from engine.return_repository import ReturnRepository
from engine.return_service import ReturnService


class TestReturnService(unittest.TestCase):
    """Tests du service Return."""

    def setUp(self):
        """Crée une base temporaire et un service pour chaque test."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.repo = ReturnRepository(db_path=self.db_path)
        self.service = ReturnService(self.repo)

    def tearDown(self):
        """Supprime la base temporaire."""
        os.unlink(self.db_path)

    def test_create_return(self):
        """Créer un retour doit fonctionner."""
        r = self.service.create_return(
            organisation_id="org-1",
            order_id="ord-1",
            product_id="prod-1",
            quantity=2,
            reason="Produit défectueux",
        )
        self.assertEqual(r.status, "draft")
        self.assertIsNotNone(self.service.get_return(r.id))

    def test_get_return_inexistant(self):
        """Récupérer un retour inexistant doit retourner None."""
        self.assertIsNone(self.service.get_return("ret-inexistant"))

    def test_list_returns(self):
        """Lister les retours d'une organisation."""
        self.service.create_return("org-1", "ord-1", "prod-1", 1, "x")
        self.service.create_return("org-1", "ord-2", "prod-2", 1, "y")
        items = self.service.list_returns("org-1")
        self.assertEqual(len(items), 2)

    def test_request_return(self):
        """Passer un retour en requested."""
        r = self.service.create_return("org-1", "ord-1", "prod-1", 1, "x")
        updated = self.service.request_return(r.id)
        self.assertEqual(updated.status, "requested")

    def test_request_return_inexistant(self):
        """Passer un retour inexistant en requested doit lever une erreur."""
        with self.assertRaises(ValueError):
            self.service.request_return("ret-inexistant")

    def test_receive_return(self):
        """Passer un retour en received."""
        r = self.service.create_return("org-1", "ord-1", "prod-1", 1, "x")
        self.service.request_return(r.id)
        updated = self.service.receive_return(r.id)
        self.assertEqual(updated.status, "received")

    def test_refund_return(self):
        """Passer un retour en refunded avec montant."""
        r = self.service.create_return("org-1", "ord-1", "prod-1", 1, "x")
        self.service.request_return(r.id)
        self.service.receive_return(r.id)
        updated = self.service.refund_return(r.id, 50.0)
        self.assertEqual(updated.status, "refunded")
        self.assertEqual(updated.refund_amount, 50.0)

    def test_cancel_return(self):
        """Annuler un retour."""
        r = self.service.create_return("org-1", "ord-1", "prod-1", 1, "x")
        updated = self.service.cancel_return(r.id)
        self.assertEqual(updated.status, "cancelled")

    def test_cancel_return_inexistant(self):
        """Annuler un retour inexistant doit lever une erreur."""
        with self.assertRaises(ValueError):
            self.service.cancel_return("ret-inexistant")


if __name__ == "__main__":
    unittest.main()
