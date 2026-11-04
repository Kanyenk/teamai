"""AuditCRMRepository — Persistance des événements d'audit CRM.

Interface :
- create(audit) : insère un événement d'audit
- list(filters) : liste paginée des événements filtrés
- get(event_id) : récupère un événement

Compatibilité avec le système SQLite existant.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict

from xohive.domain.audit_event import AuditEvent


class AuditCRMRepository:
    """Repository SQLite pour les événements d'audit CRM."""

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
                CREATE TABLE IF NOT EXISTS crm_audit_events (
                    id TEXT PRIMARY KEY,
                    organisation_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    old_values TEXT,
                    new_values TEXT,
                    payload TEXT,
                    created_at TEXT
                )
                """
            )

    def create(self, audit: AuditEvent) -> AuditEvent:
        """Insère un événement d'audit."""
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO crm_audit_events
                    (id, organisation_id, entity_type, entity_id, action,
                     old_values, new_values, payload, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit.id,
                    audit.organisation_id,
                    audit.entity_type,
                    audit.entity_id,
                    audit.action,
                    json.dumps(audit.old_values) if audit.old_values else None,
                    json.dumps(audit.new_values) if audit.new_values else None,
                    json.dumps(audit.payload) if audit.payload else None,
                    audit.created_at,
                ),
            )
        return audit

    def get(self, event_id: str) -> AuditEvent | None:
        """Récupère un événement par son identifiant."""
        cursor = self.conn.execute(
            """
            SELECT id, organisation_id, entity_type, entity_id, action,
                   old_values, new_values, payload, created_at
            FROM crm_audit_events
            WHERE id = ?
            """,
            (event_id,),
        )
        row = cursor.fetchone()
        return self._row_to_audit(row) if row else None

    def list(self, filters: Dict[str, Any] | None = None, offset: int = 0, limit: int = 50):
        """
        Liste paginée des événements d'audit filtrés.
        Filters : organisation_id, entity_type, entity_id, action
        """
        query = """
            SELECT id, organisation_id, entity_type, entity_id, action,
                   old_values, new_values, payload, created_at
            FROM crm_audit_events
            WHERE 1=1
        """
        params = []

        if filters:
            if filters.get("organisation_id"):
                query += " AND organisation_id = ?"
                params.append(filters["organisation_id"])
            if filters.get("entity_type"):
                query += " AND entity_type = ?"
                params.append(filters["entity_type"])
            if filters.get("entity_id"):
                query += " AND entity_id = ?"
                params.append(filters["entity_id"])
            if filters.get("action"):
                query += " AND action = ?"
                params.append(filters["action"])

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = self.conn.execute(query, params)
        return [self._row_to_audit(row) for row in cursor.fetchall()]

    def _row_to_audit(self, row: sqlite3.Row) -> AuditEvent:
        """Convertit une ligne SQLite en objet AuditEvent."""
        old_values = None
        if row["old_values"]:
            try:
                old_values = json.loads(row["old_values"])
            except (json.JSONDecodeError, TypeError):
                old_values = row["old_values"]

        new_values = None
        if row["new_values"]:
            try:
                new_values = json.loads(row["new_values"])
            except (json.JSONDecodeError, TypeError):
                new_values = row["new_values"]

        payload = None
        if row["payload"]:
            try:
                payload = json.loads(row["payload"])
            except (json.JSONDecodeError, TypeError):
                payload = row["payload"]

        return AuditEvent(
            id=row["id"],
            organisation_id=row["organisation_id"],
            entity_type=row["entity_type"],
            entity_id=row["entity_id"],
            action=row["action"],
            old_values=old_values,
            new_values=new_values,
            payload=payload,
            created_at=row["created_at"],
        )

    def __enter__(self) -> AuditCRMRepository:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.close()
        return False

    def close(self) -> None:
        if self.conn:
            self.conn.close()
