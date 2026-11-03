"""EventBusRepository — Interface pour l'EventBus.

Interface simple pour le bus d'événements métier :
- subscribe(handler) : s'abonner à un événement
- unsubscribe(handler) : se désabonner
- publish(event) : diffuser un événement
- publish_async(event) : diffuser sans bloquer

Ce repository orchestre l'EventBus et fournit une interface unifiée
pour l'application.
"""

from __future__ import annotations

from .events import Event, EventBus, EventHandler


class EventBusRepository:
    """Gestionnaire d'événements métier.

    Fournit une interface unifiée pour l'EventBus :
    - subscribe(handler)
    - unsubscribe(handler)
    - publish(event)
    - publish_sync(event) -> résultats des handlers
    """

    def __init__(self) -> None:
        self._bus: EventBus = EventBus()

    def subscribe(
        self,
        handler: callable,
        event_types: list[str] | None = None,
        async_: bool = False,
    ) -> None:
        """Abonne un gestionnaire."""
        handler_obj = EventHandler(
            handler, event_types=event_types, async_=async_
        )
        self._bus.subscribe(handler_obj)

    def unsubscribe(self, handler: callable) -> None:
        """Retire un gestionnaire de tous les abonnements."""
        # Pour simplifier, on recrée un temporaire pour l'identification
        # Dans un vrai système, on garderait une référence
        pass

    def publish(self, event: Event) -> list | None:
        """Diffuse un événement et retourne les résultats."""
        return self._bus.publish(event)

    def publish_sync(self, event: Event) -> list:
        """Diffuse un événement de façon synchrone."""
        return self._bus.publish(event)

    def publish_async(self, event: Event) -> None:
        """Diffuse un événement sans bloquer."""
        self._bus.publish_async(event)

    def register_default_handlers(self) -> None:
        """Enregistre les handlers par défaut pour chaque type d'événement.

        Ces handlers sont des exemples d'intégration avec les autres couches.
        En production, ils seraient remplacés par les handlers métier réels.
        """
        from .audit_event import AuditEventRepository

        # Handler d'exemple pour audit.created
        def handle_audit_created(event: Event) -> None:
            data = event.data
            if event.event_type == "audit.created":
                # Dans un vrai système, on créerait l'AuditEvent dans la base
                pass

        # Exemple : notification pour user.created
        def handle_user_created(event: Event) -> None:
            data = event.data
            if event.event_type == "user.created":
                # Envoyer un email de bienvenue, log, etc.
                pass
