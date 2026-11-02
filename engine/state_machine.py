"""Machine à états du document — XoHive socle V0.

Définit les états valides, les transitions autorisées, et l'algorithme de
chaîne de hachage immuable utilisé pour l'intégrité du document.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

# État valides d'un document
STATE_DRAFT = "brouillon"
STATE_DRAFT_PDF = "brouillon_pdf"
STATE_SENT = "envoye"
STATE_RECEIVED = "receive"
STATE_IN_PROGRESS = "en_cours"
STATE_EXECUTED = "execute"
STATE_WRITTEN = "ecrit"
STATE_CLOSED = "ferme"
STATE_CANCELLED = "annule"
STATE_DELETED = "supprime"

TRANSITIONS: dict[str, list[str]] = {
    STATE_DRAFT: [STATE_DRAFT_PDF],
    STATE_DRAFT_PDF: [STATE_SENT],
    STATE_SENT: [STATE_RECEIVED],
    STATE_RECEIVED: [STATE_IN_PROGRESS],
    STATE_IN_PROGRESS: [STATE_EXECUTED],
    STATE_EXECUTED: [STATE_WRITTEN],
    STATE_WRITTEN: [STATE_CLOSED, STATE_CANCELLED],
    STATE_CANCELLED: [STATE_WRITTEN],
    STATE_CLOSED: [],
    STATE_DELETED: [],
}

# Invariant de sécurité : le solde de toute écriture doit être équilibré
BALANCE_MIN = 0.0
BALANCE_MAX = 0.0


def compute_now() -> str:
    """Renvoie l'heure courante ISO-8601 UTC."""
    return datetime.now(timezone.utc).isoformat()


def compute_state_hash(etat: str, numero_serie: int, org_id: int, currency: str, retention: float, solde: float) -> str:
    """Chaîne de hachage immuable de l'état courant du document.

    Les paramètres explicites évitent les aléas forts de sérialisation
    (date/heure, tri de dictionnaire, etc.).
    """
    payload = f"{etat}|{numero_serie}|{org_id}|{currency}|{retention}|{solde}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


__all__ = [
    "STATE_DRAFT",
    "STATE_DRAFT_PDF",
    "STATE_SENT",
    "STATE_RECEIVED",
    "STATE_IN_PROGRESS",
    "STATE_EXECUTED",
    "STATE_WRITTEN",
    "STATE_CLOSED",
    "STATE_CANCELLED",
    "STATE_DELETED",
    "TRANSITIONS",
    "compute_now",
    "compute_state_hash",
]
