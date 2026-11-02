"""Tests exécutables de l'API HTTP du moteur de documents (engine-api-v1).

Lancez avec : python3 -m unittest discover -s tests -v
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import Document, DocumentError as EngineDocumentError, compute_state_hash
from engine.exceptions import DocumentError
from engine.documents import DocumentStore, Document as DocumentStoreDocument
from engine.exceptions import (
    EngineError,
    TransitionError,
    BalanceError,
    ValidationError,
    ConfigError,
    StorageError,
)


class TestDocumentCreation(unittest.TestCase):
    """Test de la création d'un document (engine.Document)."""

    def test_document_creation_minimal(self):
        doc = Document(
            doc_type="FACT",
            numero_serie=1,
            org_id=1,
            date_creation="2026-11-02",
            exposer="Comptable",
            currency="EUR",
        )
        self.assertEqual(doc.etat, "brouillon")
        self.assertFalse(doc.est_final())
        self.assertEqual(
            doc.etat_hash,
            compute_state_hash("brouillon", 1, 1, "EUR", 0.0, 0.0),
        )

    def test_document_type_validation(self):
        with self.assertRaises(EngineDocumentError):
            Document(
                doc_type="INVALID",
                numero_serie=1,
                date_creation="2026-11-02",
                org_id=1,
            )

    def test_document_number_serie_validation(self):
        with self.assertRaises(EngineDocumentError):
            Document(
                doc_type="FACT",
                numero_serie=0,
                date_creation="2026-11-02",
                org_id=1,
            )


class TestDocumentStore(unittest.TestCase):
    """Tests de la couche de stockage événementiel (engine.documents.Document)."""

    def setUp(self):
        self.doc_store = DocumentStore()

    def test_add_and_get(self):
        doc = DocumentStoreDocument(
            doc_type="FACT",
            numero_serie=1,
            org_id=1,
            date_creation="2026-11-02",
            exposer="Comptable",
        )
        self.doc_store.add(doc)
        found = self.doc_store.get(doc.id)
        self.assertIsNotNone(found)
        self.assertEqual(found.doc_type, "FACT")
        self.assertEqual(found.numero_serie, 1)

    def test_get_missing_returns_none(self):
        self.assertIsNone(self.doc_store.get("nonexistent"))

    def test_list_empty(self):
        self.assertEqual(self.doc_store.list(), [])

    def test_list_pagination(self):
        for i in range(5):
            doc = DocumentStoreDocument(
                doc_type="FACT",
                numero_serie=i + 1,
                org_id=1,
                date_creation="2026-11-02",
                exposer="Comptable",
            )
            self.doc_store.add(doc)
        self.assertEqual(len(self.doc_store.list()), 5)


class TestExceptions(unittest.TestCase):
    """Tests des exceptions du moteur."""

    def test_engine_error(self):
        exc = EngineError("test", code="ENGINE_ERROR")
        self.assertEqual(exc.code, "ENGINE_ERROR")
        self.assertEqual(str(exc), "test")

    def test_document_error(self):
        exc = DocumentError("test", code="DOCUMENT_ERROR")
        self.assertEqual(exc.code, "DOCUMENT_ERROR")
        self.assertEqual(str(exc), "test")

    def test_transition_error(self):
        exc = TransitionError("transition refusée", code="TRANSITION_ERROR")
        self.assertEqual(exc.code, "TRANSITION_ERROR")

    def test_balance_error(self):
        exc = BalanceError("solde déséquilibré", code="BALANCE_ERROR")
        self.assertEqual(exc.code, "BALANCE_ERROR")

    def test_validation_error(self):
        exc = ValidationError("champ invalide", code="VALIDATION_ERROR")
        self.assertEqual(exc.code, "VALIDATION_ERROR")

    def test_config_error(self):
        exc = ConfigError("configuration invalide", code="CONFIG_ERROR")
        self.assertEqual(exc.code, "CONFIG_ERROR")

    def test_storage_error(self):
        exc = StorageError("échec de stockage", code="STORAGE_ERROR")
        self.assertEqual(exc.code, "STORAGE_ERROR")


class TestComputeStateHash(unittest.TestCase):
    """Tests de la fonction de hachage immuable."""

    def test_compute_state_hash(self):
        h1 = compute_state_hash("brouillon", 1, 1, "EUR", 0.0, 0.0)
        h2 = compute_state_hash("brouillon", 1, 1, "EUR", 0.0, 0.0)
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)


if __name__ == "__main__":
    unittest.main()
