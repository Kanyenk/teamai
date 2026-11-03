"""PermissionRepository — Persistance SQLite pour Permission.

Interface :
- create(permission) : insère un Permission
- get(id) : récupère un Permission par id
- list(offset=0, limit=50) : liste paginée
- update(permission) : met à jour un Permission
- delete(id) : supprime un Permission

Relations : Permission 1→N Role (via JSON de permissions).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .permission import Permission


class PermissionRepository:
    """Repository SQLite pour les permissions."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        self._connect()

    def _connect(self) -> None:
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self) -> None:
        with self.conn:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS permissions (
                    id          TEXT PRIMARY KEY,
                    code        TEXT NOT NULL UNIQUE,
                    label       TEXT NOT NULL,
                    description TEXT,
                    module      TEXT NOT NULL,
                    action      TEXT NOT NULL,
                    organisation_id TEXT NOT NULL,
                    FOREIGN KEY (organisation_id) REFERENCES organizations(id)
                )
                """
            )

    def create(self, permission: Permission) -> Permission | None:
        """Insère un Permission. Retourne l'objet sauvegardé."""
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO permissions
                    (id, code, label, description, module, action, organisation_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    permission.id,
                    permission.code,
                    permission.label,
                    permission.description,
                    permission.module,
                    permission.action,
                    permission.organisation_id,
                ),
            )
        return self.get(permission.id)

    def get(self, permission_id: str) -> Permission | None:
        """Récupère un Permission par son identifiant."""
        cursor = self.conn.execute(
            """
            SELECT id, code, label, description, module, action, organisation_id
            FROM permissions
            WHERE id = ?
            """,
            (permission_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_permission(row)

    def list(self, offset: int = 0, limit: int = 50) -> list[Permission]:
        """Liste paginée des permissions."""
        cursor = self.conn.execute(
            """
            SELECT id, code, label, description, module, action, organisation_id
            FROM permissions
            ORDER BY label
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        return [self._row_to_permission(row) for row in cursor.fetchall()]

    def update(self, permission: Permission) -> Permission | None:
        """Met à jour un Permission."""
        with self.conn:
            self.conn.execute(
                """
                UPDATE permissions
                SET code = ?,
                    label = ?,
                    description = ?,
                    module = ?,
                    action = ?,
                    organisation_id = ?
                WHERE id = ?
                """,
                (
                    permission.code,
                    permission.label,
                    permission.description,
                    permission.module,
                    permission.action,
                    permission.organisation_id,
                    permission.id,
                ),
            )
        return self.get(permission.id)

    def delete(self, permission_id: str) -> bool:
        """Supprime un Permission. Retourne True si supprimé."""
        cursor = self.conn.execute(
            "DELETE FROM permissions WHERE id = ?", (permission_id,)
        )
        return cursor.rowcount > 0

    def _row_to_permission(self, row: sqlite3.Row) -> Permission:
        """Convertit une ligne SQLite en objet Permission."""
        return Permission(
            id=row["id"],
            code=row["code"],
            label=row["label"],
            description=row["description"],
            module=row["module"],
            action=row["action"],
            organisation_id=row["organisation_id"],
        )

    def __enter__(self) -> PermissionRepository:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.close()
        return False

    def close(self) -> None:
        """Ferme la connexion."""
        if self.conn:
            self.conn.close()
