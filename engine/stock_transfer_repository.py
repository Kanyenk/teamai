"""Repository StockTransfer."""
from __future__ import annotations

import sqlite3
from typing import List, Optional

from engine.stock_transfer import StockTransfer


class StockTransferRepository:
    """Accès SQLite aux stock_transfers."""

    def __init__(self, db_path: str = "data/teamai.db") -> None:
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS stock_transfers (
                    id TEXT PRIMARY KEY,
                    organisation_id TEXT NOT NULL,
                    from_warehouse_id TEXT NOT NULL,
                    to_warehouse_id TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    quantity TEXT NOT NULL,
                    status TEXT,
                    note TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def create(self, obj: StockTransfer) -> StockTransfer:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO stock_transfers (id, organisation_id, from_warehouse_id, to_warehouse_id, product_id, quantity, status, note, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (                    obj.id,
                    obj.organisation_id,
                    obj.from_warehouse_id,
                    obj.to_warehouse_id,
                    obj.product_id,
                    obj.quantity,
                    obj.status,
                    obj.note,
                    obj.created_at,
                    obj.updated_at,                ),
            )
        return obj

    def get(self, obj_id: str) -> Optional[StockTransfer]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM stock_transfers WHERE id = ?", (obj_id,)).fetchone()
        if row is None:
            return None
        return StockTransfer(
            organisation_id=row["organisation_id"],
            from_warehouse_id=row["from_warehouse_id"],
            to_warehouse_id=row["to_warehouse_id"],
            product_id=row["product_id"],
            quantity=int(row["quantity"]),
            status=row["status"],
            note=row["note"],
            id=row["id"],
        )

    def list(self, organisation_id: str) -> List[StockTransfer]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM stock_transfers WHERE organisation_id = ? ORDER BY created_at DESC",
                (organisation_id,),
            ).fetchall()
        return [
            StockTransfer(
                organisation_id=r["organisation_id"],
                from_warehouse_id=r["from_warehouse_id"],
                to_warehouse_id=r["to_warehouse_id"],
                product_id=r["product_id"],
                quantity=int(r["quantity"]),
                status=r["status"],
                note=r["note"],
                id=r["id"],
            )
            for r in rows
        ]

    def delete(self, obj_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("DELETE FROM stock_transfers WHERE id = ?", (obj_id,))
            return cur.rowcount > 0
