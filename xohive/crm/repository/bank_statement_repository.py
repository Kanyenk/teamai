"""BankStatementRepository — Persistance des relevés bancaires.

Interface :
- create(bank_statement) : insère un relevé bancaire
- get(bank_statement_id) : récupère un relevé
- list(filters) : liste paginée
- list_matches(statement_id, payment_id) : récupère les correspondances
- update(bank_statement) : met à jour
- delete(bank_statement_id) : supprime

Compatibilité avec le système SQLite existant.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from xohive.crm.domain.bank_statement import BankStatement, BankStatementError


class BankStatementRepository:
    """Repository SQLite pour les relevés bancaires."""

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
                CREATE TABLE IF NOT EXISTS crm_bank_statements (
                    id TEXT PRIMARY KEY,
                    organisation_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    contact_id TEXT,
                    user_id TEXT,
                    statement_date TEXT,
                    file_path TEXT,
                    file_name TEXT NOT NULL,
                    raw_data TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    is_active BOOLEAN DEFAULT 1,
                    created_by TEXT DEFAULT 'system',
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS crm_matches (
                    id TEXT PRIMARY KEY,
                    statement_id TEXT NOT NULL,
                    payment_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    reference TEXT NOT NULL UNIQUE,
                    confidence REAL DEFAULT 0.0,
                    matched_date TEXT NOT NULL,
                    created_at TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
                """
            )

    def create(self, bank_statement: BankStatement) -> BankStatement:
        """Insère un nouveau relevé bancaire."""
        if not isinstance(bank_statement, BankStatement):
            raise BankStatementError("Doit être un objet BankStatement")

        with self.conn:
            self.conn.execute(
                """
                INSERT INTO crm_bank_statements (
                    id, organisation_id, company_id, contact_id, user_id,
                    statement_date, file_path, file_name, raw_data, status,
                    is_active, created_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    bank_statement.id,
                    bank_statement.organisation_id,
                    bank_statement.company_id,
                    bank_statement.contact_id,
                    bank_statement.user_id,
                    bank_statement.statement_date,
                    bank_statement.file_path,
                    bank_statement.file_name,
                    json_dumps(bank_statement.raw_data),
                    bank_statement.status,
                    1 if bank_statement.is_active else 0,
                    bank_statement.created_by,
                    bank_statement.created_at,
                    bank_statement.updated_at,
                ),
            )
            self.conn.commit()

        return bank_statement

    def get(self, bank_statement_id: str) -> BankStatement | None:
        """Récupère un relevé par son ID."""
        cur = self.conn.execute(
            "SELECT * FROM crm_bank_statements WHERE id = ? AND is_active = 1",
            (bank_statement_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_bank_statement(row)

    def list(
        self,
        organisation_id: str | None = None,
        company_id: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[BankStatement]:
        """Liste des relevés avec filtres optionnels."""
        query = "SELECT * FROM crm_bank_statements WHERE is_active = 1"
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

        query += " ORDER BY statement_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cur = self.conn.execute(query, params)
        rows = cur.fetchall()
        return [self._row_to_bank_statement(row) for row in rows]

    def list_matches(self, statement_id: str, payment_id: str) -> list[dict]:
        """
        Récupère les correspondances pour un relevé et un paiement.
        Renvoie : [{ id, statement_id, payment_id, company_id, amount, reference, confidence, matched_date }]
        """
        cur = self.conn.execute(
            "SELECT * FROM crm_matches WHERE statement_id = ? AND payment_id = ?",
            (statement_id, payment_id),
        )
        rows = cur.fetchall()
        return [self._row_to_match_row(row) for row in rows]

    def update(self, bank_statement: BankStatement) -> BankStatement:
        """Met à jour un relevé existant."""
        with self.conn:
            self.conn.execute(
                """
                UPDATE crm_bank_statements SET
                    statement_date = ?, file_path = ?, file_name = ?, raw_data = ?,
                    status = ?, is_active = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    bank_statement.statement_date,
                    bank_statement.file_path,
                    bank_statement.file_name,
                    json_dumps(bank_statement.raw_data),
                    bank_statement.status,
                    1 if bank_statement.is_active else 0,
                    bank_statement.updated_at,
                    bank_statement.id,
                ),
            )
            self.conn.commit()
        return bank_statement

    def delete(self, bank_statement_id: str) -> bool:
        """Supprime un relevé (soft delete)."""
        cur = self.conn.execute(
            "UPDATE crm_bank_statements SET is_active = 0, updated_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), bank_statement_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def close(self) -> None:
        """Ferme la connexion SQLite."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _row_to_bank_statement(self, row: sqlite3.Row) -> BankStatement:
        """Convertit une ligne SQLite en objet BankStatement."""
        return BankStatement(
            id=row["id"],
            organisation_id=row["organisation_id"],
            company_id=row["company_id"],
            contact_id=row["contact_id"] or None,
            user_id=row["user_id"] or None,
            statement_date=row["statement_date"],
            file_path=row["file_path"],
            file_name=row["file_name"],
            raw_data=json_loads(row["raw_data"]),
            status=row["status"],
            is_active=bool(row["is_active"]),
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _row_to_match_row(self, row: sqlite3.Row) -> dict:
        """Convertit une ligne SQLite en dictionnaire."""
        return {
            "id": row["id"],
            "statement_id": row["statement_id"],
            "payment_id": row["payment_id"],
            "company_id": row["company_id"],
            "amount": row["amount"],
            "reference": row["reference"],
            "confidence": row["confidence"],
            "matched_date": row["matched_date"],
        }


def json_dumps(data: Any) -> str:
    """Sérialise en JSON."""
    import json

    return json.dumps(data, ensure_ascii=False)


def json_loads(data: str) -> Any:
    """Désérialise depuis du JSON."""
    import json

    return json.loads(data)
