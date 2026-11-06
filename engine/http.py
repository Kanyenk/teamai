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
import uuid
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
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status: int, message: str):
        self._send_json(status, {"error": message})

    def _read_body(self) -> Dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        if not raw:
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}

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
        # Routes WMS
        if path.startswith("/api/v1/wms/"):
            return self._handle_wms_get(path)
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
        # Routes WMS
        if path.startswith("/api/v1/wms/"):
            return self._handle_wms_post(path)
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

    def _handle_wms_get(self, path: str):
        """Gère les requêtes GET pour l'API WMS."""
        from urllib.parse import urlparse
        path = urlparse(path).path
        try:
            from xohive.wms.repository.product_repository import ProductRepository
            segments = [s for s in path.split("/") if s]
            # segments = [api, v1, wms, products, (id)]
            if len(segments) >= 4 and segments[3] == "products":
                product_id = segments[4] if len(segments) > 4 else None
                repo = ProductRepository(self.store.db_path)
                try:
                    if product_id:
                        product = repo.get(product_id)
                        if product is None:
                            self._send_error(404, "Product not found")
                            return
                        self._send_json(200, {"item": product.to_dict()})
                    else:
                        from urllib.parse import urlparse, parse_qs
                        query = parse_qs(urlparse(self.path).query)
                        limit = int(query.get("limit", ["50"])[0])
                        offset = int(query.get("offset", ["0"])[0])
                        products = repo.list(limit=limit, offset=offset)
                        self._send_json(200, {"items": [p.to_dict() for p in products]})
                finally:
                    repo.close()
            if len(segments) >= 4 and segments[3] == "stock-movements":
                from xohive.wms.repository.stock_movement_repository import StockMovementRepository
                movement_id = segments[4] if len(segments) > 4 else None
                repo = StockMovementRepository(self.store.db_path)
                try:
                    if movement_id:
                        movement = repo.get_by_id(movement_id)
                        if movement is None:
                            self._send_error(404, "StockMovement not found")
                            return
                        self._send_json(200, {"item": movement.to_dict()})
                    else:
                        from urllib.parse import urlparse, parse_qs
                        query = parse_qs(urlparse(self.path).query)
                        limit = int(query.get("limit", ["50"])[0])
                        offset = int(query.get("offset", ["0"])[0])
                        movements = repo.list(limit=limit, offset=offset)
                        self._send_json(200, {"items": [m.to_dict() for m in movements]})
                finally:
                    repo.close()
            if len(segments) >= 4 and segments[3] == "stock-levels":
                from xohive.wms.repository.stock_level_repository import StockLevelRepository
                level_id = segments[4] if len(segments) > 4 else None
                repo = StockLevelRepository(self.store.db_path)
                try:
                    if level_id:
                        level = repo.get_by_id(level_id)
                        if level is None:
                            self._send_error(404, "StockLevel not found")
                            return
                        self._send_json(200, {"item": level.to_dict()})
                    else:
                        from urllib.parse import urlparse, parse_qs
                        query = parse_qs(urlparse(self.path).query)
                        limit = int(query.get("limit", ["50"])[0])
                        offset = int(query.get("offset", ["0"])[0])
                        levels = repo.list(limit=limit, offset=offset)
                        self._send_json(200, {"items": [l.to_dict() for l in levels]})
                finally:
                    repo.close()
            if len(segments) >= 4 and segments[3] == "warehouses":
                from xohive.wms.repository.warehouse_repository import WarehouseRepository
                warehouse_id = segments[4] if len(segments) > 4 else None
                repo = WarehouseRepository(self.store.db_path)
                try:
                    if warehouse_id:
                        warehouse = repo.get_by_id(warehouse_id)
                        if warehouse is None:
                            self._send_error(404, "Warehouse not found")
                            return
                        self._send_json(200, {"item": warehouse.to_dict()})
                    else:
                        from urllib.parse import urlparse, parse_qs
                        query = parse_qs(urlparse(self.path).query)
                        limit = int(query.get("limit", ["50"])[0])
                        offset = int(query.get("offset", ["0"])[0])
                        warehouses = repo.list(limit=limit, offset=offset)
                        self._send_json(200, {"items": [w.to_dict() for w in warehouses]})
                finally:
                    repo.close()
            else:
                self._send_error(404, "Not Found")
        except ValueError as exc:
            self._send_error(400, str(exc))
        except Exception as exc:
            self._send_error(500, str(exc))

    def _handle_wms_post(self, path: str):
        """Gère les requêtes POST pour l'API WMS."""
        try:
            from xohive.wms.repository.product_repository import ProductRepository
            from xohive.wms.domain.product import Product
            from xohive.crm.audit.audit_crm_repository import AuditCRMRepository
            from xohive.domain.audit_event import AuditEvent
            import uuid

            body = self._read_body()
            segments = [s for s in path.split("/") if s]
            if len(segments) >= 4 and segments[3] == "products":
                product = Product(
                    organisation_id=body.get("organisation_id", ""),
                    sku=body.get("sku", ""),
                    name=body.get("name", ""),
                    description=body.get("description", ""),
                    unit=body.get("unit", "unit"),
                    category=body.get("category", ""),
                    default_price=float(body.get("default_price", 0)),
                )
                repo = ProductRepository(self.store.db_path)
                try:
                    result = repo.create(product)
                finally:
                    repo.close()

                audit_repo = AuditCRMRepository(self.store.db_path)
                try:
                    audit_repo.create(AuditEvent(
                        id=uuid.uuid4().hex,
                        organisation_id=result.organisation_id,
                        entity_type="product",
                        entity_id=result.id,
                        action="create",
                        old_values=None,
                        new_values={"id": result.id, "sku": result.sku},
                    ))
                finally:
                    audit_repo.close()

                self._send_json(201, {"item": result.to_dict()})
            elif len(segments) >= 4 and segments[3] == "stock-movements":
                from xohive.wms.repository.stock_movement_repository import StockMovementRepository
                from xohive.wms.domain.stock_movement import StockMovement
                movement = StockMovement(
                    organisation_id=body.get("organisation_id", ""),
                    product_id=body.get("product_id", ""),
                    warehouse_id=body.get("warehouse_id", ""),
                    movement_type=body.get("movement_type", ""),
                    quantity=int(body.get("quantity", 0)),
                    target_warehouse_id=body.get("target_warehouse_id"),
                    reason=body.get("reason"),
                )
                repo = StockMovementRepository(self.store.db_path)
                try:
                    result = repo.create(movement)
                finally:
                    repo.close()

                audit_repo = AuditCRMRepository(self.store.db_path)
                try:
                    audit_repo.create(AuditEvent(
                        id=uuid.uuid4().hex,
                        organisation_id=result.organisation_id,
                        entity_type="stock_movement",
                        entity_id=result.id,
                        action="create",
                        old_values=None,
                        new_values={
                            "id": result.id,
                            "product_id": result.product_id,
                            "warehouse_id": result.warehouse_id,
                            "movement_type": result.movement_type,
                            "quantity": result.quantity,
                        },
                    ))
                finally:
                    audit_repo.close()

                self._send_json(201, {"item": result.to_dict()})
            elif len(segments) >= 4 and segments[3] == "stock-levels":
                from xohive.wms.repository.stock_level_repository import StockLevelRepository
                from xohive.wms.domain.stock_level import StockLevel
                level = StockLevel(
                    organisation_id=body.get("organisation_id", ""),
                    product_id=body.get("product_id", ""),
                    warehouse_id=body.get("warehouse_id", ""),
                    quantity=int(body.get("quantity", 0)),
                )
                repo = StockLevelRepository(self.store.db_path)
                try:
                    result = repo.create(level)
                finally:
                    repo.close()

                audit_repo = AuditCRMRepository(self.store.db_path)
                try:
                    audit_repo.create(AuditEvent(
                        id=uuid.uuid4().hex,
                        organisation_id=result.organisation_id,
                        entity_type="stock_level",
                        entity_id=result.id,
                        action="create",
                        old_values=None,
                        new_values={
                            "id": result.id,
                            "product_id": result.product_id,
                            "warehouse_id": result.warehouse_id,
                            "quantity": result.quantity,
                        },
                    ))
                finally:
                    audit_repo.close()

                self._send_json(201, {"item": result.to_dict()})
            elif len(segments) >= 4 and segments[3] == "warehouses":
                from xohive.wms.repository.warehouse_repository import WarehouseRepository
                from xohive.wms.domain.warehouse import Warehouse
                warehouse = Warehouse(
                    organisation_id=body.get("organisation_id", ""),
                    code=body.get("code", ""),
                    name=body.get("name", ""),
                    address=body.get("address"),
                    is_active=bool(body.get("is_active", True)),
                )
                repo = WarehouseRepository(self.store.db_path)
                try:
                    result = repo.create(warehouse)
                finally:
                    repo.close()

                audit_repo = AuditCRMRepository(self.store.db_path)
                try:
                    audit_repo.create(AuditEvent(
                        id=uuid.uuid4().hex,
                        organisation_id=result.organisation_id,
                        entity_type="warehouse",
                        entity_id=result.id,
                        action="create",
                        old_values=None,
                        new_values={"id": result.id, "code": result.code},
                    ))
                finally:
                    audit_repo.close()

                self._send_json(201, {"item": result.to_dict()})
            else:
                self._send_error(404, "Not Found")
        except Exception as exc:
            self._send_error(400, str(exc))

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

            elif len(segments) >= 5 and segments[4] == "bank-statements":
                if self.store is None:
                    self._send_error(500, "store not configured", "INTERNAL")
                    return
                from xohive.crm.repository.bank_statement_repository import BankStatementRepository
                repo = BankStatementRepository(self.store.db_path)
                try:
                    # GET /api/v1/crm/bank-statements/{id}/matches
                    if len(segments) >= 7 and segments[6] == "matches":
                        statement_id = segments[5]
                        stmt = repo.get(statement_id)
                        if stmt is None:
                            self._send_error(404, "Bank statement not found")
                            return
                        matches = repo.list_matches(statement_id, None)
                        self._send_json(200, {"items": matches})
                        return

                    statement_id = segments[5] if len(segments) > 5 else None
                    if statement_id:
                        stmt = repo.get(statement_id)
                        if stmt is None:
                            self._send_error(404, "Bank statement not found")
                            return
                        self._send_json(200, {"item": stmt.to_dict()})
                    else:
                        statements = repo.list()
                        self._send_json(200, {"items": [s.to_dict() for s in statements]})
                finally:
                    repo.close()

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

            elif len(segments) >= 5 and segments[4] == "bank-statements" and segments[5] == "import":
                try:
                    from xohive.crm.domain.bank_statement import BankStatement
                    from xohive.crm.repository.bank_statement_repository import BankStatementRepository
                    statement_date = body.get("statement_date")
                    file_name = body.get("file_name")
                    amount = body.get("amount")
                    reference = body.get("reference")
                    if not all([statement_date, file_name is not None, amount is not None, reference is not None]):
                        self._send_error(400, "Missing required fields")
                        return
                    bank_statement = BankStatement(
                        organisation_id="org-test",
                        company_id="crm-test",
                        statement_date=statement_date,
                        file_name=file_name,
                        amount=amount,
                        reference=reference,
                        raw_data={"statement_date": statement_date, "file_name": file_name, "amount": amount, "reference": reference},
                        status="pending",
                    )
                    repo = BankStatementRepository(self.store.db_path)
                    result = repo.create(bank_statement)
                    self._send_json(201, {"item": result.to_dict()})
                except Exception as e:
                    self._send_error(400, str(e))

            elif len(segments) >= 7 and segments[4] == "bank-statements" and segments[6] == "reconcile":
                from xohive.crm.repository.bank_statement_repository import BankStatementRepository
                from xohive.crm.domain.reconciliation import Reconciliation
                from xohive.crm.repository.reconciliation_repository import ReconciliationRepository
                import uuid

                statement_id = segments[5]
                payment_id = body.get("payment_id") if body else None
                if not payment_id:
                    self._send_error(400, "payment_id required", "VALIDATION")
                    return

                repo = BankStatementRepository(self.store.db_path)
                try:
                    stmt = repo.get(statement_id)
                    if stmt is None:
                        self._send_error(404, "Bank statement not found")
                        return
                finally:
                    repo.close()

                reconciliation = Reconciliation(
                    organisation_id=stmt.organisation_id,
                    company_id=stmt.company_id,
                    payment_id=payment_id,
                    ledger_entry_id=uuid.uuid4().hex,
                    bank_date=body.get("bank_date", ""),
                    amount=float(body.get("amount", 0)),
                    currency=body.get("currency", "EUR"),
                    status="pending",
                    reference=f"REC-{uuid.uuid4().hex[:8].upper()}",
                )
                recon_repo = ReconciliationRepository(self.store.db_path)
                try:
                    result = recon_repo.create(reconciliation)
                finally:
                    recon_repo.close()

                self._send_json(201, {"item": result.to_dict()})

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
