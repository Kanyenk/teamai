"""Modèle de domaine : Warehouse (entrepôt)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class Warehouse:
    """Entrepôt physique ou logique du WMS."""

    organisation_id: str
    code: str
    name: str
    address: str | None = None
    is_active: bool = True
    id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organisation_id": self.organisation_id,
            "code": self.code,
            "name": self.name,
            "address": self.address,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


    def __post_init__(self) -> None:
        if not self.organisation_id:
            raise ValueError("organisation_id is required")
        if not self.code:
            raise ValueError("code is required")
        if not self.name:
            raise ValueError("name is required")
        # Code : lettres, chiffres, tirets, 2-32 caractères
        if not re.fullmatch(r"[A-Za-z0-9\-]{2,32}", self.code):
            raise ValueError(
                "code must be 2-32 chars, letters/digits/hyphens only"
            )
