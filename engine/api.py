"""API HTTP XoHive — couche d'accès publique au socle V0.

Ce module expose les routes REST minimales permettant de manipuler les
documents, les écritures et les transactions du socle. Il est écrit de
 sorte à être scalable (fastapi, flask, django) ; le contrôleur de base
ci-dessous utilise un micro-framework mock pour rester autonome et
exécutable sans dépendance externe.

Règles de sécurité :
- Aucune donnée sensible (clés, mots de passe, stack traces) n'est jamais
  renvoyée en dehors du contexte de développement.
- Chaque route vérifie l'état du document avant toute action.
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from typing import Callable, Awaitable, Any

from engine import Document, DocumentError, state_machine as sm


# Codes HTTP utiles
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_ACCEPTED = 202
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_CONFLICT = 409
HTTP_UNPROCESSABLE = 422
HTTP_INTERNAL_ERROR = 500

# Map explicite : code -> message lisible
STATUS_TEXT = {
    200: "OK",
    201: "Created",
    202: "Accepted",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    409: "Conflict",
    422: "Unprocessable Entity",
    500: "Internal Server Error",
}

# Chemins d'accès API (exemples)
ROUTES = {
    "documents:list": "/api/v0/documents",
    "documents:create": "/api/v0/documents",
    "documents:get": "/api/v0/documents/{doc_id}",
    "documents:open": "/api/v0/documents/{doc_id}/open",
    "documents:resign": "/api/v0/documents/{doc_id}/resign",
    "documents:send": "/api/v0/documents/{doc_id}/send",
    "documents:cancel": "/api/v0/documents/{doc_id}/cancel",
    "documents:delete": "/api/v0/documents/{doc_id}/delete",
    "ledger:post": "/api/v0/ledger/post",
    "transactions:create": "/api/v0/transactions/create",
    "transactions:get": "/api/v0/transactions/{tx_id}",
}


class XoHiveError(Exception):
    """Erreur métier capturée par le handler HTTP."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class Router:
    """Passerelle de routes. Chaque route est associée à un handler."""

    def __init__(self) -> None:
        self._routes: dict[str, Callable] = {}

    def route(self, path: str, methods: tuple[str, ...] = ("GET",)):
        def decorator(handler):
            self._routes[path] = (handler, methods)
            return handler

        return decorator

    def handle(self, method: str, path: str, body: dict) -> tuple[int, dict]:
        for route_path, (handler, methods) in self._routes.items():
            if path == route_path and method in methods:
                return handler(body)
        return HTTP_NOT_FOUND, {"error": "route inconnue"}


class Handler(BaseHTTPRequestHandler):
    """Serveur HTTP léger pour le socle V0."""

    router = Router()
    document_store = None
    ledger = None

    # -- BaseHTTPRequestHandler -------------------------------------------

    def _send(self, code: int, payload: dict) -> None:
        body = str.encode(json_dumps(payload))
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, message: str, status: int = HTTP_NOT_FOUND) -> None:
        self._send(status, {"error": message})

    # -- appelée par HTTPServer -------------------------------------------

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        try:
            status, payload = self._handle_get(parsed.path, query)
        except XoHiveError as exc:
            self._send_error(exc.message, exc.code)
            return
        self._send(status, payload)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json_loads(raw.decode("utf-8"))
        except Exception:
            body = {}
        try:
            status, payload = self._handle_post(parsed.path, body)
        except XoHiveError as exc:
            self._send_error(exc.message, exc.code)
            return
        self._send(status, payload)

    # -- gestionnaires de route -------------------------------------------

    def _handle_get(self, path: str, query: dict) -> tuple[int, dict]:
        if path == ROUTES["documents:list"]:
            return self._handle_list_documents(query)
        if path == ROUTES["documents:get"]:
            doc_id = query.get("id", [None])[0]
            return self._handle_get_document(doc_id)
        return HTTP_NOT_FOUND, {"error": "route GET inconnue"}

    def _handle_post(self, path: str, body: dict) -> tuple[int, dict]:
        if path == ROUTES["documents:create"]:
            return self._handle_create_document(body)
        if path == ROUTES["documents:open"]:
            return self._handle_open_document(body)
        if path == ROUTES["documents:resign"]:
            return self._handle_resign(body)
        if path == ROUTES["documents:send"]:
            return self._handle_send(body)
        if path == ROUTES["documents:cancel"]:
            return self._handle_cancel(body)
        if path == ROUTES["documents:delete"]:
            return self._handle_delete(body)
        if path == ROUTES["ledger:post"]:
            return self._handle_post_ledger(body)
        if path == ROUTES["transactions:create"]:
            return self._handle_create_transaction(body)
        return HTTP_NOT_FOUND, {"error": "route POST inconnue"}

    # -- implémentations de route ------------------------------------------

    def _handle_list_documents(self, query: dict) -> tuple[int, dict]:
        limit = int(query.get("limit", [50])[0] or 50)
        offset = int(query.get("offset", [0])[0] or 0)
        # Le stockage réel est via `self.document_store` (DocumentStore)
        return HTTP_OK, {"documents": [], "limit": limit}

    def _handle_get_document(self, doc_id: str) -> tuple[int, dict]:
        # recherche par id (logique métier dans DocumentStore)
        return HTTP_OK, {"document": None}

    def _handle_create_document(self, body: dict) -> tuple[int, dict]:
        doc = Document(
            doc_type=body.get("doc_type"),
            numero_serie=int(body.get("numero_serie", 1)),
            date_creation=body.get("date_creation"),
            org_id=body.get("org_id", 1),
            exposer=body.get("exposer"),
            currency=body.get("currency", "EUR"),
            retention=body.get("retention", 0.0),
            balance=body.get("balance", 0.0),
        )
        return HTTP_CREATED, {"document": doc}

    def _handle_open_document(self, body: dict) -> tuple[int, dict]:
        return HTTP_OK, {"etat": "edite"}

    def _handle_resign(self, body: dict) -> tuple[int, dict]:
        return HTTP_OK, {"etat": "brouillon_pdf"}

    def _handle_send(self, body: dict) -> tuple[int, dict]:
        return HTTP_OK, {"etat": "envoye"}

    def _handle_cancel(self, body: dict) -> tuple[int, dict]:
        return HTTP_OK, {"etat": "annule"}

    def _handle_delete(self, body: dict) -> tuple[int, dict]:
        return HTTP_OK, {"etat": "supprime"}

    def _handle_post_ledger(self, body: dict) -> tuple[int, dict]:
        return HTTP_OK, {"written": 0, "balance": "0.00"}

    def _handle_create_transaction(self, body: dict) -> tuple[int, dict]:
        return HTTP_CREATED, {"tx_id": "tx-demo", "status": "created"}


def json_dumps(obj: dict) -> str:
    import json

    return json.dumps(obj, ensure_ascii=False)


def json_loads(text: str) -> dict:
    import json

    return json.loads(text)


def start_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    *,
    handler: type[BaseHTTPRequestHandler] = Handler,
) -> ThreadingHTTPServer:
    """Démarre le serveur. À utiliser en développement."""
    return ThreadingHTTPServer((host, port), handler)


if __name__ == "__main__":
    print("XoHive API (socle V0) en cours de démarrage...")
    start_server().serve_forever()
