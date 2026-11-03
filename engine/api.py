"""API HTTP minimale du moteur de documents XoHive (engine-api-v1).

Expose une API REST de lecture sur les documents du moteur ;
aucune persistance ou écriture n'est implantée ici.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from engine import Document, DocumentError, compute_state_hash
from engine.documents import (
    DocumentEditor,
    DocumentQuery,
    DocumentStore,
)
from engine.exceptions import (
    BalanceError,
    ConfigError,
    DocumentError as EngineDocumentError,
    EngineError,
    StorageError,
    TransitionError,
    ValidationError,
    _BaseXoHiveError,
)

# Codes HTTP utilisés dans l'API minimale.
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_ACCEPTED = 202
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_CONFLICT = 409
HTTP_UNPROCESSABLE = 422
HTTP_INTERNAL_ERROR = 500

STATUS_TEXT = {
    HTTP_OK: "OK",
    HTTP_CREATED: "Created",
    HTTP_ACCEPTED: "Accepted",
    HTTP_BAD_REQUEST: "Bad Request",
    HTTP_UNAUTHORIZED: "Unauthorized",
    HTTP_FORBIDDEN: "Forbidden",
    HTTP_NOT_FOUND: "Not Found",
    HTTP_CONFLICT: "Conflict",
    HTTP_UNPROCESSABLE: "Unprocessable Entity",
    HTTP_INTERNAL_ERROR: "Internal Server Error",
}


class XoHiveError(_BaseXoHiveError):
    """Erreur générique de l'API.

    Alias de ``_BaseXoHiveError`` pour une impose de namespace
    ``engine.api.XoHiveError``.
    """

    code = "XOBHE422"
    status = HTTP_UNPROCESSABLE

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message, code or self.code)


def _error_response(exc: Exception) -> dict[str, dict[str, str]]:
    """Construit le payload ``{"error": {...}}`` partout."""
    code = getattr(exc, "code", "XOBHE422")
    message = str(exc) or exc.__class__.__name__
    return {"error": {"code": code, "message": message}}


def _ok(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Réponse ``200``."""
    return {"status": "ok", "data": payload or {}}


def find_document(store: DocumentStore, doc_id: str) -> dict[str, Any]:
    """Recherche d'un document par ``doc_id``.

    Entrée : ``doc_id`` (str)
    Sortie : ``{"id": ..., "doc_type": ..., ...}``
    """
    doc = store.get(doc_id)
    if doc is None:
        raise XoHiveError(f"document {doc_id} introuvable", code="DOC404")
    return _ok({"id": doc.id, "doc_type": doc.doc_type,
                "status": doc.etat, "numero_serie": doc.numero_serie})


def list_documents(store: DocumentStore,
                   limit: int = 50,
                   offset: int = 0) -> dict[str, Any]:
    """Liste paginée des documents.

    Entrée : ``limit`` (int), ``offset`` (int)
    Sortie : ``{"items": [...], "total": N}``
    """
    all_docs = store.list()
    total = len(all_docs)
    items = []
    for doc in all_docs[offset:offset + limit]:
        items.append({
            "id": doc.id,
            "doc_type": doc.doc_type,
            "status": doc.etat,
            "numero_serie": doc.numero_serie,
        })
    return _ok({"items": items, "total": total, "limit": limit, "offset": offset})


def validate_input(data: dict[str, Any]) -> dict[str, Any]:
    """Valide les champs d'entrée d'une requête.

    Entrée : ``data`` (dict)
    Sortie : ``data`` normalisé (dict)
    """
    if "doc_type" in data and data["doc_type"] not in (
        "FACT", "BC", "BL", "NC", "RS", "CHQ"):
        raise ValidationError("doc_type invalide", code="VAL400")
    return data


def create_document(
    doc_type: str,
    numero_serie: int,
    org_id: int,
    currency: str = "EUR",
    retention: float = 0.0,
    balance: float = 0.0,
) -> Document:
    """Crée un document après validation des règles business.

    Utilise ``DocumentValidator.validate_creation`` pour s'assurer que
    les arguments respectent les règles métier (type, numéro de série,
    org_id, devise, retention, balance).
    """
    from engine.validation import DocumentValidator

    validator = DocumentValidator()
    validator.validate_creation(
        doc_type=doc_type,
        numero_serie=numero_serie,
        org_id=org_id,
        currency=currency,
        retention=retention,
        balance=balance,
    )
    return Document(
        doc_type=doc_type,
        numero_serie=numero_serie,
        org_id=org_id,
        date_creation=datetime.now(timezone.utc).isoformat(),
        currency=currency,
        retention=retention,
        balance=balance,
    )


def transition_document(document: Document, etat: str) -> Document:
    """Applique une transition d'état après validation des règles métier.

    Utilise ``DocumentValidator.validate_transition`` pour s'assurer que
    la transition est autorisée depuis l'état courant du document.
    """
    from engine.validation import DocumentValidator

    validator = DocumentValidator()
    validator.validate_transition(document, etat)
    document.transition(etat, "system")
    return document
