"""Repository Inventory."""
from __future__ import annotations

import sqlite3
from typing import List, Optional

from engine.inventory import Inventory


class InventoryRepository:
    """Accès SQLite aux inventories."""

    def __init__(self, db_path: str = "data/teamai.db") -> None:
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS inventories (
                    id TEXT PRIMARY KEY,
                    organisation_id TEXT NOT NULL,
                    warehouse_id TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    counted_quantity TEXT NOT NULL,
                    expected_quantity TEXT NOT NULL,
                    note TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def create(self, obj: Inventory) -> Inventory:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO inventories (id, organisation_id, warehouse_id, product_id, counted_quantity, expected_quantity, note, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (                    obj.id,
                    obj.organisation_id,
                    obj.warehouse_id,
                    obj.product_id,
                    obj.counted_quantity,
                    obj.expected_quantity,
                    obj.note,
                    obj.created_at,
                    obj.updated_at,                ),
            )
        return obj

    def get(self, obj_id: str) -> Optional[Inventory]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM inventories WHERE id = ?", (obj_id,)).fetchone()
        if row is None:
            return None
        return Inventory(
            organisation_id=row["organisation_id"],
            warehouse_id=row["warehouse_id"],
            product_id=row["product_id"],
            counted_quantity=int(row["counted_quantity"]),
            expected_quantity=int(row["expected_quantity"]),
            note=row["note"],
            id=row["id"],
        )

    def list(self, organisation_id: str) -> List[Inventory]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM inventories WHERE organisation_id = ? ORDER BY created_at DESC",
                (organisation_id,),
            ).fetchall()
        return [
            Inventory(
                organisation_id=r["organisation_id"],
                warehouse_id=r["warehouse_id"],
                product_id=r["product_id"],
                counted_quantity=int(r["counted_quantity"]),
                expected_quantity=int(r["expected_quantity"]),
                note=r["note"],
                id=r["id"],
            )
            for r in rows
        ]

    def delete(self, obj_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("DELETE FROM inventories WHERE id = ?", (obj_id,))
            return cur.rowcount > 0
