"""CompanyRepository — Persistance SQLite pour Company.

CRUD :
- create(company) : insère une nouvelle société
- get(company_id) : récupère une société par id
- list(offset=0, limit=50) : liste paginée
- update(company) : met à jour une société
- delete(company_id) : supprime une société

Relation : 1 → N avec Company (via organisation_id).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from xohive.crm.domain import company
from xohive.crm.domain.company import Company, CompanyError


class CompanyRepository:
    """Repository SQLite pour les sociétés CRM."""

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
                CREATE TABLE IF NOT EXISTS crm_companies (
                    id TEXT PRIMARY KEY,
                    organisation_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    siret TEXT NOT NULL,
                    address TEXT,
                    city TEXT,
                    zip_code TEXT,
                    country TEXT DEFAULT 'FR',
                    website TEXT,
                    phone TEXT,
                    email TEXT,
                    contact_person TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_by TEXT DEFAULT 'system',
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )

    def create(self, company: Company) -> Company:
        """Insère une nouvelle société. Retourne l'objet sauvegardé."""
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO crm_companies
                    (id, organisation_id, name, siret, address, city, zip_code,
                     country, website, phone, email, contact_person, is_active,
                     created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    company.id,
                    company.organisation_id,
                    company.name,
                    company.siret,
                    company.address,
                    company.city,
                    company.zip_code,
                    company.country,
                    company.website,
                    company.phone,
                    company.email,
                    company.contact_person,
                    1 if company.is_active else 0,
                    company.created_by,
                    company.created_at,
                    company.updated_at,
                ),
            )
        return self.get(company.id)

    def get(self, company_id: str) -> Company | None:
        """Récupère une société active par son identifiant."""
        cursor = self.conn.execute(
            """
            SELECT id, organisation_id, name, siret, address, city, zip_code,
                   country, website, phone, email, contact_person, is_active,
                   created_by, created_at, updated_at
            FROM crm_companies
            WHERE id = ? AND is_active = 1
            """,
            (company_id,),
        )
        row = cursor.fetchone()
        return self._row_to_company(row) if row else None

    def list(self, offset: int = 0, limit: int = 50) -> list[Company]:
        """Liste paginée des sociétés actives."""
        cursor = self.conn.execute(
            """
            SELECT id, organisation_id, name, siret, address, city, zip_code,
                   country, website, phone, email, contact_person, is_active,
                   created_by, created_at, updated_at
            FROM crm_companies
            WHERE is_active = 1
            ORDER BY name
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        return [self._row_to_company(row) for row in cursor.fetchall()]

    def update(self, company: Company) -> Company:
        """Met à jour une société existante."""
        with self.conn:
            self.conn.execute(
                """
                UPDATE crm_companies
                SET name = ?,
                    siret = ?,
                    address = ?,
                    city = ?,
                    zip_code = ?,
                    country = ?,
                    website = ?,
                    phone = ?,
                    email = ?,
                    contact_person = ?,
                    is_active = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    company.name,
                    company.siret,
                    company.address,
                    company.city,
                    company.zip_code,
                    company.country,
                    company.website,
                    company.phone,
                    company.email,
                    company.contact_person,
                    1 if company.is_active else 0,
                    company.updated_at,
                    company.id,
                ),
            )
        return self.get(company.id)

    def delete(self, company_id: str) -> bool:
        """Désactive (soft delete) une société."""
        company = self.get(company_id)
        if company is None:
            return False
        with self.conn:
            self.conn.execute(
                "UPDATE crm_companies SET is_active = 0, updated_at = ? WHERE id = ?",
                (company.updated_at or company.created_at, company_id),
            )
        return True

    def _row_to_company(self, row: sqlite3.Row) -> Company:
        """Convertit une ligne SQLite en objet Company."""
        return Company(
            id=row["id"],
            organisation_id=row["organisation_id"],
            name=row["name"],
            siret=row["siret"],
            address=row["address"],
            city=row["city"],
            zip_code=row["zip_code"],
            country=row["country"],
            website=row["website"],
            phone=row["phone"],
            email=row["email"],
            contact_person=row["contact_person"],
            is_active=bool(row["is_active"]),
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def __enter__(self) -> CompanyRepository:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.close()
        return False

    def close(self) -> None:
        if self.conn:
            self.conn.close()
