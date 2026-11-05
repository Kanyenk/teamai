"""ReconciliationRepository — Persistance des rapprochements bancaires.

Interface :
- create(reconciliation) : insère un rapprochement dans la base de données
- get(reconciliation_id) : récupère un rapprochement
- list(filters) : liste paginée des rapprochements avec filtres
- update(reconciliation) : met à jour un rapprochement
- delete(reconciliation_id) : supprime un rapprochement

Compatibilité avec le système SQLite existant.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from xohive.crm.domain.reconciliation import Reconciliation, ReconciliationError


class ReconciliationRepository:
    """Repository SQLite pour les rapprochements bancaires."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        self._connect()

    def _connect(self) -> None:
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self) -> None:
        with self.conn:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS crm_reconciliations (
                    id TEXT PRIMARY KEY,
                    organisation_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    contact_id TEXT,
                    user_id TEXT,
                    payment_id TEXT NOT NULL,
                    ledger_entry_id TEXT NOT NULL,
                    bank_date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'EUR',
                    status TEXT DEFAULT 'open',
                    reference TEXT NOT NULL UNIQUE,
                    is_active BOOLEAN DEFAULT 1,
                    created_by TEXT DEFAULT 'system',
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )

    def create(self, reconciliation: Reconciliation) -> Reconciliation:
        """
        Crée un nouveau rapprochement.
        Vérifie que le paiement et l'entrée de livret existent.
        Un rapprochement doit lier un Payment et un LedgerEntry.
        """
        if reconciliation.status == Reconciliation.STATUS_OPEN and not reconciliation.payment_id:
            raise ReconciliationError("un rapprochement doit être lié à un paiement")

        if reconciliation.status == Reconciliation.STATUS_OPEN and not reconciliation.ledger_entry_id:
            raise ReconciliationError("un rapprochement doit être lié à un LedgerEntry")

        with self.conn:
            self.conn.execute(
                """
                INSERT INTO crm_reconciliations (
                    id, organisation_id, company_id, contact_id, user_id,
                    payment_id, ledger_entry_id, bank_date, amount, currency,
                    status, reference, is_active, created_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    reconciliation.id or f"rec-{uuid.uuid4().hex[:12]}",
                    reconciliation.organisation_id,
                    reconciliation.company_id,
                    reconciliation.contact_id,
                    reconciliation.user_id,
                    reconciliation.payment_id,
                    reconciliation.ledger_entry_id,
                    reconciliation.bank_date,
                    reconciliation.amount,
                    reconciliation.currency,
                    reconciliation.status,
                    reconciliation.reference,
                    1 if reconciliation.is_active else 0,
                    reconciliation.created_by,
                    reconciliation.created_at or datetime.now(timezone.utc).isoformat(),
                    reconciliation.updated_at,
                ),
            )
            self.conn.commit()

        return reconciliation

    def get(self, reconciliation_id: str) -> Reconciliation | None:
        """Récupère un rapprochement par son ID."""
        cur = self.conn.execute(
            "SELECT * FROM crm_reconciliations WHERE id = ? AND is_active = 1",
            (reconciliation_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_reconciliation(row)

    def list(
        self,
        organisation_id: str | None = None,
        company_id: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Reconciliation]:
        """Liste des rapprochements avec filtres optionnels."""
        query = "SELECT * FROM crm_reconciliations WHERE is_active = 1"
        conditions: list[str] = []
        params: list[Any] = []

        if organisation_id:
            conditions.append("organisation_id = ?")
            params.append(organisation_id)
        if company_id:
            conditions.append("company_id = ?")
            params.append(company_id)
        if status:
            conditions.append("status = ?")
            params.append(status)

        if conditions:
            query += " AND " + " AND ".join(conditions)

        query += " ORDER BY bank_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cur = self.conn.execute(query, params)
        rows = cur.fetchall()
        return [self._row_to_reconciliation(row) for row in rows]

    def update(self, reconciliation: Reconciliation) -> Reconciliation:
        """Met à jour un rapprochement existant."""
        with self.conn:
            self.conn.execute(
                """
                UPDATE crm_reconciliations SET
                    bank_date = ?, amount = ?, currency = ?, status = ?,
                    reference = ?, is_active = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    reconciliation.bank_date,
                    reconciliation.amount,
                    reconciliation.currency,
                    reconciliation.status,
                    reconciliation.reference,
                    1 if reconciliation.is_active else 0,
                    reconciliation.updated_at,
                    reconciliation.id,
                ),
            )
            self.conn.commit()
        return reconciliation

    def delete(self, reconciliation_id: str) -> bool:
        """Supprime un rapprochement (soft delete)."""
        cur = self.conn.execute(
            "UPDATE crm_reconciliations SET is_active = 0, updated_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), reconciliation_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def _row_to_reconciliation(self, row: sqlite3.Row) -> Reconciliation:
        """Convertit une ligne SQLite en objet Reconciliation."""
        return Reconciliation(
            id=row["id"],
            organisation_id=row["organisation_id"],
            company_id=row["company_id"],
            contact_id=row["contact_id"] or None,
            user_id=row["user_id"] or None,
            payment_id=row["payment_id"],
            ledger_entry_id=row["ledger_entry_id"],
            bank_date=row["bank_date"],
            amount=row["amount"],
            currency=row["currency"],
            status=row["status"],
            reference=row["reference"],
            is_active=bool(row["is_active"]),
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def __enter__(self) -> ReconciliationRepository:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.close()
        return False

    def close(self) -> None:
        """Ferme la connexion à la base de données."""
        try:
            self.conn.close()
        except sqlite3.Error:
            pass
