"""Contact — Entité Contact du module CRM minimal.

Attributs :
- id : TEXT/UUID (obligatoire)
- first_name : TEXT (obligatoire)
- last_name : TEXT (obligatoire)
- email : TEXT (obligatoire, unique)
- phone : TEXT (optionnel)
- company_id : TEXT (obligatoire, N→1 avec Company)
- job_title : TEXT (optionnel)
- is_active : BOOLEAN (obligatoire, default True)
- created_by : TEXT (optionnel, default "system")
- created_at : DATETIME (obligatoire)
- updated_at : DATETIME (optionnel)

Relations : N → 1 Company, N → 1 User.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


class ContactError(Exception):
    """Erreur de validation ou de manipulation d'un contact."""


class Contact:
    """Représentation d'un contact CRM (lien avec Company)."""

    def __init__(
        self,
        *,
        id: str | None = None,
        organisation_id: str,
        company_id: str,
        first_name: str,
        last_name: str,
        email: str,
        phone: str | None = None,
        job_title: str | None = None,
        is_active: bool = True,
        created_by: str = "system",
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        if not first_name:
            raise ContactError("prénom requis")
        if not last_name:
            raise ContactError("nom requis")
        if "@" not in email or not email.strip():
            raise ContactError("email invalide")
        if not company_id:
            raise ContactError("company_id requis")

        self.id: str = id or f"crm-{uuid.uuid4().hex[:12]}"
        self.organisation_id: str = organisation_id
        self.company_id: str = company_id
        self.first_name: str = first_name
        self.last_name: str = last_name
        self.email: str = email.lower().strip()
        self.phone: str | None = phone
        self.job_title: str | None = job_title
        self.is_active: bool = is_active
        self.created_by: str = created_by
        self.created_at: str = created_at or self._now_iso()
        self.updated_at: str | None = updated_at

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def deactivate(self) -> None:
        """Désactive le contact."""
        self.is_active = False
        self.updated_at = self._now_iso()

    def to_dict(self) -> dict[str, Any]:
        """Sérialise le contact en dictionnaire."""
        return {
            "id": self.id,
            "organisation_id": self.organisation_id,
            "company_id": self.company_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "job_title": self.job_title,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __repr__(self) -> str:
        return f"<Contact {self.id} {self.first_name} {self.last_name} {self.is_active}>"


if __name__ == "__main__":
    pass
