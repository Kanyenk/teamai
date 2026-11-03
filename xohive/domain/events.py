"""Événements d'entreprise pour le bus d'événements asynchrone.

Types d'événements implémentés :
- organization.created
- organization.updated
- user.created
- user.deleted
- role.updated
- audit.created
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable


class EventType:
    """Type d'événement identifié par un nom unique."""

    ORGANIZATION_CREATED = "organization.created"
    ORGANIZATION_UPDATED = "organization.updated"
    USER_CREATED = "user.created"
    USER_DELETED = "user.deleted"
    ROLE_UPDATED = "role.updated"
    AUDIT_CREATED = "audit.created"

    @classmethod
    def all(cls) -> list[str]:
        return [
            cls.ORGANIZATION_CREATED,
            cls.ORGANIZATION_UPDATED,
            cls.USER_CREATED,
            cls.USER_DELETED,
            cls.ROLE_UPDATED,
            cls.AUDIT_CREATED,
        ]

    @classmethod
    def is_valid(cls, event_type: str) -> bool:
        return event_type in cls.all()


class Event:
    """Représentation d'un événement métier.

    Attributs :
    - event_type : type de l'événement (ex: `organization.created`)
    - data : payload de l'événement (dictionnaire)
    - timestamp : horodatage ISO 8601
    - metadata : informations supplémentaires (ex: user_id, organisation_id)
    """

    def __init__(
        self,
        event_type: str,
        data: dict,
        metadata: dict | None = None,
        timestamp: str | None = None,
    ) -> None:
        if not EventType.is_valid(event_type):
            raise ValueError(f"type d'événement invalide : {event_type}")

        self.event_type: str = event_type
        self.data: dict = data or {}
        self.metadata: dict = metadata or {}
        self.timestamp: str = timestamp or self._now_iso()

    @staticmethod
    def _now_iso() -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        """Sérialise l'événement en dictionnaire."""
        return {
            "event_type": self.event_type,
            "data": self.data,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    def __repr__(self) -> str:
        return f"<Event {self.event_type} @ {self.timestamp}>"


class EventHandler:
    """Gère un gestionnaire d'événements.

    Un handler est une fonction appelée lors de la diffusion d'un événement.
    Le handler reçoit l'objet Event et peut retourner un résultat.
    """

    def __init__(
        self,
        handler: Callable,
        *,
        event_types: list[str] | None = None,
        async_: bool = False,
    ) -> None:
        """
        Args:
            handler: fonction appelée lors de la diffusion de l'événement.
            event_types: liste des types d'événements auquel s'abonner.
                         Si None, abonne au type par défaut.
            async_: si True, le handler est considéré comme asynchrone.
        """
        self.handler = handler
        self.event_types: list[str] = event_types or []
        self.async_ = async_

    def matches(self, event_type: str) -> bool:
        """Vérifie si ce handler s'abonne à un type d'événement donné."""
        if not self.event_types:
            return True
        return event_type in self.event_types

    def __call__(self, event: Event) -> Any:
        return self.handler(event)


class EventBus:
    """Bus d'événements asynchrone.

    Permet de publier des événements et d'abonner des gestionnaires.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}

    def subscribe(self, handler: EventHandler) -> None:
        """Abonne un gestionnaire à un ou plusieurs types d'événements."""
        for event_type in handler.event_types:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            if handler not in self._handlers[event_type]:
                self._handlers[event_type].append(handler)

    def unsubscribe(self, handler: EventHandler) -> None:
        """Retire un gestionnaire de tous les abonnements."""
        for event_type in list(self._handlers.keys()):
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
            if not self._handlers[event_type]:
                del self._handlers[event_type]

    def publish(self, event: Event) -> None:
        """Diffuse un événement à tous les gestionnaires abonnés.

        Retourne une liste de résultats (si les handlers sont synchrones).
        """
        handler_list = self._handlers.get(event.event_type, [])
        results = []

        for handler in handler_list:
            if handler.async_:
                # En mode asynchrone, on ne bloque pas
                continue
            try:
                result = handler(event)
                if result is not None:
                    results.append(result)
            except Exception as e:
                # En production, on loguerait l'erreur ici
                raise

        return results

    def publish_async(self, event: Event) -> None:
        """Diffuse un événement sans blocage (mode asynchrone).

        Simule un traitement asynchrone en ignorant le retour des handlers.
        """
        handler_list = self._handlers.get(event.event_type, [])
        for handler in handler_list:
            # En production, on utiliserait une file d'attente ou un worker
            pass
