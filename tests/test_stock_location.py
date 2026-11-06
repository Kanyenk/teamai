"""Tests du modèle et du repository StockLocation."""
import tempfile
import unittest
from pathlib import Path

from xohive.wms.domain.stock_location import StockLocation
from xohive.wms.repository.stock_location_repository import StockLocationRepository


class TestStockLocationModel(unittest.TestCase):
    def test_valid_location(self):
        loc = StockLocation(organisation_id="org-1", warehouse_id="wh-1", code="A-01-01")
        self.assertEqual(loc.code, "A-01-01")

    def test_missing_code_raises(self):
        with self.assertRaises(ValueError):
            StockLocation(organisation_id="org-1", warehouse_id="wh-1", code="")

    def test_missing_warehouse_raises(self):
        with self.assertRaises(ValueError):
            StockLocation(organisation_id="org-1", warehouse_id="", code="A-01-01")

    def test_to_dict(self):
        loc = StockLocation(organisation_id="org-1", warehouse_id="wh-1", code="A-01-01", name="Zone A")
        d = loc.to_dict()
        self.assertEqual(d["code"], "A-01-01")


class TestStockLocationRepository(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = StockLocationRepository(Path(self.tmp.name) / "test.db")

    def tearDown(self):
        self.repo.close()
        self.tmp.cleanup()

    def test_create_and_get_by_id(self):
        loc = StockLocation(organisation_id="org-1", warehouse_id="wh-1", code="A-01-01")
        created = self.repo.create(loc)
        fetched = self.repo.get_by_id(created.id)
        self.assertEqual(fetched.code, "A-01-01")

    def test_list_by_organisation(self):
        self.repo.create(StockLocation(organisation_id="org-1", warehouse_id="wh-1", code="A-01-01"))
        self.repo.create(StockLocation(organisation_id="org-2", warehouse_id="wh-2", code="B-01-01"))
        result = self.repo.list(organisation_id="org-1")
        self.assertEqual(len(result), 1)

    def test_list_by_warehouse(self):
        self.repo.create(StockLocation(organisation_id="org-1", warehouse_id="wh-1", code="A-01-01"))
        self.repo.create(StockLocation(organisation_id="org-1", warehouse_id="wh-2", code="B-01-01"))
        result = self.repo.list(warehouse_id="wh-1")
        self.assertEqual(len(result), 1)

    def test_update_and_delete(self):
        loc = self.repo.create(StockLocation(organisation_id="org-1", warehouse_id="wh-1", code="A-01-01"))
        loc.name = "Zone A"
        self.repo.update(loc)
        fetched = self.repo.get_by_id(loc.id)
        self.assertEqual(fetched.name, "Zone A")
        self.assertTrue(self.repo.delete(loc.id))
        self.assertIsNone(self.repo.get_by_id(loc.id))


if __name__ == "__main__":
    unittest.main()
