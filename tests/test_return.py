"""Tests unitaires de l'entité Return."""
import unittest
from engine.returns import Return


class TestReturnEntity(unittest.TestCase):
    """Tests de création et validation de l'entité Return."""

    def test_creation_valide(self):
        """Création valide doit passer sans erreur."""
        r = Return(
            organisation_id="org-1",
            order_id="ord-1",
            product_id="prod-1",
            quantity=2,
            reason="Produit défectueux",
        )
        self.assertEqual(r.status, "draft")
        self.assertEqual(r.refund_amount, 0.0)
        self.assertTrue(r.id.startswith("ret-"))

    def test_organisation_id_manquant(self):
        """organisation_id vide doit lever une erreur."""
        with self.assertRaises(ValueError):
            Return(organisation_id="", order_id="ord-1", product_id="prod-1", quantity=1, reason="x")

    def test_order_id_manquant(self):
        """order_id vide doit lever une erreur."""
        with self.assertRaises(ValueError):
            Return(organisation_id="org-1", order_id="", product_id="prod-1", quantity=1, reason="x")

    def test_product_id_manquant(self):
        """product_id vide doit lever une erreur."""
        with self.assertRaises(ValueError):
            Return(organisation_id="org-1", order_id="ord-1", product_id="", quantity=1, reason="x")

    def test_quantity_negatif(self):
        """quantity négatif doit lever une erreur."""
        with self.assertRaises(ValueError):
            Return(organisation_id="org-1", order_id="ord-1", product_id="prod-1", quantity=-1, reason="x")

    def test_reason_vide(self):
        """reason vide doit lever une erreur."""
        with self.assertRaises(ValueError):
            Return(organisation_id="org-1", order_id="ord-1", product_id="prod-1", quantity=1, reason="")

    def test_status_invalide(self):
        """status invalide doit lever une erreur."""
        with self.assertRaises(ValueError):
            Return(organisation_id="org-1", order_id="ord-1", product_id="prod-1", quantity=1, reason="x", status="inconnu")

    def test_refund_amount_negatif(self):
        """refund_amount négatif doit lever une erreur."""
        with self.assertRaises(ValueError):
            Return(organisation_id="org-1", order_id="ord-1", product_id="prod-1", quantity=1, reason="x", refund_amount=-1)

    def test_mark_requested(self):
        """draft -> requested doit fonctionner."""
        r = Return(organisation_id="org-1", order_id="ord-1", product_id="prod-1", quantity=1, reason="x")
        r.mark_requested()
        self.assertEqual(r.status, "requested")

    def test_mark_requested_depuis_received(self):
        """received -> requested doit lever une erreur."""
        r = Return(organisation_id="org-1", order_id="ord-1", product_id="prod-1", quantity=1, reason="x", status="received")
        with self.assertRaises(ValueError):
            r.mark_requested()

    def test_mark_received(self):
        """requested -> received doit fonctionner."""
        r = Return(organisation_id="org-1", order_id="ord-1", product_id="prod-1", quantity=1, reason="x", status="requested")
        r.mark_received()
        self.assertEqual(r.status, "received")

    def test_mark_refunded(self):
        """received -> refunded avec montant doit fonctionner."""
        r = Return(organisation_id="org-1", order_id="ord-1", product_id="prod-1", quantity=1, reason="x", status="received")
        r.mark_refunded(50.0)
        self.assertEqual(r.status, "refunded")
        self.assertEqual(r.refund_amount, 50.0)

    def test_mark_refunded_depuis_draft(self):
        """draft -> refunded doit lever une erreur."""
        r = Return(organisation_id="org-1", order_id="ord-1", product_id="prod-1", quantity=1, reason="x")
        with self.assertRaises(ValueError):
            r.mark_refunded(50.0)

    def test_cancel(self):
        """draft -> cancelled doit fonctionner."""
        r = Return(organisation_id="org-1", order_id="ord-1", product_id="prod-1", quantity=1, reason="x")
        r.cancel()
        self.assertEqual(r.status, "cancelled")

    def test_cancel_depuis_refunded(self):
        """refunded -> cancelled doit lever une erreur."""
        r = Return(organisation_id="org-1", order_id="ord-1", product_id="prod-1", quantity=1, reason="x", status="refunded")
        with self.assertRaises(ValueError):
            r.cancel()

    def test_to_dict(self):
        """to_dict doit retourner les bons champs."""
        r = Return(organisation_id="org-1", order_id="ord-1", product_id="prod-1", quantity=2, reason="x")
        d = r.to_dict()
        self.assertEqual(d["organisation_id"], "org-1")
        self.assertEqual(d["quantity"], 2)
        self.assertEqual(d["status"], "draft")

    def test_repr(self):
        """repr doit contenir l'id et le statut."""
        r = Return(organisation_id="org-1", order_id="ord-1", product_id="prod-1", quantity=1, reason="x")
        self.assertIn("ret-", repr(r))
        self.assertIn("draft", repr(r))


if __name__ == "__main__":
    unittest.main()
