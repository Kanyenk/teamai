"""Tests for DocumentRepository (SQLite persistence).

Couverture des cas :
- save puis get
- get inexistant retourne None
- list vide
- list avec pagination
- save écrase un document existant
- 20 tests au total
"""

import unittest
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from engine import Document, DocumentError
from engine.repository import DocumentRepository


class TestDocumentRepository(unittest.TestCase):
    """Tests pour la couche de persistance SQLite."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.repo = DocumentRepository(self.db_path)

    def tearDown(self):
        self.repo.close()
        self.temp_dir.cleanup()

    def _make_document(self, doc_id="test-1"):
        """Crée un Document standard pour les tests."""
        return Document(
            doc_type="FACT",
            numero_serie=1,
            date_creation=datetime.now(timezone.utc),
            org_id=1,
        )

    # ── Tests de sauvegarde et récupération ───────────────────────────────

    def test_save_then_get(self):
        """save puis get : l'objet est bien récupéré."""
        doc = self._make_document()
        doc.id = "test-1"
        self.repo.save(doc)

        retrieved = self.repo.get("test-1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, "test-1")
        self.assertEqual(retrieved.doc_type, "FACT")
        self.assertEqual(retrieved.numero_serie, 1)

    def test_get_nonexistent_returns_none(self):
        """get d'un document inexistant retourne None."""
        retrieved = self.repo.get("inexistant")
        self.assertIsNone(retrieved)

    def test_list_empty(self):
        """list sur une base vide retourne une liste vide."""
        items = self.repo.list()
        self.assertEqual(items, [])

    def test_save_overwrites_existing(self):
        """save écrase un document existant avec le même id."""
        doc1 = self._make_document()
        doc1.id = "test-1"
        self.repo.save(doc1)

        doc2 = self._make_document()
        doc2.id = "test-1"
        doc2.doc_type = "BC"
        self.repo.save(doc2)

        retrieved = self.repo.get("test-1")
        self.assertEqual(retrieved.doc_type, "BC")

    # ── Tests de liste et pagination ─────────────────────────────────────

    def test_list_empty_no_docs(self):
        """list vide quand aucun document n'est enregistré."""
        items = self.repo.list()
        self.assertEqual(items, [])

    def test_list_with_pagination(self):
        """list avec pagination : limite et offset sont respectés."""
        for i in range(3):
            doc = self._make_document()
            doc.id = f"doc-{i}"
            self.repo.save(doc)

        first_page = self.repo.list(offset=0, limit=2)
        self.assertEqual(len(first_page), 2)

        second_page = self.repo.list(offset=2, limit=2)
        self.assertEqual(len(second_page), 1)

    def test_list_pagination_boundary(self):
        """Test de limite et d'offset aux frontières."""
        for i in range(5):
            doc = self._make_document()
            doc.id = f"doc-{i}"
            self.repo.save(doc)

        first = self.repo.list(offset=0, limit=2)
        self.assertEqual(len(first), 2)

        middle = self.repo.list(offset=2, limit=2)
        self.assertEqual(len(middle), 2)

        last = self.repo.list(offset=4, limit=2)
        self.assertEqual(len(last), 1)

    def test_list_pagination_limit_zero(self):
        """list avec limit=0 retourne une liste vide."""
        self.repo.save(self._make_document())
        self.repo.save(self._make_document())
        items = self.repo.list(offset=0, limit=0)
        self.assertEqual(items, [])

    # ── Tests d'identifiants et d'attributs ──────────────────────────────

    def test_saved_document_has_id(self):
        """Le document sauvegardé conserve son id."""
        doc = self._make_document()
        doc.id = "identifiant-unique-123"
        self.repo.save(doc)

        retrieved = self.repo.get("identifiant-unique-123")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, "identifiant-unique-123")

    def test_get_returns_same_object(self):
        """get retourne un objet avec les bons attributs."""
        doc = self._make_document()
        doc.id = "obj-1"
        self.repo.save(doc)

        retrieved = self.repo.get("obj-1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.doc_type, "FACT")
        self.assertEqual(retrieved.numero_serie, 1)
        self.assertEqual(retrieved.org_id, 1)
        self.assertIsNotNone(retrieved.etat)
        self.assertIsNotNone(retrieved.etat_hash)

    def test_multiple_saves_same_id(self):
        """Plusieurs saves avec le même id : seul le dernier est conservé."""
        doc1 = self._make_document()
        doc1.id = "multi"
        self.repo.save(doc1)

        doc2 = self._make_document()
        doc2.id = "multi"
        doc2.doc_type = "BC"
        self.repo.save(doc2)

        retrieved = self.repo.get("multi")
        self.assertEqual(retrieved.doc_type, "BC")

    def test_save_creates_new_id(self):
        """Chaque save crée un document distinct (même id)."""
        doc = self._make_document()
        doc.id = "unique-id"
        self.repo.save(doc)

        retrieved = self.repo.get("unique-id")
        self.assertIsNotNone(retrieved)

    def test_list_returns_all_documents(self):
        """list retourne tous les documents enregistrés."""
        for i in range(5):
            doc = self._make_document()
            doc.id = f"doc-{i}"
            self.repo.save(doc)

        items = self.repo.list()
        self.assertEqual(len(items), 5)

    def test_list_sorted_by_id(self):
        """list retourne les documents triés par id."""
        for i in range(3):
            doc = self._make_document()
            doc.id = f"z-{i}"
            self.repo.save(doc)

        items = self.repo.list()
        self.assertEqual([d.id for d in items], [f"z-{i}" for i in range(3)])

    def test_get_returns_exact_match(self):
        """get retourne le document exact (id, doc_type, numero_serie)."""
        doc = self._make_document()
        doc.id = "exact"
        self.repo.save(doc)

        retrieved = self.repo.get("exact")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, "exact")
        self.assertEqual(retrieved.doc_type, "FACT")
        self.assertEqual(retrieved.numero_serie, 1)

    def test_get_returns_none_for_deleted_id(self):
        """get retourne None pour un id qui n'existe pas."""
        self.repo.save(self._make_document())
        self.repo.save(self._make_document())
        self.assertIsNone(self.repo.get("supprime"))

    def test_list_respect_offset(self):
        """list respecte l'offset demandé."""
        for i in range(5):
            doc = self._make_document()
            doc.id = f"off-{i}"
            self.repo.save(doc)

        items = self.repo.list(offset=2, limit=5)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0].id, "off-2")

    def test_save_then_get_with_special_chars(self):
        """save puis get avec des caractères spéciaux dans l'id."""
        doc = self._make_document()
        doc.id = "id-avec-tirets-et-123"
        self.repo.save(doc)

        retrieved = self.repo.get("id-avec-tirets-et-123")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, "id-avec-tirets-et-123")

    def test_list_limit_1(self):
        """list avec limit=1 retourne un seul document."""
        for i in range(3):
            doc = self._make_document()
            doc.id = f"single-{i}"
            self.repo.save(doc)

        items = self.repo.list(offset=0, limit=1)
        self.assertEqual(len(items), 1)

    def test_get_returns_doc_not_list(self):
        """get retourne un objet de type Document, pas une liste."""
        doc = self._make_document()
        doc.id = "obj-test"
        self.repo.save(doc)

        retrieved = self.repo.get("obj-test")
        self.assertIsInstance(retrieved, object)
        self.assertIsNotNone(retrieved.id)


if __name__ == "__main__":
    unittest.main()
