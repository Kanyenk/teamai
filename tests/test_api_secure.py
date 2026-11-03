"""Tests unitaires pour l'API HTTP sécurisée."""

import unittest
import tempfile
import shutil
from pathlib import Path

from engine.auth import TokenAuth
from engine.repository import DocumentRepository


class TestSecureApiLogic(unittest.TestCase):
    """Tests de la logique d'API sécurisée (sans handler réseau)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.store = DocumentRepository(self.db_path)
        self.auth = TokenAuth({"valid_token"})

    def tearDown(self):
        self.store.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_token_auth_accepts_valid_token(self):
        """Un token valide est accepté."""
        self.assertTrue(self.auth.authenticate("Bearer valid_token"))

    def test_token_auth_rejects_invalid_token(self):
        """Un token invalide est rejeté."""
        self.assertFalse(self.auth.authenticate("Bearer invalid"))

    def test_token_auth_rejects_no_token(self):
        """Aucun token n'est rejeté."""
        self.assertFalse(self.auth.authenticate(None))

    def test_token_auth_rejects_wrong_prefix(self):
        """Un token avec mauvais préfixe est rejeté."""
        self.assertFalse(self.auth.authenticate("Basic abc123"))

    def test_token_auth_requires_two_parts(self):
        """Le token doit être au format 'Bearer <token>'."""
        self.assertFalse(self.auth.authenticate("Bearer"))
        self.assertFalse(self.auth.authenticate("Token abc123"))


if __name__ == "__main__":
    unittest.main()
