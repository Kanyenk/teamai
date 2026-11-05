"""PaymentRepository — Persistance des paiements (payments).

Interface :
- create(payment) : insère un paiement dans la base de données
- get(payment_id) : récupère un paiement
- list(filters) : liste paginée des paiements avec filtres
- update(payment) : met à jour un paiement
- delete(payment_id) : supprime un paiement

Compatibilité avec le système SQLite existant.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from xohive.crm.domain.payment import Payment, PaymentError


class PaymentRepository:
    """Repository SQLite pour les paiements."""

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
                CREATE TABLE IF NOT EXISTS crm_payments (
                    id TEXT PRIMARY KEY,
                    organisation_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    contact_id TEXT,
                    user_id TEXT,
                    invoice_id TEXT NOT NULL UNIQUE,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'EUR',
                    payment_date TEXT NOT NULL,
                    method TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    is_active BOOLEAN DEFAULT 1,
                    created_by TEXT DEFAULT 'system',
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )

    def create(self, payment: Payment) -> Payment:
        """
        Crée un nouveau paiement.
        """
        if payment.status == Payment.STATUS_PENDING and not payment.invoice_id:
            raise PaymentError("un paiement doit être lié à une facture")

        with self.conn:
            self.conn.execute(
                """
                INSERT INTO crm_payments (
                    id, organisation_id, company_id, contact_id, user_id,
                    invoice_id, amount, currency, payment_date, method,
                    status, is_active, created_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payment.id or f"pay-{uuid.uuid4().hex[:12]}",
                    payment.organisation_id,
                    payment.company_id,
                    payment.contact_id,
                    payment.user_id,
                    payment.invoice_id,
                    payment.amount,
                    payment.currency,
                    payment.payment_date,
                    payment.method,
                    payment.status,
                    1 if payment.is_active else 0,
                    payment.created_by,
                    payment.created_at or datetime.now(timezone.utc).isoformat(),
                    payment.updated_at,
                ),
            )
            self.conn.commit()

        return payment

    def get(self, payment_id: str) -> Payment | None:
        """Récupère un paiement par son ID."""
        cur = self.conn.execute(
            "SELECT * FROM crm_payments WHERE id = ? AND is_active = 1",
            (payment_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_payment(row)

    def list(
        self,
        organisation_id: str | None = None,
        company_id: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Payment]:
        """Liste des paiements avec filtres optionnels."""
        query = "SELECT * FROM crm_payments WHERE is_active = 1"
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

        query += " ORDER BY payment_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cur = self.conn.execute(query, params)
        rows = cur.fetchall()
        return [self._row_to_payment(row) for row in rows]

    def update(self, payment: Payment) -> Payment:
        """Met à jour un paiement existant."""
        with self.conn:
            self.conn.execute(
                """
                UPDATE crm_payments SET
                    amount = ?, currency = ?, payment_date = ?, method = ?,
                    status = ?, is_active = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    payment.amount,
                    payment.currency,
                    payment.payment_date,
                    payment.method,
                    payment.status,
                    1 if payment.is_active else 0,
                    payment.updated_at,
                    payment.id,
                ),
            )
            self.conn.commit()
        return payment

    def delete(self, payment_id: str) -> bool:
        """Supprime un paiement (soft delete)."""
        cur = self.conn.execute(
            "UPDATE crm_payments SET is_active = 0, updated_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), payment_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def _row_to_payment(self, row: sqlite3.Row) -> Payment:
        """Convertit une ligne SQLite en objet Payment."""
        return Payment(
            id=row["id"],
            organisation_id=row["organisation_id"],
            company_id=row["company_id"],
            contact_id=row["contact_id"] or None,
            user_id=row["user_id"] or None,
            invoice_id=row["invoice_id"],
            amount=row["amount"],
            currency=row["currency"],
            payment_date=row["payment_date"],
            method=row["method"],
            status=row["status"],
            is_active=bool(row["is_active"]),
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def __enter__(self) -> PaymentRepository:
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
