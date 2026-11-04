"""Document — Entité Document du socle ERP.

Représentation d'un document comptable piloté par une machine à états.

Attributs :
- id : TEXT/UUID (obligatoire)
- organisation_id : TEXT (obligatoire, N→1 avec Organization)
- user_id : TEXT (optionnel, utilisateur créateur)
- doc_type : TEXT (obligatoire, FACT/BC/BL/NC/RS/CHQ)
- numero_serie : int (obligatoire, > 0)
- status : str (optionnel, statut courant)
- etat : str (optionnel, état courant de la machine à états)
- hash_etat : str (optionnel, haché SHA-256 de l'état)
- currency : str (optionnel, devise 3 caractères)
- retention : float (optionnel, 0-1)
- balance : float (optionnel, ≥ 0)
- created_by : str (optionnel)
- created_at : str (optionnel, datetime ISO)
- updated_at : str (optionnel, datetime ISO)

Relations : N → 1 Organisation, N → 1 User.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone


class DocumentError(Exception):
    """Erreur de validation ou de manipulation d'un document."""


class Document:
    """Représentation d'un document comptable piloté par une machine à états."""

    # États valides d'un document
    STATE_DRAFT = "brouillon"
    STATE_DRAFT_PDF = "brouillon_pdf"
    STATE_SENT = "envoye"
    STATE_RECEIVED = "receive"
    STATE_IN_PROGRESS = "en_cours"
    STATE_EXECUTED = "execute"
    STATE_WRITTEN = "ecrit"
    STATE_CLOSED = "ferme"
    STATE_CANCELLED = "annule"

    # Types de documents acceptés
    ALLOWED_TYPES = ("FACT", "BC", "BL", "NC", "RS", "CHQ")

    # Transitions autorisées
    TRANSITIONS = {
        STATE_DRAFT: [STATE_DRAFT_PDF],
        STATE_DRAFT_PDF: [STATE_SENT],
        STATE_SENT: [STATE_RECEIVED],
        STATE_RECEIVED: [STATE_IN_PROGRESS],
        STATE_IN_PROGRESS: [STATE_EXECUTED],
        STATE_EXECUTED: [STATE_WRITTEN],
        STATE_WRITTEN: [STATE_CLOSED, STATE_CANCELLED],
        STATE_CANCELLED: [STATE_WRITTEN],
        STATE_CLOSED: [],
    }

    def __init__(
        self,
        *,
        id: str | None = None,
        organisation_id: str,
        user_id: str | None = None,
        doc_type: str,
        numero_serie: int,
        status: str | None = None,
        etat: str | None = None,
        currency: str = "EUR",
        retention: float = 0.0,
        balance: float = 0.0,
        created_by: str = "system",
        created_at: str | None = None,
        updated_at: str | None = None,
        hash_etat: str | None = None,
    ) -> None:
        if doc_type not in self.ALLOWED_TYPES:
            raise DocumentError(f"type de document inconnu : {doc_type!r}")
        if not isinstance(numero_serie, int) or numero_serie <= 0:
            raise DocumentError("numéro de série invalide")
        if balance < 0:
            raise DocumentError("balance négative")
        if not isinstance(currency, str) or len(currency) != 3:
            raise DocumentError("devise invalide")

        self.id: str = id or f"doc-{uuid.uuid4().hex[:12]}"
        self.organisation_id: str = organisation_id
        self.user_id: str | None = user_id
        self.doc_type: str = doc_type
        self.numero_serie: int = numero_serie
        self.status: str | None = status
        self.etat: str = etat or self.STATE_DRAFT
        self.currency: str = currency
        self.retention: float = retention
        self.balance: float = balance
        self.created_by: str = created_by
        self.created_at: str = created_at or self._now_iso()
        self.hash_etat: str = hash_etat or self._compute_hash_etat()
        self.updated_at: str | None = updated_at

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _compute_hash_etat(self) -> str:
        """Calcule le hash SHA-256 de l'état courant du document."""
        import hashlib
        payload = f"{self.etat}|{self.numero_serie}|{self.organisation_id}|{self.currency}|{self.retention}|{self.balance}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def transition(self, etat: str, acteur: str) -> None:
        """Applique une transition d'état autorisée."""
        if etat not in self.TRANSITIONS:
            raise DocumentError(f"état inconnu : {etat!r}")
        if etat not in self.TRANSITIONS[self.etat]:
            raise DocumentError(
                f"transition refusée : {self.etat} -> {etat}"
            )
        self.etat = etat
        self.updated_at = self._now_iso()
        self.hash_etat = self._compute_hash_etat()

    def est_final(self) -> bool:
        """Vérifie si le document est dans un état final."""
        return self.etat in {self.STATE_CLOSED, self.STATE_CANCELLED}

    def to_dict(self) -> dict:
        """Sérialise le document en dictionnaire."""
        return {
            "id": self.id,
            "organisation_id": self.organisation_id,
            "user_id": self.user_id,
            "doc_type": self.doc_type,
            "numero_serie": self.numero_serie,
            "status": self.status,
            "etat": self.etat,
            "hash_etat": self.hash_etat,
            "currency": self.currency,
            "retention": self.retention,
            "balance": self.balance,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __repr__(self) -> str:
        return f"<Document {self.id} {self.doc_type} {self.etat}>"


class DocumentError(Exception):
    """Erreur de validation ou de manipulation d'un document."""
