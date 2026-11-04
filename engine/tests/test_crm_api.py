"""Tests unitaires pour l'API CRM REST."""

import unittest
import tempfile
import os
import shutil
from pathlib import Path

from engine.crm_api import CrmApiHandler


class TestCrmApiValidation(unittest.TestCase):
    """Tests de la validation de l'API CRM."""

    def test_company_required_fields(self):
        """Le nom est requis pour créer une company."""
        from xohive.crm.domain.company import Company, CompanyError
        try:
            Company(
                name="",
                siret="12345678901234",
                organisation_id="default-org",
            )
            self.fail("CompanyError non levé pour nom vide")
        except CompanyError as e:
            self.assertIn("nom", str(e).lower())

    def test_company_siret_format(self):
        """Le SIRET doit être au format 14 chiffres."""
        from xohive.crm.domain.company import Company, CompanyError
        try:
            Company(
                name="Acme",
                siret="123",
                organisation_id="default-org",
            )
            self.fail("CompanyError non levé pour SIRET invalide")
        except CompanyError as e:
            self.assertIn("siret", str(e).lower())

    def test_contact_required_fields(self):
        """Champs requis pour un contact."""
        from xohive.crm.domain.contact import Contact, ContactError
        try:
            Contact(
                organisation_id="default-org",
                company_id="crm-001",
                first_name="",
                last_name="Dupont",
                email="jean@acme.com",
            )
            self.fail("ContactError non levé pour prénom vide")
        except ContactError as e:
            self.assertIn("prénom", str(e).lower())

    def test_opportunity_amount_positive(self):
        """Le montant doit être > 0."""
        from xohive.crm.domain.opportunity import Opportunity, OpportunityError
        try:
            Opportunity(
                organisation_id="default-org",
                company_id="crm-001",
                title="Test",
                amount=-100.0,
            )
            self.fail("OpportunityError non levé pour montant négatif")
        except OpportunityError as e:
            self.assertIn("montant", str(e).lower())

    def test_pipeline_stage_valid(self):
        """Le stage doit être valide."""
        from xohive.crm.domain.pipeline import (
            PipelineError, PipelineDefinition,
        )
        schema = {
            "prospecting": ["qualifying"],
            "qualifying": ["proposition"],
            "proposition": ["negociation"],
            "negociation": ["closed"],
            "closed": [],
        }
        try:
            PipelineDefinition(
                name="Test",
                stage_schema=schema,
                initial_stage="invalide",
            )
            self.fail("PipelineError non levé pour stage inconnu")
        except PipelineError as e:
            self.assertIn("stage", str(e).lower())

    def test_activity_required_fields(self):
        """Champs requis pour une activité."""
        from xohive.crm.domain.activity import Activity, ActivityError
        try:
            Activity(
                organisation_id="default-org",
                company_id="crm-001",
                subject="",
                date="2026-11-04T10:00:00Z",
            )
            self.fail("ActivityError non levé pour sujet vide")
        except ActivityError as e:
            self.assertIn("sujet", str(e).lower())

    def test_type_dans_enum(self):
        """Le type doit être parmi les types autorisés."""
        from xohive.crm.domain.activity import Activity, ActivityError
        try:
            Activity(
                organisation_id="default-org",
                company_id="crm-001",
                subject="Test",
                date="2026-11-04T10:00:00Z",
                type="invalide",
            )
            self.fail("ActivityError non levé pour type invalide")
        except ActivityError as e:
            self.assertIn("type", str(e).lower())

    def test_pipeline_transition_refused(self):
        """Une transition invalide doit lever une erreur."""
        from xohive.crm.domain.pipeline import (
            PipelineError, PipelineDefinition, PipelineInstance,
        )
        schema = {
            "prospecting": ["qualifying"],
            "qualifying": ["proposition"],
            "proposition": ["negociation"],
            "negociation": ["closed"],
            "closed": [],
        }
        definition = PipelineDefinition(
            name="Test",
            stage_schema=schema,
            initial_stage="prospecting",
        )
        inst = PipelineInstance(
            pipeline_id=definition.id,
            definition=definition,
        )
        with self.assertRaises(PipelineError):
            inst.transition("closed", "admin")


if __name__ == "__main__":
    unittest.main()
