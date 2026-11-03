"""Tests de la configuration de déploiement Docker."""

import os
import unittest


class TestDeploymentConfig(unittest.TestCase):
    """Vérifie l'existence et le contenu des fichiers de déploiement."""

    def test_dockerfile_exists(self):
        self.assertTrue(os.path.exists("Dockerfile"),
                        "Dockerfile manquant")

    def test_docker_compose_exists(self):
        self.assertTrue(os.path.exists("docker-compose.yml"),
                        "docker-compose.yml manquant")

    def test_dockerignore_exists(self):
        self.assertTrue(os.path.exists(".dockerignore"),
                        ".dockerignore manquant")

    def test_dockerfile_contains_base_image(self):
        with open("Dockerfile", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("python:3.12-slim", content,
                      "base image python:3.12-slim manquant")

    def test_dockerfile_exposes_port_8080(self):
        with open("Dockerfile", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("EXPOSE 8080", content,
                      "EXPOSE 8080 manquant")

    def test_compose_has_teamai_api_service(self):
        with open("docker-compose.yml", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("teamai-api", content,
                      "service teamai-api manquant")

    def test_compose_maps_port_8080(self):
        with open("docker-compose.yml", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("8080:8080", content,
                      "port mapping 8080:8080 manquant")

    def test_compose_has_data_volume(self):
        with open("docker-compose.yml", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("./data:/app/data", content,
                      "volume ./data:/app/data manquant")

    def test_compose_has_db_path_env(self):
        with open("docker-compose.yml", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("TEAMAI_DB_PATH=/app/data/teamai.db", content,
                      "variable TEAMAI_DB_PATH manquante")

    def test_compose_has_tokens_env(self):
        with open("docker-compose.yml", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("TEAMAI_TOKENS", content,
                      "variable TEAMAI_TOKENS manquante")

    def test_compose_has_restart_policy(self):
        with open("docker-compose.yml", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("restart: unless-stopped", content,
                      "restart policy manquante")

    def test_dockerignore_exists(self):
        self.assertTrue(os.path.exists(".dockerignore"),
                        ".dockerignore manquant")

    def test_dockerignore_excludes_git(self):
        with open(".dockerignore", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(".git", content,
                      ".git exclu manquant")

    def test_dockerignore_excludes_venv(self):
        with open(".dockerignore", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(".venv", content,
                      ".venv exclu manquant")

    def test_dockerignore_excludes_data(self):
        with open(".dockerignore", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("data", content,
                      "dossier data exclu manquant")


if __name__ == "__main__":
    unittest.main()
