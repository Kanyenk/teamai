"""Authentification par token pour l'API HTTP.

Ce module exporte la classe ``TokenAuth`` qui vérifie la présence et la
validité d'un token Bearer dans l'en-tête ``Authorization``.
"""

from __future__ import annotations


class TokenAuth:
    """Authentifie les requêtes avec un token Bearer.

    Args:
        valid_tokens: Ensemble de tokens valides.
    """

    def __init__(self, valid_tokens: set[str]):
        self.valid_tokens = valid_tokens or set()

    def authenticate(self, token: str | None) -> bool:
        """Vérifie si le token est valide.

        Args:
            token: Valeur du header ``Authorization`` (format attendu
                ``Bearer <token>``). Si ``None`` ou mal formatté, retourne
                ``False``.

        Returns:
            ``True`` si le token est présent et dans l'ensemble des tokens
            valides, ``False`` sinon.
        """
        if token is None:
            return False
        parts = token.split()
        if len(parts) != 2 or parts[0] != "Bearer":
            return False
        return parts[1] in self.valid_tokens
