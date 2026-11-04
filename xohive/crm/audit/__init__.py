"""AuditCRM — Suivi d'audit pour le module CRM minimal.

Implémente des hooks qui génèrent un AuditEvent à chaque mutation
d'une entité CRM (Company, Contact, Opportunity, Activity).

Compatibilité avec le système d'événements EventBus.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Callable, Dict

from xohive.domain.audit_event import AuditEvent


class AuditCRM:
    """Gestionnaire d'audit pour les entités CRM."""

    # Mapping: nom de la classe -> type d'entité audit
    ENTITY_TYPES: Dict[str, str] = {
        "Company": "company",
        "Contact": "contact",
        "Opportunity": "opportunity",
        "Activity": "activity",
    }

    def __init__(self) -> None:
        # Hooks appelés après chaque mutation
        self.hooks: list[Callable[[AuditEvent], None]] = []
        # Compatibilité EventBus : souscription aux événements audit
        self.subscribers: Dict[str, list[Callable]] = {}

    def register_hook(self, hook: Callable[[AuditEvent], None]) -> None:
        """Enregistre un hook qui sera appelé après chaque mutation."""
        self.hooks.append(hook)

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Abonne un handler à un événement audit (EventBus)."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

    def _get_entity_type(self, entity: object) -> str | None:
        """Retourne le type d'entité audit pour une entité CRM."""
        class_name = entity.__class__.__name__
        return self.ENTITY_TYPES.get(class_name)

    def _emit(self, audit: AuditEvent) -> None:
        """Émet un événement audit (appelle les hooks et les subscribers)."""
        for hook in self.hooks:
            try:
                hook(audit)
            except Exception:
                pass  # Ne pas bloquer la transaction pour un échec d'audit

        for handler in self.subscribers.get("audit.created", []):
            try:
                handler(audit)
            except Exception:
                pass

    def before_create(self, entity: object) -> AuditEvent | None:
        """
        Prépare un AuditEvent pour une création.
        Appelé avant l'insertion dans la base de données.
        Retourne l'événement prêt à être émis.
        """
        entity_type = self._get_entity_type(entity)
        if entity_type is None:
            return None

        # Récupère les valeurs de l'entité (données nouvelles)
        values = self._extract_values(entity)

        # Accès aux attributs (typage dynamique)
        audit = AuditEvent(  # type: ignore[union-attr]
            organisation_id=entity.organisation_id,  # type: ignore[union-attr]
            entity_type=entity_type,
            entity_id=entity.id,  # type: ignore[union-attr]
            action="create",
            new_values=values,
        )
        return audit

    def after_create(self, audit: AuditEvent) -> None:
        """Appelé après la création, émet l'événement."""
        self._emit(audit)

    def before_update(self, entity: object, old_values: Dict[str, Any]) -> AuditEvent | None:
        """
        Prépare un AuditEvent pour une mise à jour.
        Appelé avant la mise à jour dans la base de données.
        """
        entity_type = self._get_entity_type(entity)
        if entity_type is None:
            return None

        new_values = self._extract_values(entity)
        all_values = {**old_values, **new_values}

        audit = AuditEvent(
            organisation_id=entity.organisation_id,
            entity_type=entity_type,
            entity_id=entity.id,
            action="update",
            old_values=old_values,
            new_values=new_values,
        )
        return audit

    def after_update(self, audit: AuditEvent) -> None:
        """Appelé après la mise à jour, émet l'événement."""
        self._emit(audit)

    def before_delete(self, entity: object, old_values: Dict[str, Any]) -> AuditEvent | None:
        """
        Prépare un AuditEvent pour une suppression.
        """
        entity_type = self._get_entity_type(entity)
        if entity_type is None:
            return None

        audit = AuditEvent(
            organisation_id=entity.organisation_id,
            entity_type=entity_type,
            entity_id=entity.id,
            action="delete",
            old_values=old_values,
        )
        return audit

    def after_delete(self, audit: AuditEvent) -> None:
        """Appelé après la suppression, émet l'événement."""
        self._emit(audit)

    def _extract_values(self, entity: object) -> Dict[str, Any]:
        """Extrait les valeurs d'une entité en dictionnaire."""
        if hasattr(entity, "to_dict"):
            return entity.to_dict()
        return {}


# Instance globale
audit_crm = AuditCRM()
