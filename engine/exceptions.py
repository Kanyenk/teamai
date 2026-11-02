"""Exceptions du moteur XoHive.

Groupement centralisé des exceptions métier et techniques utilisées par les
couches API, ledger et documents. Chaque exception porte une empreinte
(`code`) utilisable pour le logging et la traduction en HTTP.

Règles de sécurité :
- Aucune stack trace sensible (chemins de fichiers, DB, clés) n'est exposée à
  l'extérieur d'un contexte de développement.
- Les messages renvoyés à une API sont génériques ; les causes détaillées eux
  restent dans les logs côté serveur.
"""

from __future__ import annotations


class XoHiveError(Exception):
    """Base de toutes les exceptions métier."""

    code = "XOBHE000"
    status = 500

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.cause = cause

    def to_api(self) -> dict:
        return {"error": {"code": self.code, "message": self.message}}


class Forbidden(XoHiveError):
    """Accès non autorisé (403)."""

    code = "XOBHE403"
    status = 403


class NotFound(XoHiveError):
    """Ressource absente (404)."""

    code = "XOBHE404"
    status = 404


class Conflict(XoHiveError):
    """Conflit d'état, doublon ou verrouillage (409)."""

    code = "XOBHE409"
    status = 409


class Validation(XoHiveError):
    """Erreur de validation métier (422)."""

    code = "XOBHE422"
    status = 422


class DocumentError(Validation):
    """Erreur de transition ou de document."""

    code = "DOC001"
    status = 422


class InvariantBroken(Validation):
    """Invariant du socle rompu (débit ≠ crédit)."""

    code = "DOC002"
    status = 422


class DocumentAlreadyClosed(Validation):
    code = "DOC003"
    status = 422


class DocumentNotExecutable(Validation):
    code = "DOC004"
    status = 422


class LedgerError(Validation):
    code = "LED001"
    status = 422


class LedgerNotBalanced(LedgerError):
    code = "LED002"
    status = 422


class LedgerClosed(LedgerError):
    code = "LED003"
    status = 422


class TransactionError(Validation):
    code = "TRX001"
    status = 422


class TransactionAlreadyPosted(TransactionError):
    code = "TRX002"
    status = 422


class DocumentAlreadyFinal(DocumentError):
    code = "DOC005"
    status = 409


class DocumentOnlyDraft(DocumentError):
    code = "DOC006"
    status = 422


class PivotNotFoundError(NotFound):
    code = "PIN001"
    status = 404
