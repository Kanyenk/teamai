"""Company — Entité Company du module CRM minimal.

Attributs :
- id : TEXT/UUID (obligatoire)
- name : TEXT (obligatoire)
- siret : TEXT (requis, 14 chiffres)
- address : TEXT (optionnel)
- city : TEXT (optionnel)
- zip_code : TEXT (optionnel)
- country : TEXT (optionnel, default FR)
- website : TEXT (optionnel)
- phone : TEXT (optionnel)
- email : TEXT (optionnel, format email)
- contact_person : TEXT (optionnel)
- is_active : BOOLEAN (obligatoire, default True)
- created_by : TEXT (optionnel, default "system")
- created_at : DATETIME (obligatoire, timestamp)
- updated_at : DATETIME (optionnel)

Relations : N → 1 Organisation (via organisation_id).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


class CompanyError(Exception):
    """Erreur de validation ou de manipulation d'une company."""


class Company:
    """Représentation d'une entreprise (CRM minimal)."""

    ALLOWED_COUNTRIES = ("FR", "BE", "LU", "CH", "DE", "ES")

    def __init__(
        self,
        *,
        id: str | None = None,
        organisation_id: str,
        name: str,
        siret: str,
        address: str | None = None,
        city: str | None = None,
        zip_code: str | None = None,
        country: str = "FR",
        website: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        contact_person: str | None = None,
        is_active: bool = True,
        created_by: str = "system",
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        if not name:
            raise CompanyError("nom de la société requis")
        if not siret or len(siret) != 14 or not siret.isdigit():
            raise CompanyError("SIRET invalide (14 chiffres requis)")
        if country not in self.ALLOWED_COUNTRIES:
            raise CompanyError(f"pays invalide : {country!r}")
        if email is not None and email and "@" not in email:
            raise CompanyError("email invalide")

        self.id: str = id or f"crm-{uuid.uuid4().hex[:12]}"
        self.organisation_id: str = organisation_id
        self.name: str = name
        self.siret: str = siret
        self.address: str | None = address
        self.city: str | None = city
        self.zip_code: str | None = zip_code
        self.country: str = country
        self.website: str | None = website
        self.phone: str | None = phone
        self.email: str | None = email
        self.contact_person: str | None = contact_person
        self.is_active: bool = is_active
        self.created_by: str = created_by
        self.created_at: str = created_at or self._now_iso()
        self.updated_at: str | None = updated_at

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def deactivate(self) -> None:
        """Désactive la société."""
        self.is_active = False
        self.updated_at = self._now_iso()

    def to_dict(self) -> dict[str, Any]:
        """Sérialise la company en dictionnaire."""
        return {
            "id": self.id,
            "organisation_id": self.organisation_id,
            "name": self.name,
            "siret": self.siret,
            "address": self.address,
            "city": self.city,
            "zip_code": self.zip_code,
            "country": self.country,
            "website": self.website,
            "phone": self.phone,
            "email": self.email,
            "contact_person": self.contact_person,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __repr__(self) -> str:
        return f"<Company {self.id} {self.name} {self.is_active}>"


if __name__ == "__main__":
    pass