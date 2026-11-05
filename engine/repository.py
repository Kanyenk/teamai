"""SQLite document repository for TeamAI.

Fournit un accès persistant SQLite aux documents du moteur.
Ne modifie ni Document, ni DocumentStore, ni l'API existante.
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Any
from engine import Document, DocumentError, compute_state_hash

# Explicite pour éviter le DeprecationWarning Python 3.12 sur l'adaptateur
# datetime par défaut.
sqlite3.register_adapter(datetime, lambda d: d.isoformat())


class DocumentRepository:
    """Repository SQLite pour les documents du moteur.

    Expose une interface simple :
    - save(document) : insère ou met à jour un document
    - get(document_id) : récupère un document par son identifiant
    - list(offset=0, limit=50) : liste paginée des documents

    Les champs sauvegardés correspondent aux attributs de Document :
    id, doc_type, numero_serie, org_id, date_creation, etat, etat_hash
    """

    def __init__(self, db_path: str | Path):
        if not isinstance(db_path, (str, Path)):
            raise TypeError(f"db_path must be str or Path, got {type(db_path).__name__}")
        self.db_path = str(db_path)
        self._connect()

    def _connect(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    doc_type TEXT NOT NULL,
                    numero_serie INTEGER NOT NULL,
                    org_id INTEGER NOT NULL,
                    date_creation TEXT,
                    etat TEXT,
                    etat_hash TEXT
                )
            """)

    def save(self, document: Any) -> None:
        """Insère ou met à jour un document dans la base."""
        with self.conn:
            if document.id is None:
                import uuid
                document.id = f"doc-{uuid.uuid4().hex[:12]}"
            self.conn.execute(
                """
                INSERT INTO documents
                    (id, doc_type, numero_serie, org_id, date_creation, etat, etat_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    doc_type=excluded.doc_type,
                    numero_serie=excluded.numero_serie,
                    org_id=excluded.org_id,
                    date_creation=excluded.date_creation,
                    etat=excluded.etat,
                    etat_hash=excluded.etat_hash
                """,
                (
                    document.id,
                    document.doc_type,
                    document.numero_serie,
                    document.org_id,
                    document.date_creation,
                    document.etat,
                    document.etat_hash,
                ),
            )

    def get(self, document_id: str) -> Any | None:
        """Récupère un document par son identifiant, ou None si introuvable."""
        cursor = self.conn.execute(
            "SELECT id, doc_type, numero_serie, org_id, date_creation, etat, etat_hash "
            "FROM documents WHERE id = ?",
            (document_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_doc(row)

    def list(self, offset: int = 0, limit: int = 50) -> list[Any]:
        """Liste paginée des documents."""
        cursor = self.conn.execute(
            "SELECT id, doc_type, numero_serie, org_id, date_creation, etat, etat_hash "
            "FROM documents ORDER BY id LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = cursor.fetchall()
        return [self._row_to_doc(row) for row in rows]

    def _row_to_doc(self, row: sqlite3.Row) -> Document:
        """Convertit une ligne SQLite en objet Document."""
        doc = Document(
            doc_type=row["doc_type"],
            numero_serie=row["numero_serie"],
            date_creation=row["date_creation"],
            org_id=row["org_id"],
            currency="EUR",
            retention=0.0,
            balance=0.0,
            hash_etat=row["etat_hash"],
            created_by="system",
        )
        doc.id = row["id"]
        return doc

    def close(self):
        """Ferme la connexion à la base."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
