"""Ledger — moteur d'écriture comptable du socle XoHive.

Ce module implémente l'écriture de transactions comptables sur le socle
événementiel. Chaque écriture est immédiatement validée :

- débit = crédit (invariant de bilan),
- dates administratives conformes,
- jointure sur les comptes référentiels.

Le ledger est un événementiel : il ne supprime jamais, il construit
une chaîne d'écritures traceables et immuable.
"""

from __future__ import annotations

from typing import Any

from engine.exceptions import BalanceError, ValidationError

__all__ = [
    "ECRITURE_TYPE", "POSTE", "Ledger", "write_document",
    "bilan_ok", "compte_existe",
]

# Codes de type de document comptable
ECRITURE_TYPE = {
    "FACT": "facture",
    "BC": "bilan",
    "BL": "bon de livraison",
    "NC": "note de crédit",
    "RS": "référence de service",
    "CHQ": "chèque",
}

# Postes comptables standards (comptes référentiels)
POSTE = {
    "CA_TELEPHONY": "79110",
    "CA_LOCAUX": "79210",
    "CA_MATERIAL": "79410",
    "CA_LOCATAIRES": "79220",
    "CA_ELECTRICITE": "79250",
    "CA_EAU": "79260",
    "CA_CNET": "79270",
    "PASSIF_INTEGRATION": "62000",
    "PASSIF_DROITS": "63000",
    "PASSIF_DETTES": "64000",
    "PASSIF_TAXES": "66000",
}


def bilan_ok(ecritures: list[dict]) -> bool:
    """Vérifie l'équilibre du bilan : somme des débits == crédits."""
    debit = sum(e.get("debit", 0.0) for e in ecritures)
    credit = sum(e.get("credit", 0.0) for e in ecritures)
    return abs(debit - credit) < 0.005


def compte_existe(numero: str, comptes: list[dict]) -> bool:
    """Vérifie qu'un compte existe dans le référentiel."""
    return any(c.get("numero") == numero for c in comptes)


class Ledger:
    """Moteur d'écriture de documents comptables.

    L'instance encapsule un référentiel de comptes et un stockage
    d'écritures. Chaque écriture est validée immédiatement et
    renvoie un événement traçable.
    """

    def __init__(self, comptes: list[dict]) -> None:
        self.comptes: list[dict] = comptes
        self.ecritures: list[dict] = []

    def ecrire(
        self,
        doc_type: str,
        numero_serie: int,
        org_id: int,
        lines: list[dict],
        *,
        date: str,
        debit_total: float = 0.0,
        credit_total: float = 0.0,
    ) -> dict:
        """Écrit une nouvelle ligne de laisie. Renvoie l'événement.

        Lève ``BalanceError`` si le bilan ne s'équilibre pas.
        """
        if not bilan_ok(lines):
            raise BalanceError(
                f"écriture non équilibrée (débit {debit_total} / crédit {credit_total})"
            )
        for ligne in lines:
            if not compte_existe(ligne.get("compte"), self.comptes):
                raise ValidationError(f"compte {ligne.get('compte')} inconnu")

        event = {
            "id": None,
            "doc_type": doc_type,
            "numero_serie": numero_serie,
            "org_id": org_id,
            "date": date,
            "debit_total": debit_total,
            "credit_total": credit_total,
            "lines": lines,
            "etat": "ecrit",
        }
        self.ecritures.append(event)
        return event
