"""Service StockAdjustment (logique métier des ajustements de stock)."""
from __future__ import annotations

from typing import Optional

from engine.stock_adjustment import StockAdjustment
from engine.stock_adjustment_repository import StockAdjustmentRepository


class StockAdjustmentService:
    """Orchestre la création et la consultation des ajustements de stock."""

    def __init__(self, repo: StockAdjustmentRepository) -> None:
        self.repo = repo

    def create_adjustment(
        self,
        organisation_id: str,
        warehouse_id: str,
        product_id: str,
        quantity: int,
        reason: str,
        note: str = "",
    ) -> StockAdjustment:
        """Crée un ajustement de stock."""
        adj = StockAdjustment(
            organisation_id=organisation_id,
            warehouse_id=warehouse_id,
            product_id=product_id,
            quantity=quantity,
            reason=reason,
            note=note,
        )
        return self.repo.create(adj)

    def get_adjustment(self, adjustment_id: str) -> Optional[StockAdjustment]:
        """Récupère un ajustement par id."""
        return self.repo.get(adjustment_id)

    def list_adjustments(self, organisation_id: str):
        """Liste les ajustements d'une organisation."""
        return self.repo.list(organisation_id)

    def delete_adjustment(self, adjustment_id: str) -> bool:
        """Supprime un ajustement."""
        return self.repo.delete(adjustment_id)
