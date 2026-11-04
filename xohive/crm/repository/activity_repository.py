"""ActivityRepository — Persistance SQLite pour Activity.

CRUD :
- create(activity) : insère une nouvelle activité
- get(activity_id) : récupère une activité
- list(offset=0, limit=50) : liste paginée
- update(activity) : met à jour une activité
- delete(activity_id) : désactive une activité

Relation : N → 1 Company, N → 1 Contact, N → 1 User.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from xohive.crm.domain.activity import Activity, ActivityError


class ActivityRepository:
    """Repository SQLite pour les activités CRM."""

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
                CREATE TABLE IF NOT EXISTS crm_activities (
                    id TEXT PRIMARY KEY,
                    organisation_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    contact_id TEXT,
                    user_id TEXT,
                    type TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    description TEXT,
                    date TEXT NOT NULL,
                    duration REAL,
                    status TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_by TEXT DEFAULT 'system',
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (company_id) REFERENCES crm_companies(id),
                    FOREIGN KEY (contact_id) REFERENCES crm_contacts(id),
                    FOREIGN KEY (user_id) REFERENCES crm_users(id)
                )
                """
            )

    def create(self, activity: Activity) -> Activity:
        """Insère une nouvelle activité."""
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO crm_activities
                    (id, organisation_id, company_id, contact_id, user_id,
                     type, subject, description, date, duration, status,
                     is_active, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    activity.id,
                    activity.organisation_id,
                    activity.company_id,
                    activity.contact_id,
                    activity.user_id,
                    activity.type,
                    activity.subject,
                    activity.description,
                    activity.date,
                    activity.duration,
                    activity.status,
                    1 if activity.is_active else 0,
                    activity.created_by,
                    activity.created_at,
                    activity.updated_at,
                ),
            )
        return self.get(activity.id)

    def get(self, activity_id: str) -> Activity:
        """Récupère une activité active par son identifiant."""
        cursor = self.conn.execute(
            """
            SELECT id, organisation_id, company_id, contact_id, user_id,
                   type, subject, description, date, duration, status,
                   is_active, created_by, created_at, updated_at
            FROM crm_activities
            WHERE id = ? AND is_active = 1
            """,
            (activity_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise ActivityError(f"activité introuvable : {activity_id}")
        return self._row_to_activity(row)

    def list(self, offset: int = 0, limit: int = 50) -> list[Activity]:
        """Liste paginée des activités actives."""
        cursor = self.conn.execute(
            """
            SELECT id, organisation_id, company_id, contact_id, user_id,
                   type, subject, description, date, duration, status,
                   is_active, created_by, created_at, updated_at
            FROM crm_activities
            WHERE is_active = 1
            ORDER BY date DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        return [self._row_to_activity(row) for row in cursor.fetchall()]

    def update(self, activity: Activity) -> Activity:
        """Met à jour une activité."""
        with self.conn:
            self.conn.execute(
                """
                UPDATE crm_activities
                SET company_id = ?,
                    contact_id = ?,
                    user_id = ?,
                    type = ?,
                    subject = ?,
                    description = ?,
                    date = ?,
                    duration = ?,
                    status = ?,
                    is_active = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    activity.company_id,
                    activity.contact_id,
                    activity.user_id,
                    activity.type,
                    activity.subject,
                    activity.description,
                    activity.date,
                    activity.duration,
                    activity.status,
                    1 if activity.is_active else 0,
                    activity.updated_at,
                    activity.id,
                ),
            )
        return self.get(activity.id)

    def delete(self, activity_id: str) -> bool:
        """Désactive (soft delete) une activité."""
        activity = self.get(activity_id)
        with self.conn:
            self.conn.execute(
                "UPDATE crm_activities SET is_active = 0, updated_at = ? WHERE id = ?",
                (activity.updated_at or activity.created_at, activity_id),
            )
        return True

    def _row_to_activity(self, row: sqlite3.Row) -> Activity:
        """Convertit une ligne SQLite en objet Activity."""
        return Activity(
            id=row["id"],
            organisation_id=row["organisation_id"],
            company_id=row["company_id"],
            contact_id=row["contact_id"],
            user_id=row["user_id"],
            type=row["type"],
            subject=row["subject"],
            description=row["description"],
            date=row["date"],
            duration=row["duration"],
            status=row["status"],
            is_active=bool(row["is_active"]),
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def __enter__(self) -> ActivityRepository:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.close()
        return False

    def close(self) -> None:
        if self.conn:
            self.conn.close()
