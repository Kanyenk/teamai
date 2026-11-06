"""Repository SQLite pour StockMovement, avec mise à jour du StockLevel."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from xohive.wms.domain.stock_movement import StockMovement
from xohive.wms.domain.stock_level import StockLevel
from xohive.wms.repository.stock_level_repository import StockLevelRepository


class StockMovementRepository:
    """Enregistre les mouvements et met à jour les niveaux de stock."""

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
            CREATE TABLE IF NOT EXISTS wms_stock_movements (
                id TEXT PRIMARY KEY,
                organisation_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                warehouse_id TEXT NOT NULL,
                movement_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                target_warehouse_id TEXT,
                reason TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def _get_or_create_level(
        self, levels: StockLevelRepository, org: str, product: str, warehouse: str
    ) -> StockLevel:
        level = levels.get_by_product_and_warehouse(org, product, warehouse)
        if level is None:
            level = levels.create(StockLevel(
                organisation_id=org, product_id=product, warehouse_id=warehouse,
            ))
        return level

    def create(self, movement: StockMovement) -> StockMovement:
        now = datetime.now(timezone.utc).isoformat()
        movement_id = movement.id or str(uuid.uuid4())
        levels = StockLevelRepository(self.db_path)
        try:
            level = self._get_or_create_level(
                levels, movement.organisation_id,
                movement.product_id, movement.warehouse_id,
            )

            if movement.movement_type == "in":
                new_qty = level.quantity + movement.quantity
                levels.update_quantity(level.id, new_qty)
            elif movement.movement_type == "out":
                new_qty = level.quantity - movement.quantity
                if new_qty < 0:
                    raise ValueError(
                        f"insufficient stock: available {level.quantity}, "
                        f"requested {movement.quantity}"
                    )
                levels.update_quantity(level.id, new_qty)
            elif movement.movement_type == "adjustment":
                levels.update_quantity(level.id, movement.quantity)
            elif movement.movement_type == "transfer":
                target = self._get_or_create_level(
                    levels, movement.organisation_id,
                    movement.product_id, movement.target_warehouse_id,
                )
                new_src = level.quantity - movement.quantity
                if new_src < 0:
                    raise ValueError(
                        f"insufficient stock: available {level.quantity}, "
                        f"requested {movement.quantity}"
                    )
                levels.update_quantity(level.id, new_src)
                levels.update_quantity(target.id, target.quantity + movement.quantity)

            self.conn.execute(
                """
                INSERT INTO wms_stock_movements
                    (id, organisation_id, product_id, warehouse_id, movement_type,
                     quantity, target_warehouse_id, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    movement_id, movement.organisation_id, movement.product_id,
                    movement.warehouse_id, movement.movement_type, movement.quantity,
                    movement.target_warehouse_id, movement.reason, now,
                ),
            )
            self.conn.commit()
        finally:
            levels.close()

        return self.get_by_id(movement_id)

    def get_by_id(self, movement_id: str) -> StockMovement | None:
        row = self.conn.execute(
            "SELECT * FROM wms_stock_movements WHERE id = ?", (movement_id,)
        ).fetchone()
        return self._row_to_movement(row) if row else None

    def list_by_organisation(self, organisation_id: str) -> list[StockMovement]:
        rows = self.conn.execute(
            "SELECT * FROM wms_stock_movements WHERE organisation_id = ? ORDER BY created_at",
            (organisation_id,),
        ).fetchall()
        return [self._row_to_movement(r) for r in rows]

    def list(self) -> list[StockMovement]:
        rows = self.conn.execute(
            "SELECT * FROM wms_stock_movements ORDER BY created_at"
        ).fetchall()
        return [self._row_to_movement(r) for r in rows]

    @staticmethod
    def _row_to_movement(row: sqlite3.Row) -> StockMovement:
        return StockMovement(
            id=row["id"],
            organisation_id=row["organisation_id"],
            product_id=row["product_id"],
            warehouse_id=row["warehouse_id"],
            movement_type=row["movement_type"],
            quantity=row["quantity"],
            target_warehouse_id=row["target_warehouse_id"],
            reason=row["reason"],
            created_at=row["created_at"],
        )
