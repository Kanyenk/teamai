"""Service Return (logique métier des retours clients)."""
from __future__ import annotations

from typing import Optional

from engine.returns import Return
from engine.return_repository import ReturnRepository


class ReturnService:
    """Orchestre la création et le cycle de vie des retours clients."""

    def __init__(self, repo: ReturnRepository) -> None:
        self.repo = repo

    def create_return(
        self,
        organisation_id: str,
        order_id: str,
        product_id: str,
        quantity: int,
        reason: str,
    ) -> Return:
        """Crée un retour client (statut draft)."""
        ret = Return(
            organisation_id=organisation_id,
            order_id=order_id,
            product_id=product_id,
            quantity=quantity,
            reason=reason,
        )
        return self.repo.create(ret)

    def get_return(self, return_id: str) -> Optional[Return]:
        """Récupère un retour par id."""
        return self.repo.get(return_id)

    def list_returns(self, organisation_id: str):
        """Liste les retours d'une organisation."""
        return self.repo.list(organisation_id)

    def request_return(self, return_id: str) -> Return:
        """Passe un retour en 'requested'."""
        ret = self.repo.get(return_id)
        if ret is None:
            raise ValueError(f"retour {return_id} introuvable")
        ret.mark_requested()
        return self.repo.update(ret)

    def receive_return(self, return_id: str) -> Return:
        """Passe un retour en 'received'."""
        ret = self.repo.get(return_id)
        if ret is None:
            raise ValueError(f"retour {return_id} introuvable")
        ret.mark_received()
        return self.repo.update(ret)

    def refund_return(self, return_id: str, amount: float) -> Return:
        """Passe un retour en 'refunded' avec un montant."""
        ret = self.repo.get(return_id)
        if ret is None:
            raise ValueError(f"retour {return_id} introuvable")
        ret.mark_refunded(amount)
        return self.repo.update(ret)

    def cancel_return(self, return_id: str) -> Return:
        """Annule un retour."""
        ret = self.repo.get(return_id)
        if ret is None:
            raise ValueError(f"retour {return_id} introuvable")
        ret.cancel()
        return self.repo.update(ret)
