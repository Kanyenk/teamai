"""Tests unitaires pour l'audit CRM."""

import unittest

from xohive.crm.audit import AuditCRM
from xohive.crm.domain.company import Company


class TestAuditCRM(unittest.TestCase):
    """Tests du gestionnaire d'audit CRM."""

    def setUp(self):
        self.audit = AuditCRM()

    def test_get_entity_type_valid(self):
        company = Company(
            organisation_id="org-123",
            name="Acme",
            siret="12345678901234",
        )
        self.assertEqual(self.audit._get_entity_type(company), "company")

    def test_get_entity_type_invalid(self):
        from xohive.crm.domain.company import Company
        class Unknown:
            pass
        obj = Unknown()
        self.assertIsNone(self.audit._get_entity_type(obj))

    def test_before_create(self):
        company = Company(
            organisation_id="org-123",
            name="Acme",
            siret="12345678901234",
        )
        audit = self.audit.before_create(company)
        self.assertIsNotNone(audit)
        self.assertEqual(audit.action, "create")
        self.assertEqual(audit.entity_type, "company")
        self.assertEqual(audit.new_values["name"], "Acme")

    def test_before_create_unknown_type(self):
        from xohive.crm.domain.company import Company
        class Unknown:
            pass
        obj = Unknown()
        audit = self.audit.before_create(obj)
        self.assertIsNone(audit)

    def test_before_update(self):
        company = Company(
            organisation_id="org-123",
            name="Acme",
            siret="12345678901234",
        )
        old_values = {"name": "Acme"}
        audit = self.audit.before_update(company, old_values)
        self.assertIsNotNone(audit)
        self.assertEqual(audit.action, "update")
        self.assertEqual(audit.old_values["name"], "Acme")

    def test_before_delete(self):
        company = Company(
            organisation_id="org-123",
            name="Acme",
            siret="12345678901234",
        )
        old_values = {"name": "Acme", "siret": "12345678901234"}
        audit = self.audit.before_delete(company, old_values)
        self.assertIsNotNone(audit)
        self.assertEqual(audit.action, "delete")

    def test_register_hook(self):
        called = []
        def hook(audit):
            called.append(audit.action)
        self.audit.register_hook(hook)
        self.assertIn(hook, self.audit.hooks)

    def test_subscribe(self):
        handler = lambda audit: None
        self.audit.subscribe("audit.created", handler)
        self.assertIn("audit.created", self.audit.subscribers)
        self.assertIn(handler, self.audit.subscribers["audit.created"])


if __name__ == "__main__":
    unittest.main()
