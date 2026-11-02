"""Tests exécutables de l'API HTTP du moteur de documents (engine-api-v1).

Lancez avec : python3 -m pytest tests/test_engine_api.py -v
"""
from __future__ import annotations

import pytest

from engine.api import XoHiveError, status_map
from engine import Document, DocumentError
from engine.state_machine import compute_state_hash
from engine.documents import DocumentStore


class TestDocumentCreation:
    """Vérification de la création d'un document (route POST /api/v0/documents)."""

    def test_document_creation_minimal(self):
        doc = Document(
            doc_type="FACT",
            numero_serie=1,
            date_creation="2026-11-02",
            org_id=1,
            exposer="Comptable",
            currency="EUR",
            retention=0.0,
            balance=0.0,
        )
        assert doc.etat == "brouillon"
        assert doc.est_final() is False
        assert doc.etat_hash == compute_state_hash("brouillon", 1, 1, "EUR", 0.0, 0.0)

    def test_document_type_validation(self):
        with pytest.raises(DocumentError):
            Document(
                doc_type="INVALID",
                numero_serie=1,
                date_creation="2026-11-02",
                org_id=1,
            )

    def test_document_number_serie_validation(self):
        with pytest.raises(DocumentError):
            Document(
                doc_type="FACT",
                numero_serie=0,
                date_creation="2026-11-02",
                org_id=1,
            )


class TestDocumentStore:
    """Tests de la couche de stockage en mémoire."""

    def test_create_and_find(self, doc_store):
        doc = doc_store.create(
            doc_type="FACT",
            numero_serie=1,
            org_id=1,
            date_creation="2026-11-02",
            exposer="Comptable",
            currency="EUR",
        )
        assert doc["etat"] == "brouillon"
        found = doc_store.find(doc["id"])
        assert found["doc_type"] == "FACT"
        assert found["numero_serie"] == 1

    def test_find_missing(self, doc_store):
        with pytest.raises(Exception):  # NotFound
            doc_store.find(999)

    def test_list_empty(self, doc_store):
        assert doc_store.list() == []

    def test_list_pagination(self, doc_store):
        for i in range(5):
            doc_store.create(
                doc_type="FACT", numero_serie=i + 1, org_id=1,
                date_creation="2026-11-02", exposer="Comptable",
            )
        assert len(doc_store.list(limit=2)) == 2
        assert len(doc_store.list(limit=2, offset=2)) == 2


class TestApiErrorCodes:
    """Tests des codes d'erreur HTTP de l'API."""

    def test_status_map_contains_required_codes(self):
        required = {
            200: "OK", 201: "Created", 202: "Accepted",
            400: "Bad Request", 401: "Unauthorized",
            403: "Forbidden", 404: "Not Found", 409: "Conflict",
            422: "Unprocessable Entity", 500: "Internal Server Error",
        }
        for code, label in required.items():
            assert code in status_map
            assert status_map[code] == label

    def test_xo_hive_error_structure(self):
        exc = XoHiveError(422, "test message")
        assert exc.code == 422
        assert exc.message == "test message"
        data = exc.to_api()
        assert "error" in data
        assert data["error"]["code"] == "XOBHE422"
        assert data["error"]["message"] == "test message"


class TestDocumentTransitionRules:
    """Vérification que les transitions respectent la machine à états."""

    def test_transitions_chain(self):
        doc = Document(
            doc_type="FACT", numero_serie=1,
            date_creation="2026-11-02", org_id=1,
            exposer="Comptable",
        )
        doc.transition("brouillon_pdf", "Comptable")
        doc.transition("envoye", "Comptable")
        assert doc.etat == "envoye"
        assert doc.est_final() is False

    def test_invalid_transition(self):
        doc = Document(
            doc_type="FACT", numero_serie=1,
            date_creation="2026-11-02", org_id=1,
            exposer="Comptable",
        )
        with pytest.raises(DocumentError):
            doc.transition("brouillon_pdf", "Comptable")  # déjà "brouillon"
