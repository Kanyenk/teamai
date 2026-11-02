"""SQLite document repository for TeamAI.

Fournit un accès persistant SQLite aux documents du moteur.
Ne modifie ni Document, ni DocumentStore, ni l'API existante.
"""

import sqlite3
from pathlib import Path
from typing import Any


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
        self.db_path = str(db_path)
        self._connect()

    def _connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
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

    def _row_to_doc(self, row: sqlite3.Row) -> Any:
        """Convertit une ligne SQLite en objet Document similaire."""
        doc = type("Document", (), {})()
        doc.id = row["id"]
        doc.doc_type = row["doc_type"]
        doc.numero_serie = row["numero_serie"]
        doc.org_id = row["org_id"]
        doc.date_creation = row["date_creation"]
        doc.etat = row["etat"]
        doc.etat_hash = row["etat_hash"]
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
