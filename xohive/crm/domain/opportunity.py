"""Opportunity — Entité Opportunité du module CRM minimal.

Attributs :
- id : TEXT/UUID (obligatoire)
- company_id : TEXT (obligatoire, N→1 avec Company)
- contact_id : TEXT (optionnel, N→1 avec Contact)
- title : TEXT (obligatoire)
- amount : FLOAT (obligatoire, > 0)
- stage : TEXT (obligatoire, pipeline d'états)
- probability : FLOAT (optionnel, 0-100)
- close_date : TEXT (optionnel)
- is_active : BOOLEAN (obligatoire, default True)
- created_by : TEXT (optionnel, default "system")
- created_at : DATETIME (obligatoire)
- updated_at : DATETIME (optionnel)

Pipeline d'états : prospecting → qualifier → proposition → négociation → fermé
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


class OpportunityError(Exception):
    """Erreur de validation ou de manipulation d'une opportunité."""


class Opportunity:
    """Représentation d'une opportunité de vente."""

    # États du pipeline
    STAGE_PROSPECTING = "prospecting"
    STAGE_QUALIFYING = "qualifying"
    STAGE_PROPOSITION = "proposition"
    STAGE_NEGOTIATION = "negociation"
    STAGE_CLOSED = "closed"

    ALLOWED_STAGES = (
        STAGE_PROSPECTING,
        STAGE_QUALIFYING,
        STAGE_PROPOSITION,
        STAGE_NEGOTIATION,
        STAGE_CLOSED,
    )

    def __init__(
        self,
        *,
        id: str | None = None,
        organisation_id: str,
        company_id: str,
        contact_id: str | None = None,
        title: str,
        amount: float,
        stage: str = STAGE_PROSPECTING,
        probability: float | None = None,
        close_date: str | None = None,
        is_active: bool = True,
        created_by: str = "system",
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        if not title:
            raise OpportunityError("titre requis")
        if amount <= 0:
            raise OpportunityError("montant doit être > 0")
        if stage not in self.ALLOWED_STAGES:
            raise OpportunityError(f"stage invalide : {stage!r}")
        if probability is not None and not (0 <= probability <= 100):
            raise OpportunityError("probabilité doit être entre 0 et 100")

        self.id: str = id or f"crm-{uuid.uuid4().hex[:12]}"
        self.organisation_id: str = organisation_id
        self.company_id: str = company_id
        self.contact_id: str | None = contact_id
        self.title: str = title
        self.amount: float = amount
        self.stage: str = stage
        self.probability: float | None = probability
        self.close_date: str | None = close_date
        self.is_active: bool = is_active
        self.created_by: str = created_by
        self.created_at: str = created_at or self._now_iso()
        self.updated_at: str | None = updated_at

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def is_closed(self) -> bool:
        """Vérifie si l'opportunité est fermée."""
        return self.stage == self.STAGE_CLOSED

    def advance(self) -> None:
        """Fait progresser l'opportunité vers l'étape suivante."""
        stages = [
            self.STAGE_PROSPECTING,
            self.STAGE_QUALIFYING,
            self.STAGE_PROPOSITION,
            self.STAGE_NEGOTIATION,
            self.STAGE_CLOSED,
        ]
        idx = stages.index(self.stage)
        if idx < len(stages) - 1:
            self.stage = stages[idx + 1]
            self.updated_at = self._now_iso()

    def to_dict(self) -> dict[str, Any]:
        """Sérialise l'opportunité en dictionnaire."""
        return {
            "id": self.id,
            "organisation_id": self.organisation_id,
            "company_id": self.company_id,
            "contact_id": self.contact_id,
            "title": self.title,
            "amount": self.amount,
            "stage": self.stage,
            "probability": self.probability,
            "close_date": self.close_date,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __repr__(self) -> str:
        return f"<Opportunity {self.id} {self.title} {self.stage}>"


if __name__ == "__main__":
    pass
