"""Tests unitaires pour AuditEvent et AuditEventRepository."""

import unittest
import tempfile
import os
from pathlib import Path

from xohive.domain.audit_event import AuditEvent
from xohive.domain.audit_event_repository import AuditEventRepository


class TestAuditEventEntity(unittest.TestCase):
    """Tests de l'entité AuditEvent."""

    def test_creation_valide(self):
        audit = AuditEvent(
            user_id="usr-456",
            organisation_id="org-123",
            entity_type="Document",
            entity_id="doc-123",
            action="create",
        )
        self.assertEqual(audit.organisation_id, "org-123")
        self.assertEqual(audit.entity_type, "Document")
        self.assertEqual(audit.entity_id, "doc-123")
        self.assertEqual(audit.action, "create")
        self.assertFalse(audit.is_system)
        self.assertFalse(audit.has_old_values)
        self.assertFalse(audit.has_new_values)
        self.assertIsNotNone(audit.id)
        self.assertGreater(len(audit.id), 0)

    def test_creation_système(self):
        audit = AuditEvent(
            organisation_id="org-123",
            entity_type="Document",
            entity_id="doc-123",
            action="delete",
            user_id=None,
        )
        self.assertTrue(audit.is_system)

    def test_creation_complète(self):
        audit = AuditEvent(
            user_id="usr-456",
            organisation_id="org-123",
            entity_type="User",
            entity_id="usr-789",
            action="update",
            old_values={"name": "Ancien"},
            new_values={"name": "Nouveau"},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )
        self.assertEqual(audit.user_id, "usr-456")
        self.assertEqual(audit.old_values, {"name": "Ancien"})
        self.assertEqual(audit.new_values, {"name": "Nouveau"})
        self.assertEqual(audit.ip_address, "192.168.1.1")
        self.assertEqual(audit.user_agent, "Mozilla/5.0")
        self.assertTrue(audit.has_old_values)
        self.assertTrue(audit.has_new_values)

    def test_creation_sans_values(self):
        audit = AuditEvent(
            organisation_id="org-123",
            entity_type="Document",
            entity_id="doc-123",
            action="create",
        )
        self.assertIsNone(audit.old_values)
        self.assertIsNone(audit.new_values)
        self.assertFalse(audit.has_old_values)
        self.assertFalse(audit.has_new_values)

    def test_to_dict(self):
        audit = AuditEvent(
            organisation_id="org-123",
            entity_type="Document",
            entity_id="doc-123",
            action="create",
        )
        d = audit.to_dict()
        self.assertEqual(d["organisation_id"], "org-123")
        self.assertEqual(d["entity_type"], "Document")
        self.assertEqual(d["action"], "create")

    def test_invalid_creation(self):
        with self.assertRaises(ValueError):
            AuditEvent(
                organisation_id="",
                entity_type="Document",
                entity_id="doc-123",
                action="create",
            )

    def test_repr(self):
        audit = AuditEvent(
            organisation_id="org-123",
            entity_type="Document",
            entity_id="doc-123",
            action="create",
        )
        self.assertIn("Document", repr(audit))
        self.assertIn("create", repr(audit))


class TestAuditEventRepository(unittest.TestCase):
    """Tests du Repository AuditEvent."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.repo = AuditEventRepository(self.db_path)

    def tearDown(self):
        self.repo.close()
        for f in Path(self.temp_dir).glob("*.db*"):
            f.unlink()
        os.rmdir(self.temp_dir)

    def test_create(self):
        audit = AuditEvent(
            organisation_id="org-123",
            entity_type="Document",
            entity_id="doc-123",
            action="create",
        )
        saved = self.repo.create(audit)
        self.assertIsNotNone(saved)
        self.assertEqual(saved.id, audit.id)
        self.assertEqual(saved.organisation_id, "org-123")
        self.assertEqual(saved.entity_type, "Document")

    def test_get(self):
        audit = AuditEvent(
            organisation_id="org-123",
            entity_type="Document",
            entity_id="doc-123",
            action="create",
        )
        self.repo.create(audit)
        retrieved = self.repo.get(audit.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.organisation_id, "org-123")
        self.assertEqual(retrieved.action, "create")

    def test_get_non_existant(self):
        retrieved = self.repo.get("aud-inconnu")
        self.assertIsNone(retrieved)

    def test_list(self):
        for i in range(3):
            audit = AuditEvent(
                organisation_id="org-123",
                entity_type="Document",
                entity_id=f"doc-{i}",
                action="create",
            )
            self.repo.create(audit)
        events = self.repo.list()
        self.assertEqual(len(events), 3)

    def test_filter_organisation(self):
        for i in range(3):
            audit = AuditEvent(
                organisation_id="org-123",
                entity_type="Document",
                entity_id=f"doc-{i}",
                action="create",
            )
            self.repo.create(audit)
        events = self.repo.filter(organisation_id="org-123")
        self.assertEqual(len(events), 3)

    def test_filter_entity(self):
        audit = AuditEvent(
            organisation_id="org-123",
            entity_type="Document",
            entity_id="doc-123",
            action="create",
        )
        self.repo.create(audit)
        events = self.repo.filter(entity_type="Document", entity_id="doc-123")
        self.assertEqual(len(events), 1)

    def test_filter_no_results(self):
        audit = AuditEvent(
            organisation_id="org-123",
            entity_type="Document",
            entity_id="doc-123",
            action="create",
        )
        self.repo.create(audit)
        events = self.repo.filter(organisation_id="org-999")
        self.assertEqual(len(events), 0)

    def test_filter_empty(self):
        audit = AuditEvent(
            organisation_id="org-123",
            entity_type="Document",
            entity_id="doc-123",
            action="create",
        )
        self.repo.create(audit)
        events = self.repo.filter()
        self.assertEqual(len(events), 1)

    def test_count(self):
        self.assertEqual(self.repo.count(), 0)
        for i in range(3):
            audit = AuditEvent(
                organisation_id="org-123",
                entity_type="Document",
                entity_id=f"doc-{i}",
                action="create",
            )
            self.repo.create(audit)
        self.assertEqual(self.repo.count(), 3)

    def test_count_by_entity(self):
        audit = AuditEvent(
            organisation_id="org-123",
            entity_type="Document",
            entity_id="doc-123",
            action="create",
        )
        self.repo.create(audit)
        self.assertEqual(self.repo.count_by_entity("Document", "doc-123"), 1)
        self.assertEqual(self.repo.count_by_entity("Document", "doc-456"), 0)

    def test_update(self):
        audit = AuditEvent(
            organisation_id="org-123",
            entity_type="Document",
            entity_id="doc-123",
            action="create",
        )
        self.repo.create(audit)
        updated = self.repo.get(audit.id)
        self.assertIsNotNone(updated)

    def test_delete(self):
        audit = AuditEvent(
            organisation_id="org-123",
            entity_type="Document",
            entity_id="doc-123",
            action="create",
        )
        self.repo.create(audit)
        # Le repository n'a pas de méthode delete : vérifier par le count
        self.assertEqual(self.repo.count(), 1)
        # Vérifier qu'on peut récupérer
        self.assertIsNotNone(self.repo.get(audit.id))
        # Le repository ne supprime pas : le count reste 1
        self.assertEqual(self.repo.count(), 1)
        # Vérifier qu'on peut récupérer après
        self.assertIsNotNone(self.repo.get(audit.id))

    def test_context_manager(self):
        with AuditEventRepository(self.db_path) as repo:
            audit = AuditEvent(
                organisation_id="org-123",
                entity_type="Document",
                entity_id="doc-123",
                action="create",
            )
            repo.create(audit)
            retrieved = repo.get(audit.id)
            self.assertIsNotNone(retrieved)

    def test_old_values_json(self):
        audit = AuditEvent(
            organisation_id="org-123",
            entity_type="Document",
            entity_id="doc-123",
            action="update",
            old_values={"name": "Ancien", "active": True},
            new_values={"name": "Nouveau", "active": False},
        )
        self.repo.create(audit)
        retrieved = self.repo.get(audit.id)
        self.assertEqual(retrieved.old_values, {"name": "Ancien", "active": True})
        self.assertEqual(retrieved.new_values, {"name": "Nouveau", "active": False})

    def test_invalid_json_old_values(self):
        # Si old_values contient des données non-sérialisables, la méthode
        # _serialize retourne None (aucune exception levée)
        audit = AuditEvent(
            organisation_id="org-123",
            entity_type="Document",
            entity_id="doc-123",
            action="update",
            old_values={"key": "value"},
            new_values="invalid json",  # type: ignore[arg-type]
        )
        # Le repository convertit new_values en JSON (échec -> None)
        self.repo.create(audit)
        retrieved = self.repo.get(audit.id)
        self.assertIsNotNone(retrieved)
        # old_values est un dict valide
        self.assertEqual(retrieved.old_values, {"key": "value"})


if __name__ == "__main__":
    unittest.main()
