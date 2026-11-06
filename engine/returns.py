"""Entité Return (retour client)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict

VALID_STATUSES = {"draft", "requested", "received", "refunded", "cancelled"}


@dataclass
class Return:
    """Représente un retour client (produit renvoyé)."""

    organisation_id: str
    order_id: str
    product_id: str
    quantity: int
    reason: str
    status: str = "draft"
    refund_amount: float = 0.0
    id: str = field(default_factory=lambda: f"ret-{uuid.uuid4().hex[:12]}")
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.organisation_id or not isinstance(self.organisation_id, str):
            raise ValueError("organisation_id requis et non vide")
        if not self.order_id or not isinstance(self.order_id, str):
            raise ValueError("order_id requis et non vide")
        if not self.product_id or not isinstance(self.product_id, str):
            raise ValueError("product_id requis et non vide")
        if not isinstance(self.quantity, int) or self.quantity <= 0:
            raise ValueError("quantity doit être un entier positif")
        if not self.reason or not isinstance(self.reason, str):
            raise ValueError("reason requis et non vide")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"status invalide : {self.status}")
        if not isinstance(self.refund_amount, (int, float)) or self.refund_amount < 0:
            raise ValueError("refund_amount doit être un nombre positif ou nul")

    def mark_requested(self) -> None:
        """Passe le retour à 'requested'."""
        if self.status != "draft":
            raise ValueError("seul un retour en draft peut passer à requested")
        self.status = "requested"
        self.updated_at = datetime.now(timezone.utc)

    def mark_received(self) -> None:
        """Passe le retour à 'received'."""
        if self.status != "requested":
            raise ValueError("seul un retour en requested peut passer à received")
        self.status = "received"
        self.updated_at = datetime.now(timezone.utc)

    def mark_refunded(self, amount: float) -> None:
        """Passe le retour à 'refunded' avec un montant."""
        if self.status != "received":
            raise ValueError("seul un retour en received peut passer à refunded")
        if not isinstance(amount, (int, float)) or amount < 0:
            raise ValueError("refund_amount doit être un nombre positif ou nul")
        self.refund_amount = amount
        self.status = "refunded"
        self.updated_at = datetime.now(timezone.utc)

    def cancel(self) -> None:
        """Annule le retour."""
        if self.status in ("refunded", "cancelled"):
            raise ValueError("un retour refunded ou cancelled ne peut pas être annulé")
        self.status = "cancelled"
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'entité en dictionnaire."""
        return {
            "id": self.id,
            "organisation_id": self.organisation_id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "reason": self.reason,
            "status": self.status,
            "refund_amount": self.refund_amount,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<Return {self.id} status={self.status}>"
