"""Tests unitaires pour Ledger et LedgerEntry."""

import unittest

from xohive.domain.ledger import (
    Ledger,
    LedgerEntry,
    LedgerBalanceError,
)


class TestLedgerEntry(unittest.TestCase):
    """Tests de l'entité LedgerEntry."""

    def test_creation_defaut(self):
        entry = LedgerEntry(
            organisation_id="org-1",
            ledger_type="FACT",
            reference="F123",
        )
        self.assertEqual(entry.ledger_type, "FACT")
        self.assertEqual(entry.reference, "F123")
        self.assertEqual(entry.debit, 0)
        self.assertEqual(entry.credit, 0)
        self.assertTrue(entry.est_bilancee())

    def test_creation_avec_debit_credit(self):
        entry = LedgerEntry(
            organisation_id="org-1",
            ledger_type="FACT",
            reference="F456",
            debit=100.0,
            credit=100.0,
        )
        self.assertTrue(entry.est_bilancee())
        self.assertEqual(entry.debit, 100.0)
        self.assertEqual(entry.credit, 100.0)

    def test_creation_non_bilancee(self):
        entry = LedgerEntry(
            organisation_id="org-1",
            ledger_type="FACT",
            reference="F789",
            debit=100.0,
            credit=0.0,
        )
        self.assertFalse(entry.est_bilancee())

    def test_creation_balance_negatif(self):
        with self.assertRaises(LedgerBalanceError):
            LedgerEntry(
                organisation_id="org-1",
                ledger_type="FACT",
                reference="F1",
                balance=-10,
            )

    def test_creation_type_invalide(self):
        with self.assertRaises(LedgerBalanceError):
            LedgerEntry(
                organisation_id="org-1",
                ledger_type="INVALID",
                reference="R1",
            )

    def test_aureferance(self):
        entry = LedgerEntry(
            organisation_id="org-1",
            ledger_type="FACT",
            reference="F001",
        )
        self.assertEqual(entry.aureferance(), "FACT-F001")

    def test_to_dict(self):
        entry = LedgerEntry(
            organisation_id="org-1",
            ledger_type="BC",
            reference="B001",
            debit=500.0,
            credit=500.0,
        )
        d = entry.to_dict()
        self.assertEqual(d["ledger_type"], "BC")
        self.assertEqual(d["debit"], 500.0)
        self.assertEqual(d["credit"], 500.0)

    def test_repr(self):
        entry = LedgerEntry(
            organisation_id="org-1",
            ledger_type="FACT",
            reference="F001",
        )
        self.assertIn("LedgerEntry", repr(entry))


class TestLedger(unittest.TestCase):
    """Tests du moteur Ledger."""

    def setUp(self):
        self.ledger = Ledger()
        self.ledger.register_compte("79110", "Téléphone", "CA")
        self.ledger.register_compte("62000", "Fournisseurs", "Passif")

    def test_ecrire_equilibree(self):
        entry = self.ledger.writer(
            organisation_id="org-1",
            user_id="user-1",
            ledger_type="FACT",
            reference="F001",
            debit=100.0,
            credit=100.0,
        )
        self.assertEqual(entry.reference, "F001")
        self.assertEqual(len(self.ledger), 1)

    def test_ecrire_non_equilibree(self):
        with self.assertRaises(LedgerBalanceError):
            self.ledger.writer(
                organisation_id="org-1",
                user_id="user-1",
                ledger_type="FACT",
                reference="F002",
                debit=100.0,
                credit=0.0,
            )

    def test_calculer_balance(self):
        self.ledger.writer(
            organisation_id="org-1",
            user_id="user-1",
            ledger_type="FACT",
            reference="F003",
            debit=500.0,
            credit=500.0,
        )
        self.ledger.writer(
            organisation_id="org-1",
            user_id="user-1",
            ledger_type="FACT",
            reference="F004",
            debit=300.0,
            credit=300.0,
        )
        debit, credit = self.ledger.calculer_balance()
        self.assertEqual(debit, 800.0)
        self.assertEqual(credit, 800.0)

    def test_ecrire_avec_balance(self):
        entry = self.ledger.writer(
            organisation_id="org-1",
            user_id="user-1",
            ledger_type="FACT",
            reference="F005",
            debit=200.0,
            credit=200.0,
            balance=5000.0,
        )
        self.assertEqual(entry.balance, 5000.0)

    def test_ecrire_avec_doc_id(self):
        entry = self.ledger.writer(
            organisation_id="org-1",
            user_id="user-1",
            ledger_type="FACT",
            reference="F006",
            debit=100.0,
            credit=100.0,
            doc_id="doc-123",
        )
        self.assertEqual(entry.doc_id, "doc-123")


if __name__ == "__main__":
    unittest.main()
