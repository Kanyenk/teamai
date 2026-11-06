"""Repository SQLite pour PurchaseOrder."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from xohive.wms.domain.purchase_order import PurchaseOrder


class PurchaseOrderRepository:
    """CRUD minimal pour les commandes fournisseurs."""

    def __init__(self, db_path: str | Path):
        if not isinstance(db_path, (str, Path)):
            raise TypeError(
                f"db_path must be str or Path, got {type(db_path).__name__}"
            )
        self.db_path = str(db_path)
        self._connect()

    def _connect(self) -> None:
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS wms_purchase_orders (
                id TEXT PRIMARY KEY,
                organisation_id TEXT NOT NULL,
                supplier_name TEXT NOT NULL,
                warehouse_id TEXT NOT NULL,
                status TEXT NOT NULL,
                reference TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def create(self, order: PurchaseOrder) -> PurchaseOrder:
        now = datetime.now(timezone.utc).isoformat()
        order_id = order.id or str(uuid.uuid4())
        reference = order.reference or f"PO-{uuid.uuid4().hex[:8].upper()}"
        self.conn.execute(
            """
            INSERT INTO wms_purchase_orders
                (id, organisation_id, supplier_name, warehouse_id,
                 status, reference, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id, order.organisation_id, order.supplier_name,
                order.warehouse_id, order.status, reference, now, now,
            ),
        )
        self.conn.commit()
        return self.get_by_id(order_id)

    def get_by_id(self, order_id: str) -> PurchaseOrder | None:
        row = self.conn.execute(
            "SELECT * FROM wms_purchase_orders WHERE id = ?", (order_id,)
        ).fetchone()
        return self._row_to_order(row) if row else None

    def list_by_organisation(self, organisation_id: str) -> list[PurchaseOrder]:
        rows = self.conn.execute(
            "SELECT * FROM wms_purchase_orders WHERE organisation_id = ? ORDER BY created_at",
            (organisation_id,),
        ).fetchall()
        return [self._row_to_order(r) for r in rows]

    def update_status(self, order_id: str, status: str) -> PurchaseOrder:
        if status not in {"draft", "received", "cancelled"}:
            raise ValueError("status must be draft, received or cancelled")
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "UPDATE wms_purchase_orders SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, order_id),
        )
        self.conn.commit()
        return self.get_by_id(order_id)

    @staticmethod
    def _row_to_order(row: sqlite3.Row) -> PurchaseOrder:
        return PurchaseOrder(
            id=row["id"],
            organisation_id=row["organisation_id"],
            supplier_name=row["supplier_name"],
            warehouse_id=row["warehouse_id"],
            status=row["status"],
            reference=row["reference"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
