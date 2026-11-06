"""Repository pour les produits du WMS."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional
from uuid import uuid4

from xohive.wms.domain.product import Product, ProductError


class ProductRepository:
    """Accès aux produits en base SQLite."""

    def __init__(self, db_path: str | Path) -> None:
        if not isinstance(db_path, (str, Path)):
            raise TypeError(
                f"db_path must be str or Path, got {type(db_path).__name__}"
            )
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self.conn:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS wms_products (
                    id TEXT PRIMARY KEY,
                    organisation_id TEXT NOT NULL,
                    sku TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    unit TEXT DEFAULT 'unit',
                    category TEXT DEFAULT '',
                    default_price REAL DEFAULT 0.0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )

    def create(self, product: Product) -> Product:
        if not isinstance(product, Product):
            raise ProductError("Doit être un objet Product")
        product.id = product.id or f"prod-{uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        if not product.created_at:
            product.created_at = now
        if not product.updated_at:
            product.updated_at = now
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO wms_products (
                    id, organisation_id, sku, name, description, unit,
                    category, default_price, is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    product.id,
                    product.organisation_id,
                    product.sku,
                    product.name,
                    product.description,
                    product.unit,
                    product.category,
                    product.default_price,
                    int(product.is_active),
                    product.created_at,
                    product.updated_at,
                ),
            )
        return product

    def get(self, product_id: str) -> Optional[Product]:
        cur = self.conn.execute(
            "SELECT * FROM wms_products WHERE id = ? AND is_active = 1",
            (product_id,),
        )
        row = cur.fetchone()
        return self._row_to_product(row) if row else None

    def count(
        self,
        organisation_id: str | None = None,
        search: str | None = None,
        created_from: str | None = None,
        created_to: str | None = None,
    ) -> int:
        query = "SELECT COUNT(*) AS total FROM wms_products WHERE is_active = 1"
        params: list = []
        if organisation_id:
            query += " AND organisation_id = ?"
            params.append(organisation_id)
        if search:
            query += " AND (name LIKE ? OR sku LIKE ?)"
            like = f"%{search}%"
            params.extend([like, like])
        if created_from:
            query += " AND created_at >= ?"
            params.append(created_from)
        if created_to:
            query += " AND created_at <= ?"
            params.append(created_to)
        row = self.conn.execute(query, params).fetchone()
        return row["total"]

    def get_by_sku(self, sku: str) -> Optional[Product]:
        cur = self.conn.execute(
            "SELECT * FROM wms_products WHERE sku = ? AND is_active = 1",
            (sku,),
        )
        row = cur.fetchone()
        return self._row_to_product(row) if row else None

    def list(
        self,
        organisation_id: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
        order_by: str = "created_at",
        direction: str = "asc",
        search: str | None = None,
        created_from: str | None = None,
        created_to: str | None = None,
    ) -> List[Product]:
        if order_by not in {"created_at", "name", "sku", "default_price"}:
            raise ValueError(
                "order_by must be one of ['created_at', 'default_price', 'name', 'sku']"
            )
        if direction not in {"asc", "desc"}:
            raise ValueError("direction must be 'asc' or 'desc'")
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
        if offset < 0:
            raise ValueError("offset must be >= 0")
        query = "SELECT * FROM wms_products WHERE is_active = 1"
        params: list = []
        if organisation_id:
            query += " AND organisation_id = ?"
            params.append(organisation_id)
        if search:
            query += " AND (name LIKE ? OR sku LIKE ?)"
            like = f"%{search}%"
            params.extend([like, like])
        if created_from:
            query += " AND created_at >= ?"
            params.append(created_from)
        if created_to:
            query += " AND created_at <= ?"
            params.append(created_to)
        query += f" ORDER BY {order_by} {direction.upper()} LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cur = self.conn.execute(query, params)
        return [self._row_to_product(r) for r in cur.fetchall()]

    def update(self, product: Product) -> Product:
        if not product.id:
            raise ProductError("id requis pour la mise à jour")
        with self.conn:
            self.conn.execute(
                """
                UPDATE wms_products SET
                    name = ?, description = ?, unit = ?, category = ?,
                    default_price = ?, is_active = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    product.name,
                    product.description,
                    product.unit,
                    product.category,
                    product.default_price,
                    int(product.is_active),
                    product.updated_at,
                    product.id,
                ),
            )
        return product

    def delete(self, product_id: str) -> bool:
        with self.conn:
            cur = self.conn.execute(
                "UPDATE wms_products SET is_active = 0 WHERE id = ?",
                (product_id,),
            )
        return cur.rowcount > 0

    def close(self) -> None:
        self.conn.close()

    def _row_to_product(self, row: sqlite3.Row) -> Product:
        return Product(
            id=row["id"],
            organisation_id=row["organisation_id"],
            sku=row["sku"],
            name=row["name"],
            description=row["description"],
            unit=row["unit"],
            category=row["category"],
            default_price=row["default_price"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
