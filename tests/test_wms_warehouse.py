"""Tests unitaires du modèle et du repository Warehouse."""

import tempfile
import unittest
from pathlib import Path

from xohive.wms.domain.warehouse import Warehouse
from xohive.wms.repository.warehouse_repository import WarehouseRepository


class TestWarehouseModel(unittest.TestCase):
    def test_valid_warehouse(self):
        w = Warehouse(organisation_id="org-1", code="WH-01", name="Entrepôt Paris")
        self.assertEqual(w.code, "WH-01")
        self.assertTrue(w.is_active)

    def test_missing_code_raises(self):
        with self.assertRaises(ValueError):
            Warehouse(organisation_id="org-1", code="", name="X")

    def test_invalid_code_format_raises(self):
        with self.assertRaises(ValueError):
            Warehouse(organisation_id="org-1", code="A", name="X")  # trop court
        with self.assertRaises(ValueError):
            Warehouse(organisation_id="org-1", code="WH 01", name="X")  # espace interdit


class TestWarehouseRepository(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = WarehouseRepository(Path(self.tmp.name) / "test.db")

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_and_get_by_id(self):
        w = Warehouse(organisation_id="org-1", code="WH-01", name="Paris")
        created = self.repo.create(w)
        self.assertIsNotNone(created.id)
        fetched = self.repo.get_by_id(created.id)
        self.assertEqual(fetched.code, "WH-01")

    def test_unique_code_per_org(self):
        self.repo.create(Warehouse(organisation_id="org-1", code="WH-01", name="A"))
        with self.assertRaises(Exception):
            self.repo.create(Warehouse(organisation_id="org-1", code="WH-01", name="B"))

    def test_same_code_different_orgs_allowed(self):
        self.repo.create(Warehouse(organisation_id="org-1", code="WH-01", name="A"))
        w2 = self.repo.create(Warehouse(organisation_id="org-2", code="WH-01", name="B"))
        self.assertIsNotNone(w2.id)

    def test_list_by_organisation(self):
        self.repo.create(Warehouse(organisation_id="org-1", code="WH-01", name="A"))
        self.repo.create(Warehouse(organisation_id="org-1", code="WH-02", name="B"))
        self.repo.create(Warehouse(organisation_id="org-2", code="WH-01", name="C"))
        self.assertEqual(len(self.repo.list_by_organisation("org-1")), 2)

    def test_update_and_delete(self):
        w = self.repo.create(Warehouse(organisation_id="org-1", code="WH-01", name="A"))
        w = self.repo.update(Warehouse(**{**w.__dict__, "name": "Renommé"}))
        self.assertEqual(w.name, "Renommé")
        self.assertTrue(self.repo.delete(w.id))
        self.assertIsNone(self.repo.get_by_id(w.id))


if __name__ == "__main__":
    unittest.main()
