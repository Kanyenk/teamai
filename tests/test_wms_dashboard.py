"""Tests du dashboard WMS minimal (page HTML avec liens CSV)."""

import json
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from http.server import HTTPServer
from pathlib import Path

from engine.http import HttpHandler, make_app
from engine.auth import TokenAuth
from engine.repository import DocumentRepository


class TestWmsDashboard(unittest.TestCase):
    """Tests de la route GET /wms (dashboard HTML)."""

    def setUp(self):
        # Créer un dépôt temporaire et un serveur HTTP de test.
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = DocumentRepository(Path(self.tmp.name) / "test.db")
        self.auth = TokenAuth({"test-token"})
        self.server = HTTPServer(("127.0.0.1", 0), make_app(self.repo, auth=self.auth))
        self.server.store = self.repo
        self.server.auth = self.auth
        # Désactiver les logs HTTP pour garder la sortie de test propre.
        HttpHandler.log_message = lambda self, *a, **k: None
        # Démarrer le serveur dans un thread daemon.
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        # Arrêter la boucle serve_forever.
        self.server.shutdown()
        # Fermer la socket d'écoute (évite les ResourceWarning).
        self.server.server_close()
        # Nettoyer le répertoire temporaire.
        self.tmp.cleanup()

    def test_dashboard_returns_html(self):
        """GET /wms avec token valide doit renvoyer du HTML 200."""
        req = urllib.request.Request(
            self.base + "/wms",
            headers={"Authorization": "Bearer test-token"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(r.headers.get("Content-Type"), "text/html; charset=utf-8")
            body = r.read().decode("utf-8")
            self.assertIn("WMS - Dashboard", body)
            self.assertIn("/api/v1/wms/stock-dashboard?format=csv", body)

    def test_dashboard_without_token_returns_401(self):
        """GET /wms sans token doit renvoyer 401."""
        req = urllib.request.Request(self.base + "/wms")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=10)
        self.assertEqual(ctx.exception.code, 401)


if __name__ == "__main__":
    unittest.main()
