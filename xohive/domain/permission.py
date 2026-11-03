"""Permission — Entité Permission (module:action).

Attributs :
- id : TEXT/UUID (obligatoire)
- code : TEXT (obligatoire, code `module:action` ex: `doc:create`)
- label : TEXT (obligatoire, libellé français)
- description : TEXT (optionnel)
- module : TEXT (obligatoire, module cible)
- action : TEXT (obligatoire, action sur le module)
- organisation_id : TEXT (obligatoire, N→1 avec Organization)

Relations : 1 → N Role (via JSON de permissions).
"""

from __future__ import annotations

import uuid


class Permission:
    """Représentation d'une permission (code module:action)."""

    def __init__(
        self,
        *,
        id: str | None = None,
        code: str,
        label: str,
        description: str | None = None,
        module: str,
        action: str,
        organisation_id: str,
    ) -> None:
        if not code:
            raise ValueError("code est obligatoire")
        if not module:
            raise ValueError("module est obligatoire")
        if not action:
            raise ValueError("action est obligatoire")
        if ":" not in code:
            raise ValueError("code doit être au format module:action")

        self.id: str = id or f"per-{uuid.uuid4().hex[:12]}"
        self.code: str = code
        self.label: str = label
        self.description: str | None = description
        self.module: str = module
        self.action: str = action
        self.organisation_id: str = organisation_id

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "label": self.label,
            "description": self.description,
            "module": self.module,
            "action": self.action,
            "organisation_id": self.organisation_id,
        }

    def __repr__(self) -> str:
        return f"<Permission {self.id} {self.code}>"
