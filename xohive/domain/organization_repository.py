"""OrganizationRepository — Persistance SQLite pour Organization.

Interface :
- create(organization) : insère un Organisation dans la base
- get(id) : récupère un Organisation par son identifiant
- list(offset=0, limit=50) : liste paginée
- update(organization) : met à jour un Organisation
- delete(id) : supprime un Organisation

Champs sauvegardés correspondent aux attributs de Organization :
id, name, timezone, currency, fiscal_code, website, phone, address,
contact_email, created_by, created_at, updated_at, is_active,
callback_webhook.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .organization import Organization


class OrganizationRepository:
    """Repository SQLite pour les organisations."""

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
                CREATE TABLE IF NOT EXISTS organizations (
                    id            TEXT PRIMARY KEY,
                    name          TEXT NOT NULL,
                    timezone      TEXT NOT NULL DEFAULT 'UTC',
                    currency      TEXT NOT NULL DEFAULT 'EUR',
                    fiscal_code   TEXT,
                    website       TEXT,
                    phone         TEXT,
                    address       TEXT,
                    contact_email TEXT,
                    created_by    TEXT DEFAULT 'system',
                    created_at    TEXT,
                    updated_at    TEXT,
                    is_active     BOOLEAN NOT NULL DEFAULT 1,
                    callback_webhook TEXT
                )
                """
            )

    def create(self, organization: Organization) -> Organization:
        """Insère un Organisation. Retourne l'objet sauvegardé."""
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO organizations
                    (id, name, timezone, currency, fiscal_code, website,
                     phone, address, contact_email, created_by, created_at,
                     updated_at, is_active, callback_webhook)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    organization.id,
                    organization.name,
                    organization.timezone,
                    organization.currency,
                    organization.fiscal_code,
                    organization.website,
                    organization.phone,
                    organization.address,
                    organization.contact_email,
                    organization.created_by,
                    organization.created_at,
                    organization.updated_at or organization.created_at,
                    1 if organization.is_active else 0,
                    organization.callback_webhook,
                ),
            )
        return self.get(organization.id)

    def get(self, organization_id: str) -> Organization | None:
        """Récupère un Organisation par son identifiant."""
        cursor = self.conn.execute(
            """
            SELECT id, name, timezone, currency, fiscal_code, website,
                   phone, address, contact_email, created_by, created_at,
                   updated_at, is_active, callback_webhook
            FROM organizations
            WHERE id = ?
            """,
            (organization_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_org(row)

    def list(self, offset: int = 0, limit: int = 50) -> list[Organization]:
        """Liste paginée des organisations actives."""
        cursor = self.conn.execute(
            """
            SELECT id, name, timezone, currency, fiscal_code, website,
                   phone, address, contact_email, created_by, created_at,
                   updated_at, is_active, callback_webhook
            FROM organizations
            WHERE is_active = 1
            ORDER BY name
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        return [self._row_to_org(row) for row in cursor.fetchall()]

    def update(self, organization: Organization) -> Organization:
        """Met à jour un Organisation."""
        with self.conn:
            self.conn.execute(
                """
                UPDATE organizations
                SET name = ?,
                    timezone = ?,
                    currency = ?,
                    fiscal_code = ?,
                    website = ?,
                    phone = ?,
                    address = ?,
                    contact_email = ?,
                    created_by = ?,
                    created_at = ?,
                    updated_at = ?,
                    is_active = ?,
                    callback_webhook = ?
                WHERE id = ?
                """,
                (
                    organization.name,
                    organization.timezone,
                    organization.currency,
                    organization.fiscal_code,
                    organization.website,
                    organization.phone,
                    organization.address,
                    organization.contact_email,
                    organization.created_by,
                    organization.created_at,
                    organization.updated_at or organization.created_at,
                    1 if organization.is_active else 0,
                    organization.callback_webhook,
                    organization.id,
                ),
            )
        return self.get(organization.id)

    def delete(self, organization_id: str) -> bool:
        """Supprime un Organisation. Retourne True si supprimé."""
        cursor = self.conn.execute(
            "DELETE FROM organizations WHERE id = ?", (organization_id,)
        )
        return cursor.rowcount > 0

    def _row_to_org(self, row: sqlite3.Row) -> Organization:
        """Convertit une ligne SQLite en objet Organization."""
        return Organization(
            id=row["id"],
            name=row["name"],
            tz=row["timezone"],
            currency=row["currency"],
            fiscal_code=row["fiscal_code"],
            website=row["website"],
            phone=row["phone"],
            address=row["address"],
            contact_email=row["contact_email"],
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            is_active=bool(row["is_active"]),
            callback_webhook=row["callback_webhook"],
        )

    def __enter__(self) -> OrganizationRepository:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.close()
        return False

    def close(self) -> None:
        """Ferme la connexion."""
        if self.conn:
            self.conn.close()
