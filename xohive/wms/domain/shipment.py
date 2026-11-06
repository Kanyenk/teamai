"""Modèle de domaine : Shipment (expédition client)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Shipment:
    """Expédition d'un produit vers un client."""

    organisation_id: str
    order_id: str
    warehouse_id: str
    product_id: str
    quantity: int
    status: str = "draft"
    carrier: str | None = None
    tracking_number: str | None = None
    id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organisation_id": self.organisation_id,
            "order_id": self.order_id,
            "warehouse_id": self.warehouse_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "status": self.status,
            "carrier": self.carrier,
            "tracking_number": self.tracking_number,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __post_init__(self) -> None:
        if not self.organisation_id:
            raise ValueError("organisation_id is required")
        if not self.order_id:
            raise ValueError("order_id is required")
        if not self.warehouse_id:
            raise ValueError("warehouse_id is required")
        if not self.product_id:
            raise ValueError("product_id is required")
        if not isinstance(self.quantity, int) or isinstance(self.quantity, bool) or self.quantity <= 0:
            raise ValueError("quantity must be a positive integer")
        if self.status not in {"draft", "shipped"}:
            raise ValueError("status must be draft or shipped")
