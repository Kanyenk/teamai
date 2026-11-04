"""Tests unitaires pour Activity et ActivityRepository."""

import unittest
import tempfile
import shutil
from pathlib import Path

from xohive.crm.domain.activity import Activity, ActivityError
from xohive.crm.repository.activity_repository import ActivityRepository


class TestActivityEntity(unittest.TestCase):
    """Tests de l'entité Activity."""

    def test_creation_valide(self):
        act = Activity(
            organisation_id="org-123",
            company_id="crm-001",
            subject="Appel client",
            date="2026-11-04T10:00:00Z",
        )
        self.assertEqual(act.subject, "Appel client")
        self.assertEqual(act.type, Activity.TYPE_CALL)
        self.assertEqual(act.status, Activity.STATUS_PENDING)
        self.assertIsNotNone(act.id)

    def test_creation_personnalisee(self):
        act = Activity(
            organisation_id="org-123",
            company_id="crm-001",
            contact_id="crm-002",
            user_id="usr-456",
            type=Activity.TYPE_MEETING,
            subject="Réunion d'équipe",
            description="Réunion mensuelle",
            date="2026-11-05T14:00:00Z",
            duration=60.0,
            status=Activity.STATUS_PENDING,
            is_active=True,
            created_by="admin",
        )
        self.assertEqual(act.type, Activity.TYPE_MEETING)
        self.assertEqual(act.duration, 60.0)

    def test_creation_type_invalide(self):
        with self.assertRaises(ActivityError):
            Activity(
                organisation_id="org-123",
                company_id="crm-001",
                subject="Test",
                date="2026-11-04T10:00:00Z",
                type="invalide",
            )

    def test_creation_status_invalide(self):
        with self.assertRaises(ActivityError):
            Activity(
                organisation_id="org-123",
                company_id="crm-001",
                subject="Test",
                date="2026-11-04T10:00:00Z",
                status="invalide",
            )

    def test_creation_date_invalide(self):
        with self.assertRaises(ActivityError):
            Activity(
                organisation_id="org-123",
                company_id="crm-001",
                subject="Test",
                date="2026-11-04",
            )

    def test_creation_duration_negatif(self):
        with self.assertRaises(ActivityError):
            Activity(
                organisation_id="org-123",
                company_id="crm-001",
                subject="Test",
                date="2026-11-04T10:00:00Z",
                duration=-10.0,
            )

    def test_subject_vide(self):
        with self.assertRaises(ActivityError):
            Activity(
                organisation_id="org-123",
                company_id="crm-001",
                subject="",
                date="2026-11-04T10:00:00Z",
            )

    def test_mark_done(self):
        act = Activity(
            organisation_id="org-123",
            company_id="crm-001",
            subject="Test",
            date="2026-11-04T10:00:00Z",
        )
        self.assertEqual(act.status, Activity.STATUS_PENDING)
        act.mark_done()
        self.assertEqual(act.status, Activity.STATUS_DONE)

    def test_mark_cancelled(self):
        act = Activity(
            organisation_id="org-123",
            company_id="crm-001",
            subject="Test",
            date="2026-11-04T10:00:00Z",
        )
        act.mark_cancelled()
        self.assertEqual(act.status, Activity.STATUS_CANCELLED)

    def test_to_dict(self):
        act = Activity(
            organisation_id="org-123",
            company_id="crm-001",
            subject="Test",
            date="2026-11-04T10:00:00Z",
            is_active=False,
        )
        d = act.to_dict()
        self.assertEqual(d["subject"], "Test")
        self.assertFalse(d["is_active"])

    def test_repr(self):
        act = Activity(
            organisation_id="org-123",
            company_id="crm-001",
            subject="Test",
            date="2026-11-04T10:00:00Z",
        )
        self.assertIn("Activity", repr(act))


class TestActivityRepository(unittest.TestCase):
    """Tests du repository Activity."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.repo = ActivityRepository(self.db_path)

    def tearDown(self):
        self.repo.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create(self):
        act = Activity(
            organisation_id="org-123",
            company_id="crm-001",
            subject="Appel client",
            date="2026-11-04T10:00:00Z",
        )
        saved = self.repo.create(act)
        self.assertIsNotNone(saved)
        self.assertEqual(saved.subject, "Appel client")

    def test_get(self):
        act = Activity(
            organisation_id="org-123",
            company_id="crm-001",
            subject="Appel client",
            date="2026-11-04T10:00:00Z",
        )
        self.repo.create(act)
        retrieved = self.repo.get(act.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.subject, "Appel client")

    def test_get_non_existant(self):
        with self.assertRaises(ActivityError):
            self.repo.get("crm-inconnu")

    def test_update(self):
        act = Activity(
            organisation_id="org-123",
            company_id="crm-001",
            subject="Appel client",
            date="2026-11-04T10:00:00Z",
        )
        self.repo.create(act)
        act.subject = "Appel suppléant"
        act.updated_at = act._now_iso()
        updated = self.repo.update(act)
        self.assertEqual(updated.subject, "Appel suppléant")

    def test_delete(self):
        act = Activity(
            organisation_id="org-123",
            company_id="crm-001",
            subject="Appel client",
            date="2026-11-04T10:00:00Z",
        )
        self.repo.create(act)
        result = self.repo.delete(act.id)
        self.assertTrue(result)
        with self.assertRaises(ActivityError):
            self.repo.get(act.id)

    def test_list(self):
        for i in range(3):
            act = Activity(
                organisation_id="org-123",
                company_id="crm-001",
                subject=f"Appel {i}",
                date="2026-11-04T10:00:00Z",
            )
            self.repo.create(act)
        acts = self.repo.list()
        self.assertEqual(len(acts), 3)

    def test_list_empty(self):
        acts = self.repo.list()
        self.assertEqual(len(acts), 0)


if __name__ == "__main__":
    unittest.main()
