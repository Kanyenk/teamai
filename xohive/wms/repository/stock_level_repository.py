"""Repository SQLite pour StockLevel."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from xohive.wms.domain.stock_level import StockLevel


class StockLevelRepository:
    """CRUD + unicité (produit, entrepôt) par organisation."""

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
            CREATE TABLE IF NOT EXISTS wms_stock_levels (
                id TEXT PRIMARY KEY,
                organisation_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                warehouse_id TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(organisation_id, product_id, warehouse_id)
            )
            """
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def create(self, level: StockLevel) -> StockLevel:
        now = datetime.now(timezone.utc).isoformat()
        level_id = level.id or str(uuid.uuid4())
        self.conn.execute(
            """
            INSERT INTO wms_stock_levels
                (id, organisation_id, product_id, warehouse_id, quantity, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                level_id, level.organisation_id, level.product_id,
                level.warehouse_id, level.quantity, now, now,
            ),
        )
        self.conn.commit()
        return self.get_by_id(level_id)

    def get_by_id(self, level_id: str) -> StockLevel | None:
        row = self.conn.execute(
            "SELECT * FROM wms_stock_levels WHERE id = ?", (level_id,)
        ).fetchone()
        return self._row_to_level(row) if row else None

    def get_by_product_and_warehouse(
        self, organisation_id: str, product_id: str, warehouse_id: str
    ) -> StockLevel | None:
        row = self.conn.execute(
            """
            SELECT * FROM wms_stock_levels
            WHERE organisation_id = ? AND product_id = ? AND warehouse_id = ?
            """,
            (organisation_id, product_id, warehouse_id),
        ).fetchone()
        return self._row_to_level(row) if row else None

    def list_by_organisation(self, organisation_id: str) -> list[StockLevel]:
        rows = self.conn.execute(
            "SELECT * FROM wms_stock_levels WHERE organisation_id = ? ORDER BY created_at",
            (organisation_id,),
        ).fetchall()
        return [self._row_to_level(r) for r in rows]

    def list(self) -> list[StockLevel]:
        rows = self.conn.execute(
            "SELECT * FROM wms_stock_levels ORDER BY created_at"
        ).fetchall()
        return [self._row_to_level(r) for r in rows]

    def update_quantity(self, level_id: str, quantity: int) -> StockLevel:
        if quantity < 0:
            raise ValueError("quantity must be >= 0")
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "UPDATE wms_stock_levels SET quantity = ?, updated_at = ? WHERE id = ?",
            (quantity, now, level_id),
        )
        self.conn.commit()
        return self.get_by_id(level_id)

    def delete(self, level_id: str) -> bool:
        cur = self.conn.execute(
            "DELETE FROM wms_stock_levels WHERE id = ?", (level_id,)
        )
        self.conn.commit()
        return cur.rowcount > 0

    @staticmethod
    def _row_to_level(row: sqlite3.Row) -> StockLevel:
        return StockLevel(
            id=row["id"],
            organisation_id=row["organisation_id"],
            product_id=row["product_id"],
            warehouse_id=row["warehouse_id"],
            quantity=row["quantity"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
