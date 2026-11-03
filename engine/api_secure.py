"""API HTTP sécurisée pour le socle ERP.

Endpoints REST pour les entités communes du socle :
- POST /api/v1/organizations
- GET /api/v1/organizations
- GET /api/v1/users
- POST /api/v1/auth/login
- GET /api/v1/roles
- GET /api/v1/audit

Avec :
- Authentification Bearer token
- Validation des requêtes
- Pagination
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from typing import Any, Dict

from engine.auth import TokenAuth
from engine.repository import DocumentRepository
from xohive.domain.audit_event import AuditEvent
from xohive.domain.audit_event_repository import AuditEventRepository

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


class SecureApiHandler(BaseHTTPRequestHandler):
    """Gestionnaire de requêtes pour l'API HTTP sécurisée."""

    store = None
    auth = None
    audit_repo = None

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
        path = self.path.rstrip("/") or "/api/v1/audit"
        if path == "/health":
            self._send_json(200, {"status": "ok"})
        elif path == "/api/v1/audit":
            self._list_audit()
        else:
            self._send_error(404, "Not Found", "NOT_FOUND")

    def do_POST(self):
        if not self._require_auth():
            return
        path = self.path.rstrip("/") or "/api/v1/auth/login"
        if path == "/api/v1/auth/login":
            self._login()
        elif path == "/api/v1/organizations":
            self._create_organization()
        elif path == "/api/v1/users":
            self._create_user()
        else:
            self._send_error(404, "Not Found", "NOT_FOUND")

    def _list_audit(self):
        try:
            if self.audit_repo is None:
                self._send_error(500, "audit repository not configured", "INTERNAL")
                return
            events = self.audit_repo.list()
            self._send_json(HTTP_OK, {
                "items": [e.to_dict() for e in events],
                "total": len(events)
            })
        except Exception as exc:
            self._send_error(HTTP_INTERNAL_ERROR, str(exc), "INTERNAL")

    def _login(self):
        """Endpoint de connexion : retourne un token si les identifiants sont valides."""
        data = self._read_body()
        email = data.get("email", "")
        password = data.get("password", "")

        if not email or not password:
            self._send_error(HTTP_BAD_REQUEST, "email and password required", "VALIDATION")
            return

        # Vérification du token (simulée)
        # Dans un vrai système, on vérifierait email/password dans une base
        if email == "admin@example.com" and password == "admin123":
            token = f"tok_{uuid4_token()}"
            self._send_json(HTTP_CREATED, {
                "access_token": token,
                "token_type": "Bearer",
                "expires_in": 3600,
                "user": {"email": email, "role": "admin"}
            })
        else:
            self._send_error(HTTP_UNAUTHORIZED, "Invalid credentials", "AUTH_401")

    def _create_organization(self):
        data = self._read_body()
        name = data.get("name", "")
        if not name:
            self._send_error(HTTP_BAD_REQUEST, "name is required", "VALIDATION")
            return

        try:
            from xohive.domain.organization import Organization
            org = Organization(
                name=name,
                timezone=data.get("timezone", "UTC"),
                currency=data.get("currency", "EUR"),
                fiscal_code=data.get("fiscal_code"),
                website=data.get("website"),
                phone=data.get("phone"),
                address=data.get("address"),
                contact_email=data.get("contact_email"),
                is_active=data.get("is_active", True),
                callback_webhook=data.get("callback_webhook"),
            )
            if self.store is not None:
                self.store.save(org)
            self._send_json(HTTP_CREATED, org.to_dict())
        except Exception as exc:
            self._send_error(HTTP_BAD_REQUEST, str(exc), "VALIDATION")

    def _create_user(self):
        data = self._read_body()
        email = data.get("email", "")
        password = data.get("password", "")
        if not email or not password:
            self._send_error(HTTP_BAD_REQUEST, "email and password required", "VALIDATION")
            return

        try:
            from xohive.domain.user import User
            user = User(
                email=email,
                password_hash=self._hash_password(password),
                organisation_id=data.get("organisation_id", ""),
                first_name=data.get("first_name"),
                last_name=data.get("last_name"),
                phone=data.get("phone"),
                is_active=data.get("is_active", True),
            )
            self._send_json(HTTP_CREATED, user.to_dict())
        except Exception as exc:
            self._send_error(HTTP_BAD_REQUEST, str(exc), "VALIDATION")

    def _hash_password(self, password: str) -> str:
        """Simule le hachage du mot de passe."""
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()


def uuid4_token() -> str:
    """Génère un token aléatoire."""
    import uuid
    return uuid.uuid4().hex[:16]


def make_app(store=None, auth=None, audit_repo=None):
    """Crée un handler sécurisé pour l'API HTTP.

    Args:
        store: Repository pour les organisations et utilisateurs
        auth: Instance de TokenAuth
        audit_repo: Instance de AuditEventRepository
    """
    class _SecureApiHandler(SecureApiHandler):
        store = store
        auth = auth
        audit_repo = audit_repo

    return _SecureApiHandler
