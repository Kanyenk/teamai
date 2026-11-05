"""Reconciliation — Rapprochement Bancaire du module Ventes & Facturation.

Entité :
- Reconciliation : rattache un paiement (Payment) à une entrée du livret de caisse (LedgerEntry)
- Champs : id, organisation_id, company_id, contact_id, user_id, payment_id (lien N→1),
           ledger_entry_id (lien N→1), bank_date, amount, currency, status (open, pending, closed), reference

Relations : N → 1 Organisation, N → 1 Company, N → 1 Contact, N → 1 User,
            N → 1 Payment, N → 1 LedgerEntry
Dépendances : tâche 22 (Payment), tâche 10 (LedgerEntry)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from engine.exceptions import ValidationError

from xohive.crm.domain.payment import PaymentError


class ReconciliationError(Exception):
    """Erreur de manipulation d'un rapprochement bancaire."""


class Reconciliation:
    """Représentation d'un rapprochement bancaire."""

    # Statuts du rapprochement
    STATUS_OPEN = "open"
    STATUS_PENDING = "pending"
    STATUS_CLOSED = "closed"

    ALLOWED_STATUS = (
        STATUS_OPEN,
        STATUS_PENDING,
        STATUS_CLOSED,
    )

    def __init__(
        self,
        *,
        id: str | None = None,
        organisation_id: str,
        company_id: str,
        contact_id: str | None = None,
        user_id: str | None = None,
        payment_id: str,
        ledger_entry_id: str,
        bank_date: str | None = None,
        amount: float,
        currency: str = "EUR",
        status: str = STATUS_OPEN,
        reference: str | None = None,
        is_active: bool = True,
        created_by: str = "system",
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        if not organisation_id:
            raise ReconciliationError("organisation_id requis")
        if not company_id:
            raise ReconciliationError("company_id requis")
        if not payment_id:
            raise ReconciliationError("payment_id requis")
        if not ledger_entry_id:
            raise ReconciliationError("ledger_entry_id requis")
        if status not in self.ALLOWED_STATUS:
            raise ReconciliationError(
                f"status invalide : {status}. Valeurs possibles : {self.ALLOWED_STATUS}"
            )
        if amount < 0:
            raise ReconciliationError("amount ne peut pas être négatif")
        if currency and len(currency) != 3:
            raise ReconciliationError("currency doit faire 3 caractères")

        self.id: str = id or f"rec-{uuid.uuid4().hex[:12]}"
        self.organisation_id: str = organisation_id
        self.company_id: str = company_id
        self.contact_id: str | None = contact_id
        self.user_id: str | None = user_id
        self.payment_id: str = payment_id
        self.ledger_entry_id: str = ledger_entry_id
        self.bank_date: str = bank_date or datetime.now(timezone.utc).isoformat()
        self.amount: float = amount
        self.currency: str = currency or "EUR"
        self.status: str = status
        self.reference: str = reference or f"REC-{uuid.uuid4().hex[:8].upper()}"
        self.is_active: bool = is_active
        self.created_by: str = created_by
        self.created_at: str = created_at or datetime.now(timezone.utc).isoformat()
        self.updated_at: str | None = updated_at

    def to_dict(self) -> dict[str, Any]:
        """Sérialise l'objet en dictionnaire."""
        return {
            "id": self.id,
            "organisation_id": self.organisation_id,
            "company_id": self.company_id,
            "contact_id": self.contact_id,
            "user_id": self.user_id,
            "payment_id": self.payment_id,
            "ledger_entry_id": self.ledger_entry_id,
            "bank_date": self.bank_date,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "reference": self.reference,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __repr__(self) -> str:
        return f"<Reconciliation {self.id} status={self.status} amount={self.amount}>"
