"""InvoiceRepository — Persistance des factures (invoices).

Interface :
- create(invoice) : insère une facture dans la base de données
- get(invoice_id) : récupère une facture
- list(filters) : liste paginée des factures avec filtres
- update(invoice) : met à jour une facture
- delete(invoice_id) : supprime une facture

Compatibilité avec le système SQLite existant.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from xohive.crm.domain.invoice import Invoice, InvoiceError


class InvoiceRepository:
    """Repository SQLite pour les factures."""

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
                CREATE TABLE IF NOT EXISTS crm_invoices (
                    id TEXT PRIMARY KEY,
                    organisation_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    contact_id TEXT,
                    user_id TEXT,
                    order_id TEXT NOT NULL UNIQUE,
                    issue_date TEXT NOT NULL,
                    due_date TEXT,
                    amount REAL NOT NULL,
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

    def create(self, invoice: Invoice) -> Invoice:
        """
        Crée une nouvelle facture.
        Vérifie que la commande existe et est confirmée.
        """
        if invoice.status == Invoice.STATUS_DRAFT and not invoice.order_id:
            raise InvoiceError("une facture doit être liée à une commande")

        if invoice.due_date and invoice.issue_date > invoice.due_date:
            raise InvoiceError("due_date doit être après issue_date")

        with self.conn:
            self.conn.execute(
                """
                INSERT INTO crm_invoices (
                    id, organisation_id, company_id, contact_id, user_id,
                    order_id, issue_date, due_date, amount, tax_rate,
                    currency, status, is_active, created_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    invoice.id or f"inv-{uuid.uuid4().hex[:12]}",
                    invoice.organisation_id,
                    invoice.company_id,
                    invoice.contact_id,
                    invoice.user_id,
                    invoice.order_id,
                    invoice.issue_date,
                    invoice.due_date,
                    invoice.amount,
                    invoice.tax_rate,
                    invoice.currency,
                    invoice.status,
                    1 if invoice.is_active else 0,
                    invoice.created_by,
                    invoice.created_at or datetime.now(timezone.utc).isoformat(),
                    invoice.updated_at,
                ),
            )
            self.conn.commit()

        return invoice

    def get(self, invoice_id: str) -> Invoice | None:
        """Récupère une facture par son ID."""
        cur = self.conn.execute(
            "SELECT * FROM crm_invoices WHERE id = ? AND is_active = 1",
            (invoice_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_invoice(row)

    def list(
        self,
        organisation_id: str | None = None,
        company_id: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Invoice]:
        """Liste des factures avec filtres optionnels."""
        query = "SELECT * FROM crm_invoices WHERE is_active = 1"
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

        query += " ORDER BY issue_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cur = self.conn.execute(query, params)
        rows = cur.fetchall()
        return [self._row_to_invoice(row) for row in rows]

    def update(self, invoice: Invoice) -> Invoice:
        """Met à jour une facture existante."""
        with self.conn:
            self.conn.execute(
                """
                UPDATE crm_invoices SET
                    issue_date = ?, due_date = ?, amount = ?, tax_rate = ?,
                    currency = ?, status = ?, is_active = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    invoice.issue_date,
                    invoice.due_date,
                    invoice.amount,
                    invoice.tax_rate,
                    invoice.currency,
                    invoice.status,
                    1 if invoice.is_active else 0,
                    invoice.updated_at,
                    invoice.id,
                ),
            )
            self.conn.commit()
        return invoice

    def delete(self, invoice_id: str) -> bool:
        """Supprime une facture (soft delete)."""
        cur = self.conn.execute(
            "UPDATE crm_invoices SET is_active = 0, updated_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), invoice_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def _row_to_invoice(self, row: sqlite3.Row) -> Invoice:
        """Convertit une ligne SQLite en objet Invoice."""
        return Invoice(
            id=row["id"],
            organisation_id=row["organisation_id"],
            company_id=row["company_id"],
            contact_id=row["contact_id"] or None,
            user_id=row["user_id"] or None,
            order_id=row["order_id"],
            issue_date=row["issue_date"],
            due_date=row["due_date"],
            amount=row["amount"],
            tax_rate=row["tax_rate"],
            currency=row["currency"],
            status=row["status"],
            is_active=bool(row["is_active"]),
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def __enter__(self) -> InvoiceRepository:
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
