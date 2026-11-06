"""Entité Barcode."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass
class Barcode:
    """Représente un(e) barcode."""

    organisation_id: str
    product_id: str
    code: str
    type: str
    label: str = ''
    id: str = field(default_factory=lambda: f"brc-{uuid.uuid4().hex[:12]}")
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.organisation_id or not isinstance(self.organisation_id, str):
            raise ValueError("organisation_id requis et non vide")
        if not self.product_id or not isinstance(self.product_id, str):
            raise ValueError("product_id requis et non vide")
        if not self.code or not isinstance(self.code, str):
            raise ValueError("code requis et non vide")
        if not self.type or not isinstance(self.type, str):
            raise ValueError("type requis et non vide")

    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'entité en dictionnaire."""
        return {
            "id": self.id,
            "organisation_id": self.organisation_id,
            "product_id": self.product_id,
            "code": self.code,
            "type": self.type,
            "label": self.label,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<Barcode {self.id}>"
