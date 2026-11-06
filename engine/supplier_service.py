"""Service Supplier."""
from __future__ import annotations

from typing import Optional

from engine.supplier import Supplier
from engine.supplier_repository import SupplierRepository


class SupplierService:
    """Orchestre la création et la consultation des suppliers."""

    def __init__(self, repo: SupplierRepository) -> None:
        self.repo = repo

    def create(self, **kwargs) -> Supplier:
        obj = Supplier(**kwargs)
        return self.repo.create(obj)

    def get(self, obj_id: str) -> Optional[Supplier]:
        return self.repo.get(obj_id)

    def list(self, organisation_id: str):
        return self.repo.list(organisation_id)

    def delete(self, obj_id: str) -> bool:
        return self.repo.delete(obj_id)
