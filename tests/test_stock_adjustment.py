"""Tests unitaires de l'entité StockAdjustment."""
import unittest
from engine.stock_adjustment import StockAdjustment


class TestStockAdjustmentEntity(unittest.TestCase):
    """Tests de création et validation de l'entité StockAdjustment."""

    def test_creation_valide(self):
        """Création valide doit passer sans erreur."""
        a = StockAdjustment(
            organisation_id="org-1",
            warehouse_id="wh-1",
            product_id="prod-1",
            quantity=5,
            reason="correction",
        )
        self.assertEqual(a.quantity, 5)
        self.assertEqual(a.reason, "correction")
        self.assertTrue(a.id.startswith("adj-"))

    def test_organisation_id_manquant(self):
        """organisation_id vide doit lever une erreur."""
        with self.assertRaises(ValueError):
            StockAdjustment(organisation_id="", warehouse_id="wh-1", product_id="prod-1", quantity=1, reason="correction")

    def test_warehouse_id_manquant(self):
        """warehouse_id vide doit lever une erreur."""
        with self.assertRaises(ValueError):
            StockAdjustment(organisation_id="org-1", warehouse_id="", product_id="prod-1", quantity=1, reason="correction")

    def test_product_id_manquant(self):
        """product_id vide doit lever une erreur."""
        with self.assertRaises(ValueError):
            StockAdjustment(organisation_id="org-1", warehouse_id="wh-1", product_id="", quantity=1, reason="correction")

    def test_quantity_zero(self):
        """quantity à zéro doit lever une erreur."""
        with self.assertRaises(ValueError):
            StockAdjustment(organisation_id="org-1", warehouse_id="wh-1", product_id="prod-1", quantity=0, reason="correction")

    def test_quantity_negative_valide(self):
        """quantity négatif doit être accepté (sortie)."""
        a = StockAdjustment(organisation_id="org-1", warehouse_id="wh-1", product_id="prod-1", quantity=-3, reason="loss")
        self.assertEqual(a.quantity, -3)

    def test_raison_invalide(self):
        """raison invalide doit lever une erreur."""
        with self.assertRaises(ValueError):
            StockAdjustment(organisation_id="org-1", warehouse_id="wh-1", product_id="prod-1", quantity=1, reason="inconnu")

    def test_note_defaut(self):
        """note doit être vide par défaut."""
        a = StockAdjustment(organisation_id="org-1", warehouse_id="wh-1", product_id="prod-1", quantity=1, reason="other")
        self.assertEqual(a.note, "")

    def test_to_dict(self):
        """to_dict doit retourner les bons champs."""
        a = StockAdjustment(organisation_id="org-1", warehouse_id="wh-1", product_id="prod-1", quantity=2, reason="damage", note="casse")
        d = a.to_dict()
        self.assertEqual(d["organisation_id"], "org-1")
        self.assertEqual(d["quantity"], 2)
        self.assertEqual(d["reason"], "damage")
        self.assertEqual(d["note"], "casse")

    def test_repr(self):
        """repr doit contenir l'id, la quantité et la raison."""
        a = StockAdjustment(organisation_id="org-1", warehouse_id="wh-1", product_id="prod-1", quantity=3, reason="found")
        self.assertIn("adj-", repr(a))
        self.assertIn("3", repr(a))
        self.assertIn("found", repr(a))


if __name__ == "__main__":
    unittest.main()
