"""Documents — couche de gestion des documents du socle XoHive.

Ce module fournit une vue de recherche et un éditeur de documents
(comptables). Il repose sur `engine.ledger.Ledger` et `engine.transactions`.
Il fournit :
- `DocumentStore` : stockage événementiel des documents (immuable, hashé),
- `DocumentQuery` : recherche et filtres sur les documents,
- `DocumentEditor` : éditeur de documents avec validation des transitions.
"""

from __future__ import annotations

from engine.exceptions import DocumentError
from engine.transactions import TransactionStore

__all__ = ["DocumentStore", "DocumentQuery", "DocumentEditor"]


class Document:
    """Représentation immuable d'un document dans le socle.

    Chaque document possède :
    - un identifiant unique (UUID),
    - un type de document (FACT, BC, BL, NC, RS, CHQ),
    - un numéro de série,
    - un état courant issu de la machine à états,
    - un hachage de l'état (immuable),
    - un hachage PDF,
    - une liste des historiques d'états,
    - un lien vers la première transaction,
    - un lien vers la dernière transaction.

    Tout changement d'état doit passer par une `Transaction` et être
    enregistré dans le `TransactionStore` associé.
    """

    def __init__(
        self,
        doc_type: str,
        numero_serie: int,
        org_id: int,
        *,
        date_creation: str,
        created_by: str = "system",
        etat_initial: str = "brouillon",
        numero_series: str | None = None,
        exposer: str | None = None,
        currency: str = "EUR",
        retention: float = 0.0,
        balance: float = 0.0,
        hash_etat: str | None = None,
        hash_pdf: str | None = None,
    ) -> None:
        self.id: str = numero_serie  # identifiant affichage
        self.doc_type: str = doc_type
        self.numero_serie: int = numero_serie
        self.org_id: int = org_id
        self.date_creation: str = date_creation
        self.created_by: str = created_by
        self.numero_series: str | None = numero_series
        self.exposer: str | None = exposer
        self.currency: str = currency
        self.retention: float = retention
        self.balance: float = balance
        self.hash_etat: str = (
            hash_etat if hash_etat else f"{etat_initial}|{numero_serie}|{org_id}|{currency}|{retention}|{balance}"
        )
        self.hash_pdf: str | None = hash_pdf
        self.etat_initial: str = etat_initial
        self.etat_courant: str = etat_initial
        self.etats_history: list[dict] = [
            {
                "etat": etat_initial,
                "date_etat": date_creation,
                "acteur": created_by,
            }
        ]

    def etat_courant_vide(self) -> bool:
        return self.etat_courant in {"brouillon", "brouillon_pdf"}


class DocumentStore:
    """Stockage événementiel des documents du socle.

    Le document est immuable : toute modification crée une nouvelle
    Transaction et un nouvel historique d'états. Le stockage est un
    tableau : ajout seul, jamais suppression.
    """

    def __init__(self) -> None:
        self._docs: dict[str, Document] = {}
        self._txn_store: "TransactionStore" = TransactionStore()

    def add(self, doc: Document) -> None:
        self._docs[doc.id] = doc

    def get(self, doc_id: str) -> Document | None:
        return self._docs.get(doc_id)

    def list(self) -> list[Document]:
        return list(self._docs.values())

    # -- synchronisation avec la couche transactions ----------------------

    def register_transaction(self, txn: "Transaction") -> None:
        self._txn_store.add(txn)

    def transactions(self, doc_id: str) -> list:
        return self._txn_store.find(doc_id)

    def all_transactions(self) -> list:
        return self._txn_store.all()


class DocumentQuery:
    """Requêtes et filtres sur l'ensemble des documents."""

    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def by_type(self, doc_type: str) -> list[Document]:
        return [d for d in self._store.list() if d.doc_type == doc_type]

    def by_org(self, org_id: int) -> list[Document]:
        return [d for d in self._store.list() if d.org_id == org_id]

    def by_state(self, etat: str) -> list[Document]:
        return [d for d in self._store.list() if d.etat_courant == etat]

    def final(self) -> list[Document]:
        return [d for d in self._store.list() if d.est_final()]

    def search(self, query: str) -> list[Document]:
        return [d for d in self._store.list() if query in d.id or query in d.doc_type]


class DocumentEditor:
    """Editeur de documents avec validation des transitions."""

    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def envoyer(
        self,
        doc_id: str,
        acteur: str,
        *,
        date: str,
        numero_series: str | None = None,
        exposer: str | None = None,
    ) -> Document:
        doc = self._store.get(doc_id)
        if doc is None:
            raise DocumentError(f"document {doc_id} introuvable")

        from engine import STATE_SENT
        if doc.etat_courant != "brouillon_pdf":
            raise DocumentError(
                f"ne peut pas passer de {doc.etat_courant} à envoye"
            )

        doc.numero_series = numero_series
        doc.exposer = exposer
        trx = Transaction(
            doc.id, acteur, "ECRITURE", {
                "date": date,
                "acteur": acteur,
                "numero_series": numero_series,
                "exposer": exposer,
            }
        )
        self._store.register_transaction(trx)
        return doc
