"""Modèle de domaine : StockMovement (mouvement de stock)."""

from __future__ import annotations

from dataclasses import dataclass

VALID_MOVEMENT_TYPES = {"in", "out", "transfer", "adjustment"}


@dataclass(frozen=True)
class StockMovement:
    """Mouvement de stock : entrée, sortie, transfert ou ajustement."""

    organisation_id: str
    product_id: str
    warehouse_id: str
    movement_type: str
    quantity: int
    target_warehouse_id: str | None = None
    reason: str | None = None
    id: str | None = None
    created_at: str | None = None

    def __post_init__(self) -> None:
        if not self.organisation_id:
            raise ValueError("organisation_id is required")
        if not self.product_id:
            raise ValueError("product_id is required")
        if not self.warehouse_id:
            raise ValueError("warehouse_id is required")
        if self.movement_type not in VALID_MOVEMENT_TYPES:
            raise ValueError(
                f"movement_type must be one of {sorted(VALID_MOVEMENT_TYPES)}"
            )
        if self.quantity <= 0:
            raise ValueError("quantity must be > 0")
        if self.movement_type == "transfer" and not self.target_warehouse_id:
            raise ValueError("target_warehouse_id is required for transfer")
        if self.movement_type != "transfer" and self.target_warehouse_id:
            raise ValueError(
                "target_warehouse_id only allowed for transfer"
            )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organisation_id": self.organisation_id,
            "product_id": self.product_id,
            "warehouse_id": self.warehouse_id,
            "movement_type": self.movement_type,
            "quantity": self.quantity,
            "target_warehouse_id": self.target_warehouse_id,
            "reason": self.reason,
            "created_at": self.created_at,
        }
