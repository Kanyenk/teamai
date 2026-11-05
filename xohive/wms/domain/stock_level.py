"""Modèle de domaine : StockLevel (niveau de stock)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StockLevel:
    """Quantité d'un produit dans un entrepôt donné."""

    organisation_id: str
    product_id: str
    warehouse_id: str
    quantity: int = 0
    id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    def __post_init__(self) -> None:
        if not self.organisation_id:
            raise ValueError("organisation_id is required")
        if not self.product_id:
            raise ValueError("product_id is required")
        if not self.warehouse_id:
            raise ValueError("warehouse_id is required")
        if self.quantity < 0:
            raise ValueError("quantity must be >= 0")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organisation_id": self.organisation_id,
            "product_id": self.product_id,
            "warehouse_id": self.warehouse_id,
            "quantity": self.quantity,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
