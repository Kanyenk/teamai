"""Modèle de domaine : PurchaseOrder (commande fournisseur)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class PurchaseOrder:
    """Commande d'achat auprès d'un fournisseur."""

    organisation_id: str
    supplier_name: str
    warehouse_id: str
    status: str = "draft"
    reference: str | None = None
    id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organisation_id": self.organisation_id,
            "supplier_name": self.supplier_name,
            "warehouse_id": self.warehouse_id,
            "status": self.status,
            "reference": self.reference,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __post_init__(self) -> None:
        if not self.organisation_id:
            raise ValueError("organisation_id is required")
        if not self.supplier_name:
            raise ValueError("supplier_name is required")
        if not self.warehouse_id:
            raise ValueError("warehouse_id is required")
        if self.status not in {"draft", "received", "cancelled"}:
            raise ValueError("status must be draft, received or cancelled")
