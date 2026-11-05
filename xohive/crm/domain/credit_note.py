"""CreditNote — Avoir (Créance) du module Ventes & Facturation.

Entité :
- CreditNote : avoir opposé à une facture existante, réduisant le montant dû
- Champs : id, organisation_id, company_id, contact_id, user_id, invoice_id (lien N→1),
           credit_date, amount, reason, currency, status (draft, approved, issued, refused), is_active

Relations : N → 1 Organisation, N → 1 Company, N → 1 Contact, N → 1 User, N → 1 Invoice
Dépendances : tâche 20 (Invoice)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from engine.exceptions import ValidationError


class CreditNoteError(Exception):
    """Erreur de manipulation d'un avoir (credit note)."""


class CreditNote:
    """Représentation d'un avoir."""

    # Statuts de l'avoir
    STATUS_DRAFT = "draft"
    STATUS_APPROVED = "approved"
    STATUS_ISSUED = "issued"
    STATUS_REFUSED = "refused"

    ALLOWED_STATUS = (
        STATUS_DRAFT,
        STATUS_APPROVED,
        STATUS_ISSUED,
        STATUS_REFUSED,
    )

    def __init__(
        self,
        *,
        id: str | None = None,
        organisation_id: str,
        company_id: str,
        contact_id: str | None = None,
        user_id: str | None = None,
        invoice_id: str,
        credit_date: str | None = None,
        amount: float,
        reason: str = "",
        currency: str = "EUR",
        status: str = STATUS_DRAFT,
        is_active: bool = True,
        created_by: str = "system",
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        if not organisation_id:
            raise CreditNoteError("organisation_id requis")
        if not company_id:
            raise CreditNoteError("company_id requis")
        if not invoice_id:
            raise CreditNoteError("invoice_id requis")
        if status not in self.ALLOWED_STATUS:
            raise CreditNoteError(
                f"status invalide : {status}. Valeurs possibles : {self.ALLOWED_STATUS}"
            )
        if amount < 0:
            raise CreditNoteError("amount ne peut pas être négatif")
        if currency and len(currency) != 3:
            raise CreditNoteError("currency doit faire 3 caractères")

        self.id: str = id or f"cn-{uuid.uuid4().hex[:12]}"
        self.organisation_id: str = organisation_id
        self.company_id: str = company_id
        self.contact_id: str | None = contact_id
        self.user_id: str | None = user_id
        self.invoice_id: str = invoice_id
        self.credit_date: str = credit_date or datetime.now(timezone.utc).isoformat()
        self.amount: float = amount
        self.reason: str = reason
        self.currency: str = currency or "EUR"
        self.status: str = status
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
            "invoice_id": self.invoice_id,
            "credit_date": self.credit_date,
            "amount": self.amount,
            "reason": self.reason,
            "currency": self.currency,
            "status": self.status,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __repr__(self) -> str:
        return f"<CreditNote {self.id} status={self.status} amount={self.amount}>"
