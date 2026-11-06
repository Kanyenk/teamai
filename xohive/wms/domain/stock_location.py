"""Modèle StockLocation (emplacement de stock)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class StockLocation:
    organisation_id: str
    warehouse_id: str
    code: str
    name: str = ""
    zone: str = ""
    id: str = field(default="")
    created_at: str = field(default="")

    def __post_init__(self):
        if not self.organisation_id:
            raise ValueError("organisation_id is required")
        if not self.warehouse_id:
            raise ValueError("warehouse_id is required")
        if not self.code:
            raise ValueError("code is required")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organisation_id": self.organisation_id,
            "warehouse_id": self.warehouse_id,
            "code": self.code,
            "name": self.name,
            "zone": self.zone,
            "created_at": self.created_at,
        }

    def __repr__(self) -> str:
        return f"StockLocation(id={self.id!r}, code={self.code!r})"
