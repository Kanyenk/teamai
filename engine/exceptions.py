"""Exceptions du moteur XoHive.

Groupement centralisé des exceptions métier et techniques utilisées par les
couches API, ledger et documents. Chaque exception porte une empreinte
(`code`) utilisable pour le dégagement d'erreurs et le logging structuré.
"""

from __future__ import annotations

__all__ = [
    "EngineError",
    "DocumentError",
    "TransitionError",
    "BalanceError",
    "ValidationError",
    "ConfigError",
    "StorageError",
]


class EngineError(Exception):
    """Erreur de base du moteur XoHive."""

    def __init__(self, message: str, code: str = "ENGINE_ERROR") -> None:
        super().__init__(message)
        self.code: str = code


class DocumentError(EngineError):
    """Erreur de validation ou de manipulation d'un document."""

    def __init__(self, message: str, code: str = "DOCUMENT_ERROR") -> None:
        super().__init__(message, code)


class TransitionError(DocumentError):
    """Refus d'une transition d'état invalide."""

    def __init__(self, message: str, code: str = "TRANSITION_ERROR") -> None:
        super().__init__(message, code)


class BalanceError(DocumentError):
    """Erreur d'équilibre comptable (débit ≠ crédit)."""

    def __init__(self, message: str, code: str = "BALANCE_ERROR") -> None:
        super().__init__(message, code)


class ValidationError(DocumentError):
    """Erreur de validation métier (champ manquant, format invalide)."""

    def __init__(self, message: str, code: str = "VALIDATION_ERROR") -> None:
        super().__init__(message, code)


class ConfigError(EngineError):
    """Erreur de configuration du moteur."""

    def __init__(self, message: str, code: str = "CONFIG_ERROR") -> None:
        super().__init__(message, code)


class StorageError(EngineError):
    """Erreur de stockage ou d'accès aux données."""

    def __init__(self, message: str, code: str = "STORAGE_ERROR") -> None:
        super().__init__(message, code)
