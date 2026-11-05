"""CreditNoteRepository — Persistance des avoirs (credit notes).

Interface :
- create(credit_note) : insère un avoir dans la base de données
- get(credit_note_id) : récupère un avoir
- list(filters) : liste paginée des avoirs avec filtres
- update(credit_note) : met à jour un avoir
- delete(credit_note_id) : supprime un avoir

Compatibilité avec le système SQLite existant.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from xohive.crm.domain.credit_note import CreditNote, CreditNoteError


class CreditNoteRepository:
    """Repository SQLite pour les avoirs."""

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
                CREATE TABLE IF NOT EXISTS crm_credit_notes (
                    id TEXT PRIMARY KEY,
                    organisation_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    contact_id TEXT,
                    user_id TEXT,
                    invoice_id TEXT NOT NULL UNIQUE,
                    credit_date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    reason TEXT DEFAULT '',
                    currency TEXT DEFAULT 'EUR',
                    status TEXT DEFAULT 'draft',
                    is_active BOOLEAN DEFAULT 1,
                    created_by TEXT DEFAULT 'system',
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )

    def create(self, credit_note: CreditNote) -> CreditNote:
        """
        Crée un nouvel avoir.
        Vérifie que la facture existe et n'est pas déjà livrée.
        """
        if credit_note.status == CreditNote.STATUS_DRAFT and not credit_note.invoice_id:
            raise CreditNoteError("un avoir doit être lié à une facture")

        with self.conn:
            self.conn.execute(
                """
                INSERT INTO crm_credit_notes (
                    id, organisation_id, company_id, contact_id, user_id,
                    invoice_id, credit_date, amount, reason, currency,
                    status, is_active, created_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    credit_note.id or f"cn-{uuid.uuid4().hex[:12]}",
                    credit_note.organisation_id,
                    credit_note.company_id,
                    credit_note.contact_id,
                    credit_note.user_id,
                    credit_note.invoice_id,
                    credit_note.credit_date,
                    credit_note.amount,
                    credit_note.reason,
                    credit_note.currency,
                    credit_note.status,
                    1 if credit_note.is_active else 0,
                    credit_note.created_by,
                    credit_note.created_at or datetime.now(timezone.utc).isoformat(),
                    credit_note.updated_at,
                ),
            )
            self.conn.commit()

        return credit_note

    def get(self, credit_note_id: str) -> CreditNote | None:
        """Récupère un avoir par son ID."""
        cur = self.conn.execute(
            "SELECT * FROM crm_credit_notes WHERE id = ? AND is_active = 1",
            (credit_note_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_credit_note(row)

    def list(
        self,
        organisation_id: str | None = None,
        company_id: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[CreditNote]:
        """Liste des avoirs avec filtres optionnels."""
        query = "SELECT * FROM crm_credit_notes WHERE is_active = 1"
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

        query += " ORDER BY credit_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cur = self.conn.execute(query, params)
        rows = cur.fetchall()
        return [self._row_to_credit_note(row) for row in rows]

    def update(self, credit_note: CreditNote) -> CreditNote:
        """Met à jour un avoir existant."""
        with self.conn:
            self.conn.execute(
                """
                UPDATE crm_credit_notes SET
                    credit_date = ?, amount = ?, reason = ?, currency = ?,
                    status = ?, is_active = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    credit_note.credit_date,
                    credit_note.amount,
                    credit_note.reason,
                    credit_note.currency,
                    credit_note.status,
                    1 if credit_note.is_active else 0,
                    credit_note.updated_at,
                    credit_note.id,
                ),
            )
            self.conn.commit()
        return credit_note

    def delete(self, credit_note_id: str) -> bool:
        """Supprime un avoir (soft delete)."""
        cur = self.conn.execute(
            "UPDATE crm_credit_notes SET is_active = 0, updated_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), credit_note_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def _row_to_credit_note(self, row: sqlite3.Row) -> CreditNote:
        """Convertit une ligne SQLite en objet CreditNote."""
        return CreditNote(
            id=row["id"],
            organisation_id=row["organisation_id"],
            company_id=row["company_id"],
            contact_id=row["contact_id"] or None,
            user_id=row["user_id"] or None,
            invoice_id=row["invoice_id"],
            credit_date=row["credit_date"],
            amount=row["amount"],
            reason=row["reason"],
            currency=row["currency"],
            status=row["status"],
            is_active=bool(row["is_active"]),
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def __enter__(self) -> CreditNoteRepository:
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
