"""LedgerEntry — Écritures comptables du socle ERP.

Entités :
- LedgerEntry : une écriture comptable (débit/crédit)
- Ledger : moteur qui calcule le solde et validate l'équilibre
- LedgerBalanceError : erreur quand débit != crédit

Relations : N → 1 Organisation, N → 1 User, N → 1 Document.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from .audit_event import AuditEvent


class LedgerBalanceError(Exception):
    """Erreur de cohérence comptable : débit != crédit."""


class LedgerEntry:
    """Représentation d'une écriture comptable."""

    ALLOWED_TYPES = ("FACT", "BC", "BL", "NC", "RS", "CHQ")

    # Types d'écriture
    TYPE_DEBIT = "Debit"
    TYPE_CREDIT = "Credit"

    def __init__(
        self,
        *,
        id: str | None = None,
        organisation_id: str,
        user_id: str | None = None,
        ledger_type: str,
        reference: str,
        debit: float = 0.0,
        credit: float = 0.0,
        balance: float = 0.0,
        doc_id: str | None = None,
        created_by: str = "system",
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        if ledger_type not in self.ALLOWED_TYPES:
            raise LedgerBalanceError(f"type de ledger invalide : {ledger_type!r}")
        if debit < 0 or credit < 0:
            raise LedgerBalanceError("débit/crédit négatif")
        if balance < 0:
            raise LedgerBalanceError("solde négatif")

        self.id: str = id or f"led-{uuid.uuid4().hex[:12]}"
        self.organisation_id: str = organisation_id
        self.user_id: str | None = user_id
        self.ledger_type: str = ledger_type
        self.reference: str = reference
        self.debit: float = debit
        self.credit: float = credit
        self.balance: float = balance
        self.doc_id: str | None = doc_id
        self.created_by: str = created_by
        self.created_at: str = created_at or self._now_iso()
        self.updated_at: str | None = updated_at

    @staticmethod
    def _now_iso() -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()

    def est_bilancee(self) -> bool:
        """Vérifie que l'écriture est équilibrée."""
        return abs((self.debit - self.credit)) < 0.005

    def aureferance(self) -> str:
        """Retourne la référence complète."""
        return f"{self.ledger_type}-{self.reference}"

    def to_dict(self) -> dict[str, Any]:
        """Sérialise l'écriture."""
        return {
            "id": self.id,
            "organisation_id": self.organisation_id,
            "user_id": self.user_id,
            "ledger_type": self.ledger_type,
            "reference": self.reference,
            "debit": self.debit,
            "credit": self.credit,
            "balance": self.balance,
            "doc_id": self.doc_id,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __repr__(self) -> str:
        return f"<LedgerEntry {self.id} {self.reference} {self.debit}/{self.credit}>"


class Ledger:
    """Moteur d'écriture comptable.

    Valide l'équilibre (débit = crédit), calcule le solde
    et génère un AuditEvent pour chaque écriture.
    """

    def __init__(self) -> None:
        self.comptes: dict[str, dict[str, Any]] = {}
        self.ecritures: list[LedgerEntry] = []

    def register_compte(
        self,
        numero: str,
        libelle: str,
        nature: str,
    ) -> None:
        """Enregistre un compte dans le référentiel."""
        self.comptes[numero] = {
            "numero": numero,
            "libelle": libelle,
            "nature": nature,
        }

    def calculer_balance(self) -> tuple[float, float]:
        """Calcule le total des débits et crédits."""
        debit = sum(e.debit for e in self.ecritures)
        credit = sum(e.credit for e in self.ecritures)
        return debit, credit

    def writer(
        self,
        organisation_id: str,
        user_id: str,
        ledger_type: str,
        reference: str,
        debit: float,
        credit: float,
        balance: float = 0.0,
        doc_id: str | None = None,
    ) -> LedgerEntry:
        """Écrit une nouvelle écriture comptable."""
        # Validation de l'équilibre
        if not self._est_equilibree(debit, credit):
            raise LedgerBalanceError(
                f"écriture non équilibrée : débit {debit} != crédit {credit}"
            )

        entry = LedgerEntry(
            organisation_id=organisation_id,
            user_id=user_id,
            ledger_type=ledger_type,
            reference=reference,
            debit=debit,
            credit=credit,
            balance=balance,
            doc_id=doc_id,
            created_by=user_id,
            created_at=LedgerEntry._now_iso(),
        )

        self.ecritures.append(entry)

        # Génération d'un AuditEvent
        audit = AuditEvent(
            organisation_id=organisation_id,
            user_id=user_id,
            entity_type="LedgerEntry",
            entity_id=entry.id,
            action="create",
            new_values={
                "reference": reference,
                "debit": debit,
                "credit": credit,
            },
        )
        # (à persister via AuditEventRepository si disponible)

        return entry

    def _est_equilibree(self, debit: float, credit: float) -> bool:
        return abs(debit - credit) < 0.005

    def __len__(self) -> int:
        return len(self.ecritures)
