"""Tests unitaires pour Document et DocumentRepository."""

import unittest
import tempfile
import os
import shutil
from pathlib import Path

from xohive.domain.document import Document, DocumentError
from xohive.domain.document_repository import DocumentRepository


class TestDocumentEntity(unittest.TestCase):
    """Tests de l'entité Document."""

    def test_creation_valide(self):
        doc = Document(
            organisation_id="org-123",
            doc_type="FACT",
            numero_serie=123,
        )
        self.assertEqual(doc.doc_type, "FACT")
        self.assertEqual(doc.numero_serie, 123)
        self.assertEqual(doc.etat, Document.STATE_DRAFT)
        self.assertIsNotNone(doc.id)
        self.assertGreater(len(doc.id), 0)

    def test_creation_sans_id(self):
        doc = Document(
            organisation_id="org-123",
            doc_type="BC",
            numero_serie=456,
        )
        self.assertTrue(doc.id.startswith("doc-"))

    def test_creation_avec_id(self):
        doc = Document(
            id="custom-id",
            organisation_id="org-123",
            doc_type="NC",
            numero_serie=789,
        )
        self.assertEqual(doc.id, "custom-id")

    def test_creation_avec_user(self):
        doc = Document(
            organisation_id="org-123",
            doc_type="RS",
            numero_serie=999,
            user_id="usr-789",
        )
        self.assertEqual(doc.user_id, "usr-789")

    def test_creation_avec_date_creation(self):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        doc = Document(
            organisation_id="org-123",
            doc_type="NC",
            numero_serie=42,
            created_at=now,
        )
        self.assertEqual(doc.created_at, now)

    def test_creation_type_invalide(self):
        with self.assertRaises(DocumentError):
            Document(
                organisation_id="org-123",
                doc_type="INVALID",
                numero_serie=1,
            )

    def test_creation_numero_serie_negatif(self):
        with self.assertRaises(DocumentError):
            Document(
                organisation_id="org-123",
                doc_type="FACT",
                numero_serie=-1,
            )

    def test_creation_balance_negative(self):
        with self.assertRaises(DocumentError):
            Document(
                organisation_id="org-123",
                doc_type="FACT",
                numero_serie=1,
                balance=-100,
            )

    def test_creation_currency_invalid(self):
        with self.assertRaises(DocumentError):
            Document(
                organisation_id="org-123",
                doc_type="FACT",
                numero_serie=1,
                currency="EURX",
            )

    def test_to_dict(self):
        doc = Document(
            organisation_id="org-123",
            doc_type="FACT",
            numero_serie=123,
            user_id="usr-456",
        )
        d = doc.to_dict()
        self.assertEqual(d["doc_type"], "FACT")
        self.assertEqual(d["organisation_id"], "org-123")
        self.assertEqual(d["user_id"], "usr-456")
        self.assertEqual(d["etat"], Document.STATE_DRAFT)

    def test_to_dict_with_status(self):
        doc = Document(
            organisation_id="org-123",
            doc_type="FACT",
            numero_serie=1,
            status="brouillon_pdf",
        )
        self.assertEqual(doc.status, "brouillon_pdf")
        self.assertEqual(doc.etat, Document.STATE_DRAFT)

    def test_est_final(self):
        doc = Document(organisation_id="org-123", doc_type="FACT", numero_serie=1)
        self.assertFalse(doc.est_final())

    def test_repr(self):
        doc = Document(
            organisation_id="org-123",
            doc_type="FACT",
            numero_serie=1,
        )
        self.assertIn("Document", repr(doc))
        self.assertIn(doc.id, repr(doc))


class TestDocumentRepository(unittest.TestCase):
    """Tests du Repository Document."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.repo = DocumentRepository(self.db_path)

    def tearDown(self):
        self.repo.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create(self):
        doc = Document(
            organisation_id="org-123",
            doc_type="FACT",
            numero_serie=1,
        )
        saved = self.repo.save(doc)
        self.assertIsNotNone(saved)
        self.assertEqual(saved.id, doc.id)
        self.assertEqual(saved.doc_type, "FACT")

    def test_get(self):
        doc = Document(
            organisation_id="org-123",
            doc_type="FACT",
            numero_serie=1,
        )
        self.repo.save(doc)
        retrieved = self.repo.get(doc.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.doc_type, "FACT")

    def test_get_non_existant(self):
        retrieved = self.repo.get("doc-inconnu")
        self.assertIsNone(retrieved)

    def test_list(self):
        for i in range(3):
            doc = Document(
                organisation_id="org-123",
                doc_type="FACT",
                numero_serie=i + 1,
            )
            self.repo.save(doc)
        docs = self.repo.list()
        self.assertEqual(len(docs), 3)

    def test_list_with_offset(self):
        for i in range(5):
            doc = Document(
                organisation_id="org-123",
                doc_type="FACT",
                numero_serie=i + 1,
            )
            self.repo.save(doc)
        docs = self.repo.list(offset=2, limit=2)
        # L'ordre est celui d'insertion (par id), pas par numero_serie
        self.assertEqual(len(docs), 2)

    def test_save_and_get(self):
        doc = Document(
            organisation_id="org-123",
            doc_type="NC",
            numero_serie=100,
        )
        self.repo.save(doc)
        retrieved = self.repo.get(doc.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.numero_serie, 100)

    def test_context_manager(self):
        with DocumentRepository(self.db_path) as repo:
            doc = Document(
                organisation_id="org-123",
                doc_type="FACT",
                numero_serie=42,
            )
            repo.save(doc)
            retrieved = repo.get(doc.id)
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.doc_type, "FACT")


if __name__ == "__main__":
    unittest.main()
