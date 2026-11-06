"""Service Inventory."""
from __future__ import annotations

from typing import Optional

from engine.inventory import Inventory
from engine.inventory_repository import InventoryRepository


class InventoryService:
    """Orchestre la création et la consultation des inventories."""

    def __init__(self, repo: InventoryRepository) -> None:
        self.repo = repo

    def create(self, **kwargs) -> Inventory:
        obj = Inventory(**kwargs)
        return self.repo.create(obj)

    def get(self, obj_id: str) -> Optional[Inventory]:
        return self.repo.get(obj_id)

    def list(self, organisation_id: str):
        return self.repo.list(organisation_id)

    def delete(self, obj_id: str) -> bool:
        return self.repo.delete(obj_id)
