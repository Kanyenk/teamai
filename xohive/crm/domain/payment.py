"""Payment — Paiement du module Ventes & Facturation.

Entité :
- Payment : enregistrement d'un paiement reçu
- Champs : id, organisation_id, company_id, contact_id, user_id, invoice_id (lien N→1),
           amount, currency, payment_date, method (card, bank_transfer, cash),
           status (pending, completed, failed, cancelled), is_active

Relations : N → 1 Organisation, N → 1 Company, N → 1 Contact, N → 1 User, N → 1 Invoice
Dépendances : tâche 21 (Credit Note)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from engine.exceptions import ValidationError


class PaymentError(Exception):
    """Erreur de manipulation d'un paiement."""


class Payment:
    """Représentation d'un paiement."""

    # Statuts de paiement
    STATUS_PENDING = "pending"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"

    ALLOWED_STATUS = (
        STATUS_PENDING,
        STATUS_COMPLETED,
        STATUS_FAILED,
        STATUS_CANCELLED,
    )

    # Méthodes de paiement
    PAYMENT_METHODS = ("card", "bank_transfer", "cash")

    def __init__(
        self,
        *,
        id: str | None = None,
        organisation_id: str,
        company_id: str,
        contact_id: str | None = None,
        user_id: str | None = None,
        invoice_id: str,
        amount: float,
        currency: str = "EUR",
        payment_date: str | None = None,
        method: str = "bank_transfer",
        status: str = STATUS_PENDING,
        is_active: bool = True,
        created_by: str = "system",
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        if not organisation_id:
            raise PaymentError("organisation_id requis")
        if not company_id:
            raise PaymentError("company_id requis")
        if not invoice_id:
            raise PaymentError("invoice_id requis")
        if status not in self.ALLOWED_STATUS:
            raise PaymentError(
                f"status invalide : {status}. Valeurs possibles : {self.ALLOWED_STATUS}"
            )
        if method not in self.PAYMENT_METHODS:
            raise PaymentError(
                f"method invalide : {method}. Valeurs possibles : {self.PAYMENT_METHODS}"
            )
        if amount < 0:
            raise PaymentError("amount ne peut pas être négatif")
        if currency and len(currency) != 3:
            raise PaymentError("currency doit faire 3 caractères")

        self.id: str = id or f"pay-{uuid.uuid4().hex[:12]}"
        self.organisation_id: str = organisation_id
        self.company_id: str = company_id
        self.contact_id: str | None = contact_id
        self.user_id: str | None = user_id
        self.invoice_id: str = invoice_id
        self.amount: float = amount
        self.currency: str = currency or "EUR"
        self.payment_date: str = payment_date or datetime.now(timezone.utc).isoformat()
        self.method: str = method
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
            "amount": self.amount,
            "currency": self.currency,
            "payment_date": self.payment_date,
            "method": self.method,
            "status": self.status,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __repr__(self) -> str:
        return f"<Payment {self.id} status={self.status} amount={self.amount}>"
