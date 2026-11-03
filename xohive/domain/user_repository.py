"""UserRepository — Persistance SQLite pour User.

Interface :
- create(user) : insère un User
- get(id) : récupère un User par id
- list(offset=0, limit=50) : liste paginée
- update(user) : met à jour un User
- delete(id) : supprime un User

Relations : User N→1 Organisation (organisation_id).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .organization import Organization
from .user import User


class UserRepository:
    """Repository SQLite pour les utilisateurs."""

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
                CREATE TABLE IF NOT EXISTS users (
                    id              TEXT PRIMARY KEY,
                    email           TEXT NOT NULL UNIQUE,
                    password_hash   TEXT NOT NULL,
                    first_name      TEXT,
                    last_name       TEXT,
                    phone           TEXT,
                    timezone        TEXT NOT NULL DEFAULT 'UTC',
                    language        TEXT NOT NULL DEFAULT 'fr',
                    is_active       BOOLEAN NOT NULL DEFAULT 1,
                    is_verified     BOOLEAN NOT NULL DEFAULT 0,
                    organisation_id TEXT NOT NULL,
                    created_by      TEXT DEFAULT 'system',
                    created_at      TEXT,
                    updated_at      TEXT,
                    FOREIGN KEY (organisation_id) REFERENCES organizations(id)
                )
                """
            )

    def create(self, user: User) -> User | None:
        """Insère un User. Retourne l'objet sauvegardé."""
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO users
                    (id, email, password_hash, first_name, last_name, phone,
                     timezone, language, is_active, is_verified, organisation_id,
                     created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user.id,
                    user.email,
                    user.password_hash,
                    user.first_name,
                    user.last_name,
                    user.phone,
                    user.timezone,
                    user.language,
                    1 if user.is_active else 0,
                    1 if user.is_verified else 0,
                    user.organisation_id,
                    user.created_by,
                    user.created_at,
                    user.updated_at or user.created_at,
                ),
            )
        return self.get(user.id)

    def get(self, user_id: str) -> User | None:
        """Récupère un User par son identifiant."""
        cursor = self.conn.execute(
            """
            SELECT id, email, password_hash, first_name, last_name, phone,
                   timezone, language, is_active, is_verified, organisation_id,
                   created_by, created_at, updated_at
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_user(row)

    def list(self, offset: int = 0, limit: int = 50) -> list[User]:
        """Liste paginée des utilisateurs actifs."""
        cursor = self.conn.execute(
            """
            SELECT id, email, password_hash, first_name, last_name, phone,
                   timezone, language, is_active, is_verified, organisation_id,
                   created_by, created_at, updated_at
            FROM users
            WHERE is_active = 1
            ORDER BY email
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        return [self._row_to_user(row) for row in cursor.fetchall()]

    def update(self, user: User) -> User | None:
        """Met à jour un User."""
        with self.conn:
            self.conn.execute(
                """
                UPDATE users
                SET email = ?,
                    password_hash = ?,
                    first_name = ?,
                    last_name = ?,
                    phone = ?,
                    timezone = ?,
                    language = ?,
                    is_active = ?,
                    is_verified = ?,
                    organisation_id = ?,
                    created_by = ?,
                    created_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    user.email,
                    user.password_hash,
                    user.first_name,
                    user.last_name,
                    user.phone,
                    user.timezone,
                    user.language,
                    1 if user.is_active else 0,
                    1 if user.is_verified else 0,
                    user.organisation_id,
                    user.created_by,
                    user.created_at,
                    user.updated_at or user.created_at,
                    user.id,
                ),
            )
        return self.get(user.id)

    def delete(self, user_id: str) -> bool:
        """Supprime un User. Retourne True si supprimé."""
        cursor = self.conn.execute(
            "DELETE FROM users WHERE id = ?", (user_id,)
        )
        return cursor.rowcount > 0

    def _row_to_user(self, row: sqlite3.Row) -> User:
        """Convertit une ligne SQLite en objet User."""
        return User(
            id=row["id"],
            email=row["email"],
            password_hash=row["password_hash"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            phone=row["phone"],
            timezone=row["timezone"],
            language=row["language"],
            is_active=bool(row["is_active"]),
            is_verified=bool(row["is_verified"]),
            organisation_id=row["organisation_id"],
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def __enter__(self) -> UserRepository:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.close()
        return False

    def close(self) -> None:
        """Ferme la connexion."""
        if self.conn:
            self.conn.close()
