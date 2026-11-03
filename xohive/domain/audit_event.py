"""AuditEvent — Événement d'audit pour le suivi des modifications.

Attributs :
- id : TEXT/UUID (obligatoire)
- user_id : TEXT (optionnel, NULL si système)
- organisation_id : TEXT (obligatoire)
- entity_type : TEXT (obligatoire, type d'entité modifiée)
- entity_id : TEXT (obligatoire, ID de l'entité)
- action : TEXT (obligatoire, `create`, `update`, `delete`, `transition`)
- old_values : TEXT (optionnel, valeur AVANT, JSON)
- new_values : TEXT (optionnel, valeur APRÈS, JSON)
- ip_address : TEXT (optionnel, IP source)
- user_agent : TEXT (optionnel, User-Agent)
- created_at : DATETIME (obligatoire, horodatage)

Relations : N → 1 Organisation, N → 1 User.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone


class AuditEvent:
    """Représentation d'un événement d'audit (trail de modification).

    Chaque mutation d'entité (create, update, delete, transition)
    produit un AuditEvent pour le suivi d'audit.
    """

    def __init__(
        self,
        *,
        id: str | None = None,
        user_id: str | None = None,
        organisation_id: str,
        entity_type: str,
        entity_id: str,
        action: str,
        old_values: dict | None = None,
        new_values: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        created_at: str | None = None,
    ) -> None:
        if not organisation_id:
            raise ValueError("organisation_id est obligatoire")
        if not entity_type:
            raise ValueError("entity_type est obligatoire")
        if not entity_id:
            raise ValueError("entity_id est obligatoire")
        if not action:
            raise ValueError("action est obligatoire")

        self.id: str = id or f"aud-{uuid.uuid4().hex[:12]}"
        self.user_id: str | None = user_id  # NULL si système
        self.organisation_id: str = organisation_id
        self.entity_type: str = entity_type
        self.entity_id: str = entity_id
        self.action: str = action
        self.old_values: dict | None = old_values
        self.new_values: dict | None = new_values
        self.ip_address: str | None = ip_address
        self.user_agent: str | None = user_agent
        self.created_at: str = created_at or self._now_iso()

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        """Sérialise l'AuditEvent en dictionnaire."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "organisation_id": self.organisation_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "action": self.action,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at,
        }

    @property
    def is_system(self) -> bool:
        """True si l'événement a été créé par le système."""
        return self.user_id is None

    @property
    def has_old_values(self) -> bool:
        """True si l'événement contient des valeurs AVANT."""
        return self.old_values is not None

    @property
    def has_new_values(self) -> bool:
        """True si l'événement contient des valeurs APRÈS."""
        return self.new_values is not None

    def __repr__(self) -> str:
        return f"<AuditEvent {self.id} {self.entity_type}/{self.entity_id} {self.action}>"
