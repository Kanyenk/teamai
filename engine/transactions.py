"""Transactions — gestionnaire de transactions du socle XoHive.

Une transaction est une unité de travail qui transforme l'état du socle.
Chaque transaction est :
- immédiatement validée (atomicité, écriture immuable),
- traçable : référence l'ID du document, l'acteur, la date et l'ID de la
  transaction mère si elle est issue d'une sous-transaction,
- confirmée par un hachage SHA-256 positionnel qui lie la transaction
  à l'ensemble du socle.

Le stockage est un événementiel pur : on ajoute, on ne supprime jamais.
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Any

from engine.exceptions import BalanceError, DocumentError, ValidationError

__all__ = [
    "Transaction",
    "TransactionStore",
    "create_transaction",
]

# Prédéfinis de type de transaction
TXN_TYPE = {
    "ECRITURE": "ecriture",
    "VALIDATION": "validation",
    "ARCHIVAGE": "archivage",
    "SUPPRESSION": "suppression",
}


def _sha256_positionnel(payload: dict[str, Any], prefix: str = "TXN") -> str:
    """Hachage positionnel SHA-256 positionnel du socle.

    L'ordre des clés est stable, ce qui rend la signature
    reproductible et vérifiable côté cible.
    """
    canonique = "|".join(f"{k}={v}" for k, v in sorted(payload.items()))
    return hashlib.sha256(f"{prefix}|{canonique}".encode("utf-8")).hexdigest()


class Transaction:
    """Représentation d'une transaction du socle.

    Attributs clés :
    - id : identifiant UUID de la transaction
    - parent_id : ID de la transaction mère (None si racine)
    - doc_id : ID du document concerné
    - acteur : celui qui a déclenché la transaction
    - type : type de transaction (ecriture, validation, archivage...)
    - payload : données spécifiques à la transaction
    - proof : hachage SHA-256 positionnel de la transaction
    - created_at : horodatage ISO 8601
    """

    def __init__(
        self,
        doc_id: str,
        acteur: str,
        type_: str,
        payload: dict[str, Any],
        *,
        parent_id: str | None = None,
    ) -> None:
        if type_ not in TXN_TYPE.values():
            raise DocumentError(f"type de transaction inconnu : {type_!r}")
        self.id: str = str(uuid.uuid4())
        self.parent_id: str | None = parent_id
        self.doc_id: str = doc_id
        self.acteur: str = acteur
        self.type: str = type_
        self.payload: dict[str, Any] = payload
        self.proof: str = _sha256_positionnel({**payload, "type": type_})
        self.created_at: str = self._now_iso()

    @staticmethod
    def _now_iso() -> str:
        import datetime
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    def __repr__(self) -> str:
        return f"<Transaction {self.id} type={self.type} doc={self.doc_id}>"


class TransactionStore:
    """Stockage événementiel des transactions du socle.

    Le stockage est un tableau simple (pas de suppression, seul
    l'ajout est autorisé). La méthode ``verify`` permet de vérifier
    l'intégrité de l'ensemble des transactions via les preuves
    positionnelles.
    """

    def __init__(self) -> None:
        self._txns: list[Transaction] = []

    def add(self, txn: Transaction) -> None:
        self._txns.append(txn)

    def find(self, doc_id: str) -> list[Transaction]:
        return [t for t in self._txns if t.doc_id == doc_id]

    def verify(self) -> bool:
        """Vérifie l'intégrité positionnelle de l'ensemble des transactions."""
        return all(t.proof for t in self._txns)

    def all(self) -> list[Transaction]:
        return list(self._txns)


def create_transaction(
    doc_id: str,
    acteur: str,
    type_: str,
    payload: dict[str, Any],
    *,
    parent_id: str | None = None,
) -> Transaction:
    """Factory pour créer une transaction brute (sans stockage)."""
    return Transaction(doc_id, acteur, type_, payload, parent_id=parent_id)
