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

    # État du pipeline CRM
    STAGE_PROSPECTING = "prospecting"
    STAGE_QUALIFICATION = "qualification"
    STAGE_PROPOSAL = "proposal"
    STAGE_NEGOTIATION = "negociation"
    STAGE_WON = "won"
    STAGE_LOST = "lost"

    # Schéma des transitions
    STAGE_SCHEMA = {
        STAGE_PROSPECTING: [STAGE_QUALIFICATION],
        STAGE_QUALIFICATION: [STAGE_PROPOSAL],
        STAGE_PROPOSAL: [STAGE_NEGOTIATION],
        STAGE_NEGOTIATION: [STAGE_WON, STAGE_LOST],
        STAGE_WON: [],
        STAGE_LOST: [],
    }

    # Libellés des stages
    STAGE_LABELS = {
        STAGE_PROSPECTING: "Prospection",
        STAGE_QUALIFICATION: "Qualification",
        STAGE_PROPOSAL: "Proposition",
        STAGE_NEGOTIATION: "Négociation",
        STAGE_WON: "Gagné",
        STAGE_LOST: "Perdu",
    }

    # Couleurs des stages
    STAGE_COLORS = {
        STAGE_PROSPECTING: "#3B82F6",
        STAGE_QUALIFICATION: "#F59E0B",
        STAGE_PROPOSAL: "#10B981",
        STAGE_NEGOTIATION: "#8B5CF6",
        STAGE_WON: "#10B981",
        STAGE_LOST: "#EF4444",
    }

    def __init__(
        self,
        *,
        id: str | None = None,
        name: str,
        stage_schema: dict[str, list[str]] | None = None,
        initial_stage: str = STAGE_PROSPECTING,
        description: str = "",
    ) -> None:
        if not name:
            raise PipelineError("nom du pipeline requis")

        if stage_schema is None:
            stage_schema = self.STAGE_SCHEMA

        if initial_stage not in stage_schema:
            raise PipelineError(
                f"stage initial inconnu : {initial_stage!r}. "
                f"Valeurs possibles : {list(stage_schema.keys())}"
            )

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

    def get_stage_label(self, stage: str) -> str:
        """Retourne le libellé d'un stage."""
        return self.STAGE_LABELS.get(stage, stage)

    def get_stage_color(self, stage: str) -> str:
        """Retourne la couleur d'un stage."""
        return self.STAGE_COLORS.get(stage, "#9CA3AF")

    def is_terminal_stage(self, stage: str) -> bool:
        """Vérifie si un stage est terminal."""
        return stage in (self.STAGE_WON, self.STAGE_LOST)

    def stage_order(self, stage: str) -> int:
        """Retourne l'ordre du stage dans le pipeline."""
        for order, (s, _) in enumerate(self.stage_schema.items(), 1):
            if s == stage:
                return order
        return 0

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

    def can_transitions(self) -> list[str]:
        """Retourne les stages vers lesquels on peut transiter."""
        return self.definition.get_next_stages(self.stage)

    def is_terminal(self) -> bool:
        """Vérifie si l'instance est dans un stage terminal."""
        return self.definition.is_terminal_stage(self.stage)

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


class PipelineProgression:
    """Gestion de la progression d'une opportunité dans le pipeline."""

    def __init__(self, engine: PipelineEngine):
        self.engine = engine

    def start_opportunity(
        self,
        opportunity_id: str,
        pipeline_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> PipelineInstance:
        """Démarre une opportunité dans le pipeline."""
        definition = self.engine.definitions.get(pipeline_id)
        if definition is None:
            raise PipelineError(f"définition inconnue : {pipeline_id}")

        instance = PipelineInstance(
            pipeline_id=pipeline_id,
            definition=definition,
            stage=definition.initial_stage,
            opportunity_id=opportunity_id,
            metadata=metadata or {},
        )
        return instance

    def advance_opportunity(
        self,
        instance: PipelineInstance,
        acteur: str,
        metadata: dict[str, Any] | None = None,
    ) -> PipelineInstance:
        """Avance une opportunité d'un stage vers le suivant."""
        if instance.is_terminal():
            raise PipelineError(
                f"impossible de progresser : stage terminal ({instance.stage})"
            )

        next_stages = instance.can_transitions()
        if not next_stages:
            raise PipelineError(f"aucun stage suivant pour {instance.stage}")

        next_stage = next_stages[0]
        instance.transition(next_stage, acteur)
        if metadata:
            instance.metadata.update(metadata)

        return instance

    def get_progress(self, instance: PipelineInstance) -> dict[str, Any]:
        """Retourne l'état de progression d'une opportunité."""
        stages = list(instance.definition.stage_schema.keys())
        current_index = stages.index(instance.stage) if instance.stage in stages else 0
        total = len(stages)
        progress = round((current_index / total) * 100, 1) if total else 0

        return {
            "current_stage": instance.stage,
            "current_stage_label": instance.definition.get_stage_label(instance.stage),
            "stage_order": instance.definition.stage_order(instance.stage),
            "total_stages": total,
            "progress_percentage": progress,
            "terminal": instance.is_terminal(),
            "terminal_stage": instance.stage if instance.is_terminal() else None,
            "next_stages": instance.can_transitions(),
            "is_won": instance.stage == instance.definition.STAGE_WON,
            "is_lost": instance.stage == instance.definition.STAGE_LOST,
        }

    def calculate_progress(self, instance: PipelineInstance) -> float:
        """Calcule le pourcentage de progression."""
        stages = list(instance.definition.stage_schema.keys())
        current_index = stages.index(instance.stage) if instance.stage in stages else 0
        total = len(stages)
        return round((current_index / total) * 100, 1) if total else 0

    def reset_opportunity(self, instance: PipelineInstance) -> None:
        """Réinitialise une opportunité au stage de départ."""
        instance.stage = instance.definition.initial_stage
        instance.updated_at = datetime.now(timezone.utc).isoformat()


class PipelineEngine:
    """Moteur d'orchestration de pipelines."""

    def __init__(self) -> None:
        self.hooks: dict[str, dict[str, Callable]] = {}
        self.definitions: dict[str, PipelineDefinition] = {}
        self.progression: PipelineProgression | None = None

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
            stage=definition.initial_stage,
            opportunity_id=opportunity_id,
            metadata=metadata or {},
            current_user=current_user,
        )

    def start_opportunity(
        self,
        pipeline_id: str,
        opportunity_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> PipelineInstance:
        """Démarre une opportunité dans le pipeline."""
        from .pipeline_progression import PipelineProgression

        if self.progression is None:
            self.progression = PipelineProgression(self)
        return self.progression.start_opportunity(
            opportunity_id, pipeline_id, metadata
        )

    def advance_opportunity(
        self,
        instance: PipelineInstance,
        acteur: str,
        metadata: dict[str, Any] | None = None,
    ) -> PipelineInstance:
        """Avance une opportunité d'un stage."""
        if self.progression is None:
            self.progression = PipelineProgression(self)
        return self.progression.advance_opportunity(instance, acteur, metadata)

    def get_progress(self, instance: PipelineInstance) -> dict[str, Any]:
        """Retourne l'état de progression d'une opportunité."""
        if self.progression is None:
            self.progression = PipelineProgression(self)
        return self.progression.get_progress(instance)

    def reset_opportunity(self, instance: PipelineInstance) -> None:
        """Réinitialise une opportunité au stage de départ."""
        if self.progression is None:
            self.progression = PipelineProgression(self)
        self.progression.reset_opportunity(instance)
