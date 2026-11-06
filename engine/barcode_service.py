"""Service Barcode."""
from __future__ import annotations

from typing import Optional

from engine.barcode import Barcode
from engine.barcode_repository import BarcodeRepository


class BarcodeService:
    """Orchestre la création et la consultation des barcodes."""

    def __init__(self, repo: BarcodeRepository) -> None:
        self.repo = repo

    def create(self, **kwargs) -> Barcode:
        obj = Barcode(**kwargs)
        return self.repo.create(obj)

    def get(self, obj_id: str) -> Optional[Barcode]:
        return self.repo.get(obj_id)

    def list(self, organisation_id: str):
        return self.repo.list(organisation_id)

    def lookup(self, organisation_id: str, code: str) -> Optional[Barcode]:
        return self.repo.get_by_code(organisation_id, code)

    def delete(self, obj_id: str) -> bool:
        return self.repo.delete(obj_id)
