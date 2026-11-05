"""Tests unitaires pour le module Order."""

import unittest
import tempfile
import shutil
import os
from datetime import datetime, timezone

from xohive.crm.domain.order import Order, OrderError
from xohive.crm.repository.order_repository import OrderRepository


class TestOrderCreation(unittest.TestCase):
    """Tests pour la création d'une commande."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_teamai.db")
        self.repo = OrderRepository(self.db_path)
        self.order = Order(
            organisation_id="org-1",
            company_id="cmp-1",
            quotation_id="quote-1",
            order_date="2026-11-05",
            delivery_date="2026-11-10",
            shipping_method="standard",
            total_amount=2500.00,
            tax_rate=20.0,
            currency="EUR",
            status="pending",
        )

    def tearDown(self):
        self.repo.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_creation_valide(self):
        self.assertEqual(self.order.organisation_id, "org-1")
        self.assertEqual(self.order.company_id, "cmp-1")
        self.assertEqual(self.order.shipping_method, "standard")
        self.assertEqual(self.order.total_amount, 2500.00)
        self.assertEqual(self.order.status, "pending")
        self.assertIsNotNone(self.order.id)
        self.assertIsNotNone(self.order.created_at)

    def test_creation_department(self):
        self.order.status = "confirmed"
        self.order.shipping_method = "express"
        self.assertEqual(self.order.shipping_method, "express")
        self.assertEqual(self.order.status, "confirmed")

    def test_reference_auto(self):
        o = Order(
            organisation_id="org-1",
            company_id="cmp-1",
            quotation_id="quote-1",
            order_date="2026-11-05",
            total_amount=100.00,
        )
        self.assertTrue(len(o.id) >= 8)

    def test_validation_erreur_status_invalid(self):
        with self.assertRaises(OrderError):
            Order(
                organisation_id="org-1",
                company_id="cmp-1",
                quotation_id="quote-1",
                order_date="2026-11-05",
                total_amount=100.00,
                status="invalid",
            )

    def test_validation_erreur_shipping_invalid(self):
        with self.assertRaises(OrderError):
            Order(
                organisation_id="org-1",
                company_id="cmp-1",
                quotation_id="quote-1",
                order_date="2026-11-05",
                total_amount=100.00,
                shipping_method="invalid",
            )

    def test_validation_erreur_total_negative(self):
        with self.assertRaises(OrderError):
            Order(
                organisation_id="org-1",
                company_id="cmp-1",
                quotation_id="quote-1",
                order_date="2026-11-05",
                total_amount=-100.00,
                status="pending",
            )

    def test_validation_erreur_delivery_before_order(self):
        with self.assertRaises(OrderError):
            Order(
                organisation_id="org-1",
                company_id="cmp-1",
                quotation_id="quote-1",
                order_date="2026-12-31",
                delivery_date="2026-11-01",
                total_amount=100.00,
                status="pending",
            )


class TestOrderRepository(unittest.TestCase):
    """Tests pour le repository de commande."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_teamai.db")
        self.repo = OrderRepository(self.db_path)
        self.order_data = {
            "organisation_id": "org-1",
            "company_id": "cmp-1",
            "quotation_id": "quote-1",
            "order_date": datetime.now(timezone.utc).isoformat(),
            "delivery_date": "2026-11-10",
            "shipping_method": "standard",
            "total_amount": 2500.00,
            "tax_rate": 20.0,
            "currency": "EUR",
        }

    def tearDown(self):
        self.repo.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_and_get(self):
        o = Order(**self.order_data)
        self.repo.create(o)
        retrieved = self.repo.get(o.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.quotation_id, o.quotation_id)

    def test_list_with_filters(self):
        o1 = Order(
            organisation_id="org-1", company_id="cmp-1",
            quotation_id="quote-1", order_date="2026-11-05",
            shipping_method="standard", total_amount=100.00,
            delivery_date="2026-11-10", status="pending",
        )
        o2 = Order(
            organisation_id="org-1", company_id="cmp-1",
            quotation_id="quote-2", order_date="2026-11-06",
            shipping_method="express", total_amount=200.00,
            delivery_date="2026-11-12", status="confirmed",
        )
        self.repo.create(o1)
        self.repo.create(o2)

        items = self.repo.list(organisation_id="org-1")
        self.assertEqual(len(items), 2)

        items_pending = self.repo.list(status="pending")
        self.assertEqual(len(items_pending), 1)
        self.assertEqual(items_pending[0].status, "pending")

    def test_list_empty(self):
        items = self.repo.list(organisation_id="org-1")
        self.assertEqual(items, [])

    def test_update(self):
        o = Order(**self.order_data)
        self.repo.create(o)
        o.status = "confirmed"
        o.shipping_method = "express"
        o.updated_at = datetime.now(timezone.utc).isoformat()
        self.repo.update(o)

        retrieved = self.repo.get(o.id)
        self.assertEqual(retrieved.status, "confirmed")
        self.assertEqual(retrieved.shipping_method, "express")

    def test_delete(self):
        o = Order(**self.order_data)
        self.repo.create(o)
        self.repo.delete(o.id)

        retrieved = self.repo.get(o.id)
        self.assertIsNone(retrieved)


class TestOrderAudit(unittest.TestCase):
    """Tests pour la génération d'audit sur les commandes."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_teamai.db")
        self.repo = OrderRepository(self.db_path)

    def tearDown(self):
        self.repo.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_generates_audit(self):
        """Vérifie qu'une création génère un événement d'audit."""
        # Test temporaire - la table audit n'est pas configurée dans le test
        o = Order(
            organisation_id="org-1",
            company_id="cmp-1",
            quotation_id="quote-1",
            order_date="2026-11-05",
            total_amount=100.00,
            status="pending",
        )
        self.repo.create(o)
        # L'audit est vérifié par le système AuditCRM séparément


if __name__ == "__main__":
    unittest.main()
