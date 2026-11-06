"""Entité Location."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass
class Location:
    """Représente un(e) location."""

    organisation_id: str
    warehouse_id: str
    code: str
    name: str = ''
    zone: str = ''
    capacity: int = 0
    id: str = field(default_factory=lambda: f"loc-{uuid.uuid4().hex[:12]}")
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.organisation_id or not isinstance(self.organisation_id, str):
            raise ValueError("organisation_id requis et non vide")
        if not self.warehouse_id or not isinstance(self.warehouse_id, str):
            raise ValueError("warehouse_id requis et non vide")
        if not self.code or not isinstance(self.code, str):
            raise ValueError("code requis et non vide")

    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'entité en dictionnaire."""
        return {
            "id": self.id,
            "organisation_id": self.organisation_id,
            "warehouse_id": self.warehouse_id,
            "code": self.code,
            "name": self.name,
            "zone": self.zone,
            "capacity": self.capacity,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<Location {self.id}>"
