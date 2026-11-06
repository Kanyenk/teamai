"""Entité StockAdjustment (ajustement de stock)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict

VALID_REASONS = {"damage", "loss", "found", "correction", "other"}


@dataclass
class StockAdjustment:
    """Représente un ajustement de stock (entrée ou sortie non liée à une commande)."""

    organisation_id: str
    warehouse_id: str
    product_id: str
    quantity: int
    reason: str
    note: str = ""
    id: str = field(default_factory=lambda: f"adj-{uuid.uuid4().hex[:12]}")
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.organisation_id or not isinstance(self.organisation_id, str):
            raise ValueError("organisation_id requis et non vide")
        if not self.warehouse_id or not isinstance(self.warehouse_id, str):
            raise ValueError("warehouse_id requis et non vide")
        if not self.product_id or not isinstance(self.product_id, str):
            raise ValueError("product_id requis et non vide")
        if not isinstance(self.quantity, int) or self.quantity == 0:
            raise ValueError("quantity doit être un entier non nul (positif ou négatif)")
        if self.reason not in VALID_REASONS:
            raise ValueError(f"raison invalide : {self.reason}")
        if not isinstance(self.note, str):
            raise ValueError("note doit être une chaîne")

    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'entité en dictionnaire."""
        return {
            "id": self.id,
            "organisation_id": self.organisation_id,
            "warehouse_id": self.warehouse_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "reason": self.reason,
            "note": self.note,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<StockAdjustment {self.id} qty={self.quantity} reason={self.reason}>"
