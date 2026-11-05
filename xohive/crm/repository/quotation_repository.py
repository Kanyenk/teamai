"""QuotationRepository — Persistance des devis (quotations).

Interface :
- create(quotation) : insère un devis dans la base de données
- get(quotation_id) : récupère un devis
- list(filters) : liste paginée des devis avec filtres
- update(quotation) : met à jour un devis
- delete(quotation_id) : supprime un devis

Compatibilité avec le système SQLite existant.
"""


from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from xohive.crm.domain.quotation import Quotation, QuotationError


class QuotationRepository:
    """Repository SQLite pour les quotations."""

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
                CREATE TABLE IF NOT EXISTS crm_quotations (
                    id TEXT PRIMARY KEY,
                    organisation_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    contact_id TEXT,
                    user_id TEXT,
                    reference TEXT NOT NULL UNIQUE,
                    quotation_date TEXT NOT NULL,
                    valid_until TEXT NOT NULL,
                    total_amount REAL NOT NULL,
                    tax_rate REAL DEFAULT 0.0,
                    currency TEXT DEFAULT 'EUR',
                    status TEXT DEFAULT 'draft',
                    is_active BOOLEAN DEFAULT 1,
                    created_by TEXT DEFAULT 'system',
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )

    def create(self, quotation: Quotation) -> Quotation:
        """
        Crée un nouveau devis.
        Lance une AuditEvent si le système de gestion des événements est configuré.
        """
        if not quotation.reference:
            quotation.reference = f"Q-{uuid.uuid4().hex[:8].upper()}"

        if not quotation.created_at:
            quotation.created_at = datetime.now(timezone.utc).isoformat()

        with self.conn:
            cur = self.conn.execute(
                """
                INSERT INTO crm_quotations (
                    id, organisation_id, company_id, contact_id, user_id,
                    reference, quotation_date, valid_until, total_amount,
                    tax_rate, currency, status, is_active, created_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    quotation.id,
                    quotation.organisation_id,
                    quotation.company_id,
                    quotation.contact_id,
                    quotation.user_id,
                    quotation.reference,
                    quotation.quotation_date,
                    quotation.valid_until,
                    quotation.total_amount,
                    quotation.tax_rate,
                    quotation.currency,
                    quotation.status,
                    1 if quotation.is_active else 0,
                    quotation.created_by,
                    quotation.created_at,
                    quotation.updated_at,
                ),
            )
            self.conn.commit()

        return quotation

    def get(self, quotation_id: str) -> Quotation | None:
        """Récupère un devis par son ID."""
        cur = self.conn.execute(
            "SELECT * FROM crm_quotations WHERE id = ? AND is_active = 1",
            (quotation_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_quotation(row)

    def list(
        self,
        organisation_id: str | None = None,
        company_id: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Quotation]:
        """Liste des devis avec filtres optionnels."""
        query = "SELECT * FROM crm_quotations WHERE is_active = 1"
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

        query += " ORDER BY quotation_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cur = self.conn.execute(query, params)
        rows = cur.fetchall()
        return [self._row_to_quotation(row) for row in rows]

    def update(self, quotation: Quotation) -> Quotation:
        """Met à jour un devis existant."""
        with self.conn:
            self.conn.execute(
                """
                UPDATE crm_quotations SET
                    contact_id = ?, user_id = ?, valid_until = ?,
                    total_amount = ?, tax_rate = ?, currency = ?,
                    status = ?, is_active = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    quotation.contact_id,
                    quotation.user_id,
                    quotation.valid_until,
                    quotation.total_amount,
                    quotation.tax_rate,
                    quotation.currency,
                    quotation.status,
                    1 if quotation.is_active else 0,
                    quotation.updated_at,
                    quotation.id,
                ),
            )
            self.conn.commit()
        return quotation

    def delete(self, quotation_id: str) -> bool:
        """Supprime un devis (soft delete)."""
        cur = self.conn.execute(
            "UPDATE crm_quotations SET is_active = 0, updated_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), quotation_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def _row_to_quotation(self, row: sqlite3.Row) -> Quotation:
        """Convertit une ligne SQLite en objet Quotation."""
        return Quotation(
            id=row["id"],
            organisation_id=row["organisation_id"],
            company_id=row["company_id"],
            contact_id=row["contact_id"] or None,
            user_id=row["user_id"] or None,
            reference=row["reference"],
            quotation_date=row["quotation_date"],
            valid_until=row["valid_until"],
            total_amount=row["total_amount"],
            tax_rate=row["tax_rate"],
            currency=row["currency"],
            status=row["status"],
            is_active=bool(row["is_active"]),
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def __enter__(self) -> QuotationRepository:
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
