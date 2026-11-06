"""Repository SQLite pour Shipment, avec expédition (mouvement out)."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from xohive.wms.domain.shipment import Shipment
from xohive.wms.domain.stock_movement import StockMovement
from xohive.wms.repository.stock_movement_repository import (
    StockMovementRepository,
)


class ShipmentRepository:
    """Gère les expéditions clients et les mouvements de stock associés."""

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
            CREATE TABLE IF NOT EXISTS wms_shipments (
                id TEXT PRIMARY KEY,
                organisation_id TEXT NOT NULL,
                order_id TEXT NOT NULL,
                warehouse_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                status TEXT NOT NULL,
                carrier TEXT,
                tracking_number TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def create(self, shipment: Shipment) -> Shipment:
        now = datetime.now(timezone.utc).isoformat()
        shipment_id = shipment.id or str(uuid.uuid4())
        self.conn.execute(
            """
            INSERT INTO wms_shipments
                (id, organisation_id, order_id, warehouse_id, product_id,
                 quantity, status, carrier, tracking_number,
                 created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                shipment_id, shipment.organisation_id, shipment.order_id,
                shipment.warehouse_id, shipment.product_id,
                shipment.quantity, shipment.status, shipment.carrier,
                shipment.tracking_number, now, now,
            ),
        )
        self.conn.commit()
        return self.get_by_id(shipment_id)

    def get_by_id(self, shipment_id: str) -> Shipment | None:
        row = self.conn.execute(
            "SELECT * FROM wms_shipments WHERE id = ?", (shipment_id,)
        ).fetchone()
        return self._row_to_shipment(row) if row else None

    def list_by_organisation(self, organisation_id: str) -> list[Shipment]:
        rows = self.conn.execute(
            "SELECT * FROM wms_shipments WHERE organisation_id = ? ORDER BY created_at",
            (organisation_id,),
        ).fetchall()
        return [self._row_to_shipment(r) for r in rows]

    def ship(self, shipment_id: str, carrier: str | None = None,
             tracking_number: str | None = None) -> dict:
        """Expédie une expédition (crée un mouvement out et passe à shipped)."""
        shipment = self.get_by_id(shipment_id)
        if shipment is None:
            raise ValueError(f"shipment {shipment_id} not found")
        if shipment.status != "draft":
            raise ValueError(f"shipment {shipment_id} is already shipped")

        # Créer un mouvement de sortie (out).
        movements = StockMovementRepository(self.db_path)
        try:
            movement = movements.create(StockMovement(
                organisation_id=shipment.organisation_id,
                product_id=shipment.product_id,
                warehouse_id=shipment.warehouse_id,
                movement_type="out",
                quantity=shipment.quantity,
                reason=f"shipment {shipment_id}",
            ))
            movement_id = movement.id
        finally:
            movements.close()

        # Marquer l'expédition comme expédiée.
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            """
            UPDATE wms_shipments
            SET status = 'shipped', carrier = ?, tracking_number = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (carrier, tracking_number, now, shipment_id),
        )
        self.conn.commit()

        return {
            "shipment": self.get_by_id(shipment_id).to_dict(),
            "movement_id": movement_id,
        }

    @staticmethod
    def _row_to_shipment(row: sqlite3.Row) -> Shipment:
        return Shipment(
            id=row["id"],
            organisation_id=row["organisation_id"],
            order_id=row["order_id"],
            warehouse_id=row["warehouse_id"],
            product_id=row["product_id"],
            quantity=row["quantity"],
            status=row["status"],
            carrier=row["carrier"],
            tracking_number=row["tracking_number"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
