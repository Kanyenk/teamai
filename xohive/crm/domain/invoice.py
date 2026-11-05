"""Invoice — Facture du module Ventes & Facturation.

Entité :
- Invoice : facture issue d'une commande ou d'un devis
- Champs : id, organisation_id, company_id, contact_id, user_id, order_id,
           issue_date, due_date, amount, tax_rate, currency, status (draft, sent, paid, void), is_active

Relations : N → 1 Organisation, N → 1 Company, N → 1 Contact, N → 1 User, N → 1 Order
Dépendances : tâche 19 (Order)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from engine.exceptions import ValidationError


class InvoiceError(Exception):
    """Erreur de manipulation d'une facture."""


class Invoice:
    """Représentation d'une facture."""

    # Statuts de la facture
    STATUS_DRAFT = "draft"
    STATUS_SENT = "sent"
    STATUS_PAID = "paid"
    STATUS_VOID = "void"

    ALLOWED_STATUS = (
        STATUS_DRAFT,
        STATUS_SENT,
        STATUS_PAID,
        STATUS_VOID,
    )

    def __init__(
        self,
        *,
        id: str | None = None,
        organisation_id: str,
        company_id: str,
        contact_id: str | None = None,
        user_id: str | None = None,
        order_id: str,
        issue_date: str | None = None,
        due_date: str | None = None,
        amount: float,
        tax_rate: float = 0.0,
        currency: str = "EUR",
        status: str = STATUS_DRAFT,
        is_active: bool = True,
        created_by: str = "system",
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        if not organisation_id:
            raise InvoiceError("organisation_id requis")
        if not company_id:
            raise InvoiceError("company_id requis")
        if not order_id:
            raise InvoiceError("order_id requis")
        if status not in self.ALLOWED_STATUS:
            raise InvoiceError(
                f"status invalide : {status}. Valeurs possibles : {self.ALLOWED_STATUS}"
            )
        if amount < 0:
            raise InvoiceError("amount ne peut pas être négatif")
        if currency and len(currency) != 3:
            raise InvoiceError("currency doit faire 3 caractères")

        self.id: str = id or f"inv-{uuid.uuid4().hex[:12]}"
        self.organisation_id: str = organisation_id
        self.company_id: str = company_id
        self.contact_id: str | None = contact_id
        self.user_id: str | None = user_id
        self.order_id: str = order_id
        self.issue_date: str = issue_date or datetime.now(timezone.utc).isoformat()
        self.due_date: str | None = due_date
        self.amount: float = amount
        self.tax_rate: float = tax_rate
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
            "order_id": self.order_id,
            "issue_date": self.issue_date,
            "due_date": self.due_date,
            "amount": self.amount,
            "tax_rate": self.tax_rate,
            "currency": self.currency,
            "status": self.status,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __repr__(self) -> str:
        return f"<Invoice {self.id} status={self.status} amount={self.amount}>"
