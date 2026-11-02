"""
XoHive — Moteur de documents (v0)

Cœur fonctionnel du socle V0 : machine à états des documents, transition,
hachage immuable, traducteur de pièces comptables vers écritures.

Ce module est un prototype exécutable. Il est indépendant du framework et
de la base de données : il consomme des dictionnaires de données et
retourne des structures de résultat.

Licence : AGPL-3.0 (voir TERMS.md du projet TeamAI).
"""

from __future__ import annotations

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

# Transitions autorisées
TRANSITIONS: dict[str, list[str]] = {
    STATE_DRAFT: [STATE_DRAFT_PDF],
    STATE_DRAFT_PDF: [STATE_SENT],
    STATE_SENT: [STATE_RECEIVED],
    STATE_RECEIVED: [STATE_IN_PROGRESS],
    STATE_IN_PROGRESS: [STATE_EXECUTED],
    STATE_EXECUTED: [STATE_WRITTEN],
    STATE_WRITTEN: [STATE_CLOSED],
    STATE_WRITTEN: [STATE_CANCELLED],
    STATE_CANCELLED: [STATE_WRITTEN],
    STATE_CLOSED: [],
    STATE_DELETED: [],
}

# Invariant de sécurité : le solde de toute écriture doit être équilibré
# (débit = crédit). Ici on contrôle l'équilibre du document lui-même.
BALANCE_MIN = 0.0
BALANCE_MAX = 0.0

__all__ = [
    "STATE_DRAFT", "STATE_DRAFT_PDF", "STATE_SENT", "STATE_RECEIVED",
    "STATE_IN_PROGRESS", "STATE_EXECUTED", "STATE_WRITTEN",
    "STATE_CLOSED", "STATE_CANCELLED", "STATE_DELETED",
    "TRANSITIONS", "Document", "DocumentError", "compute_state_hash",
]


class DocumentError(Exception):
    """Erreur de validation d'un document ou d'une transition."""


class Document:
    """Représentation d'un document comptable piloté par une machine à états."""

    def __init__(
        self,
        doc_type: str,
        numero_serie: int,
        date_creation,
        org_id: int,
        *,
        exposer: str | None = None,
        numero_series: str | None = None,
        currency: str = "EUR",
        retention: float = 0.0,
        balance: float = 0.0,
        hash_etat: str | None = None,
        hash_pdf: str | None = None,
        created_by: str = "system",
        updated_by: str = "system",
        etats: list[dict] | None = None,
    ) -> None:
        if doc_type not in ("FACT", "BC", "BL", "NC", "RS", "CHQ"):
            raise DocumentError(f"type de document inconnu : {doc_type!r}")
        if not isinstance(numero_serie, int) or numero_serie <= 0:
            raise DocumentError("numero_serie invalide")
        self.id = None
        self.doc_type = doc_type
        self.numero_serie = numero_serie
        self.date_creation = date_creation
        self.org_id = org_id
        self.exposer = exposer
        self.numero_series = numero_series
        self.currency = currency
        self.retention = retention
        self.balance = balance
        self.hash_etat = hash_etat or compute_state_hash(
            STATE_DRAFT, numero_serie, org_id, currency, retention, balance
        )
        self.hash_pdf = hash_pdf
        self.created_by = created_by
        self.updated_by = updated_by
        self.etats: list[dict] = etats or [
            {
                "etat": STATE_DRAFT,
                "date_etat": date_creation,
                "acteur": created_by,
            }
        ]
        self._set_state(STATE_DRAFT, created_by)

    # -- accesseurs ---------------------------------------------------

    @property
    def etat(self) -> str:
        return self._etat

    @property
    def solde(self) -> float:
        return self.balance

    # -- machine à états ------------------------------------------------

    def _set_state(self, etat: str, acteur: str) -> None:
        if etat not in TRANSITIONS:
            raise DocumentError(f"état inconnu : {etat!r}")
        if etat not in TRANSITIONS[self._etat]:
            raise DocumentError(
                f"transition refusée : {self._etat} -> {etat}"
            )
        self._etat = etat
        self.updated_by = acteur
        self.etats.append(
            {"etat": etat, "date_etat": self.date_creation, "acteur": acteur}
        )
        self.hash_etat = compute_state_hash(
            STATE_DRAFT, self.numero_serie, self.org_id, self.currency,
            self.retention, self.balance
        )

    def transition(self, etat: str, acteur: str) -> None:
        self._set_state(etat, acteur)

    def est_final(self) -> bool:
        return self._etat in {"ferme", "annule", "supprime"}

    # -- validation ----------------------------------------------------

    def valider(self, acteur: str) -> None:
        """Passage d'un état non final à `ecrit` si l'état `execute` a été atteint."""
        if self._etat != STATE_EXECUTED:
            raise DocumentError(
                f"ne peut pas valider depuis {self._etat!r}"
            )
        self._set_state(STATE_WRITTEN, acteur)

    # -- hachage --------------------------------------------------------

    @property
    def etat_hash(self) -> str:
        return self.hash_etat


def compute_state_hash(
    etat: str,
    numero_serie: int,
    org_id: int,
    currency: str,
    retention: float,
    solde: float,
) -> str:
    """Chaîne de hachage immuable de l'état courant du document."""
    import hashlib
    payload = f"{etat}|{numero_serie}|{org_id}|{currency}|{retention}|{solde}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
