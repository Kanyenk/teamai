"""Tests unitaires pour l'entité User et son Repository."""

import unittest
import tempfile
import os
from pathlib import Path

from xohive.domain.user import User
from xohive.domain.user_repository import UserRepository


class TestUserEntity(unittest.TestCase):
    """Tests de l'entité User."""

    def test_creation_valide(self):
        user = User(
            email="alice@acme.com",
            password_hash="hash123",
            organisation_id="org-test-123",
        )
        self.assertEqual(user.email, "alice@acme.com")
        self.assertEqual(user.is_active, True)
        self.assertFalse(user.is_verified)
        self.assertIsNotNone(user.id)
        self.assertGreater(len(user.id), 0)

    def test_creation_personnalisee(self):
        user = User(
            email="bob@acme.com",
            password_hash="hash456",
            organisation_id="org-test-456",
            first_name="Bob",
            last_name="Martin",
            phone="+33612345678",
            timezone="Europe/Paris",
            language="fr",
            is_active=True,
            is_verified=True,
            created_by="admin",
        )
        self.assertEqual(user.email, "bob@acme.com")
        self.assertEqual(user.first_name, "Bob")
        self.assertEqual(user.last_name, "Martin")
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_verified)
        self.assertEqual(user.organisation_id, "org-test-456")

    def test_email_invalide(self):
        with self.assertRaises(ValueError):
            User(email="invalid-email", password_hash="hash123", organisation_id="org-1")

    def test_email_vide(self):
        with self.assertRaises(ValueError):
            User(email="", password_hash="hash123", organisation_id="org-1")

    def test_password_hash_vide(self):
        with self.assertRaises(ValueError):
            User(email="alice@acme.com", password_hash="", organisation_id="org-1")

    def test_organisation_id_vide(self):
        with self.assertRaises(ValueError):
            User(email="alice@acme.com", password_hash="hash123", organisation_id="")

    def test_to_dict(self):
        user = User(
            email="alice@acme.com",
            password_hash="hash123",
            organisation_id="org-123",
            first_name="Alice",
            last_name="Martin",
            is_verified=True,
        )
        d = user.to_dict()
        self.assertEqual(d["email"], "alice@acme.com")
        self.assertTrue(d["is_verified"])
        self.assertEqual(d["first_name"], "Alice")

    def test_repr(self):
        user = User(email="alice@acme.com", password_hash="hash123", organisation_id="org-1")
        self.assertIn("alice@acme.com", repr(user))
        self.assertIn("usr-", repr(user))


class TestUserRepository(unittest.TestCase):
    """Tests du Repository User."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.repo = UserRepository(self.db_path)

    def tearDown(self):
        self.repo.close()
        for f in Path(self.temp_dir).glob("*.db*"):
            f.unlink()
        os.rmdir(self.temp_dir)

    def test_create(self):
        user = User(
            email="alice@acme.com",
            password_hash="hash123",
            organisation_id="org-test-123",
        )
        saved = self.repo.create(user)
        self.assertIsNotNone(saved)
        self.assertEqual(saved.id, user.id)
        self.assertEqual(saved.email, "alice@acme.com")

    def test_get(self):
        user = User(
            email="alice@acme.com",
            password_hash="hash123",
            organisation_id="org-test-123",
        )
        self.repo.create(user)
        retrieved = self.repo.get(user.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.email, "alice@acme.com")

    def test_get_non_existant(self):
        retrieved = self.repo.get("usr-inconnu")
        self.assertIsNone(retrieved)

    def test_list(self):
        for i in range(3):
            user = User(
                email=f"user{i}@acme.com",
                password_hash="hash",
                organisation_id="org-test",
            )
            self.repo.create(user)
        users = self.repo.list()
        self.assertEqual(len(users), 3)
        self.assertEqual(users[0].email, "user0@acme.com")

    def test_update(self):
        user = User(
            email="alice@acme.com",
            password_hash="hash123",
            organisation_id="org-test-123",
        )
        self.repo.create(user)
        user.email = "alice.new@acme.com"
        user.is_active = False
        updated = self.repo.update(user)
        self.assertEqual(updated.email, "alice.new@acme.com")
        self.assertFalse(updated.is_active)

    def test_delete(self):
        user = User(
            email="alice@acme.com",
            password_hash="hash123",
            organisation_id="org-test-123",
        )
        self.repo.create(user)
        deleted = self.repo.delete(user.id)
        self.assertTrue(deleted)
        self.assertIsNone(self.repo.get(user.id))

    def test_delete_non_existant(self):
        deleted = self.repo.delete("usr-inconnu")
        self.assertFalse(deleted)

    def test_list_requin(self):
        for i in range(5):
            user = User(
                email=f"user{i}@acme.com",
                password_hash="hash",
                organisation_id="org-test",
            )
            self.repo.create(user)
        users = self.repo.list()
        self.assertEqual(len(users), 5)

    def test_context_manager(self):
        with UserRepository(self.db_path) as repo:
            user = User(
                email="alice@acme.com",
                password_hash="hash123",
                organisation_id="org-test-123",
            )
            repo.create(user)
            retrieved = repo.get(user.id)
            self.assertIsNotNone(retrieved)


if __name__ == "__main__":
    unittest.main()
