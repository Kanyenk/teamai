"""Repository Supplier."""
from __future__ import annotations

import sqlite3
from typing import List, Optional

from engine.supplier import Supplier


class SupplierRepository:
    """Accès SQLite aux suppliers."""

    def __init__(self, db_path: str = "data/teamai.db") -> None:
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS suppliers (
                    id TEXT PRIMARY KEY,
                    organisation_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    address TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def create(self, obj: Supplier) -> Supplier:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO suppliers (id, organisation_id, name, email, phone, address, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (                    obj.id,
                    obj.organisation_id,
                    obj.name,
                    obj.email,
                    obj.phone,
                    obj.address,
                    obj.created_at,
                    obj.updated_at,                ),
            )
        return obj

    def get(self, obj_id: str) -> Optional[Supplier]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM suppliers WHERE id = ?", (obj_id,)).fetchone()
        if row is None:
            return None
        return Supplier(
            organisation_id=row["organisation_id"],
            name=row["name"],
            email=row["email"],
            phone=row["phone"],
            address=row["address"],
            id=row["id"],
        )

    def list(self, organisation_id: str) -> List[Supplier]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM suppliers WHERE organisation_id = ? ORDER BY created_at DESC",
                (organisation_id,),
            ).fetchall()
        return [
            Supplier(
                organisation_id=r["organisation_id"],
                name=r["name"],
                email=r["email"],
                phone=r["phone"],
                address=r["address"],
                id=r["id"],
            )
            for r in rows
        ]

    def delete(self, obj_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("DELETE FROM suppliers WHERE id = ?", (obj_id,))
            return cur.rowcount > 0
