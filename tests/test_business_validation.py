"""Tests de validation métier des documents XoHive."""

import unittest
from datetime import datetime, timezone

from engine import Document, DocumentError, TRANSITIONS
from engine.validation import DocumentValidator


class TestDocumentValidatorCreation(unittest.TestCase):
    """Tests des règles de création."""

    def setUp(self):
        self.validator = DocumentValidator()

    def test_creation_valide(self):
        """Création valide doit passer sans erreur."""
        self.validator.validate_creation(
            doc_type="FACT",
            numero_serie=1,
            org_id=1,
            currency="EUR",
            retention=0.0,
            balance=0.0,
        )

    def test_type_invalide(self):
        """Type de document inconnu doit lever une erreur."""
        with self.assertRaises(DocumentError):
            self.validator.validate_creation(
                doc_type="FACTURE",
                numero_serie=1,
                org_id=1,
                currency="EUR",
                retention=0.0,
                balance=0.0,
            )

    def test_numero_serie_invalide(self):
        """Numéro de série invalide (0 ou négatif) doit lever une erreur."""
        with self.assertRaises(DocumentError):
            self.validator.validate_creation(
                doc_type="FACT",
                numero_serie=0,
                org_id=1,
                currency="EUR",
                retention=0.0,
                balance=0.0,
            )
        with self.assertRaises(DocumentError):
            self.validator.validate_creation(
                doc_type="FACT",
                numero_serie=-1,
                org_id=1,
                currency="EUR",
                retention=0.0,
                balance=0.0,
            )

    def test_org_id_invalide(self):
        """org_id invalide (0 ou négatif) doit lever une erreur."""
        with self.assertRaises(DocumentError):
            self.validator.validate_creation(
                doc_type="FACT",
                numero_serie=1,
                org_id=0,
                currency="EUR",
                retention=0.0,
                balance=0.0,
            )
        with self.assertRaises(DocumentError):
            self.validator.validate_creation(
                doc_type="FACT",
                numero_serie=1,
                org_id=-1,
                currency="EUR",
                retention=0.0,
                balance=0.0,
            )

    def test_devise_invalide(self):
        """Devise invalide (non de 3 caractères) doit lever une erreur."""
        with self.assertRaises(DocumentError):
            self.validator.validate_creation(
                doc_type="FACT",
                numero_serie=1,
                org_id=1,
                currency="Euro",
                retention=0.0,
                balance=0.0,
            )
        with self.assertRaises(DocumentError):
            self.validator.validate_creation(
                doc_type="FACT",
                numero_serie=1,
                org_id=1,
                currency="E",
                retention=0.0,
                balance=0.0,
            )

    def test_retention_hors_limites(self):
        """Retention hors limites (<0 ou >1) doit lever une erreur."""
        with self.assertRaises(DocumentError):
            self.validator.validate_creation(
                doc_type="FACT",
                numero_serie=1,
                org_id=1,
                currency="EUR",
                retention=-0.1,
                balance=0.0,
            )
        with self.assertRaises(DocumentError):
            self.validator.validate_creation(
                doc_type="FACT",
                numero_serie=1,
                org_id=1,
                currency="EUR",
                retention=1.1,
                balance=0.0,
            )

    def test_balance_negatif(self):
        """Balance négative doit lever une erreur."""
        with self.assertRaises(DocumentError):
            self.validator.validate_creation(
                doc_type="FACT",
                numero_serie=1,
                org_id=1,
                currency="EUR",
                retention=0.0,
                balance=-100.0,
            )


class TestDocumentValidatorTransition(unittest.TestCase):
    """Tests des règles de transition."""

    def setUp(self):
        self.validator = DocumentValidator()
        self.document = Document(
            doc_type="FACT",
            numero_serie=1,
            org_id=1,
            date_creation="2026-11-02",
            currency="EUR",
            balance=0.0,
        )

    def test_transition_valide(self):
        """Transition valide doit passer sans erreur (la transition sera appliquée par l'API)."""
        self.validator.validate_transition(self.document, "brouillon_pdf")
        # L'état ne change pas ici - la transition est uniquement validée

    def test_transition_invalide(self):
        """Transition interdite (brouillon -> envoye) doit lever une erreur."""
        with self.assertRaises(DocumentError):
            self.validator.validate_transition(self.document, "envoye")

    def test_etat_inexistant(self):
        """État inconnu doit lever une erreur."""
        with self.assertRaises(DocumentError):
            self.validator.validate_transition(self.document, "inconnu")


class TestDocumentValid(unittest.TestCase):
    """Tests de validation directe de l'objet Document (contract existant)."""

    def test_document_creation(self):
        doc = Document(
            doc_type="FACT",
            numero_serie=1,
            org_id=1,
            date_creation="2026-11-02",
        )
        self.assertEqual(doc.doc_type, "FACT")
        self.assertEqual(doc.numero_serie, 1)
        self.assertEqual(doc.org_id, 1)
        self.assertEqual(doc.etat, "brouillon")

    def test_document_type_inconnu_raises(self):
        with self.assertRaises(DocumentError):
            Document(
                doc_type="FACTURE",
                numero_serie=1,
                org_id=1,
                date_creation="2026-11-02",
            )

    def test_numero_serie_invalide_raises(self):
        with self.assertRaises(DocumentError):
            Document(
                doc_type="FACT",
                numero_serie=0,
                org_id=1,
                date_creation="2026-11-02",
            )
        with self.assertRaises(DocumentError):
            Document(
                doc_type="FACT",
                numero_serie=-1,
                org_id=1,
                date_creation="2026-11-02",
            )
