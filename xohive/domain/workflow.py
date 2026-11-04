"""Workflow — Machine à états (ERP workflow engine).

Modules :
- WorkflowDefinition : définit le schéma des états et transitions
- WorkflowInstance : instance d'un workflow en cours d'exécution
- WorkflowEngine : orchestre les transitions et appelle les hooks

Relations : N → 1 WorkflowDefinition (chaque instance référence une définition).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Callable


class WorkflowError(Exception):
    """Erreur de gestion d'un workflow."""


class WorkflowDefinition:
    """Définition d'un workflow : schéma des états et des transitions."""

    def __init__(
        self,
        *,
        id: str | None = None,
        name: str,
        state_schema: dict[str, list[str]],
        initial_state: str,
        description: str = "",
    ) -> None:
        if not name:
            raise WorkflowError("nom du workflow requis")
        if initial_state not in state_schema:
            raise WorkflowError(f"état initial inconnu : {initial_state!r}")
        missing = set(state_schema.keys()) - set(state_schema.keys())
        for state, transitions in state_schema.items():
            if not isinstance(state, str):
                raise WorkflowError(f"état invalide : {state!r}")
            for t in transitions:
                if t not in state_schema:
                    raise WorkflowError(f"destination d'état inconnue : {t!r}")
        if not isinstance(state_schema, dict):
            raise WorkflowError("state_schema doit être un dictionnaire")

        self.id: str = id or f"wf-{uuid.uuid4().hex[:12]}"
        self.name: str = name
        self.state_schema: dict[str, list[str]] = state_schema
        self.initial_state: str = initial_state
        self.description: str = description

    def est_transition_valide(self, from_state: str, to_state: str) -> bool:
        """Vérifie si une transition est autorisée."""
        return to_state in self.state_schema.get(from_state, [])

    def __repr__(self) -> str:
        return f"<WorkflowDefinition {self.id} {self.name}>"


class WorkflowInstance:
    """Instance d'un workflow en cours d'exécution."""

    def __init__(
        self,
        *,
        id: str | None = None,
        workflow_id: str,
        definition: WorkflowDefinition,
        current_state: str | None = None,
        metadata: dict[str, Any] | None = None,
        created_by: str = "system",
        created_at: str | None = None,
    ) -> None:
        if definition.id != workflow_id:
            raise WorkflowError("la définition ne correspond pas à l'instance")
        if current_state is None:
            current_state = definition.initial_state
        if current_state not in definition.state_schema:
            raise WorkflowError(f"état initial inconnu : {current_state!r}")

        self.id: str = id or f"wfinst-{uuid.uuid4().hex[:12]}"
        self.workflow_id: str = workflow_id
        self.definition: WorkflowDefinition = definition
        self.current_state: str = current_state
        self.metadata: dict[str, Any] = metadata or {}
        self.created_by: str = created_by
        self.created_at: str = created_at or self._now_iso()
        self.updated_at: str | None = None

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def transition(self, to_state: str, acteur: str) -> None:
        """Applique une transition vers un nouvel état."""
        if not self.definition.est_transition_valide(self.current_state, to_state):
            raise WorkflowError(
                f"transition refusée : {self.current_state} -> {to_state}"
            )
        self.current_state = to_state
        self.updated_at = self._now_iso()

    def to_dict(self) -> dict[str, Any]:
        """Sérialise l'instance en dictionnaire."""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "definition_id": self.definition.id,
            "current_state": self.current_state,
            "metadata": self.metadata,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __repr__(self) -> str:
        return f"<WorkflowInstance {self.id} {self.current_state}>"


class WorkflowEngine:
    """Moteur d'orchestration de workflows."""

    def __init__(self) -> None:
        self.hooks: dict[str, Callable[[WorkflowInstance, str], None]] = {}
        self.definitions: dict[str, WorkflowDefinition] = {}

    def register_definition(self, definition: WorkflowDefinition) -> None:
        """Enregistre une définition de workflow."""
        self.definitions[definition.id] = definition

    def register_hook(self, state: str, hook: Callable[[WorkflowInstance, str], None]) -> None:
        """Enregistre un hook à exécuter lors d'une transition vers un état."""
        self.hooks[state] = hook

    def transition(
        self,
        instance: WorkflowInstance,
        to_state: str,
        acteur: str,
    ) -> None:
        """Orchestre une transition : validation + execution des hooks."""
        definition = self.definitions.get(instance.workflow_id)
        if definition is None:
            raise WorkflowError(f"définition inconnue : {instance.workflow_id}")

        if not definition.est_transition_valide(instance.current_state, to_state):
            raise WorkflowError(
                f"transition refusée : {instance.current_state} -> {to_state}"
            )

        instance.transition(to_state, acteur)

        hook = self.hooks.get(to_state)
        if hook is not None:
            hook(instance, acteur)

    def get_definition(self, workflow_id: str) -> WorkflowDefinition | None:
        """Récupère une définition de workflow par id."""
        return self.definitions.get(workflow_id)

    def create_instance(
        self,
        workflow_id: str,
        metadata: dict[str, Any] | None = None,
        created_by: str = "system",
    ) -> WorkflowInstance:
        """Crée une nouvelle instance de workflow."""
        definition = self.definitions.get(workflow_id)
        if definition is None:
            raise WorkflowError(f"définition inconnue : {workflow_id}")
        return WorkflowInstance(
            workflow_id=workflow_id,
            definition=definition,
            metadata=metadata or {},
            created_by=created_by,
        )
