"""Entité StockTransfer."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass
class StockTransfer:
    """Représente un(e) stock transfer."""

    organisation_id: str
    from_warehouse_id: str
    to_warehouse_id: str
    product_id: str
    quantity: int
    status: str = "draft"
    note: str = ""
    id: str = field(default_factory=lambda: f"trf-{uuid.uuid4().hex[:12]}")
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.organisation_id or not isinstance(self.organisation_id, str):
            raise ValueError("organisation_id requis et non vide")
        if not self.from_warehouse_id or not isinstance(self.from_warehouse_id, str):
            raise ValueError("from_warehouse_id requis et non vide")
        if not self.to_warehouse_id or not isinstance(self.to_warehouse_id, str):
            raise ValueError("to_warehouse_id requis et non vide")
        if not self.product_id or not isinstance(self.product_id, str):
            raise ValueError("product_id requis et non vide")
        if not isinstance(self.quantity, int) or self.quantity <= 0:
            raise ValueError("quantity doit être un entier non nul")

    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'entité en dictionnaire."""
        return {
            "id": self.id,
            "organisation_id": self.organisation_id,
            "from_warehouse_id": self.from_warehouse_id,
            "to_warehouse_id": self.to_warehouse_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "status": self.status,
            "note": self.note,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<StockTransfer {self.id}>"
