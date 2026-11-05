"""Quotation — Devis du module Ventes & Facturation.

Entité :
- Quotation : document provisoire qui précède une commande
- Champs : id, organisation_id, company_id, contact_id, user_id, reference,
           quotation_date, valid_until, total_amount, tax_rate, currency,
           status (draft, sent, accepted, rejected), is_active

Relations : N → 1 Organisation, N → 1 Company, N → 1 Contact, N → 1 User
Dépendances : Organisation (task 2), Company (task 11), Contact (task 12), User (task 3)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from engine.exceptions import ValidationError


class QuotationError(Exception):
    """Erreur de manipulation d'une quotation."""


class Quotation:
    """Représentation d'un devis (quotation)."""

    # Statuts du devis
    STATUS_DRAFT = "draft"
    STATUS_SENT = "sent"
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"

    ALLOWED_STATUS = (STATUS_DRAFT, STATUS_SENT, STATUS_ACCEPTED, STATUS_REJECTED)

    def __init__(
        self,
        *,
        id: str | None = None,
        organisation_id: str,
        company_id: str,
        contact_id: str | None = None,
        user_id: str | None = None,
        reference: str | None = None,
        quotation_date: str | None = None,
        valid_until: str | None = None,
        total_amount: float,
        tax_rate: float = 0.0,
        currency: str = "EUR",
        status: str = STATUS_DRAFT,
        is_active: bool = True,
        created_by: str = "system",
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        if not organisation_id:
            raise QuotationError("organisation_id requis")
        if not company_id:
            raise QuotationError("company_id requis")

        # Set default values for optional fields
        if not quotation_date:
            self.quotation_date = datetime.now(timezone.utc).isoformat()
        else:
            self.quotation_date = quotation_date

        if valid_until is None:
            self.valid_until = datetime.now(timezone.utc).isoformat()
        else:
            self.valid_until = valid_until

        if self.valid_until < self.quotation_date:
            raise QuotationError("valid_until doit être après quotation_date")

        if total_amount < 0:
            raise QuotationError("total_amount ne peut pas être négatif")

        if currency and len(currency) != 3:
            raise QuotationError("currency doit faire 3 caractères")

        if status not in self.ALLOWED_STATUS:
            raise QuotationError(
                f"status invalide : {status}. Valeurs possibles : {self.ALLOWED_STATUS}"
            )

        self.id: str = id or f"quota-{uuid.uuid4().hex[:12]}"
        self.organisation_id: str = organisation_id
        self.company_id: str = company_id
        self.contact_id: str = contact_id or None
        self.user_id: str | None = user_id
        self.reference: str = reference or f"Q-{uuid.uuid4().hex[:8].upper()}"
        self.total_amount: float = total_amount
        self.tax_rate: float = tax_rate
        self.currency: str = currency or "EUR"
        self.status: str = status
        self.is_active: bool = is_active
        self.created_by: str = created_by
        self.created_at: str = created_at or datetime.now(timezone.utc).isoformat()
        self.updated_at: str | None = updated_at

        # Set default values for optional fields
        if not quotation_date:
            self.quotation_date = datetime.now(timezone.utc).isoformat()
        else:
            self.quotation_date = quotation_date

        if valid_until is None:
            self.valid_until = datetime.now(timezone.utc).isoformat()
        else:
            self.valid_until = valid_until

        if self.valid_until < self.quotation_date:
            raise QuotationError("valid_until doit être après quotation_date")

        if self.total_amount < 0:
            raise QuotationError("total_amount ne peut pas être négatif")

        if self.currency and len(self.currency) != 3:
            raise QuotationError("currency doit faire 3 caractères")

        if self.status not in self.ALLOWED_STATUS:
            raise QuotationError(
                f"status invalide : {self.status}. Valeurs possibles : {self.ALLOWED_STATUS}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Sérialise l'objet en dictionnaire."""
        return {
            "id": self.id,
            "organisation_id": self.organisation_id,
            "company_id": self.company_id,
            "contact_id": self.contact_id,
            "user_id": self.user_id,
            "reference": self.reference,
            "quotation_date": self.quotation_date,
            "valid_until": self.valid_until,
            "total_amount": self.total_amount,
            "tax_rate": self.tax_rate,
            "currency": self.currency,
            "status": self.status,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __repr__(self) -> str:
        return f"<Quotation {self.id} {self.reference} status={self.status}>"
