"""Tests unitaires du service Location."""
import os, tempfile, unittest
from engine.location_repository import LocationRepository
from engine.location_service import LocationService


class TestLocationService(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.repo = LocationRepository(db_path=self.db_path)
        self.service = LocationService(self.repo)

    def tearDown(self):
        os.unlink(self.db_path)

    @staticmethod
    def _defaults():
        return {
            "organisation_id": 'org-1',
            "warehouse_id": 'wh-1',
            "code": 'A-01-03',
            "name": 'Allée A, rayon 01, niveau 03',
            "zone": 'picking',
            "capacity": 100,        }

    def test_create(self):
        obj = self.service.create(**self._defaults())
        self.assertIsNotNone(self.service.get(obj.id))

    def test_get_inexistant(self):
        self.assertIsNone(self.service.get("loc-inexistant"))

    def test_list(self):
        self.service.create(**self._defaults())
        self.service.create(**self._defaults())
        self.assertEqual(len(self.service.list("org-1")), 2)

    def test_delete(self):
        obj = self.service.create(**self._defaults())
        self.assertTrue(self.service.delete(obj.id))
        self.assertIsNone(self.service.get(obj.id))

    def test_delete_inexistant(self):
        self.assertFalse(self.service.delete("loc-inexistant"))


if __name__ == "__main__":
    unittest.main()
