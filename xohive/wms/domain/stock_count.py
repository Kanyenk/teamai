"""Modèle de domaine : StockCount (comptage physique d'inventaire)."""

from __future__ import annotations

from dataclasses import dataclass

# Statuts possibles d'un comptage :
# - draft : comptage saisi, pas encore ajusté ;
# - adjusted : ajustement de stock appliqué.
VALID_COUNT_STATUSES = {"draft", "adjusted"}


@dataclass(frozen=True)
class StockCount:
    """Comptage physique d'un produit dans un entrepôt."""

    organisation_id: str
    warehouse_id: str
    product_id: str
    counted_quantity: int
    status: str = "draft"
    id: str | None = None
    created_at: str | None = None

    def __post_init__(self) -> None:
        # Validations de base : champs obligatoires et cohérence.
        if not self.organisation_id:
            raise ValueError("organisation_id is required")
        if not self.warehouse_id:
            raise ValueError("warehouse_id is required")
        if not self.product_id:
            raise ValueError("product_id is required")
        if self.counted_quantity < 0:
            raise ValueError("counted_quantity must be >= 0")
        if self.status not in VALID_COUNT_STATUSES:
            raise ValueError(
                f"status must be one of {sorted(VALID_COUNT_STATUSES)}"
            )

    def to_dict(self) -> dict:
        """Sérialise le comptage en dictionnaire (pour l'API)."""
        return {
            "id": self.id,
            "organisation_id": self.organisation_id,
            "warehouse_id": self.warehouse_id,
            "product_id": self.product_id,
            "counted_quantity": self.counted_quantity,
            "status": self.status,
            "created_at": self.created_at,
        }
