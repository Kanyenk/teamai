"""Organization — Entité Organisation d'entreprise.

Attributs :
- id : TEXT/UUID (obligatoire)
- name : TEXT (obligatoire)
- timezone : TEXT (optionnel)
- currency : TEXT (obligatoire)
- fiscal_code : TEXT (optionnel)
- website : TEXT (optionnel)
- phone : TEXT (optionnel)
- address : TEXT (optionnel)
- contact_email : TEXT (optionnel)
- created_by : TEXT (optionnel)
- created_at : DATETIME (optionnel)
- updated_at : DATETIME (optionnel)
- is_active : BOOLEAN (obligatoire)
- callback_webhook : TEXT (optionnel)

Relations : 1 → N avec User, Document, AuditEvent, LedgerEntry.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


class Organization:
    """Représentation d'une organisation (entreprise)."""

    ALLOWED_CURRENCIES = ("EUR", "USD", "GBP", "JPY", "CHF")

    def __init__(
        self,
        *,
        id: str | None = None,
        name: str,
        tz: str = "UTC",
        currency: str = "EUR",
        fiscal_code: str | None = None,
        website: str | None = None,
        phone: str | None = None,
        address: str | None = None,
        contact_email: str | None = None,
        created_by: str = "system",
        created_at: str | None = None,
        updated_at: str | None = None,
        is_active: bool = True,
        callback_webhook: str | None = None,
    ) -> None:
        if not name:
            raise ValueError("name est obligatoire")
        if currency not in self.ALLOWED_CURRENCIES:
            raise ValueError(f"currency invalide : {currency}")

        self.id: str = id or f"org-{uuid.uuid4().hex[:12]}"
        self.name: str = name
        self.timezone: str = tz
        self.currency: str = currency
        self.fiscal_code: str | None = fiscal_code
        self.website: str | None = website
        self.phone: str | None = phone
        self.address: str | None = address
        self.contact_email: str | None = contact_email
        self.created_by: str = created_by
        self.created_at: str = created_at or datetime.now(timezone.utc).isoformat()
        self._updated_at: str | None = updated_at
        self.is_active: bool = is_active
        self.callback_webhook: str | None = callback_webhook

    @property
    def updated_at(self) -> str:
        return self._updated_at or self.created_at

    @updated_at.setter
    def updated_at(self, value: str | None) -> None:
        self._updated_at = value

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "timezone": self.timezone,
            "currency": self.currency,
            "fiscal_code": self.fiscal_code,
            "website": self.website,
            "phone": self.phone,
            "address": self.address,
            "contact_email": self.contact_email,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_active": self.is_active,
            "callback_webhook": self.callback_webhook,
        }

    def __repr__(self) -> str:
        return f"<Organization {self.id} {self.name}>"
