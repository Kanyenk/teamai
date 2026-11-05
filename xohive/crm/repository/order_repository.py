"""OrderRepository — Persistance des commandes (orders).

Interface :
- create(order) : insère une commande dans la base de données
- get(order_id) : récupère une commande
- list(filters) : liste paginée des commandes avec filtres
- update(order) : met à jour une commande
- delete(order_id) : supprime une commande

Compatibilité avec le système SQLite existant.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from xohive.crm.domain.order import Order, OrderError


class OrderRepository:
    """Repository SQLite pour les commandes."""

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
                CREATE TABLE IF NOT EXISTS crm_orders (
                    id TEXT PRIMARY KEY,
                    organisation_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    contact_id TEXT,
                    user_id TEXT,
                    quotation_id TEXT NOT NULL UNIQUE,
                    order_date TEXT NOT NULL,
                    delivery_date TEXT,
                    shipping_method TEXT NOT NULL,
                    total_amount REAL NOT NULL,
                    tax_rate REAL DEFAULT 0.0,
                    currency TEXT DEFAULT 'EUR',
                    status TEXT DEFAULT 'pending',
                    is_active BOOLEAN DEFAULT 1,
                    created_by TEXT DEFAULT 'system',
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )

    def create(self, order: Order) -> Order:
        """
        Crée une nouvelle commande.
        Vérifie que la quotation existe et est acceptée.
        """
        if not order.quotation_id:
            raise OrderError("quotation_id requis")

        if order.delivery_date and order.order_date > order.delivery_date:
            raise OrderError("delivery_date doit être après order_date")

        if order.status == Order.STATUS_PENDING and not order.quotation_id:
            raise OrderError("une commande doit être liée à une quotation")

        with self.conn:
            self.conn.execute(
                """
                INSERT INTO crm_orders (
                    id, organisation_id, company_id, contact_id, user_id,
                    quotation_id, order_date, delivery_date, shipping_method,
                    total_amount, tax_rate, currency, status, is_active,
                    created_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order.id or f"order-{uuid.uuid4().hex[:12]}",
                    order.organisation_id,
                    order.company_id,
                    order.contact_id,
                    order.user_id,
                    order.quotation_id,
                    order.order_date,
                    order.delivery_date,
                    order.shipping_method,
                    order.total_amount,
                    order.tax_rate,
                    order.currency,
                    order.status,
                    1 if order.is_active else 0,
                    order.created_by,
                    order.created_at or datetime.now(timezone.utc).isoformat(),
                    order.updated_at,
                ),
            )
            self.conn.commit()

        return order

    def get(self, order_id: str) -> Order | None:
        """Récupère une commande par son ID."""
        cur = self.conn.execute(
            "SELECT * FROM crm_orders WHERE id = ? AND is_active = 1",
            (order_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_order(row)

    def list(
        self,
        organisation_id: str | None = None,
        company_id: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Order]:
        """Liste des commandes avec filtres optionnels."""
        query = "SELECT * FROM crm_orders WHERE is_active = 1"
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

        query += " ORDER BY order_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cur = self.conn.execute(query, params)
        rows = cur.fetchall()
        return [self._row_to_order(row) for row in rows]

    def update(self, order: Order) -> Order:
        """Met à jour une commande existante."""
        with self.conn:
            self.conn.execute(
                """
                UPDATE crm_orders SET
                    order_date = ?, delivery_date = ?, shipping_method = ?,
                    total_amount = ?, tax_rate = ?, currency = ?,
                    status = ?, is_active = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    order.order_date,
                    order.delivery_date,
                    order.shipping_method,
                    order.total_amount,
                    order.tax_rate,
                    order.currency,
                    order.status,
                    1 if order.is_active else 0,
                    order.updated_at,
                    order.id,
                ),
            )
            self.conn.commit()
        return order

    def delete(self, order_id: str) -> bool:
        """Supprime une commande (soft delete)."""
        cur = self.conn.execute(
            "UPDATE crm_orders SET is_active = 0, updated_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), order_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def _row_to_order(self, row: sqlite3.Row) -> Order:
        """Convertit une ligne SQLite en objet Order."""
        return Order(
            id=row["id"],
            organisation_id=row["organisation_id"],
            company_id=row["company_id"],
            contact_id=row["contact_id"] or None,
            user_id=row["user_id"] or None,
            quotation_id=row["quotation_id"],
            order_date=row["order_date"],
            delivery_date=row["delivery_date"],
            shipping_method=row["shipping_method"],
            total_amount=row["total_amount"],
            tax_rate=row["tax_rate"],
            currency=row["currency"],
            status=row["status"],
            is_active=bool(row["is_active"]),
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def __enter__(self) -> OrderRepository:
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
