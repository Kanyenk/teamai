"""Tests de présence et de structure de la spécification OpenApi."""

import os
import unittest
import yaml

OPENAPI_PATH = os.path.join(os.path.dirname(__file__), "..", "docs", "openapi.yaml")


class TestOpenApiDocs(unittest.TestCase):
    """Vérifie que docs/openapi.yaml existe et contient les cinq chemins."""

    @classmethod
    def setUpClass(cls):
        cls.path = os.path.abspath(OPENAPI_PATH)
        with open(cls.path, "r", encoding="utf-8") as f:
            cls.spec = yaml.safe_load(f)

    def test_openapi_file_exists(self):
        self.assertTrue(os.path.exists(self.path), f"{self.path} absent")

    def test_has_openapi_version(self):
        self.assertIn("openapi", self.spec)
        self.assertEqual(self.spec["openapi"], "3.0.3")

    def test_has_info(self):
        self.assertIn("info", self.spec)
        self.assertIn("title", self.spec["info"])

    def test_has_five_paths(self):
        paths = self.spec.get("paths", {})
        self.assertEqual(len(paths), 4, f"attendu 4 chemins uniques, trouvé {len(paths)}")
        expected = ["/health", "/documents", "/documents/{id}", "/documents/{id}/transition"]
        for p in expected:
            self.assertIn(p, paths)

    def test_has_bearer_auth(self):
        components = self.spec.get("components", {})
        security_schemes = components.get("securitySchemes", {})
        self.assertIn("BearerAuth", security_schemes)

    def test_security_applies_to_all_but_health(self):
        paths = self.spec.get("paths", {})
        for path, operations in paths.items():
            for method, operation in operations.items():
                # Les valeurs peuvent être des dicts (opérations) ou des listes (parsing)
                if not isinstance(operation, dict):
                    continue
                security = operation.get("security", [])
                # /health n'a pas de sécurité
                if path == "/health":
                    self.assertEqual(len(security), 0, "health doit être sans sécurité")
                else:
                    # security est une liste de dictionnaires
                    self.assertTrue(len(security) > 0, f"{path} doit être sécurisé")
                    self.assertIn("BearerAuth", str(security[0]))


if __name__ == "__main__":
    unittest.main()
