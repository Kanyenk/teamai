"""Service StockTransfer."""
from __future__ import annotations

from typing import Optional

from engine.stock_transfer import StockTransfer
from engine.stock_transfer_repository import StockTransferRepository


class StockTransferService:
    """Orchestre la création et la consultation des stock_transfers."""

    def __init__(self, repo: StockTransferRepository) -> None:
        self.repo = repo

    def create(self, **kwargs) -> StockTransfer:
        obj = StockTransfer(**kwargs)
        return self.repo.create(obj)

    def get(self, obj_id: str) -> Optional[StockTransfer]:
        return self.repo.get(obj_id)

    def list(self, organisation_id: str):
        return self.repo.list(organisation_id)

    def delete(self, obj_id: str) -> bool:
        return self.repo.delete(obj_id)
