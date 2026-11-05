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
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from typing import Any, Dict

from engine import Document, DocumentError

try:
    from engine.auth import TokenAuth
except ImportError:
    TokenAuth = None


class HttpHandler(BaseHTTPRequestHandler):
    """Gestionnaire de requêtes HTTP pour l'API documents."""

    store = None  # défini par l'application avant de démarrer
    auth = None   # défini par l'application avant de démarrer (TokenAuth)

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

    def _require_auth(self) -> bool:
        """Vérifie l'authentification sauf pour /health.

        Retourne True si l'accès est autorisé, False si 401 doit être envoyé.
        """
        if self.path == "/health":
            return True
        if self.auth is None:
            # Pas d'authentification configurée : toutes les routes accessibles
            return True
        if self.auth.authenticate(self.headers.get("Authorization")):
            return True
        self._send_error(401, "Unauthorized: missing or invalid token")
        return False

    def do_GET(self):
        if not self._require_auth():
            return
        path = self.path.rstrip("/") or "/documents"
        # Routes CRM
        if path.startswith("/api/v1/crm/"):
            return self._handle_crm_get(path)
        # Routes Document
        if path == "/documents":
            self._list_documents()
        elif path == "/health":
            self._send_json(200, {"status": "ok"})
        else:
            match = re.match(r"^/documents/([^/]+)$", path)
            if match:
                self._get_document(match.group(1))
            else:
                self._send_error(404, "Not Found")

    def do_POST(self):
        if not self._require_auth():
            return
        path = self.path.rstrip("/") or "/documents"
        # Routes CRM
        if path.startswith("/api/v1/crm/"):
            return self._handle_crm_post(path)
        # Routes Document
        if path == "/documents":
            self._create_document()
        else:
            match = re.match(r"^/documents/([^/]+)/transition$", path)
            if match:
                self._transition_document(match.group(1))
                return
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

    def _handle_crm_get(self, path: str):
        """Gère les requêtes GET pour l'API CRM."""
        try:
            from xohive.crm.repository.company_repository import CompanyRepository
            from xohive.crm.repository.contact_repository import ContactRepository
            from xohive.crm.repository.opportunity_repository import OpportunityRepository
            from xohive.crm.repository.activity_repository import ActivityRepository
            from xohive.crm.repository.quotation_repository import QuotationRepository
            from xohive.crm.repository.order_repository import OrderRepository
            from xohive.crm.repository.invoice_repository import InvoiceRepository
            from xohive.crm.repository.credit_note_repository import CreditNoteRepository
            from xohive.crm.repository.payment_repository import PaymentRepository
            from xohive.crm.repository.reconciliation_repository import ReconciliationRepository

            segments = path.split("/")
            # Segments: ["", "api", "v1", "crm", "companies"] ou ["", "api", "v1", "crm", "companies", id]

            if len(segments) >= 5 and segments[4] == "companies":
                company_id = segments[5] if len(segments) > 5 else None
                if company_id:
                    repo = CompanyRepository(self.store)
                    company = repo.get(company_id)
                    if company:
                        self._send_json(200, {"item": {
                            "id": company.id,
                            "name": company.name,
                            "siret": company.siret,
                            "city": company.city,
                            "zip_code": company.zip_code,
                            "country": company.country,
                            "website": company.website,
                            "contact_person": company.contact_person,
                            "email": company.email,
                            "is_active": company.is_active
                        }})
                    else:
                        self._send_error(404, "Company not found")
                else:
                    repo = CompanyRepository(self.store)
                    companies = repo.list()
                    self._send_json(200, {"items": [{
                        "id": c.id, "name": c.name, "siret": c.siret,
                        "city": c.city, "zip_code": c.zip_code, "country": c.country,
                        "is_active": c.is_active
                    } for c in companies]})

            elif len(segments) >= 5 and segments[4] == "contacts":
                contact_id = segments[5] if len(segments) > 5 else None
                if contact_id:
                    repo = ContactRepository(self.store)
                    contact = repo.get(contact_id)
                    if contact:
                        self._send_json(200, {"item": {
                            "id": contact.id,
                            "first_name": contact.first_name,
                            "last_name": contact.last_name,
                            "email": contact.email,
                            "phone": contact.phone,
                            "company_id": contact.company_id,
                            "is_active": contact.is_active
                        }})
                    else:
                        self._send_error(404, "Contact not found")
                else:
                    repo = ContactRepository(self.store)
                    contacts = repo.list()
                    self._send_json(200, {"items": [{
                        "id": c.id, "first_name": c.first_name, "last_name": c.last_name,
                        "email": c.email, "phone": c.phone, "company_id": c.company_id,
                        "is_active": c.is_active
                    } for c in contacts]})

            elif len(segments) >= 5 and segments[4] == "opportunities":
                opp_id = segments[5] if len(segments) > 5 else None
                if opp_id:
                    repo = OpportunityRepository(self.store)
                    opp = repo.get(opp_id)
                    if opp:
                        self._send_json(200, {"item": {
                            "id": opp.id,
                            "title": opp.title,
                            "company_id": opp.company_id,
                            "amount": opp.amount,
                            "stage": opp.stage,
                            "probability": opp.probability,
                            "close_date": opp.close_date,
                            "is_active": opp.is_active
                        }})
                    else:
                        self._send_error(404, "Opportunity not found")
                else:
                    repo = OpportunityRepository(self.store)
                    opps = repo.list()
                    self._send_json(200, {"items": [{
                        "id": o.id, "title": o.title, "amount": o.amount,
                        "stage": o.stage, "probability": o.probability,
                        "company_id": o.company_id, "is_active": o.is_active
                    } for o in opps]})

            elif len(segments) >= 5 and segments[4] == "activities":
                activity_id = segments[5] if len(segments) > 5 else None
                if activity_id:
                    repo = ActivityRepository(self.store)
                    activity = repo.get(activity_id)
                    if activity:
                        self._send_json(200, {"item": {
                            "id": activity.id,
                            "type": activity.type,
                            "status": activity.status,
                            "date": activity.date,
                            "subject": activity.subject,
                            "description": activity.description,
                            "contact_id": activity.contact_id,
                            "company_id": activity.company_id,
                            "is_active": activity.is_active
                        }})
                    else:
                        self._send_error(404, "Activity not found")
                else:
                    repo = ActivityRepository(self.store)
                    activities = repo.list()
                    self._send_json(200, {"items": [{
                        "id": a.id, "type": a.type, "status": a.status,
                        "date": a.date, "company_id": a.company_id,
                        "is_active": a.is_active
                    } for a in activities]})

            elif len(segments) >= 5 and segments[4] == "pipeline":
                company_id = segments[5] if len(segments) > 5 else None
                if company_id:
                    repo = OpportunityRepository(self.store)
                    opps = repo.list()
                    repo.close()
                    active = [o for o in opps if o.company_id == company_id]
                    stages = {}
                    for o in active:
                        if o.company_id not in stages:
                            stages[o.company_id] = {"count": 0, "stage": o.stage}
                        stages[o.company_id]["count"] += 1
                    self._send_json(200, {
                        "company_id": company_id,
                        "pipeline_stage": stages.get(company_id, {}).get("stage", "prospecting"),
                        "opportunities_count": stages.get(company_id, {}).get("count", 0),
                        "items": [{"id": o.id, "title": o.title, "stage": o.stage, "amount": o.amount}
                                  for o in active]
                    })
                else:
                    repo = OpportunityRepository(self.store)
                    opps = repo.list()
                    repo.close()
                    self._send_json(200, {
                        "pipeline_stage": "prospecting",
                        "opportunities_count": len(opps),
                        "items": [{"id": o.id, "title": o.title, "stage": o.stage, "amount": o.amount}
                                  for o in opps]
                    })

            elif len(segments) >= 5 and segments[4] == "quotations":
                quote_id = segments[5] if len(segments) > 5 else None
                if quote_id:
                    repo = QuotationRepository(self.store)
                    quote = repo.get(quote_id)
                    repo.close()
                    if quote:
                        self._send_json(200, {"item": quote.to_dict()})
                    else:
                        self._send_error(404, "Quotation not found")
                else:
                    repo = QuotationRepository(self.store)
                    quotes = repo.list()
                    repo.close()
                    self._send_json(200, {"items": [q.to_dict() for q in quotes]})

            elif len(segments) >= 5 and segments[4] == "orders":
                order_id = segments[5] if len(segments) > 5 else None
                if order_id:
                    repo = OrderRepository(self.store)
                    order = repo.get(order_id)
                    repo.close()
                    if order:
                        self._send_json(200, {"item": order.to_dict()})
                    else:
                        self._send_error(404, "Order not found")
                else:
                    repo = OrderRepository(self.store)
                    orders = repo.list()
                    repo.close()
                    self._send_json(200, {"items": [o.to_dict() for o in orders]})

            elif len(segments) >= 5 and segments[4] == "invoices":
                invoice_id = segments[5] if len(segments) > 5 else None
                if invoice_id:
                    repo = InvoiceRepository(self.store)
                    invoice = repo.get(invoice_id)
                    repo.close()
                    if invoice:
                        self._send_json(200, {"item": invoice.to_dict()})
                    else:
                        self._send_error(404, "Invoice not found")
                else:
                    repo = InvoiceRepository(self.store)
                    invoices = repo.list()
                    repo.close()
                    self._send_json(200, {"items": [i.to_dict() for i in invoices]})

            elif len(segments) >= 5 and segments[4] == "credit-notes":
                credit_note_id = segments[5] if len(segments) > 5 else None
                if credit_note_id:
                    repo = CreditNoteRepository(self.store)
                    credit_note = repo.get(credit_note_id)
                    repo.close()
                    if credit_note:
                        self._send_json(200, {"item": credit_note.to_dict()})
                    else:
                        self._send_error(404, "CreditNote not found")
                else:
                    repo = CreditNoteRepository(self.store)
                    credit_notes = repo.list()
                    repo.close()
                    self._send_json(200, {"items": [c.to_dict() for c in credit_notes]})

            elif len(segments) >= 5 and segments[4] == "payments":
                payment_id = segments[5] if len(segments) > 5 else None
                if payment_id:
                    repo = PaymentRepository(self.store)
                    payment = repo.get(payment_id)
                    repo.close()
                    if payment:
                        self._send_json(200, {"item": payment.to_dict()})
                    else:
                        self._send_error(404, "Payment not found")
                else:
                    repo = PaymentRepository(self.store)
                    payments = repo.list()
                    repo.close()
                    self._send_json(200, {"items": [p.to_dict() for p in payments]})

            elif len(segments) >= 5 and segments[4] == "reconciliations":
                reconciliation_id = segments[5] if len(segments) > 5 else None
                if reconciliation_id:
                    repo = ReconciliationRepository(self.store)
                    reconciliation = repo.get(reconciliation_id)
                    repo.close()
                    if reconciliation:
                        self._send_json(200, {"item": reconciliation.to_dict()})
                    else:
                        self._send_error(404, "Reconciliation not found")
                else:
                    repo = ReconciliationRepository(self.store)
                    reconciliations = repo.list()
                    repo.close()
                    self._send_json(200, {"items": [r.to_dict() for r in reconciliations]})
        except Exception as exc:
            self._send_error(500, str(exc))

    def _handle_crm_post(self, path: str):
        """Gère les requêtes POST pour l'API CRM."""
        try:
            from xohive.crm.repository.company_repository import CompanyRepository
            from xohive.crm.repository.contact_repository import ContactRepository
            from xohive.crm.repository.opportunity_repository import OpportunityRepository
            from xohive.crm.repository.activity_repository import ActivityRepository
            from xohive.crm.repository.quotation_repository import QuotationRepository
            from xohive.crm.repository.order_repository import OrderRepository
            from xohive.crm.repository.invoice_repository import InvoiceRepository
            from xohive.crm.repository.credit_note_repository import CreditNoteRepository
            from xohive.crm.repository.payment_repository import PaymentRepository
            from xohive.crm.repository.reconciliation_repository import ReconciliationRepository
            from xohive.crm.domain.company import Company
            from xohive.crm.domain.contact import Contact
            from xohive.crm.domain.opportunity import Opportunity
            from xohive.crm.domain.activity import Activity
            from xohive.crm.domain.quotation import Quotation
            from xohive.crm.domain.order import Order
            from xohive.crm.domain.invoice import Invoice
            from xohive.crm.domain.credit_note import CreditNote
            from xohive.crm.domain.payment import Payment
            from xohive.crm.domain.reconciliation import Reconciliation

            segments = path.split("/")
            body = self._read_body()

            if len(segments) >= 5 and segments[4] == "companies":
                try:
                    company = Company(**body)
                    repo = CompanyRepository(self.store)
                    result = repo.create(company)
                    repo.close()
                    self._send_json(201, {"item": result.to_dict()})
                except Exception as e:
                    self._send_error(400, str(e))

            elif len(segments) >= 5 and segments[4] == "contacts":
                try:
                    contact = Contact(**body)
                    repo = ContactRepository(self.store)
                    result = repo.create(contact)
                    repo.close()
                    self._send_json(201, {"item": result.to_dict()})
                except Exception as e:
                    self._send_error(400, str(e))

            elif len(segments) >= 6 and segments[4] == "opportunities" and segments[6] == "pipeline":
                opp_id = segments[5]
                try:
                    repo = OpportunityRepository(self.store)
                    opp = repo.get(opp_id)
                    repo.close()
                    if opp:
                        if body.get("stage") in opp.ALLOWED_STAGES:
                            opp.stage = body["stage"]
                            opp.updated_at = opp._now_iso()
                            repo = OpportunityRepository(self.store)
                            result = repo.update(opp)
                            repo.close()
                            self._send_json(200, {"stage": result.stage})
                        else:
                            self._send_error(400, f"stage invalide : {body.get('stage')}")
                    else:
                        self._send_error(404, "Opportunity not found")
                except Exception as e:
                    self._send_error(400, str(e))

            elif len(segments) >= 5 and segments[4] == "opportunities":
                try:
                    opp = Opportunity(**body)
                    repo = OpportunityRepository(self.store)
                    result = repo.create(opp)
                    repo.close()
                    self._send_json(201, {"item": result.to_dict()})
                except Exception as e:
                    self._send_error(400, str(e))

            elif len(segments) >= 5 and segments[4] == "activities":
                try:
                    activity = Activity(**body)
                    repo = ActivityRepository(self.store)
                    result = repo.create(activity)
                    repo.close()
                    self._send_json(201, {"item": result.to_dict()})
                except Exception as e:
                    self._send_error(400, str(e))

            elif len(segments) >= 5 and segments[4] == "quotations":
                try:
                    quote = Quotation(**body)
                    repo = QuotationRepository(self.store)
                    result = repo.create(quote)
                    repo.close()
                    self._send_json(201, {"item": result.to_dict()})
                except Exception as e:
                    self._send_error(400, str(e))

            elif len(segments) >= 5 and segments[4] == "orders":
                try:
                    order = Order(**body)
                    repo = OrderRepository(self.store)
                    result = repo.create(order)
                    repo.close()
                    self._send_json(201, {"item": result.to_dict()})
                except Exception as e:
                    self._send_error(400, str(e))

            elif len(segments) >= 5 and segments[4] == "invoices":
                try:
                    invoice = Invoice(**body)
                    repo = InvoiceRepository(self.store)
                    result = repo.create(invoice)
                    repo.close()
                    self._send_json(201, {"item": result.to_dict()})
                except Exception as e:
                    self._send_error(400, str(e))

            elif len(segments) >= 5 and segments[4] == "credit-notes":
                try:
                    credit_note = CreditNote(**body)
                    repo = CreditNoteRepository(self.store)
                    result = repo.create(credit_note)
                    repo.close()
                    self._send_json(201, {"item": result.to_dict()})
                except Exception as e:
                    self._send_error(400, str(e))

            elif len(segments) >= 5 and segments[4] == "payments":
                try:
                    payment = Payment(**body)
                    repo = PaymentRepository(self.store)
                    result = repo.create(payment)
                    repo.close()
                    self._send_json(201, {"item": result.to_dict()})
                except Exception as e:
                    self._send_error(400, str(e))

            elif len(segments) >= 5 and segments[4] == "reconciliations":
                try:
                    reconciliation = Reconciliation(**body)
                    repo = ReconciliationRepository(self.store)
                    result = repo.create(reconciliation)
                    repo.close()
                    self._send_json(201, {"item": result.to_dict()})
                except Exception as e:
                    self._send_error(400, str(e))

            else:
                self._send_error(404, "Not Found")
        except Exception as exc:
            self._send_error(400, str(exc))

    def _doc_to_dict(self, doc: Any) -> Dict:
        return {
            "id": doc.id,
            "doc_type": doc.doc_type,
            "numero_serie": doc.numero_serie,
            "org_id": doc.org_id,
            "date_creation": doc.date_creation,
            "etat": doc.etat,
        }


def make_app(store, auth=None):
    """Retourne un handler typé pour le repository donné.

    Args:
        store: Le DocumentRepository.
        auth: Instance de TokenAuth (optionnel).
    """
    class _HttpHandler(HttpHandler):
        pass

    _HttpHandler.store = store
    _HttpHandler.auth = auth
    return _HttpHandler

if __name__ == "__main__":
    import argparse
    import os
    from http.server import HTTPServer

    from engine.auth import TokenAuth
    from engine.repository import DocumentRepository

    parser = argparse.ArgumentParser(description="TeamAI HTTP API")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--db", default=os.path.join("data", "teamai.db"))
    args = parser.parse_args()

    raw_tokens = os.environ.get("TEAMAI_TOKENS", "").strip()
    if not raw_tokens:
        raise SystemExit("TEAMAI_TOKENS manquant : refus de démarrer sans token")

    valid_tokens = {t.strip() for t in raw_tokens.split(",") if t.strip()}
    auth = TokenAuth(valid_tokens)
    store = DocumentRepository(args.db)
    handler = make_app(store, auth=auth)

    os.makedirs(os.path.dirname(args.db) or ".", exist_ok=True)
    server = HTTPServer((args.host, args.port), handler)
    print(f"TeamAI API listening on {args.host}:{args.port}", flush=True)
    server.serve_forever()
