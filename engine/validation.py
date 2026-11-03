"""Règles de validation business pour les documents XoHive.

Ce module exporte la classe ``DocumentValidator`` qui centralise les règles
de création et de transition d'un document, indépendamment de la couche API.
"""

from __future__ import annotations

from engine import TRANSITIONS, DocumentError, Document


class DocumentValidator:
    """Valide les règles business de création et de transition.

    Usage:
        validator = DocumentValidator()
        validator.validate_creation("FACT", 1, 1, "EUR", 0.0, 0.0)
        validator.validate_transition(document, "brouillon_pdf")
    """

    #: Types de documents acceptés (énumération stricte)
    ALLOWED_TYPES = ("FACT", "BC", "BL", "NC", "RS", "CHQ")

    #: Devise valide : chaîne non vide de 3 caractères exacts
    CURRENCY_PATTERN = "^[A-Z]{3}$"

    def validate_creation(
        self,
        doc_type: str,
        numero_serie: int,
        org_id: int,
        currency: str,
        retention: float,
        balance: float,
    ) -> None:
        """Valide les règles de création d'un document."""
        if doc_type not in self.ALLOWED_TYPES:
            raise DocumentError(f"type de document inconnu : {doc_type!r}")
        if not isinstance(numero_serie, int) or numero_serie <= 0:
            raise DocumentError("numero_serie invalide")
        if not isinstance(org_id, int) or org_id <= 0:
            raise DocumentError("org_id invalide")
        if not isinstance(currency, str) or len(currency) != 3:
            raise DocumentError("currency invalide")
        if not isinstance(retention, (int, float)) or not (0 <= retention <= 1):
            raise DocumentError("retention hors limites")
        if not isinstance(balance, (int, float)):
            raise DocumentError("balance invalide")
        if balance < 0:
            raise DocumentError("balance négative")

    def validate_transition(self, document: Document, etat: str) -> None:
        """Valide une transition d'état sur un document existant."""
        if etat not in TRANSITIONS:
            raise DocumentError(f"état inconnu : {etat!r}")
        if etat not in TRANSITIONS[document.etat]:
            raise DocumentError(
                f"transition refusée : {document.etat} -> {etat}"
            )
