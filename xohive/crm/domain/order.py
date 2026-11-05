"""Order — Commande du module Ventes & Facturation.

Entité :
- Order : commande reprenant les lignes d'un devis et les transforme en commande conforme
- Champs : id, organisation_id, company_id, contact_id, user_id, quotation_id,
           order_date, delivery_date, shipping_method, total_amount, tax_rate,
           currency, status (pending, confirmed, shipped, delivered, cancelled), is_active

Relations : N → 1 Organisation, N → 1 Company, N → 1 Contact, N → 1 User, N → 1 Quotation
Dépendances : tâche 18 (Quotation)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from engine.exceptions import ValidationError


class OrderError(Exception):
    """Erreur de manipulation d'une commande."""


class Order:
    """Représentation d'une commande."""

    # Statuts de la commande
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"

    ALLOWED_STATUS = (
        STATUS_PENDING,
        STATUS_CONFIRMED,
        STATUS_SHIPPED,
        STATUS_DELIVERED,
        STATUS_CANCELLED,
    )

    # Méthodes de livraison
    SHIPPING_METHODS = ("standard", "express", "pickup", "courrier")

    def __init__(
        self,
        *,
        id: str | None = None,
        organisation_id: str,
        company_id: str,
        contact_id: str | None = None,
        user_id: str | None = None,
        quotation_id: str,
        order_date: str | None = None,
        delivery_date: str | None = None,
        shipping_method: str = "standard",
        total_amount: float,
        tax_rate: float = 0.0,
        currency: str = "EUR",
        status: str = STATUS_PENDING,
        is_active: bool = True,
        created_by: str = "system",
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        if not organisation_id:
            raise OrderError("organisation_id requis")
        if not company_id:
            raise OrderError("company_id requis")
        if not quotation_id:
            raise OrderError("quotation_id requis")
        if shipping_method not in self.SHIPPING_METHODS:
            raise OrderError(
                f"shipping_method invalide : {shipping_method}. "
                f"Valeurs possibles : {self.SHIPPING_METHODS}"
            )
        if status not in self.ALLOWED_STATUS:
            raise OrderError(
                f"status invalide : {status}. Valeurs possibles : {self.ALLOWED_STATUS}"
            )
        if total_amount < 0:
            raise OrderError("total_amount ne peut pas être négatif")
        if currency and len(currency) != 3:
            raise OrderError("currency doit faire 3 caractères")

        # Validation des dates
        if delivery_date is not None and order_date is not None:
            if order_date > delivery_date:
                raise OrderError("delivery_date doit être après order_date")

        self.id: str = id or f"order-{uuid.uuid4().hex[:12]}"
        self.organisation_id: str = organisation_id
        self.company_id: str = company_id
        self.contact_id: str | None = contact_id
        self.user_id: str | None = user_id
        self.quotation_id: str = quotation_id
        self.order_date: str = order_date or datetime.now(timezone.utc).isoformat()
        self.delivery_date: str | None = delivery_date
        self.shipping_method: str = shipping_method
        self.total_amount: float = total_amount
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
            "quotation_id": self.quotation_id,
            "order_date": self.order_date,
            "delivery_date": self.delivery_date,
            "shipping_method": self.shipping_method,
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
        return f"<Order {self.id} status={self.status} total={self.total_amount}>"
