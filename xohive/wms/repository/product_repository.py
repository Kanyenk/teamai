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
        cols = [r[1] for r in self.conn.execute("PRAGMA table_info(wms_products)")]
        if "alert_threshold" not in cols:
            self.conn.execute(
                "ALTER TABLE wms_products ADD COLUMN alert_threshold INTEGER"
            )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS wms_alert_threshold_history (
                id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                old_threshold INTEGER,
                new_threshold INTEGER NOT NULL,
                changed_at TEXT NOT NULL
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

    def set_alert_threshold(self, product_id: str, threshold: int) -> Optional[int]:
        """Définit le seuil d'alerte d'un produit et journalise le changement."""
        cur = self.conn.execute(
            "SELECT alert_threshold FROM wms_products WHERE id = ? AND is_active = 1",
            (product_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        old_threshold = row["alert_threshold"]
        now = datetime.now(timezone.utc).isoformat()
        with self.conn:
            self.conn.execute(
                "UPDATE wms_products SET alert_threshold = ?, updated_at = ? WHERE id = ?",
                (threshold, now, product_id),
            )
            self.conn.execute(
                "INSERT INTO wms_alert_threshold_history "
                "(id, product_id, old_threshold, new_threshold, changed_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (f"th-{uuid4().hex[:12]}", product_id, old_threshold, threshold, now),
            )
        return threshold

    def list_threshold_history(self, product_id: str) -> List[dict]:
        """Retourne l'historique des seuils d'un produit, du plus récent."""
        cur = self.conn.execute(
            "SELECT old_threshold, new_threshold, changed_at "
            "FROM wms_alert_threshold_history WHERE product_id = ? "
            "ORDER BY changed_at DESC",
            (product_id,),
        )
        return [
            {"old_threshold": r["old_threshold"], "new_threshold": r["new_threshold"],
             "changed_at": r["changed_at"]}
            for r in cur
        ]

    def get_alert_threshold(self, product_id: str) -> Optional[int]:
        """Retourne le seuil d'alerte d'un produit, ou None."""
        cur = self.conn.execute(
            "SELECT alert_threshold FROM wms_products WHERE id = ? AND is_active = 1",
            (product_id,),
        )
        row = cur.fetchone()
        return row["alert_threshold"] if row else None

    def list_alert_thresholds(self) -> dict:
        """Retourne {product_id: threshold} pour les produits avec seuil."""
        cur = self.conn.execute(
            "SELECT id, alert_threshold FROM wms_products "
            "WHERE alert_threshold IS NOT NULL AND is_active = 1"
        )
        return {r["id"]: r["alert_threshold"] for r in cur}
