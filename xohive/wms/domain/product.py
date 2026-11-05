"""Modèle Product pour le WMS."""

from dataclasses import dataclass, field
from typing import Optional


class ProductError(Exception):
    """Erreur liée à un produit."""


@dataclass
class Product:
    """Représentation d'un produit géré en stock."""

    id: Optional[str] = None
    organisation_id: str = ""
    sku: str = ""
    name: str = ""
    description: str = ""
    unit: str = "unit"
    category: str = ""
    default_price: float = 0.0
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        if not self.sku:
            raise ProductError("sku requis")
        if not self.name:
            raise ProductError("name requis")
        if self.default_price < 0:
            raise ProductError("default_price ne peut pas être négatif")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organisation_id": self.organisation_id,
            "sku": self.sku,
            "name": self.name,
            "description": self.description,
            "unit": self.unit,
            "category": self.category,
            "default_price": self.default_price,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
