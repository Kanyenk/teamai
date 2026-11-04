"""OpportunityRepository — Persistance SQLite pour Opportunity.

CRUD :
- create(opportunity) : insère une nouvelle opportunité
- get(opportunity_id) : récupère une opportunité
- list(offset=0, limit=50) : liste paginée
- update(opportunity) : met à jour une opportunité
- delete(opportunity_id) : désactive une opportunité

Relation : N → 1 Company, N → 1 Contact.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from xohive.crm.domain.opportunity import Opportunity, OpportunityError


class OpportunityRepository:
    """Repository SQLite pour les opportunités CRM."""

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
                CREATE TABLE IF NOT EXISTS crm_opportunities (
                    id TEXT PRIMARY KEY,
                    organisation_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    contact_id TEXT,
                    title TEXT NOT NULL,
                    amount REAL NOT NULL,
                    stage TEXT NOT NULL,
                    probability REAL,
                    close_date TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_by TEXT DEFAULT 'system',
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (company_id) REFERENCES crm_companies(id),
                    FOREIGN KEY (contact_id) REFERENCES crm_contacts(id)
                )
                """
            )

    def create(self, opportunity: Opportunity) -> Opportunity:
        """Insère une nouvelle opportunité."""
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO crm_opportunities
                    (id, organisation_id, company_id, contact_id, title, amount,
                     stage, probability, close_date, is_active, created_by,
                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    opportunity.id,
                    opportunity.organisation_id,
                    opportunity.company_id,
                    opportunity.contact_id,
                    opportunity.title,
                    opportunity.amount,
                    opportunity.stage,
                    opportunity.probability,
                    opportunity.close_date,
                    1 if opportunity.is_active else 0,
                    opportunity.created_by,
                    opportunity.created_at,
                    opportunity.updated_at,
                ),
            )
        return self.get(opportunity.id)

    def get(self, opportunity_id: str) -> Opportunity:
        """Récupère une opportunité active par son identifiant."""
        cursor = self.conn.execute(
            """
            SELECT id, organisation_id, company_id, contact_id, title, amount,
                   stage, probability, close_date, is_active, created_by,
                   created_at, updated_at
            FROM crm_opportunities
            WHERE id = ? AND is_active = 1
            """,
            (opportunity_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise OpportunityError(f"opportunité introuvable : {opportunity_id}")
        return self._row_to_opportunity(row)

    def list(self, offset: int = 0, limit: int = 50) -> list[Opportunity]:
        """Liste paginée des opportunités actives."""
        cursor = self.conn.execute(
            """
            SELECT id, organisation_id, company_id, contact_id, title, amount,
                   stage, probability, close_date, is_active, created_by,
                   created_at, updated_at
            FROM crm_opportunities
            WHERE is_active = 1
            ORDER BY amount DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        return [self._row_to_opportunity(row) for row in cursor.fetchall()]

    def update(self, opportunity: Opportunity) -> Opportunity:
        """Met à jour une opportunité."""
        with self.conn:
            self.conn.execute(
                """
                UPDATE crm_opportunities
                SET company_id = ?,
                    contact_id = ?,
                    title = ?,
                    amount = ?,
                    stage = ?,
                    probability = ?,
                    close_date = ?,
                    is_active = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    opportunity.company_id,
                    opportunity.contact_id,
                    opportunity.title,
                    opportunity.amount,
                    opportunity.stage,
                    opportunity.probability,
                    opportunity.close_date,
                    1 if opportunity.is_active else 0,
                    opportunity.updated_at,
                    opportunity.id,
                ),
            )
        return self.get(opportunity.id)

    def delete(self, opportunity_id: str) -> bool:
        """Désactive (soft delete) une opportunité."""
        opportunity = self.get(opportunity_id)
        with self.conn:
            self.conn.execute(
                "UPDATE crm_opportunities SET is_active = 0, updated_at = ? WHERE id = ?",
                (opportunity.updated_at or opportunity.created_at, opportunity_id),
            )
        return True

    def _row_to_opportunity(self, row: sqlite3.Row) -> Opportunity:
        """Convertit une ligne SQLite en objet Opportunity."""
        return Opportunity(
            id=row["id"],
            organisation_id=row["organisation_id"],
            company_id=row["company_id"],
            contact_id=row["contact_id"],
            title=row["title"],
            amount=row["amount"],
            stage=row["stage"],
            probability=row["probability"],
            close_date=row["close_date"],
            is_active=bool(row["is_active"]),
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def __enter__(self) -> OpportunityRepository:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.close()
        return False

    def close(self) -> None:
        if self.conn:
            self.conn.close()
