"""CRM API REST — Endpoints pour le module CRM minimal.

Endpoints :
- GET /api/v1/crm/companies
- POST /api/v1/crm/companies
- GET /api/v1/crm/companies/{id}
- PUT /api/v1/crm/companies/{id}
- GET /api/v1/crm/contacts
- POST /api/v1/crm/contacts
- GET /api/v1/crm/contacts/{id}
- GET /api/v1/crm/opportunities
- POST /api/v1/crm/opportunities
- GET /api/v1/crm/opportunities/{id}
- GET /api/v1/crm/pipeline/{company_id}
- GET /api/v1/crm/activities
- POST /api/v1/crm/activities

Avec :
- Authentification Bearer token
- Validation des requêtes
- Pagination
- Réponses JSON cohérentes
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from typing import Any, Dict
from urllib.parse import urlparse, unquote

from engine.auth import TokenAuth
from engine.exceptions import ValidationError
from xohive.crm.domain.company import Company
from xohive.crm.domain.contact import Contact
from xohive.crm.domain.opportunity import Opportunity
from xohive.crm.domain.activity import Activity
from xohive.crm.repository.company_repository import CompanyRepository
from xohive.crm.repository.contact_repository import ContactRepository
from xohive.crm.repository.opportunity_repository import OpportunityRepository
from xohive.crm.repository.activity_repository import ActivityRepository

# Codes HTTP utilisés dans l'API sécurisée
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_INTERNAL_ERROR = 500

STATUS_TEXT = {
    HTTP_OK: "OK",
    HTTP_CREATED: "Created",
    HTTP_BAD_REQUEST: "Bad Request",
    HTTP_UNAUTHORIZED: "Unauthorized",
    HTTP_FORBIDDEN: "Forbidden",
    HTTP_NOT_FOUND: "Not Found",
    HTTP_INTERNAL_ERROR: "Internal Server Error",
}


class CrmApiHandler(BaseHTTPRequestHandler):
    """Gestionnaire de requêtes pour l'API HTTP CRM."""

    store = None
    auth = None

    def _send_json(self, status: int, data: Dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status: int, message: str, code: str = "ERR"):
        self._send_json(status, {"error": {"code": code, "message": message}})

    def _read_body(self) -> Dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}

    def _require_auth(self) -> bool:
        """Vérifie l'authentification pour toutes les routes sauf /health."""
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
            return True

        if self.auth is None:
            return True

        if self.auth.authenticate(self.headers.get("Authorization")):
            return True

        self._send_error(
            HTTP_UNAUTHORIZED,
            "Unauthorized: missing or invalid token",
            "AUTH_401"
        )
        return False

    def do_GET(self):
        if not self._require_auth():
            return
        path = self.path.rstrip("/")
        parsed = urlparse(path)
        segments = [s for s in parsed.path.split("/") if s]

        if path == "/health":
            self._send_json(200, {"status": "ok"})
        elif parsed.path == "/api/v1/crm/companies":
            self._list_companies(segments)
        elif parsed.path == "/api/v1/crm/companies" and segments:
            self._get_company(segments)
        elif parsed.path == "/api/v1/crm/contacts":
            self._list_contacts(segments)
        elif parsed.path == "/api/v1/crm/contacts" and segments:
            self._get_contact(segments)
        elif parsed.path == "/api/v1/crm/opportunities":
            self._list_opportunities(segments)
        elif parsed.path == "/api/v1/crm/opportunities" and segments:
            self._get_opportunity(segments)
        elif parsed.path == "/api/v1/crm/pipeline":
            self._get_pipeline(segments)
        elif parsed.path == "/api/v1/crm/activities":
            self._list_activities(segments)
        else:
            self._send_error(404, "Not Found", "NOT_FOUND")

    def do_POST(self):
        if not self._require_auth():
            return
        path = self.path.rstrip("/")
        parsed = urlparse(path)
        segments = [s for s in parsed.path.split("/") if s]

        if parsed.path == "/api/v1/crm/companies":
            self._create_company()
        elif parsed.path == "/api/v1/crm/contacts":
            self._create_contact()
        elif parsed.path == "/api/v1/crm/opportunities":
            self._create_opportunity()
        elif parsed.path == "/api/v1/crm/activities":
            self._create_activity()
        else:
            self._send_error(404, "Not Found", "NOT_FOUND")

    def do_PUT(self):
        if not self._require_auth():
            return
        path = self.path.rstrip("/")
        parsed = urlparse(path)
        segments = [s for s in parsed.path.split("/") if s]

        if parsed.path == "/api/v1/crm/companies" and len(segments) == 3:
            self._update_company(segments)
        else:
            self._send_error(404, "Not Found", "NOT_FOUND")

    def _list_companies(self, segments):
        try:
            if self.store is None:
                self._send_error(500, "store not configured", "INTERNAL")
                return
            page = int(self.headers.get("X-Page", "1"))
            limit = int(self.headers.get("X-Limit", "50"))
            offset = (page - 1) * limit
            repo = CompanyRepository(self.store)
            companies = repo.list(offset=offset, limit=limit)
            repo.close()
            self._send_json(HTTP_OK, {
                "items": [c.to_dict() for c in companies],
                "page": page,
                "limit": limit,
                "total": len(companies),
            })
        except Exception as exc:
            self._send_error(HTTP_INTERNAL_ERROR, str(exc), "INTERNAL")

    def _get_company(self, segments):
        try:
            company_id = unquote(segments[2])
            if self.store is None:
                self._send_error(500, "store not configured", "INTERNAL")
                return
            repo = CompanyRepository(self.store)
            company = repo.get(company_id)
            repo.close()
            if company is None:
                self._send_error(HTTP_NOT_FOUND, "Company not found", "NOT_FOUND")
            else:
                self._send_json(HTTP_OK, company.to_dict())
        except Exception as exc:
            self._send_error(HTTP_INTERNAL_ERROR, str(exc), "INTERNAL")

    def _create_company(self):
        try:
            data = self._read_body()
            company = Company(
                name=data.get("name", ""),
                siret=data.get("siret", ""),
                address=data.get("address"),
                city=data.get("city"),
                zip_code=data.get("zip_code"),
                country=data.get("country", "FR"),
                website=data.get("website"),
                phone=data.get("phone"),
                email=data.get("email"),
                contact_person=data.get("contact_person"),
                is_active=data.get("is_active", True),
                organisation_id=data.get("organisation_id", "default-org"),
            )
            if self.store is not None:
                repo = CompanyRepository(self.store)
                result = repo.create(company)
                repo.close()
                self._send_json(HTTP_CREATED, result.to_dict())
            else:
                self._send_error(500, "store not configured", "INTERNAL")
        except ValidationError as exc:
            self._send_error(HTTP_BAD_REQUEST, str(exc), "VALIDATION")
        except Exception as exc:
            self._send_error(HTTP_INTERNAL_ERROR, str(exc), "INTERNAL")

    def _update_company(self, segments):
        try:
            company_id = unquote(segments[2])
            data = self._read_body()
            if self.store is None:
                self._send_error(500, "store not configured", "INTERNAL")
                return
            repo = CompanyRepository(self.store)
            company = repo.get(company_id)
            if company is None:
                repo.close()
                self._send_error(HTTP_NOT_FOUND, "Company not found", "NOT_FOUND")
                return
            company.name = data.get("name", company.name)
            company.siret = data.get("siret", company.siret)
            company.email = data.get("email", company.email)
            company.phone = data.get("phone", company.phone)
            company.address = data.get("address", company.address)
            company.city = data.get("city", company.city)
            company.zip_code = data.get("zip_code", company.zip_code)
            company.country = data.get("country", company.country)
            company.website = data.get("website", company.website)
            company.contact_person = data.get("contact_person", company.contact_person)
            company.is_active = data.get("is_active", company.is_active)
            company.updated_at = datetime.now(timezone.utc).isoformat()
            result = repo.update(company)
            repo.close()
            self._send_json(HTTP_OK, result.to_dict())
        except Exception as exc:
            self._send_error(HTTP_INTERNAL_ERROR, str(exc), "INTERNAL")

    def _list_contacts(self, segments):
        try:
            if self.store is None:
                self._send_error(500, "store not configured", "INTERNAL")
                return
            page = int(self.headers.get("X-Page", "1"))
            limit = int(self.headers.get("X-Limit", "50"))
            offset = (page - 1) * limit
            repo = ContactRepository(self.store)
            contacts = repo.list(offset=offset, limit=limit)
            repo.close()
            self._send_json(HTTP_OK, {
                "items": [c.to_dict() for c in contacts],
                "page": page,
                "limit": limit,
                "total": len(contacts),
            })
        except Exception as exc:
            self._send_error(HTTP_INTERNAL_ERROR, str(exc), "INTERNAL")

    def _get_contact(self, segments):
        try:
            contact_id = unquote(segments[2])
            if self.store is None:
                self._send_error(500, "store not configured", "INTERNAL")
                return
            repo = ContactRepository(self.store)
            contact = repo.get(contact_id)
            repo.close()
            if contact is None:
                self._send_error(HTTP_NOT_FOUND, "Contact not found", "NOT_FOUND")
            else:
                self._send_json(HTTP_OK, contact.to_dict())
        except Exception as exc:
            self._send_error(HTTP_INTERNAL_ERROR, str(exc), "INTERNAL")

    def _create_contact(self):
        try:
            data = self._read_body()
            contact = Contact(
                organisation_id=data.get("organisation_id", "default-org"),
                company_id=data.get("company_id", ""),
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", ""),
                email=data.get("email", ""),
                phone=data.get("phone"),
                job_title=data.get("job_title"),
                is_active=data.get("is_active", True),
            )
            if self.store is not None:
                repo = ContactRepository(self.store)
                result = repo.create(contact)
                repo.close()
                self._send_json(HTTP_CREATED, result.to_dict())
            else:
                self._send_error(500, "store not configured", "INTERNAL")
        except ValidationError as exc:
            self._send_error(HTTP_BAD_REQUEST, str(exc), "VALIDATION")
        except Exception as exc:
            self._send_error(HTTP_INTERNAL_ERROR, str(exc), "INTERNAL")

    def _list_opportunities(self, segments):
        try:
            if self.store is None:
                self._send_error(500, "store not configured", "INTERNAL")
                return
            page = int(self.headers.get("X-Page", "1"))
            limit = int(self.headers.get("X-Limit", "50"))
            offset = (page - 1) * limit
            repo = OpportunityRepository(self.store)
            opportunities = repo.list(offset=offset, limit=limit)
            repo.close()
            self._send_json(HTTP_OK, {
                "items": [o.to_dict() for o in opportunities],
                "page": page,
                "limit": limit,
                "total": len(opportunities),
            })
        except Exception as exc:
            self._send_error(HTTP_INTERNAL_ERROR, str(exc), "INTERNAL")

    def _get_opportunity(self, segments):
        try:
            opp_id = unquote(segments[2])
            if self.store is None:
                self._send_error(500, "store not configured", "INTERNAL")
                return
            repo = OpportunityRepository(self.store)
            opp = repo.get(opp_id)
            repo.close()
            self._send_json(HTTP_OK, opp.to_dict())
        except Exception as exc:
            self._send_error(HTTP_INTERNAL_ERROR, str(exc), "INTERNAL")

    def _create_opportunity(self):
        try:
            data = self._read_body()
            opp = Opportunity(
                organisation_id=data.get("organisation_id", "default-org"),
                company_id=data.get("company_id", ""),
                contact_id=data.get("contact_id"),
                title=data.get("title", ""),
                amount=data.get("amount", 0.0),
                stage=data.get("stage", Opportunity.STAGE_PROSPECTING),
                probability=data.get("probability"),
                close_date=data.get("close_date"),
                is_active=data.get("is_active", True),
            )
            if self.store is not None:
                repo = OpportunityRepository(self.store)
                result = repo.create(opp)
                repo.close()
                self._send_json(HTTP_CREATED, result.to_dict())
            else:
                self._send_error(500, "store not configured", "INTERNAL")
        except ValidationError as exc:
            self._send_error(HTTP_BAD_REQUEST, str(exc), "VALIDATION")
        except Exception as exc:
            self._send_error(HTTP_INTERNAL_ERROR, str(exc), "INTERNAL")

    def _get_pipeline(self, segments):
        try:
            company_id = unquote(segments[2])
            if self.store is None:
                self._send_error(500, "store not configured", "INTERNAL")
                return
            repo = OpportunityRepository(self.store)
            opportunities = repo.list(offset=0, limit=100)
            repo.close()
            active = [o for o in opportunities if o.company_id == company_id]
            stages = {}
            for o in active:
                if o.company_id not in stages:
                    stages[o.company_id] = {"count": 0, "stage": o.stage}
                stages[o.company_id]["count"] += 1
            self._send_json(HTTP_OK, {
                "company_id": company_id,
                "pipeline_stage": stages.get(company_id, {}).get("stage", "prospecting"),
                "opportunities_count": stages.get(company_id, {}).get("count", 0),
            })
        except Exception as exc:
            self._send_error(HTTP_INTERNAL_ERROR, str(exc), "INTERNAL")

    def _list_activities(self, segments):
        try:
            if self.store is None:
                self._send_error(500, "store not configured", "INTERNAL")
                return
            page = int(self.headers.get("X-Page", "1"))
            limit = int(self.headers.get("X-Limit", "50"))
            offset = (page - 1) * limit
            repo = ActivityRepository(self.store)
            activities = repo.list(offset=offset, limit=limit)
            repo.close()
            self._send_json(HTTP_OK, {
                "items": [a.to_dict() for a in activities],
                "page": page,
                "limit": limit,
                "total": len(activities),
            })
        except Exception as exc:
            self._send_error(HTTP_INTERNAL_ERROR, str(exc), "INTERNAL")

    def _create_activity(self):
        try:
            data = self._read_body()
            act = Activity(
                organisation_id=data.get("organisation_id", "default-org"),
                company_id=data.get("company_id", ""),
                contact_id=data.get("contact_id"),
                user_id=data.get("user_id"),
                type=data.get("type", Activity.TYPE_CALL),
                subject=data.get("subject", ""),
                description=data.get("description"),
                date=data.get("date"),
                duration=data.get("duration"),
                status=data.get("status", Activity.STATUS_PENDING),
                is_active=data.get("is_active", True),
            )
            if self.store is not None:
                repo = ActivityRepository(self.store)
                result = repo.create(act)
                repo.close()
                self._send_json(HTTP_CREATED, result.to_dict())
            else:
                self._send_error(500, "store not configured", "INTERNAL")
        except ValidationError as exc:
            self._send_error(HTTP_BAD_REQUEST, str(exc), "VALIDATION")
        except Exception as exc:
            self._send_error(HTTP_INTERNAL_ERROR, str(exc), "INTERNAL")
