"""Repository SQLite pour Warehouse."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from xohive.wms.domain.warehouse import Warehouse


class WarehouseRepository:
    """CRUD + unicité de code par organisation."""

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
            CREATE TABLE IF NOT EXISTS wms_warehouses (
                id TEXT PRIMARY KEY,
                organisation_id TEXT NOT NULL,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                address TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(organisation_id, code)
            )
            """
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def create(self, warehouse: Warehouse) -> Warehouse:
        now = datetime.now(timezone.utc).isoformat()
        wh_id = warehouse.id or str(uuid.uuid4())
        self.conn.execute(
            """
            INSERT INTO wms_warehouses
                (id, organisation_id, code, name, address, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                wh_id, warehouse.organisation_id, warehouse.code, warehouse.name,
                warehouse.address, int(warehouse.is_active), now, now,
            ),
        )
        self.conn.commit()
        return self.get_by_id(wh_id)

    def get_by_id(self, warehouse_id: str) -> Warehouse | None:
        row = self.conn.execute(
            "SELECT * FROM wms_warehouses WHERE id = ?", (warehouse_id,)
        ).fetchone()
        return self._row_to_warehouse(row) if row else None

    def list(
        self,
        limit: int = 50,
        offset: int = 0,
        organisation_id: str | None = None,
        order_by: str = "created_at",
        direction: str = "asc",
    ) -> list[Warehouse]:
        if order_by not in {"created_at", "name", "code"}:
            raise ValueError(
                "order_by must be one of ['code', 'created_at', 'name']"
            )
        if direction not in {"asc", "desc"}:
            raise ValueError("direction must be 'asc' or 'desc'")
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
        if offset < 0:
            raise ValueError("offset must be >= 0")
        query = "SELECT * FROM wms_warehouses WHERE 1=1"
        params: list = []
        if organisation_id:
            query += " AND organisation_id = ?"
            params.append(organisation_id)
        query += f" ORDER BY {order_by} {direction.upper()} LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = self.conn.execute(query, params).fetchall()
        return [self._row_to_warehouse(r) for r in rows]

    def get_by_code(self, organisation_id: str, code: str) -> Warehouse | None:
        row = self.conn.execute(
            "SELECT * FROM wms_warehouses WHERE organisation_id = ? AND code = ?",
            (organisation_id, code),
        ).fetchone()
        return self._row_to_warehouse(row) if row else None

    def list_by_organisation(self, organisation_id: str) -> list[Warehouse]:
        rows = self.conn.execute(
            "SELECT * FROM wms_warehouses WHERE organisation_id = ? ORDER BY created_at",
            (organisation_id,),
        ).fetchall()
        return [self._row_to_warehouse(r) for r in rows]

    def update(self, warehouse: Warehouse) -> Warehouse:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            """
            UPDATE wms_warehouses
            SET code = ?, name = ?, address = ?, is_active = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                warehouse.code, warehouse.name, warehouse.address,
                int(warehouse.is_active), now, warehouse.id,
            ),
        )
        self.conn.commit()
        return self.get_by_id(warehouse.id)

    def delete(self, warehouse_id: str) -> bool:
        cur = self.conn.execute(
            "DELETE FROM wms_warehouses WHERE id = ?", (warehouse_id,)
        )
        self.conn.commit()
        return cur.rowcount > 0

    def count(self, organisation_id: str | None = None) -> int:
        query = "SELECT COUNT(*) AS total FROM wms_warehouses WHERE 1=1"
        params: list = []
        if organisation_id:
            query += " AND organisation_id = ?"
            params.append(organisation_id)
        row = self.conn.execute(query, params).fetchone()
        return row["total"]

    @staticmethod
    def _row_to_warehouse(row: sqlite3.Row) -> Warehouse:
        return Warehouse(
            id=row["id"],
            organisation_id=row["organisation_id"],
            code=row["code"],
            name=row["name"],
            address=row["address"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
