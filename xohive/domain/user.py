"""User — Entité Utilisateur du socle ERP.

Attributs :
- id : TEXT/UUID (obligatoire)
- email : TEXT (obligatoire, unique)
- password_hash : TEXT (obligatoire)
- first_name : TEXT (optionnel)
- last_name : TEXT (optionnel)
- phone : TEXT (optionnel)
- timezone : TEXT (optionnel)
- language : TEXT (optionnel)
- is_active : BOOLEAN (obligatoire)
- is_verified : BOOLEAN (obligatoire)
- organisation_id : TEXT (obligatoire, N→1 avec Organization)
- created_by : TEXT (optionnel)
- created_at : DATETIME (optionnel)
- updated_at : DATETIME (optionnel)

Relations : N → 1 Organisation, 1 → N Roles, 1 → N AuditEvent.
"""

from __future__ import annotations

import uuid


class User:
    """Représentation d'un utilisateur de la plateforme."""

    def __init__(
        self,
        *,
        id: str | None = None,
        email: str,
        password_hash: str,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
        timezone: str = "UTC",
        language: str = "fr",
        is_active: bool = True,
        is_verified: bool = False,
        organisation_id: str,
        created_by: str = "system",
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        if not email:
            raise ValueError("email est obligatoire")
        if "@" not in email or "." not in email:
            raise ValueError("email invalide")
        if not password_hash:
            raise ValueError("password_hash est obligatoire")
        if not organisation_id:
            raise ValueError("organisation_id est obligatoire")

        self.id: str = id or f"usr-{uuid.uuid4().hex[:12]}"
        self.email: str = email.lower().strip()
        self.password_hash: str = password_hash
        self.first_name: str | None = first_name
        self.last_name: str | None = last_name
        self.phone: str | None = phone
        self.timezone: str = timezone
        self.language: str = language
        self.is_active: bool = is_active
        self.is_verified: bool = is_verified
        self.organisation_id: str = organisation_id
        self.created_by: str = created_by
        self.created_at: str = created_at or self._now_iso()
        self._updated_at: str | None = updated_at

    def _now_iso(self) -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()

    @property
    def updated_at(self) -> str:
        return self._updated_at or self.created_at

    @updated_at.setter
    def updated_at(self, value: str | None) -> None:
        self._updated_at = value

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "password_hash": self.password_hash,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "timezone": self.timezone,
            "language": self.language,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "organisation_id": self.organisation_id,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __repr__(self) -> str:
        return f"<User {self.id} {self.email}>"
