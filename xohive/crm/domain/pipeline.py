"""Pipeline — Machine à états (workflow d'opportunités CRM).

Entités :
- PipelineDefinition : définit le schéma des stages et leur séquence
- PipelineInstance : instance d'un pipeline en cours d'exécution
- PipelineEngine : orchestre les transitions et les hooks

Relations : N → 1 PipelineDefinition (chaque instance référence une définition).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Callable


class PipelineError(Exception):
    """Erreur de gestion d'un pipeline."""


class PipelineDefinition:
    """Définition d'un pipeline : schéma des stages et transitions."""

    def __init__(
        self,
        *,
        id: str | None = None,
        name: str,
        stage_schema: dict[str, list[str]],
        initial_stage: str,
        description: str = "",
    ) -> None:
        if not name:
            raise PipelineError("nom du pipeline requis")
        if initial_stage not in stage_schema:
            raise PipelineError(f"stage initial inconnu : {initial_stage!r}")

        self.id: str = id or f"pipe-{uuid.uuid4().hex[:12]}"
        self.name: str = name
        self.stage_schema: dict[str, list[str]] = stage_schema
        self.initial_stage: str = initial_stage
        self.description: str = description

    def est_transition_valide(self, from_stage: str, to_stage: str) -> bool:
        """Vérifie si une transition est autorisée."""
        return to_stage in self.stage_schema.get(from_stage, [])

    def get_next_stages(self, current_stage: str) -> list[str]:
        """Retourne les stages suivants possibles."""
        return self.stage_schema.get(current_stage, [])

    def __repr__(self) -> str:
        return f"<PipelineDefinition {self.id} {self.name}>"


class PipelineInstance:
    """Instance d'un pipeline en cours d'exécution."""

    def __init__(
        self,
        *,
        id: str | None = None,
        pipeline_id: str,
        definition: PipelineDefinition,
        stage: str | None = None,
        opportunity_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        current_user: str = "system",
    ) -> None:
        if definition.id != pipeline_id:
            raise PipelineError("la définition ne correspond pas à l'instance")
        if stage is None:
            stage = definition.initial_stage
        if stage not in definition.stage_schema:
            raise PipelineError(f"stage inconnu : {stage!r}")

        self.id: str = id or f"pinst-{uuid.uuid4().hex[:12]}"
        self.pipeline_id: str = pipeline_id
        self.definition: PipelineDefinition = definition
        self.stage: str = stage
        self.opportunity_id: str | None = opportunity_id
        self.metadata: dict[str, Any] = metadata or {}
        self.current_user: str = current_user
        self.created_at: str = datetime.now(timezone.utc).isoformat()
        self.updated_at: str | None = None

    def transition(self, to_stage: str, acteur: str) -> None:
        """Applique une transition vers un nouvel état."""
        if not self.definition.est_transition_valide(self.stage, to_stage):
            raise PipelineError(
                f"transition refusée : {self.stage} -> {to_stage}"
            )
        self.stage = to_stage
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Sérialise l'instance en dictionnaire."""
        return {
            "id": self.id,
            "pipeline_id": self.pipeline_id,
            "definition_id": self.definition.id,
            "stage": self.stage,
            "opportunity_id": self.opportunity_id,
            "metadata": self.metadata,
            "current_user": self.current_user,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __repr__(self) -> str:
        return f"<PipelineInstance {self.id} {self.stage}>"


class PipelineEngine:
    """Moteur d'orchestration de pipelines."""

    def __init__(self) -> None:
        self.hooks: dict[str, dict[str, Callable]] = {}
        self.definitions: dict[str, PipelineDefinition] = {}

    def register_definition(self, definition: PipelineDefinition) -> None:
        """Enregistre une définition de pipeline."""
        self.definitions[definition.id] = definition

    def register_hook(
        self,
        pipeline_id: str,
        stage: str,
        hook: Callable[[PipelineInstance, str], None],
    ) -> None:
        """Enregistre un hook pour une transition vers un stage."""
        if pipeline_id not in self.hooks:
            self.hooks[pipeline_id] = {}
        self.hooks[pipeline_id][stage] = hook

    def transition(
        self,
        instance: PipelineInstance,
        to_stage: str,
        acteur: str,
    ) -> None:
        """Orchestre une transition : validation + execution des hooks."""
        definition = self.definitions.get(instance.pipeline_id)
        if definition is None:
            raise PipelineError(f"définition inconnue : {instance.pipeline_id}")

        if not definition.est_transition_valide(instance.stage, to_stage):
            raise PipelineError(
                f"transition refusée : {instance.stage} -> {to_stage}"
            )

        instance.transition(to_stage, acteur)

        # Exécution des hooks (par pipeline)
        for pid, hooks in self.hooks.items():
            if pid == instance.pipeline_id and to_stage in hooks:
                hooks[to_stage](instance, acteur)

    def create_instance(
        self,
        pipeline_id: str,
        opportunity_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        current_user: str = "system",
    ) -> PipelineInstance:
        """Crée une nouvelle instance de pipeline."""
        definition = self.definitions.get(pipeline_id)
        if definition is None:
            raise PipelineError(f"définition inconnue : {pipeline_id}")
        return PipelineInstance(
            pipeline_id=pipeline_id,
            definition=definition,
            opportunity_id=opportunity_id,
            metadata=metadata or {},
            current_user=current_user,
        )
