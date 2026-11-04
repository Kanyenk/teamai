"""ContactRepository — Persistance SQLite pour Contact.

CRUD :
- create(contact) : insère un nouveau contact
- get(contact_id) : récupère un contact par id
- list(offset=0, limit=50) : liste paginée des contacts actifs
- update(contact) : met à jour un contact
- delete(contact_id) : désactive un contact

Relation : N → 1 Company.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from xohive.crm.domain.contact import Contact, ContactError


class ContactRepository:
    """Repository SQLite pour les contacts CRM."""

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
                CREATE TABLE IF NOT EXISTS crm_contacts (
                    id TEXT PRIMARY KEY,
                    organisation_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    phone TEXT,
                    job_title TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_by TEXT DEFAULT 'system',
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )

    def create(self, contact: Contact) -> Contact:
        """Insère un nouveau contact."""
        self._validate_email_uniqueness(contact)
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO crm_contacts
                    (id, organisation_id, company_id, first_name, last_name,
                     email, phone, job_title, is_active, created_by, created_at,
                     updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    contact.id,
                    contact.organisation_id,
                    contact.company_id,
                    contact.first_name,
                    contact.last_name,
                    contact.email,
                    contact.phone,
                    contact.job_title,
                    1 if contact.is_active else 0,
                    contact.created_by,
                    contact.created_at,
                    contact.updated_at,
                ),
            )
        return self.get(contact.id)

    def _validate_email_uniqueness(self, contact: Contact) -> None:
        """Vérifie que l'email n'existe pas pour une autre société active."""
        cursor = self.conn.execute(
            """
            SELECT id FROM crm_contacts
            WHERE email = ? AND company_id != ? AND is_active = 1
            """,
            (contact.email, contact.company_id),
        )
        if cursor.fetchone():
            raise ContactError(f"email déjà utilisé : {contact.email}")

    def get(self, contact_id: str) -> Contact:
        """Récupère un contact par son identifiant."""
        cursor = self.conn.execute(
            """
            SELECT id, organisation_id, company_id, first_name, last_name,
                   email, phone, job_title, is_active, created_by, created_at,
                   updated_at
            FROM crm_contacts
            WHERE id = ? AND is_active = 1
            """,
            (contact_id,),
        )
        row = cursor.fetchone()
        return self._row_to_contact(row) if row else None

    def list(self, offset: int = 0, limit: int = 50) -> list[Contact]:
        """Liste paginée des contacts actifs."""
        cursor = self.conn.execute(
            """
            SELECT id, organisation_id, company_id, first_name, last_name,
                   email, phone, job_title, is_active, created_by, created_at,
                   updated_at
            FROM crm_contacts
            WHERE is_active = 1
            ORDER BY last_name, first_name
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        return [self._row_to_contact(row) for row in cursor.fetchall()]

    def update(self, contact: Contact) -> Contact:
        """Met à jour un contact."""
        self._validate_email_uniqueness(contact)
        with self.conn:
            self.conn.execute(
                """
                UPDATE crm_contacts
                SET company_id = ?,
                    first_name = ?,
                    last_name = ?,
                    email = ?,
                    phone = ?,
                    job_title = ?,
                    is_active = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    contact.company_id,
                    contact.first_name,
                    contact.last_name,
                    contact.email,
                    contact.phone,
                    contact.job_title,
                    1 if contact.is_active else 0,
                    contact.updated_at,
                    contact.id,
                ),
            )
        return self.get(contact.id)

    def delete(self, contact_id: str) -> bool:
        """Désactive (soft delete) un contact."""
        contact = self.get(contact_id)
        if contact is None:
            return False
        with self.conn:
            self.conn.execute(
                "UPDATE crm_contacts SET is_active = 0, updated_at = ? WHERE id = ?",
                (contact.updated_at or contact.created_at, contact_id),
            )
        return True

    def _row_to_contact(self, row: sqlite3.Row) -> Contact:
        """Convertit une ligne SQLite en objet Contact."""
        return Contact(
            id=row["id"],
            organisation_id=row["organisation_id"],
            company_id=row["company_id"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            email=row["email"],
            phone=row["phone"],
            job_title=row["job_title"],
            is_active=bool(row["is_active"]),
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def __enter__(self) -> ContactRepository:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.close()
        return False

    def close(self) -> None:
        if self.conn:
            self.conn.close()
