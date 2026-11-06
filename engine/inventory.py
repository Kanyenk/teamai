"""Entité Inventory."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass
class Inventory:
    """Représente un(e) inventory."""

    organisation_id: str
    warehouse_id: str
    product_id: str
    counted_quantity: int
    expected_quantity: int
    note: str = ""
    id: str = field(default_factory=lambda: f"inv-{uuid.uuid4().hex[:12]}")
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.organisation_id or not isinstance(self.organisation_id, str):
            raise ValueError("organisation_id requis et non vide")
        if not self.warehouse_id or not isinstance(self.warehouse_id, str):
            raise ValueError("warehouse_id requis et non vide")
        if not self.product_id or not isinstance(self.product_id, str):
            raise ValueError("product_id requis et non vide")
        if not isinstance(self.counted_quantity, int) or self.counted_quantity < 0:
            raise ValueError("counted_quantity doit être un entier positif ou nul")
        if not isinstance(self.expected_quantity, int) or self.expected_quantity < 0:
            raise ValueError("expected_quantity doit être un entier positif ou nul")

    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'entité en dictionnaire."""
        return {
            "id": self.id,
            "organisation_id": self.organisation_id,
            "warehouse_id": self.warehouse_id,
            "product_id": self.product_id,
            "counted_quantity": self.counted_quantity,
            "expected_quantity": self.expected_quantity,
            "note": self.note,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<Inventory {self.id}>"
