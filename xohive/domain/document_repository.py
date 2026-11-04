"""DocumentRepository — Persistance SQLite pour Document.

Interface :
- save(document) : insère ou met à jour un document
- get(document_id) : récupère un document par id
- list(offset=0, limit=50) : liste paginée

Relation : N → 1 Organisation.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .document import Document, DocumentError


class DocumentRepository:
    """Repository SQLite pour les documents."""

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
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    organisation_id TEXT NOT NULL,
                    user_id TEXT,
                    doc_type TEXT NOT NULL,
                    numero_serie INTEGER NOT NULL,
                    status TEXT,
                    etat TEXT,
                    hash_etat TEXT,
                    currency TEXT,
                    retention REAL,
                    balance REAL,
                    created_by TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )

    def save(self, document: Document) -> Document:
        """Insère ou met à jour un document. Retourne l'objet sauvegardé."""
        with self.conn:
            if document.id is None:
                import uuid
                document.id = f"doc-{uuid.uuid4().hex[:12]}"
            self.conn.execute(
                """
                INSERT INTO documents
                    (id, organisation_id, user_id, doc_type, numero_serie,
                     status, etat, hash_etat, currency, retention, balance,
                     created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    organisation_id=excluded.organisation_id,
                    user_id=excluded.user_id,
                    doc_type=excluded.doc_type,
                    numero_serie=excluded.numero_serie,
                    status=excluded.status,
                    etat=excluded.etat,
                    hash_etat=excluded.hash_etat,
                    currency=excluded.currency,
                    retention=excluded.retention,
                    balance=excluded.balance,
                    created_by=excluded.created_by,
                    created_at=excluded.created_at,
                    updated_at=excluded.updated_at
                """,
                (
                    document.id,
                    document.organisation_id,
                    document.user_id,
                    document.doc_type,
                    document.numero_serie,
                    document.status,
                    document.etat,
                    document.hash_etat,
                    document.currency,
                    document.retention,
                    document.balance,
                    document.created_by,
                    document.created_at,
                    document.updated_at,
                ),
            )
        return self.get(document.id)

    def get(self, document_id: str) -> Document | None:
        """Récupère un document par son identifiant."""
        cursor = self.conn.execute(
            """
            SELECT id, organisation_id, user_id, doc_type, numero_serie,
                   status, etat, hash_etat, currency, retention, balance,
                   created_by, created_at, updated_at
            FROM documents
            WHERE id = ?
            """,
            (document_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_doc(row)

    def list(self, offset: int = 0, limit: int = 50) -> list[Document]:
        """Liste paginée des documents."""
        cursor = self.conn.execute(
            """
            SELECT id, organisation_id, user_id, doc_type, numero_serie,
                   status, etat, hash_etat, currency, retention, balance,
                   created_by, created_at, updated_at
            FROM documents
            ORDER BY id
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        return [self._row_to_doc(row) for row in cursor.fetchall()]

    def _row_to_doc(self, row: sqlite3.Row) -> Document:
        """Convertit une ligne SQLite en objet Document."""
        return Document(
            id=row["id"],
            organisation_id=row["organisation_id"],
            user_id=row["user_id"],
            doc_type=row["doc_type"],
            numero_serie=row["numero_serie"],
            status=row["status"],
            etat=row["etat"],
            hash_etat=row["hash_etat"],
            currency=row["currency"],
            retention=row["retention"],
            balance=row["balance"],
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def __enter__(self) -> DocumentRepository:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.close()
        return False

    def close(self) -> None:
        if self.conn:
            self.conn.close()
