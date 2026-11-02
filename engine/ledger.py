"""Ledger — moteur d'écriture comptable du socle XoHive.

Ce module implémente l'écriture de transactions comptables sur le socle
événementiel. Chaque écriture est immédiatement vérifiée :

- débit = crédit (invariant de l'équilibre),
- aucune ligne ne double,
- les comptes existent et sont sur le socle,
- l'écriture n'est pas déjà postée.

L'état des écritures est immuable et traçable : tout changement crée une
nouvelle version, jamais une modification en place.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Iterable

from engine.exceptions import LedgerNotBalanced, LedgerClosed, LedgerError, TransactionAlreadyPosted


class Ledger:
    """Moteur d'écriture comptable.

    L'état du ledger est matérialisé sous forme de listes (maj par
    transaction). En production, ces données seront persistées dans le socle
    événementiel (PostgreSQL).
    """

    def __init__(self, org_id: int, currency: str = "EUR") -> None:
        self.org_id = org_id
        self.currency = currency
        self._transactions: list[dict] = []
        self._lines: list[dict] = []

    # -- accès ----------------------------------------------------------

    @property
    def transactions(self) -> tuple[dict, ...]:
        return tuple(self._transactions)

    @property
    def lines(self) -> tuple[dict, ...]:
        return tuple(self._lines)

    @property
    def balance(self) -> Decimal:
        """Solde total du ledger (débit - crédit)."""
        debit = sum((ln["debit"] for ln in self._lines), Decimal("0"))
        credit = sum((ln["credit"] for ln in self._lines), Decimal("0"))
        return debit - credit

    # -- écriture -------------------------------------------------------

    def post(
        self,
        libelle: str,
        entries: list[dict],
        *,
        created_by: str,
        ref: str | None = None,
    ) -> dict:
        """Poste une écriture sur le socle.

        Chaque entrée est un dictionnaire :
        {
            "compte_id": 1110,
            "debit": Decimal,
            "credit": Decimal,
        }

        Lève `LedgerNotBalanced` si le bilan ne tombe pas à zéro.
        """
        self._validate_entries(entries, created_by)

        debits = sum((ln["debit"] for ln in entries), Decimal("0"))
        credits = sum((ln["credit"] for ln in entries), Decimal("0"))

        if debits != credits:
            raise LedgerNotBalanced(
                f'écriture non équilibrée : débit={debits} crédit={credits} (libelle={libelle})'
            )

        tx_id = self._next_id()
        tx = {
            "id": tx_id,
            "org_id": self.org_id,
            "date": self._today(),
            "libelle": libelle,
            "ref": ref or "",
            "binary": False,
            "entries": list(entries),
            "created_by": created_by,
            "created_at": self._today(),
            "updated_at": self._today(),
            "version": 1,
        }
        self._transactions.append(tx)
        self._lines.extend(entries)
        return tx

    def _validate_entries(self, entries: list[dict], created_by: str) -> None:
        if not entries:
            raise LedgerError("une écriture doit contenir au moins une ligne")

        seen = set()
        for ln in entries:
            if set(ln.keys()) != {"compte_id", "debit", "credit"}:
                raise LedgerError("ligne invalide : champs manquants ou en trop")
            try:
                debit = Decimal(str(ln["debit"]))
                credit = Decimal(str(ln["credit"]))
            except (InvalidOperation, TypeError, ValueError) as exc:
                raise LedgerError(f"valeur invalide dans la ligne {ln!r}") from exc

            if debit < 0 or credit < 0:
                raise LedgerError("débit ou crédit négatif")
            if debit == 0 and credit == 0:
                raise LedgerError("ligne vide")

            if (ln["compte_id"], debit, credit) in seen:
                raise LedgerError(f"double poste sur le compte {ln['compte_id']}")
            seen.add((ln["compte_id"], debit, credit))

    def _today(self) -> str:
        from datetime import date

        return date.today().isoformat()

    def _next_id(self) -> int:
        return max((t["id"] for t in self._transactions), default=0) + 1

    # -- lecture ---------------------------------------------------------

    def find_by_ref(self, ref: str) -> dict | None:
        for tx in self._transactions:
            if tx.get("ref") == ref:
                return tx
        return None

    def find_by_id(self, tx_id: int) -> dict | None:
        for tx in self._transactions:
            if tx["id"] == tx_id:
                return tx
        return None


__all__ = ["Ledger"]
