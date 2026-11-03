"""AuditEventRepository — Persistance SQLite pour AuditEvent.

Interface :
- create(audit) : insère un AuditEvent
- get(id) : récupère un AuditEvent par id
- list(offset=0, limit=50) : liste paginée
- filter(organisation_id=None, user_id=None, entity_type=None, entity_id=None, action=None) : filtrage avancé
- count() : nombre total d'événements

Par défaut, les AuditEvents sont stockés dans la même base SQLite que les
autres entités (data/audit.db), ou plus précisément dans la même base que
l'application.

Relations : N → 1 Organisation, N → 1 User.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .audit_event import AuditEvent


class AuditEventRepository:
    """Repository SQLite pour les événements d'audit.

    Stocke les audit events dans la table `audit_events` dans la même base
    SQLite que les autres entités.
    """

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
                CREATE TABLE IF NOT EXISTS audit_events (
                    id              TEXT PRIMARY KEY,
                    user_id         TEXT,                  -- NULL si système
                    organisation_id TEXT NOT NULL,
                    entity_type     TEXT NOT NULL,
                    entity_id       TEXT NOT NULL,
                    action          TEXT NOT NULL,
                    old_values      TEXT,                  -- JSON
                    new_values      TEXT,                  -- JSON
                    ip_address      TEXT,                  -- IPv4 / IPv6 / nom
                    user_agent      TEXT,
                    created_at      TEXT NOT NULL
                )
                """
            )

    def create(self, audit: AuditEvent) -> AuditEvent | None:
        """Insère un AuditEvent. Retourne l'objet sauvegardé."""
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO audit_events
                    (id, user_id, organisation_id, entity_type, entity_id,
                     action, old_values, new_values, ip_address, user_agent,
                     created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit.id,
                    audit.user_id,
                    audit.organisation_id,
                    audit.entity_type,
                    audit.entity_id,
                    audit.action,
                    self._serialize(audit.old_values),
                    self._serialize(audit.new_values),
                    audit.ip_address,
                    audit.user_agent,
                    audit.created_at,
                ),
            )
        return self.get(audit.id)

    def get(self, audit_id: str) -> AuditEvent | None:
        """Récupère un AuditEvent par son identifiant."""
        cursor = self.conn.execute(
            """
            SELECT id, user_id, organisation_id, entity_type, entity_id,
                   action, old_values, new_values, ip_address, user_agent,
                   created_at
            FROM audit_events
            WHERE id = ?
            """,
            (audit_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_audit(row)

    def list(self, offset: int = 0, limit: int = 50) -> list[AuditEvent]:
        """Liste paginée des audit events (plus récents d'abord)."""
        cursor = self.conn.execute(
            """
            SELECT id, user_id, organisation_id, entity_type, entity_id,
                   action, old_values, new_values, ip_address, user_agent,
                   created_at
            FROM audit_events
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        return [self._row_to_audit(row) for row in cursor.fetchall()]

    def filter(
        self,
        organisation_id: str | None = None,
        user_id: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        action: str | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Filtre les audit events avec les critères donnés.

        Tous les filtres sont facultatifs ; si aucun filtre n'est fourni,
        retourne les `limit` plus récents.
        """
        clauses = []
        params: list[Any] = []

        if organisation_id is not None:
            clauses.append("organisation_id = ?")
            params.append(organisation_id)
        if user_id is not None:
            clauses.append("user_id = ?")
            params.append(user_id)
        if entity_type is not None:
            clauses.append("entity_type = ?")
            params.append(entity_type)
        if entity_id is not None:
            clauses.append("entity_id = ?")
            params.append(entity_id)
        if action is not None:
            clauses.append("action = ?")
            params.append(action)

        where = " AND ".join(clauses) if clauses else "1=1"
        cursor = self.conn.execute(
            f"""
            SELECT id, user_id, organisation_id, entity_type, entity_id,
                   action, old_values, new_values, ip_address, user_agent,
                   created_at
            FROM audit_events
            WHERE {where}
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (*params, limit),
        )
        return [self._row_to_audit(row) for row in cursor.fetchall()]

    def count(self) -> int:
        """Retourne le nombre total d'audit events."""
        cursor = self.conn.execute(
            "SELECT COUNT(*) as count FROM audit_events"
        )
        return cursor.fetchone()["count"]

    def count_by_entity(self, entity_type: str, entity_id: str) -> int:
        """Retourne le nombre d'audit events pour une entité donnée."""
        cursor = self.conn.execute(
            """
            SELECT COUNT(*) as count FROM audit_events
            WHERE entity_type = ? AND entity_id = ?
            """,
            (entity_type, entity_id),
        )
        return cursor.fetchone()["count"]

    def _row_to_audit(self, row: sqlite3.Row) -> AuditEvent:
        """Convertit une ligne SQLite en objet AuditEvent."""
        old_values = None
        new_values = None

        if row["old_values"]:
            try:
                old_values = json.loads(row["old_values"])
            except (json.JSONDecodeError, TypeError):
                old_values = None

        if row["new_values"]:
            try:
                new_values = json.loads(row["new_values"])
            except (json.JSONDecodeError, TypeError):
                new_values = None

        return AuditEvent(
            id=row["id"],
            user_id=row["user_id"],
            organisation_id=row["organisation_id"],
            entity_type=row["entity_type"],
            entity_id=row["entity_id"],
            action=row["action"],
            old_values=old_values,
            new_values=new_values,
            ip_address=row["ip_address"],
            user_agent=row["user_agent"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _serialize(value: Any) -> str | None:
        """Sérialise une valeur en JSON.

        Retourne None si la valeur est None ou si la sérialisation échoue.
        """
        if value is None:
            return None
        try:
            return json.dumps(value)
        except (TypeError, ValueError):
            return None

    def __enter__(self) -> AuditEventRepository:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.close()
        return False

    def close(self) -> None:
        """Ferme la connexion."""
        if self.conn:
            self.conn.close()
