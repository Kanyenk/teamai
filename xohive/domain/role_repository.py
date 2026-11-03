"""RoleRepository — Persistance SQLite pour Role.

Interface :
- create(role) : insère un Role
- get(id) : récupère un Role par id
- list(offset=0, limit=50) : liste paginée
- update(role) : met à jour un Role
- delete(id) : supprime un Role

Relations : Role N→1 Organisation, N→1 User.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .role import Role


class RoleRepository:
    """Repository SQLite pour les rôles."""

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
                CREATE TABLE IF NOT EXISTS roles (
                    id              TEXT PRIMARY KEY,
                    code            TEXT NOT NULL,
                    label           TEXT NOT NULL,
                    description     TEXT,
                    organisation_id TEXT NOT NULL,
                    permissions     TEXT NOT NULL,
                    created_by      TEXT DEFAULT 'system',
                    created_at      TEXT,
                    updated_at      TEXT,
                    FOREIGN KEY (organisation_id) REFERENCES organizations(id)
                )
                """
            )

    def create(self, role: Role) -> Role | None:
        """Insère un Role. Retourne l'objet sauvegardé."""
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO roles
                    (id, code, label, description, organisation_id, permissions,
                     created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    role.id,
                    role.code,
                    role.label,
                    role.description,
                    role.organisation_id,
                    ",".join(role.permissions),
                    role.created_by,
                    role.created_at,
                    role.updated_at or role.created_at,
                ),
            )
        return self.get(role.id)

    def get(self, role_id: str) -> Role | None:
        """Récupère un Role par son identifiant."""
        cursor = self.conn.execute(
            """
            SELECT id, code, label, description, organisation_id, permissions,
                   created_by, created_at, updated_at
            FROM roles
            WHERE id = ?
            """,
            (role_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_role(row)

    def list(self, offset: int = 0, limit: int = 50) -> list[Role]:
        """Liste paginée des rôles."""
        cursor = self.conn.execute(
            """
            SELECT id, code, label, description, organisation_id, permissions,
                   created_by, created_at, updated_at
            FROM roles
            ORDER BY label
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        return [self._row_to_role(row) for row in cursor.fetchall()]

    def update(self, role: Role) -> Role | None:
        """Met à jour un Role."""
        with self.conn:
            self.conn.execute(
                """
                UPDATE roles
                SET code = ?,
                    label = ?,
                    description = ?,
                    organisation_id = ?,
                    permissions = ?,
                    created_by = ?,
                    created_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    role.code,
                    role.label,
                    role.description,
                    role.organisation_id,
                    ",".join(role.permissions),
                    role.created_by,
                    role.created_at,
                    role.updated_at or role.created_at,
                    role.id,
                ),
            )
        return self.get(role.id)

    def delete(self, role_id: str) -> bool:
        """Supprime un Role. Retourne True si supprimé."""
        cursor = self.conn.execute(
            "DELETE FROM roles WHERE id = ?", (role_id,)
        )
        return cursor.rowcount > 0

    def _row_to_role(self, row: sqlite3.Row) -> Role:
        """Convertit une ligne SQLite en objet Role."""
        permissions = (
            [p.strip() for p in row["permissions"].split(",") if p.strip()]
            if row["permissions"]
            else []
        )
        return Role(
            id=row["id"],
            code=row["code"],
            label=row["label"],
            description=row["description"],
            organisation_id=row["organisation_id"],
            permissions=permissions,
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def __enter__(self) -> RoleRepository:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.close()
        return False

    def close(self) -> None:
        """Ferme la connexion."""
        if self.conn:
            self.conn.close()
