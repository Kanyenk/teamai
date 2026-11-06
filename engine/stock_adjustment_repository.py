"""Repository StockAdjustment (ajustements de stock)."""
from __future__ import annotations

import sqlite3
from typing import List, Optional

from engine.stock_adjustment import StockAdjustment


class StockAdjustmentRepository:
    """Accès SQLite aux ajustements de stock."""

    def __init__(self, db_path: str = "data/teamai.db") -> None:
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Crée la table stock_adjustments si absente."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS stock_adjustments (
                    id TEXT PRIMARY KEY,
                    organisation_id TEXT NOT NULL,
                    warehouse_id TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    note TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def create(self, adj: StockAdjustment) -> StockAdjustment:
        """Insère un ajustement."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO stock_adjustments (id, organisation_id, warehouse_id, product_id, quantity, reason, note, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    adj.id,
                    adj.organisation_id,
                    adj.warehouse_id,
                    adj.product_id,
                    adj.quantity,
                    adj.reason,
                    adj.note,
                    adj.created_at.isoformat(),
                    adj.updated_at.isoformat(),
                ),
            )
        return adj

    def get(self, adjustment_id: str) -> Optional[StockAdjustment]:
        """Récupère un ajustement par id."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM stock_adjustments WHERE id = ?", (adjustment_id,)).fetchone()
        if row is None:
            return None
        return StockAdjustment(
            organisation_id=row["organisation_id"],
            warehouse_id=row["warehouse_id"],
            product_id=row["product_id"],
            quantity=row["quantity"],
            reason=row["reason"],
            note=row["note"],
            id=row["id"],
        )

    def list(self, organisation_id: str) -> List[StockAdjustment]:
        """Liste les ajustements d'une organisation."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM stock_adjustments WHERE organisation_id = ? ORDER BY created_at DESC",
                (organisation_id,),
            ).fetchall()
        return [
            StockAdjustment(
                organisation_id=r["organisation_id"],
                warehouse_id=r["warehouse_id"],
                product_id=r["product_id"],
                quantity=r["quantity"],
                reason=r["reason"],
                note=r["note"],
                id=r["id"],
            )
            for r in rows
        ]

    def delete(self, adjustment_id: str) -> bool:
        """Supprime un ajustement."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("DELETE FROM stock_adjustments WHERE id = ?", (adjustment_id,))
            return cur.rowcount > 0
