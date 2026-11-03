"""Role — Entité Rôle avec permissions.

Attributs :
- id : TEXT/UUID (obligatoire)
- code : TEXT (obligatoire, code du rôle ex: `admin`, `worker`, `auditor`)
- label : TEXT (obligatoire, libellé français)
- description : TEXT (optionnel)
- organisation_id : TEXT (obligatoire, N→1 avec Organization)
- permissions : TEXT (obligatoire, listes des codes de permission, JSON)
- created_by : TEXT (optionnel)
- created_at : DATETIME (optionnel)
- updated_at : DATETIME (optionnel)

Relations : N → 1 Organisation, N → 1 User.
"""

from __future__ import annotations

import uuid


class Role:
    """Représentation d'un rôle avec ses permissions."""

    def __init__(
        self,
        *,
        id: str | None = None,
        code: str,
        label: str,
        description: str | None = None,
        organisation_id: str,
        permissions: list[str] | None = None,
        created_by: str = "system",
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        if not code:
            raise ValueError("code est obligatoire")
        if not label:
            raise ValueError("label est obligatoire")
        if not organisation_id:
            raise ValueError("organisation_id est obligatoire")

        self.id: str = id or f"rol-{uuid.uuid4().hex[:12]}"
        self.code: str = code
        self.label: str = label
        self.description: str | None = description
        self.organisation_id: str = organisation_id
        self.permissions: list[str] = permissions or []
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

    def add_permission(self, permission_code: str) -> None:
        """Ajoute une permission au rôle."""
        if permission_code not in self.permissions:
            self.permissions.append(permission_code)

    def remove_permission(self, permission_code: str) -> None:
        """Retire une permission du rôle."""
        if permission_code in self.permissions:
            self.permissions.remove(permission_code)

    def has_permission(self, permission_code: str) -> bool:
        """Vérifie si le rôle possède une permission."""
        return permission_code in self.permissions

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "label": self.label,
            "description": self.description,
            "organisation_id": self.organisation_id,
            "permissions": self.permissions,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __repr__(self) -> str:
        return f"<Role {self.id} {self.code} {self.label}>"
