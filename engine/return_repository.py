"""Repository Return (retours clients)."""
from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional

from engine.returns import Return


class ReturnRepository:
    """Accès SQLite aux retours clients."""

    def __init__(self, db_path: str = "data/teamai.db") -> None:
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Crée la table returns si absente."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS returns (
                    id TEXT PRIMARY KEY,
                    organisation_id TEXT NOT NULL,
                    order_id TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    status TEXT NOT NULL,
                    refund_amount REAL NOT NULL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def create(self, ret: Return) -> Return:
        """Insère un retour."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO returns (id, organisation_id, order_id, product_id, quantity, reason, status, refund_amount, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ret.id,
                    ret.organisation_id,
                    ret.order_id,
                    ret.product_id,
                    ret.quantity,
                    ret.reason,
                    ret.status,
                    ret.refund_amount,
                    ret.created_at.isoformat(),
                    ret.updated_at.isoformat(),
                ),
            )
        return ret

    def get(self, return_id: str) -> Optional[Return]:
        """Récupère un retour par id."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM returns WHERE id = ?", (return_id,)).fetchone()
        if row is None:
            return None
        return Return(
            organisation_id=row["organisation_id"],
            order_id=row["order_id"],
            product_id=row["product_id"],
            quantity=row["quantity"],
            reason=row["reason"],
            status=row["status"],
            refund_amount=row["refund_amount"],
            id=row["id"],
        )

    def list(self, organisation_id: str) -> List[Return]:
        """Liste les retours d'une organisation."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM returns WHERE organisation_id = ? ORDER BY created_at DESC",
                (organisation_id,),
            ).fetchall()
        return [
            Return(
                organisation_id=r["organisation_id"],
                order_id=r["order_id"],
                product_id=r["product_id"],
                quantity=r["quantity"],
                reason=r["reason"],
                status=r["status"],
                refund_amount=r["refund_amount"],
                id=r["id"],
            )
            for r in rows
        ]

    def update(self, ret: Return) -> Return:
        """Met à jour un retour."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE returns
                SET status = ?, refund_amount = ?, updated_at = ?
                WHERE id = ?
                """,
                (ret.status, ret.refund_amount, ret.updated_at.isoformat(), ret.id),
            )
        return ret

    def delete(self, return_id: str) -> bool:
        """Supprime un retour."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("DELETE FROM returns WHERE id = ?", (return_id,))
            return cur.rowcount > 0
