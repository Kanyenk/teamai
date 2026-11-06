"""Service Location."""
from __future__ import annotations

from typing import Optional

from engine.location import Location
from engine.location_repository import LocationRepository


class LocationService:
    """Orchestre la création et la consultation des locations."""

    def __init__(self, repo: LocationRepository) -> None:
        self.repo = repo

    def create(self, **kwargs) -> Location:
        obj = Location(**kwargs)
        return self.repo.create(obj)

    def get(self, obj_id: str) -> Optional[Location]:
        return self.repo.get(obj_id)

    def list(self, organisation_id: str):
        return self.repo.list(organisation_id)

    def delete(self, obj_id: str) -> bool:
        return self.repo.delete(obj_id)
