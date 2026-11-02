"""HTTP API minimale pour le moteur de documents TeamAI.

Utilise http.server (standard library) sans framework externe.
Expose :
- POST /documents : création
- GET /documents/{id} : lecture
- GET /documents : liste
- POST /documents/{id}/transition : transition d'état

Usage:
    from engine.http import HttpHandler
    from engine.repository import DocumentRepository
    from http.server import HTTPServer

    store = DocumentRepository("documents.db")
    server = HTTPServer(("127.0.0.1", 8000), make_app(store))
    server.serve_forever()
"""

import json
import re
from http.server import BaseHTTPRequestHandler
from typing import Any, Dict

from engine import Document, DocumentError


class HttpHandler(BaseHTTPRequestHandler):
    """Gestionnaire de requêtes HTTP pour l'API documents."""

    store = None  # défini par l'application avant de démarrer

    def _send_json(self, status: int, data: Dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status: int, message: str):
        self._send_json(status, {"error": message})

    def _read_body(self) -> Dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def do_GET(self):
        path = self.path.rstrip("/") or "/documents"
        if path == "/documents":
            self._list_documents()
        else:
            match = re.match(r"^/documents/([^/]+)$", path)
            if match:
                self._get_document(match.group(1))
            else:
                self._send_error(404, "Not Found")

    def do_POST(self):
        path = self.path.rstrip("/") or "/documents"
        if path == "/documents":
            self._create_document()
        else:
            match = re.match(r"^/documents/([^/]+)/transition$", path)
            if match:
                self._transition_document(match.group(1))
            else:
                self._send_error(404, "Not Found")

    def _list_documents(self):
        try:
            if self.store is None:
                self._send_error(500, "store not configured")
                return
            documents = self.store.list()
            self._send_json(200, {"items": [self._doc_to_dict(d) for d in documents]})
        except Exception as exc:
            self._send_error(500, str(exc))

    def _get_document(self, doc_id: str):
        try:
            if self.store is None:
                self._send_error(500, "store not configured")
                return
            doc = self.store.get(doc_id)
            if doc is None:
                self._send_error(404, "Document not found")
            else:
                self._send_json(200, {"item": self._doc_to_dict(doc)})
        except Exception as exc:
            self._send_error(500, str(exc))

    def _create_document(self):
        try:
            if self.store is None:
                self._send_error(500, "store not configured")
                return
            data = self._read_body()
            doc_type = data.get("doc_type")
            numero_serie = data.get("numero_serie")
            org_id = data.get("org_id")
            date_creation = data.get("date_creation")

            if not all([doc_type, numero_serie is not None, org_id is not None]):
                self._send_error(400, "Missing required fields")
                return

            document = Document(
                doc_type=doc_type,
                numero_serie=numero_serie,
                date_creation=date_creation,
                org_id=org_id,
            )
            self.store.save(document)
            self._send_json(201, {"item": self._doc_to_dict(document)})
        except DocumentError as exc:
            self._send_error(400, str(exc))
        except Exception as exc:
            self._send_error(500, str(exc))

    def _transition_document(self, doc_id: str):
        try:
            if self.store is None:
                self._send_error(500, "store not configured")
                return
            data = self._read_body()
            etat = data.get("etat")
            acteur = data.get("acteur", "system")

            if not etat:
                self._send_error(400, "Missing required field: etat")
                return

            document = self.store.get(doc_id)
            if document is None:
                self._send_error(404, "Document not found")
                return

            document.transition(etat, acteur)
            self.store.save(document)
            self._send_json(200, {"item": self._doc_to_dict(document)})
        except DocumentError as exc:
            self._send_error(400, str(exc))
        except Exception as exc:
            self._send_error(500, str(exc))

    def _doc_to_dict(self, doc: Any) -> Dict:
        return {
            "id": doc.id,
            "doc_type": doc.doc_type,
            "numero_serie": doc.numero_serie,
            "org_id": doc.org_id,
            "date_creation": doc.date_creation,
            "etat": doc.etat,
        }


def make_app(store):
    """Retourne un handler typé pour le repository donné."""
    class _HttpHandler(HttpHandler):
        pass
    _HttpHandler.store = store
    return _HttpHandler
