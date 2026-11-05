"""BankStatement — Relevé bancaire du module Ventes & Facturation.

Entité :
- BankStatement : relevé bancaire importé (CSV)
- Champs : id, organisation_id, company_id, contact_id, user_id,
          statement_date, file_path, file_name, status (pending, matched, closed),
          raw_data (JSON), is_active

Relations : N → 1 Organisation, N → 1 Company, N → 1 Contact, N → 1 User

Liens : N → 1 Reconciliation (via statement_id)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


class BankStatementError(Exception):
    """Erreur de manipulation d'un relevé bancaire."""


class BankStatement:
    """Représentation d'un relevé bancaire importé."""

    # Statuts du relevé bancaire
    STATUS_PENDING = "pending"
    STATUS_MATCHED = "matched"
    STATUS_CLOSED = "closed"

    ALLOWED_STATUS = (
        STATUS_PENDING,
        STATUS_MATCHED,
        STATUS_CLOSED,
    )

    def __init__(
        self,
        *,
        id: str | None = None,
        organisation_id: str,
        company_id: str,
        contact_id: str | None = None,
        user_id: str | None = None,
        statement_date: str | None = None,
        file_path: str | None = None,
        file_name: str | None = None,
        amount: float | None = None,
        reference: str | None = None,
        raw_data: dict | None = None,
        status: str = STATUS_PENDING,
        is_active: bool = True,
        created_by: str = "system",
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        if not organisation_id:
            raise BankStatementError("organisation_id requis")
        if not company_id:
            raise BankStatementError("company_id requis")
        if not file_name:
            raise BankStatementError("file_name requis")
        if statement_date:
            from datetime import datetime as _dt
            from datetime import timezone as _tz

            dt = _dt.fromisoformat(statement_date)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=_tz.utc)
        if status not in self.ALLOWED_STATUS:
            raise BankStatementError(
                f"status invalide : {status}. Valeurs possibles : {self.ALLOWED_STATUS}"
            )
        if not isinstance(raw_data, dict):
            raise BankStatementError("raw_data doit être un dictionnaire")

        self.id: str = id or f"bs-{uuid.uuid4().hex[:12]}"
        self.organisation_id: str = organisation_id
        self.company_id: str = company_id
        self.contact_id: str | None = contact_id
        self.user_id: str | None = user_id
        self.statement_date: str | None = statement_date
        self.file_path: str | None = file_path
        self.file_name: str = file_name
        self.amount: float | None = amount
        self.reference: str | None = reference
        self.raw_data: dict = raw_data or {}
        self.status: str = status
        self.is_active: bool = is_active
        self.created_by: str = created_by
        self.created_at: str = created_at or datetime.now(timezone.utc).isoformat()
        self.updated_at: str | None = updated_at

    def to_dict(self) -> dict[str, Any]:
        """Sérialise l'objet en dictionnaire."""
        return {
            "id": self.id,
            "organisation_id": self.organisation_id,
            "company_id": self.company_id,
            "contact_id": self.contact_id,
            "user_id": self.user_id,
            "statement_date": self.statement_date,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "amount": self.amount,
            "reference": self.reference,
            "raw_data": self.raw_data,
            "status": self.status,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __repr__(self) -> str:
        return f"<BankStatement {self.id} status={self.status} file={self.file_name}>"


if __name__ == "__main__":
    pass
