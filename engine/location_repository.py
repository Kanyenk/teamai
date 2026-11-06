"""Repository Location."""
from __future__ import annotations

import sqlite3
from typing import List, Optional

from engine.location import Location


class LocationRepository:
    """Accès SQLite aux locations."""

    def __init__(self, db_path: str = "data/teamai.db") -> None:
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS locations (
                    id TEXT PRIMARY KEY,
                    organisation_id TEXT NOT NULL,
                    warehouse_id TEXT NOT NULL,
                    code TEXT NOT NULL,
                    name TEXT,
                    zone TEXT,
                    capacity TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def create(self, obj: Location) -> Location:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO locations (id, organisation_id, warehouse_id, code, name, zone, capacity, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (                    obj.id,
                    obj.organisation_id,
                    obj.warehouse_id,
                    obj.code,
                    obj.name,
                    obj.zone,
                    obj.capacity,
                    obj.created_at,
                    obj.updated_at,                ),
            )
        return obj

    def get(self, obj_id: str) -> Optional[Location]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM locations WHERE id = ?", (obj_id,)).fetchone()
        if row is None:
            return None
        return Location(
            organisation_id=row["organisation_id"],
            warehouse_id=row["warehouse_id"],
            code=row["code"],
            name=row["name"],
            zone=row["zone"],
            capacity=int(row["capacity"]),
            id=row["id"],
        )

    def list(self, organisation_id: str) -> List[Location]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM locations WHERE organisation_id = ? ORDER BY created_at DESC",
                (organisation_id,),
            ).fetchall()
        return [
            Location(
                organisation_id=r["organisation_id"],
                warehouse_id=r["warehouse_id"],
                code=r["code"],
                name=r["name"],
                zone=r["zone"],
                capacity=int(r["capacity"]),
                id=r["id"],
            )
            for r in rows
        ]

    def delete(self, obj_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("DELETE FROM locations WHERE id = ?", (obj_id,))
            return cur.rowcount > 0
