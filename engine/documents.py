"""Documents — couche de gestion des documents du socle XoHive.

Ce module fournit une vue de recherche et un éditeur de documents
(comptables). Il repose sur `engine.ledger.Ledger` et `engine.transactions`.

Le document est toujours manipulé via un état de machine à états ; la
transition vers un nouvel état est uniquement possible si la règle métier
le permet (voir `engine/state_machine` pour la définition des états).

Concerne les documents comptables (factures, bons de commande, bons de
livraison, notes de crédit, reçus, chèques).
"""

from __future__ import annotations

from engine.exceptions import (
    DocumentAlreadyClosed,
    DocumentAlreadyFinal,
    DocumentNotExecutable,
    DocumentOnlyDraft,
    NotFound,
)
from engine import state_machine as sm


class DocumentStore:
    """Magasin mémoire des documents.

    En production, cette classe sera remplacée par un accès au socle
    événementiel (PostgreSQL). Le contrat reste le même : lecture,
    recherche et mise à jour d'un document par une clé stable.
    """

    def __init__(self, org_id: int) -> None:
        self.org_id = org_id
        self._docs: dict[int, dict] = {}

    # -- lecture ---------------------------------------------------------

    def find(self, doc_id: int) -> dict:
        doc = self._docs.get(doc_id)
        if doc is None:
            raise NotFound(
                f"document {doc_id!r} introuvable pour l'organisation {self.org_id}"
            )
        return dict(doc)

    def list(self, limit: int | None = 50, offset: int = 0) -> list[dict]:
        return list(self._docs.values())[offset : offset + limit]

    # -- création ---------------------------------------------------------

    def create(
        self,
        doc_type: str,
        numero_serie: int,
        *,
        org_id: int,
        date_creation,
        exposer: str,
        numero_series: str | None = None,
        currency: str = "EUR",
        retention: float = 0.0,
        balance: float = 0.0,
    ) -> dict:
        """Crée un nouveau document et le met en `brouillon`."""
        doc = {
            "id": self._next_id(),
            "org_id": org_id,
            "doc_type": doc_type,
            "numero_serie": numero_serie,
            "date_creation": date_creation,
            "exposer": exposer,
            "numero_series": numero_series,
            "currency": currency,
            "retention": retention,
            "balance": balance,
            "etat": "brouillon",
            "hash_etat": sm.compute_state_hash("brouillon"),
            "etat_date": date_creation,
            "updated_at": date_creation,
            "created_by": exposer,
            "created_at": date_creation,
        }
        self._docs[doc["id"]] = doc
        return dict(doc)

    # -- mises à jour ------------------------------------------------------

    def open_for_editing(self, doc_id: int, actor: str) -> dict:
        doc = self.find(doc_id)
        if doc["etat"] != "brouillon":
            raise DocumentOnlyDraft(
                f"document {doc_id!r} n'est pas en `brouillon` (état courant : {doc['etat']!r})"
            )
        doc["etat"] = "edite"
        doc["hash_etat"] = lambda e="edite": None  # placeholder (non sérialisé)
        doc["updated_at"] = sm.compute_now()
        return dict(doc)

    def resign(self, doc_id: int, actor: str) -> dict:
        doc = self.find(doc_id)
        if doc["etat"] != "edite":
            raise DocumentOnlyDraft(
                f"document {doc_id!r} n'est pas en `edite` (état courant : {doc['etat']!r})"
            )
        doc["etat"] = "brouillon_pdf"
        doc["updated_at"] = sm.compute_now()
        return dict(doc)

    def send(self, doc_id: int, actor: str) -> dict:
        doc = self.find(doc_id)
        if doc["etat"] != "brouillon_pdf":
            raise DocumentOnlyDraft(
                f"document {doc_id!r} doit être `brouillon_pdf` avant envoi"
            )
        doc["etat"] = "envoye"
        doc["updated_at"] = sm.compute_now()
        return dict(doc)

    def cancel(self, doc_id: int, actor: str) -> dict:
        doc = self.find(doc_id)
        if doc["etat"] not in {"brouillon", "edite", "brouillon_pdf", "envoye"}:
            raise RuntimeError(f"annulation non autorisée depuis {doc['etat']!r}")
        doc["etat"] = "annule"
        doc["updated_at"] = sm.compute_now()
        return dict(doc)

    def delete(self, doc_id: int, actor: str) -> dict:
        doc = self.find(doc_id)
        doc["etat"] = "supprime"
        doc["updated_at"] = sm.compute_now()
        del self._docs[doc_id]
        return dict(doc)

    # -- helpers -----------------------------------------------------------

    def _next_id(self) -> int:
        return max((d["id"] for d in self._docs.values()), default=0) + 1


__all__ = ["DocumentStore"]
