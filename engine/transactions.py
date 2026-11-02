"""Transactions — gestionnaire de transactions du socle XoHive.

Une transaction est une unité de travail qui transforme l'état du socle.
Chaque transaction est :
- immédiatement validée (atomicité),
- tracée (audit complet de l'acteur et du moment),
- d'identifiant stable (UUID ou séquence).

La classe Transaction ne fait que regrouper les données métier ; elle ne fait
pas appel à la base de données.
"""

from __future__ import annotations

from uuid import uuid4
from datetime import datetime, timezone

from engine.exceptions import TransactionError, TransactionAlreadyPosted


class Transaction:
    """Transaction métier du socle.

    Chaque instance représente une action métier (exemple : "envoi d'un
    document", "règlement d'une facture", "mise à jour d'un tiers").

    Les transactions sont conçues pour être journalisées dans le socle,
    sous forme d'événement immuable et réversible.
    """

    def __init__(
        self,
        type_: str,
        payload: dict,
        *,
        actor: str | None = None,
        org_id: int | None = None,
        metadata: dict | None = None,
    ) -> None:
        self.id = str(uuid4())
        self.type_ = type_
        self.payload = dict(payload or {})
        self.actor = actor
        self.org_id = org_id
        self.metadata = dict(metadata or {})
        self.status = "pending"
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at

    # -- statuts ---------------------------------------------------------

    def validate(self) -> None:
        """Valide la transaction et la marque comme validée."""
        if self.status != "pending":
            raise RuntimeError(f"impossible de valider une transaction {self.status!r}")
        self.status = "validated"
        self.updated_at = datetime.now(timezone.utc)

    def reject(self, reason: str) -> None:
        """Rejette la transaction."""
        self.status = "rejected"
        self.metadata["rejection_reason"] = reason
        self.updated_at = datetime.now(timezone.utc)

    def reject_for_self(self) -> None:
        self.reject("auto: traitement incomplet")

    @property
    def is_validated(self) -> bool:
        return self.status == "validated"

    @property
    def is_rejected(self) -> bool:
        return self.status == "rejected"

    @property
    def is_pending(self) -> bool:
        return self.status == "pending"

    # -- hydratation ------------------------------------------------------

    @classmethod
    def from_payload(
        cls,
        type_: str,
        payload: dict,
        *,
        actor: str | None = None,
        created_at: str | None = None,
    ) -> "Transaction":
        """Instancie une transaction à partir d'un dictionnaire."""
        tx = cls(type_, payload, actor=actor)
        if created_at:
            try:
                created = datetime.fromisoformat(created_at)
            except ValueError:
                created = datetime.now(timezone.utc)
            tx.created_at = created
            tx.updated_at = created
        return tx


class TransactionManager:
    """Gestionnaire de transactions persistantes."""

    def __init__(self) -> None:
        self._store: dict[str, Transaction] = {}

    # -- opérations ---------------------------------------------------------

    def create(self, type_: str, payload: dict, *, actor=None, org_id=None) -> Transaction:
        tx = Transaction(type_, payload, actor=actor, org_id=org_id)
        self._store[tx.id] = tx
        return tx

    def get(self, tx_id: str) -> Transaction | None:
        return self._store.get(tx_id)

    def list(self, *, status: str | None = None) -> list[Transaction]:
        txs = list(self._store.values())
        if status is not None:
            txs = [t for t in txs if t.status == status]
        return txs

    def update_status(self, tx_id: str, status: str, *, reason=None) -> Transaction:
        tx = self.get(tx_id)
        if tx is None:
            raise KeyError(f"transaction introuvable : {tx_id}")
        if status == "rejected":
            tx.reject(reason or "manual")
        else:
            tx.status = status
        tx.updated_at = datetime.now(timezone.utc)
        return tx

    def delete(self, tx_id: str) -> None:
        self._store.pop(tx_id, None)

    def size(self) -> int:
        return len(self._store)


__all__ = ["Transaction", "TransactionManager"]
