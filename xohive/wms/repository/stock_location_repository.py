"""Repository SQLite pour StockLocation."""
from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from xohive.wms.domain.stock_location import StockLocation


class StockLocationRepository:
    def __init__(self, db_path):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS stock_locations (
                id TEXT PRIMARY KEY,
                organisation_id TEXT NOT NULL,
                warehouse_id TEXT NOT NULL,
                code TEXT NOT NULL,
                name TEXT DEFAULT '',
                zone TEXT DEFAULT '',
                created_at TEXT DEFAULT ''
            )"""
        )
        self._conn.commit()

    def create(self, loc: StockLocation) -> StockLocation:
        loc.id = loc.id or f"loc-{uuid.uuid4().hex[:12]}"
        loc.created_at = loc.created_at or datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "INSERT INTO stock_locations (id, organisation_id, warehouse_id, code, name, zone, created_at) VALUES (?,?,?,?,?,?,?)",
            (loc.id, loc.organisation_id, loc.warehouse_id, loc.code, loc.name, loc.zone, loc.created_at),
        )
        self._conn.commit()
        return loc

    def get_by_id(self, loc_id: str):
        row = self._conn.execute("SELECT * FROM stock_locations WHERE id = ?", (loc_id,)).fetchone()
        if row is None:
            return None
        return StockLocation(
            organisation_id=row[1],
            warehouse_id=row[2],
            code=row[3],
            name=row[4],
            zone=row[5],
            id=row[0],
            created_at=row[6],
        )

    def list(self, organisation_id: str | None = None, warehouse_id: str | None = None, limit: int = 50, offset: int = 0):
        query = "SELECT * FROM stock_locations"
        params = []
        conditions = []
        if organisation_id:
            conditions.append("organisation_id = ?")
            params.append(organisation_id)
        if warehouse_id:
            conditions.append("warehouse_id = ?")
            params.append(warehouse_id)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY id LIMIT ? OFFSET ?"
        params += [limit, offset]
        rows = self._conn.execute(query, params).fetchall()
        return [
            StockLocation(
                organisation_id=row[1],
                warehouse_id=row[2],
                code=row[3],
                name=row[4],
                zone=row[5],
                id=row[0],
                created_at=row[6],
            )
            for row in rows
        ]

    def update(self, loc: StockLocation) -> StockLocation:
        self._conn.execute(
            "UPDATE stock_locations SET code = ?, name = ?, zone = ? WHERE id = ?",
            (loc.code, loc.name, loc.zone, loc.id),
        )
        self._conn.commit()
        return loc

    def delete(self, loc_id: str) -> bool:
        cur = self._conn.execute("DELETE FROM stock_locations WHERE id = ?", (loc_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def close(self):
        self._conn.close()
