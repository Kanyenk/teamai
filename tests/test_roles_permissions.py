"""Tests unitaires pour Role, Permission et leurs repositories."""

import unittest
import tempfile
import os
from pathlib import Path

from xohive.domain.role import Role
from xohive.domain.role_repository import RoleRepository
from xohive.domain.permission import Permission
from xohive.domain.permission_repository import PermissionRepository


class TestRoleEntity(unittest.TestCase):
    """Tests de l'entité Role."""

    def test_creation_valide(self):
        role = Role(
            code="admin",
            label="Administrateur",
            organisation_id="org-test-123",
        )
        self.assertEqual(role.code, "admin")
        self.assertEqual(role.label, "Administrateur")
        self.assertEqual(role.permissions, [])
        self.assertIsNotNone(role.id)
        self.assertIn("rol-", role.id)

    def test_creation_personnalisee(self):
        role = Role(
            code="auditor",
            label="Auditeur",
            description="Utilisateur lecture seule",
            organisation_id="org-test-456",
            permissions=["doc:read", "audit:read"],
            created_by="system",
        )
        self.assertEqual(role.code, "auditor")
        self.assertEqual(role.label, "Auditeur")
        self.assertEqual(role.description, "Utilisateur lecture seule")
        self.assertEqual(role.permissions, ["doc:read", "audit:read"])

    def test_code_vide(self):
        with self.assertRaises(ValueError):
            Role(code="", label="Test", organisation_id="org-1")

    def test_label_vide(self):
        with self.assertRaises(ValueError):
            Role(code="admin", label="", organisation_id="org-1")

    def test_organisation_id_vide(self):
        with self.assertRaises(ValueError):
            Role(code="admin", label="Test", organisation_id="")

    def test_add_permission(self):
        role = Role(code="admin", label="Admin", organisation_id="org-1")
        role.add_permission("doc:create")
        role.add_permission("doc:read")
        self.assertEqual(role.permissions, ["doc:create", "doc:read"])

    def test_add_permission_doublon(self):
        role = Role(code="admin", label="Admin", organisation_id="org-1")
        role.add_permission("doc:create")
        role.add_permission("doc:create")  # doublon
        self.assertEqual(role.permissions, ["doc:create"])

    def test_remove_permission(self):
        role = Role(
            code="admin", label="Admin", organisation_id="org-1",
            permissions=["doc:create", "doc:read"],
        )
        role.remove_permission("doc:create")
        self.assertEqual(role.permissions, ["doc:read"])

    def test_remove_non_existant(self):
        role = Role(code="admin", label="Admin", organisation_id="org-1")
        role.remove_permission("doc:create")  # inexistant, sans erreur
        self.assertEqual(role.permissions, [])

    def test_has_permission(self):
        role = Role(
            code="admin", label="Admin", organisation_id="org-1",
            permissions=["doc:create", "doc:read"],
        )
        self.assertTrue(role.has_permission("doc:create"))
        self.assertTrue(role.has_permission("doc:read"))
        self.assertFalse(role.has_permission("audit:read"))

    def test_to_dict(self):
        role = Role(
            code="admin", label="Admin", organisation_id="org-1",
            permissions=["doc:create"],
        )
        d = role.to_dict()
        self.assertEqual(d["code"], "admin")
        self.assertEqual(d["permissions"], ["doc:create"])

    def test_repr(self):
        role = Role(code="admin", label="Admin", organisation_id="org-1")
        self.assertIn("admin", repr(role))
        self.assertIn("rol-", repr(role))


class TestRoleRepository(unittest.TestCase):
    """Tests du Repository Role."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.repo = RoleRepository(self.db_path)

    def tearDown(self):
        self.repo.close()
        for f in Path(self.temp_dir).glob("*.db*"):
            f.unlink()
        os.rmdir(self.temp_dir)

    def test_create(self):
        role = Role(code="admin", label="Administrateur", organisation_id="org-1")
        saved = self.repo.create(role)
        self.assertIsNotNone(saved)
        self.assertEqual(saved.id, role.id)
        self.assertEqual(saved.code, "admin")

    def test_get(self):
        role = Role(code="admin", label="Administrateur", organisation_id="org-1")
        self.repo.create(role)
        retrieved = self.repo.get(role.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.code, "admin")

    def test_get_non_existant(self):
        retrieved = self.repo.get("rol-inconnu")
        self.assertIsNone(retrieved)

    def test_list(self):
        for i in range(2):
            role = Role(code=f"role{i}", label=f"Rôle {i}", organisation_id="org-1")
            self.repo.create(role)
        roles = self.repo.list()
        self.assertEqual(len(roles), 2)

    def test_update(self):
        role = Role(code="admin", label="Administrateur", organisation_id="org-1")
        self.repo.create(role)
        role.label = "Admin"
        role.permissions.append("doc:read")
        updated = self.repo.update(role)
        self.assertEqual(updated.label, "Admin")
        self.assertIn("doc:read", updated.permissions)

    def test_delete(self):
        role = Role(code="admin", label="Administrateur", organisation_id="org-1")
        self.repo.create(role)
        deleted = self.repo.delete(role.id)
        self.assertTrue(deleted)
        self.assertIsNone(self.repo.get(role.id))

    def test_delete_non_existant(self):
        deleted = self.repo.delete("rol-inconnu")
        self.assertFalse(deleted)

    def test_list_requin(self):
        for i in range(5):
            role = Role(code=f"role{i}", label=f"Rôle {i}", organisation_id="org-1")
            self.repo.create(role)
        roles = self.repo.list()
        self.assertEqual(len(roles), 5)

    def test_context_manager(self):
        with RoleRepository(self.db_path) as repo:
            role = Role(code="admin", label="Administrateur", organisation_id="org-1")
            repo.create(role)
            retrieved = repo.get(role.id)
            self.assertIsNotNone(retrieved)


class TestPermissionEntity(unittest.TestCase):
    """Tests de l'entité Permission."""

    def test_creation_valide(self):
        perm = Permission(
            code="doc:create",
            label="Créer un document",
            module="doc",
            action="create",
            organisation_id="org-1",
        )
        self.assertEqual(perm.code, "doc:create")
        self.assertEqual(perm.label, "Créer un document")
        self.assertEqual(perm.module, "doc")
        self.assertEqual(perm.action, "create")
        self.assertIsNotNone(perm.id)
        self.assertIn("per-", perm.id)

    def test_code_invalide(self):
        with self.assertRaises(ValueError):
            Permission(code="docreate", label="Test", module="doc", action="create", organisation_id="org-1")

    def test_module_vide(self):
        with self.assertRaises(ValueError):
            Permission(code="doc:create", label="Test", module="", action="create", organisation_id="org-1")

    def test_action_vide(self):
        with self.assertRaises(ValueError):
            Permission(code="doc:create", label="Test", module="doc", action="", organisation_id="org-1")

    def test_to_dict(self):
        perm = Permission(
            code="doc:create",
            label="Créer un document",
            module="doc",
            action="create",
            organisation_id="org-1",
        )
        d = perm.to_dict()
        self.assertEqual(d["code"], "doc:create")
        self.assertEqual(d["module"], "doc")
        self.assertEqual(d["action"], "create")

    def test_repr(self):
        perm = Permission(code="doc:create", label="Test", module="doc", action="create", organisation_id="org-1")
        self.assertIn("doc:create", repr(perm))
        self.assertIn("per-", repr(perm))


class TestPermissionRepository(unittest.TestCase):
    """Tests du Repository Permission."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.repo = PermissionRepository(self.db_path)

    def tearDown(self):
        self.repo.close()
        for f in Path(self.temp_dir).glob("*.db*"):
            f.unlink()
        os.rmdir(self.temp_dir)

    def test_create(self):
        perm = Permission(
            code="doc:create",
            label="Créer un document",
            module="doc",
            action="create",
            organisation_id="org-1",
        )
        saved = self.repo.create(perm)
        self.assertIsNotNone(saved)
        self.assertEqual(saved.id, perm.id)
        self.assertEqual(saved.code, "doc:create")

    def test_get(self):
        perm = Permission(
            code="doc:create",
            label="Créer un document",
            module="doc",
            action="create",
            organisation_id="org-1",
        )
        self.repo.create(perm)
        retrieved = self.repo.get(perm.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.code, "doc:create")

    def test_get_non_existant(self):
        retrieved = self.repo.get("per-inconnu")
        self.assertIsNone(retrieved)

    def test_list(self):
        for i in range(2):
            perm = Permission(
                code=f"doc:{i}",
                label=f"DOC {i}",
                module="doc",
                action="create",
                organisation_id="org-1",
            )
            self.repo.create(perm)
        perms = self.repo.list()
        self.assertEqual(len(perms), 2)

    def test_update(self):
        perm = Permission(
            code="doc:create",
            label="Créer un document",
            module="doc",
            action="create",
            organisation_id="org-1",
        )
        self.repo.create(perm)
        perm.label = "Créer un document (nouveau)"
        perm.module = "document"
        updated = self.repo.update(perm)
        self.assertEqual(updated.label, "Créer un document (nouveau)")
        self.assertEqual(updated.module, "document")

    def test_delete(self):
        perm = Permission(
            code="doc:create",
            label="Créer un document",
            module="doc",
            action="create",
            organisation_id="org-1",
        )
        self.repo.create(perm)
        deleted = self.repo.delete(perm.id)
        self.assertTrue(deleted)
        self.assertIsNone(self.repo.get(perm.id))

    def test_delete_non_existant(self):
        deleted = self.repo.delete("per-inconnu")
        self.assertFalse(deleted)

    def test_list_requin(self):
        for i in range(5):
            perm = Permission(
                code=f"doc:{i}",
                label=f"DOC {i}",
                module="doc",
                action="create",
                organisation_id="org-1",
            )
            self.repo.create(perm)
        perms = self.repo.list()
        self.assertEqual(len(perms), 5)

    def test_context_manager(self):
        with PermissionRepository(self.db_path) as repo:
            perm = Permission(
                code="doc:create",
                label="Créer un document",
                module="doc",
                action="create",
                organisation_id="org-1",
            )
            repo.create(perm)
            retrieved = repo.get(perm.id)
            self.assertIsNotNone(retrieved)


if __name__ == "__main__":
    unittest.main()
