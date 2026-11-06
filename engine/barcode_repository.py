"""Repository Barcode."""
from __future__ import annotations

import sqlite3
from typing import List, Optional

from engine.barcode import Barcode


class BarcodeRepository:
    """Accès SQLite aux barcodes."""

    def __init__(self, db_path: str = "data/teamai.db") -> None:
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS barcodes (
                    id TEXT PRIMARY KEY,
                    organisation_id TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    code TEXT NOT NULL,
                    type TEXT NOT NULL,
                    label TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def create(self, obj: Barcode) -> Barcode:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO barcodes (id, organisation_id, product_id, code, type, label, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (                    obj.id,
                    obj.organisation_id,
                    obj.product_id,
                    obj.code,
                    obj.type,
                    obj.label,
                    obj.created_at,
                    obj.updated_at,                ),
            )
        return obj

    def get(self, obj_id: str) -> Optional[Barcode]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM barcodes WHERE id = ?", (obj_id,)).fetchone()
        if row is None:
            return None
        return Barcode(
            organisation_id=row["organisation_id"],
            product_id=row["product_id"],
            code=row["code"],
            type=row["type"],
            label=row["label"],
            id=row["id"],
        )

    def list(self, organisation_id: str) -> List[Barcode]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM barcodes WHERE organisation_id = ? ORDER BY created_at DESC",
                (organisation_id,),
            ).fetchall()
        return [
            Barcode(
                organisation_id=r["organisation_id"],
                product_id=r["product_id"],
                code=r["code"],
                type=r["type"],
                label=r["label"],
                id=r["id"],
            )
            for r in rows
        ]

    def get_by_code(self, organisation_id: str, code: str) -> Optional[Barcode]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM barcodes WHERE organisation_id = ? AND code = ?",
                (organisation_id, code),
            ).fetchone()
        if row is None:
            return None
        return Barcode(
            organisation_id=row["organisation_id"],
            product_id=row["product_id"],
            code=row["code"],
            type=row["type"],
            label=row["label"],
            id=row["id"],
        )

    def delete(self, obj_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("DELETE FROM barcodes WHERE id = ?", (obj_id,))
            return cur.rowcount > 0
