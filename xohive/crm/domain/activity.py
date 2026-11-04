"""Activity — Entité Activité du module CRM minimal.

Attributs :
- id : TEXT/UUID (obligatoire)
- company_id : TEXT (obligatoire, N→1 avec Company)
- contact_id : TEXT (optionnel, N→1 avec Contact)
- user_id : TEXT (optionnel, N→1 avec User)
- type : TEXT (obligatoire, type d'activité)
- subject : TEXT (obligatoire)
- description : TEXT (optionnel)
- date : TEXT (obligatoire, date ISO)
- duration : FLOAT (optionnel, durée en minutes)
- status : TEXT (obligatoire, status de l'activité)
- is_active : BOOLEAN (obligatoire, default True)
- created_by : TEXT (optionnel, default "system")
- created_at : DATETIME (obligatoire)
- updated_at : DATETIME (optionnel)

Types d'activités : appel, réunion, email, note
Status : pending, done, cancelled
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


class ActivityError(Exception):
    """Erreur de validation ou de manipulation d'une activité."""


class Activity:
    """Représentation d'une activité CRM."""

    # Types d'activités
    TYPE_CALL = "appel"
    TYPE_MEETING = "reunion"
    TYPE_EMAIL = "email"
    TYPE_NOTE = "note"

    ALLOWED_TYPES = (TYPE_CALL, TYPE_MEETING, TYPE_EMAIL, TYPE_NOTE)

    # Status d'activité
    STATUS_PENDING = "pending"
    STATUS_DONE = "done"
    STATUS_CANCELLED = "cancelled"

    ALLOWED_STATUS = (STATUS_PENDING, STATUS_DONE, STATUS_CANCELLED)

    def __init__(
        self,
        *,
        id: str | None = None,
        organisation_id: str,
        company_id: str,
        contact_id: str | None = None,
        user_id: str | None = None,
        type: str = TYPE_CALL,
        subject: str,
        description: str | None = None,
        date: str | None = None,
        duration: float | None = None,
        status: str = STATUS_PENDING,
        is_active: bool = True,
        created_by: str = "system",
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        if not subject:
            raise ActivityError("sujet requis")
        if type not in self.ALLOWED_TYPES:
            raise ActivityError(f"type d'activité invalide : {type!r}")
        if status not in self.ALLOWED_STATUS:
            raise ActivityError(f"status invalide : {status!r}")
        if date is not None and "T" not in date:
            raise ActivityError("date doit être au format ISO (YYYY-MM-DDT...)")
        if duration is not None and duration < 0:
            raise ActivityError("durée négative")

        self.id: str = id or f"crm-{uuid.uuid4().hex[:12]}"
        self.organisation_id: str = organisation_id
        self.company_id: str = company_id
        self.contact_id: str | None = contact_id
        self.user_id: str | None = user_id
        self.type: str = type
        self.subject: str = subject
        self.description: str | None = description
        self.date: str = date or self._now_iso()
        self.duration: float | None = duration
        self.status: str = status
        self.is_active: bool = is_active
        self.created_by: str = created_by
        self.created_at: str = created_at or self._now_iso()
        self.updated_at: str | None = updated_at

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def mark_done(self) -> None:
        """Marque l'activité comme terminée."""
        self.status = self.STATUS_DONE
        self.updated_at = self._now_iso()

    def mark_cancelled(self) -> None:
        """Marque l'activité comme annulée."""
        self.status = self.STATUS_CANCELLED
        self.updated_at = self._now_iso()

    def to_dict(self) -> dict[str, Any]:
        """Sérialise l'activité en dictionnaire."""
        return {
            "id": self.id,
            "organisation_id": self.organisation_id,
            "company_id": self.company_id,
            "contact_id": self.contact_id,
            "user_id": self.user_id,
            "type": self.type,
            "subject": self.subject,
            "description": self.description,
            "date": self.date,
            "duration": self.duration,
            "status": self.status,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __repr__(self) -> str:
        return f"<Activity {self.id} {self.type} {self.subject}>"


if __name__ == "__main__":
    pass
