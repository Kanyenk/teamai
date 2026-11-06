"""Repository SQLite pour StockCount, avec ajustement de stock."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from xohive.wms.domain.stock_count import StockCount
from xohive.wms.domain.stock_movement import StockMovement
from xohive.wms.repository.stock_level_repository import StockLevelRepository
from xohive.wms.repository.stock_movement_repository import (
    StockMovementRepository,
)


class StockCountRepository:
    """Gère les comptages physiques et les ajustements de stock."""

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
        # Table des comptages physiques.
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS wms_stock_counts (
                id TEXT PRIMARY KEY,
                organisation_id TEXT NOT NULL,
                warehouse_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                counted_quantity INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def create(self, count: StockCount) -> StockCount:
        """Crée un comptage (statut draft par défaut)."""
        count_id = count.id or f"count-{uuid.uuid4().hex[:12]}"
        created_at = count.created_at or datetime.now(
            timezone.utc
        ).isoformat()
        self.conn.execute(
            """
            INSERT INTO wms_stock_counts (
                id, organisation_id, warehouse_id, product_id,
                counted_quantity, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                count_id,
                count.organisation_id,
                count.warehouse_id,
                count.product_id,
                count.counted_quantity,
                count.status,
                created_at,
            ),
        )
        self.conn.commit()
        return StockCount(
            organisation_id=count.organisation_id,
            warehouse_id=count.warehouse_id,
            product_id=count.product_id,
            counted_quantity=count.counted_quantity,
            status=count.status,
            id=count_id,
            created_at=created_at,
        )

    def get(self, count_id: str) -> StockCount | None:
        """Récupère un comptage par son id."""
        row = self.conn.execute(
            "SELECT * FROM wms_stock_counts WHERE id = ?", (count_id,)
        ).fetchone()
        if row is None:
            return None
        return StockCount(
            organisation_id=row["organisation_id"],
            warehouse_id=row["warehouse_id"],
            product_id=row["product_id"],
            counted_quantity=row["counted_quantity"],
            status=row["status"],
            id=row["id"],
            created_at=row["created_at"],
        )

    def list_by_organisation(self, org: str) -> list[StockCount]:
        """Liste les comptages d'une organisation."""
        rows = self.conn.execute(
            "SELECT * FROM wms_stock_counts WHERE organisation_id = ?",
            (org,),
        ).fetchall()
        return [
            StockCount(
                organisation_id=r["organisation_id"],
                warehouse_id=r["warehouse_id"],
                product_id=r["product_id"],
                counted_quantity=r["counted_quantity"],
                status=r["status"],
                id=r["id"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def adjust(self, count_id: str, reason: str | None = None) -> dict:
        """Ajuste le stock à partir d'un comptage validé.

        - Récupère le comptage et vérifie qu'il est en draft.
        - Calcule l'écart entre quantité comptée et stock théorique.
        - Si écart != 0, crée un mouvement correctif (in ou out).
        - Marque le comptage comme "adjusted".
        """
        count = self.get(count_id)
        if count is None:
            raise ValueError(f"stock count {count_id} not found")
        if count.status != "draft":
            raise ValueError(
                f"stock count {count_id} is already adjusted"
            )

        # Lire le stock théorique actuel.
        levels = StockLevelRepository(self.db_path)
        try:
            level = levels.get_by_product_and_warehouse(
                count.organisation_id,
                count.product_id,
                count.warehouse_id,
            )
            theoretical = level.quantity if level else 0
        finally:
            levels.close()

        # Calcul de l'écart (compté - théorique).
        diff = count.counted_quantity - theoretical

        movement_id = None
        if diff != 0:
            # Créer un mouvement correctif :
            # - diff < 0 → sortie (out) de |diff| unités ;
            # - diff > 0 → entrée (in) de diff unités.
            movement_type = "out" if diff < 0 else "in"
            movements = StockMovementRepository(self.db_path)
            try:
                movement = movements.create(StockMovement(
                    organisation_id=count.organisation_id,
                    product_id=count.product_id,
                    warehouse_id=count.warehouse_id,
                    movement_type=movement_type,
                    quantity=abs(diff),
                    reason=reason or "stock count adjustment",
                ))
                movement_id = movement.id
            finally:
                movements.close()

        # Marquer le comptage comme ajusté.
        self.conn.execute(
            "UPDATE wms_stock_counts SET status = 'adjusted' WHERE id = ?",
            (count_id,),
        )
        self.conn.commit()

        return {
            "count_id": count_id,
            "theoretical_quantity": theoretical,
            "counted_quantity": count.counted_quantity,
            "difference": diff,
            "movement_id": movement_id,
            "status": "adjusted",
        }
