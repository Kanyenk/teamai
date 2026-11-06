"""Tests unitaires du modèle et du repository PurchaseOrder."""

import tempfile
import unittest
from pathlib import Path

from xohive.wms.domain.purchase_order import PurchaseOrder
from xohive.wms.repository.purchase_order_repository import (
    PurchaseOrderRepository,
)


class TestPurchaseOrderModel(unittest.TestCase):
    def test_valid_order(self):
        order = PurchaseOrder(
            organisation_id="org-1",
            supplier_name="Fournisseur A",
            warehouse_id="wh-1",
        )
        self.assertEqual(order.status, "draft")
        self.assertIsNone(order.reference)

    def test_missing_fields_raise(self):
        with self.assertRaises(ValueError):
            PurchaseOrder(organisation_id="", supplier_name="A", warehouse_id="wh-1")
        with self.assertRaises(ValueError):
            PurchaseOrder(organisation_id="org-1", supplier_name="", warehouse_id="wh-1")
        with self.assertRaises(ValueError):
            PurchaseOrder(organisation_id="org-1", supplier_name="A", warehouse_id="")

    def test_invalid_status_raises(self):
        with self.assertRaises(ValueError):
            PurchaseOrder(
                organisation_id="org-1",
                supplier_name="A",
                warehouse_id="wh-1",
                status="unknown",
            )


class TestPurchaseOrderRepository(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = PurchaseOrderRepository(Path(self.tmp.name) / "test.db")

    def tearDown(self):
        self.repo.close()
        self.tmp.cleanup()

    def test_create_and_get_by_id(self):
        order = self.repo.create(PurchaseOrder(
            organisation_id="org-1",
            supplier_name="Fournisseur A",
            warehouse_id="wh-1",
        ))
        self.assertIsNotNone(order.id)
        self.assertIsNotNone(order.reference)
        fetched = self.repo.get_by_id(order.id)
        self.assertEqual(fetched.supplier_name, "Fournisseur A")

    def test_list_by_organisation(self):
        self.repo.create(PurchaseOrder(
            organisation_id="org-1", supplier_name="A", warehouse_id="wh-1",
        ))
        self.repo.create(PurchaseOrder(
            organisation_id="org-2", supplier_name="B", warehouse_id="wh-1",
        ))
        self.assertEqual(len(self.repo.list_by_organisation("org-1")), 1)

    def test_update_status(self):
        order = self.repo.create(PurchaseOrder(
            organisation_id="org-1", supplier_name="A", warehouse_id="wh-1",
        ))
        updated = self.repo.update_status(order.id, "received")
        self.assertEqual(updated.status, "received")

    def test_update_status_invalid_raises(self):
        order = self.repo.create(PurchaseOrder(
            organisation_id="org-1", supplier_name="A", warehouse_id="wh-1",
        ))
        with self.assertRaises(ValueError):
            self.repo.update_status(order.id, "unknown")


if __name__ == "__main__":
    unittest.main()
