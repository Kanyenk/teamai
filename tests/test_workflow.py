"""Tests unitaires pour Workflow et WorkflowEngine."""

import unittest

from xohive.domain.workflow import (
    WorkflowError,
    WorkflowDefinition,
    WorkflowInstance,
    WorkflowEngine,
)


class TestWorkflowDefinition(unittest.TestCase):
    """Tests de l'entité WorkflowDefinition."""

    def test_creation(self):
        schema = {
            "brouillon": ["brouillon_pdf"],
            "brouillon_pdf": ["envoye"],
            "envoye": ["receive"],
            "receive": [],
        }
        wf = WorkflowDefinition(
            name="Test workflow",
            state_schema=schema,
            initial_state="brouillon",
        )
        self.assertEqual(wf.name, "Test workflow")
        self.assertEqual(wf.initial_state, "brouillon")
        self.assertEqual(wf.state_schema["brouillon"], ["brouillon_pdf"])

    def test_creation_sans_id(self):
        wf = WorkflowDefinition(
            name="Test",
            state_schema={"a": ["b"], "b": []},
            initial_state="a",
        )
        self.assertTrue(wf.id.startswith("wf-"))

    def test_creation_avec_id(self):
        wf = WorkflowDefinition(
            id="custom",
            name="Test",
            state_schema={"a": ["b"], "b": []},
            initial_state="a",
        )
        self.assertEqual(wf.id, "custom")

    def test_transition_valide(self):
        schema = {"a": ["b"], "b": ["c"], "c": []}
        wf = WorkflowDefinition(
            name="Test",
            state_schema=schema,
            initial_state="a",
        )
        self.assertTrue(wf.est_transition_valide("a", "b"))
        self.assertFalse(wf.est_transition_valide("a", "c"))
        self.assertFalse(wf.est_transition_valide("b", "a"))

    def test_creation_etat_inconnu(self):
        with self.assertRaises(WorkflowError):
            WorkflowDefinition(
                name="Test",
                state_schema={"a": ["b"], "b": []},
                initial_state="inconnu",
            )

    def test_creation_schema_vide(self):
        with self.assertRaises(WorkflowError):
            WorkflowDefinition(
                name="Test",
                state_schema={},
                initial_state="a",
            )


class TestWorkflowInstance(unittest.TestCase):
    """Tests de l'entité WorkflowInstance."""

    def setUp(self):
        self.schema = {
            "brouillon": ["brouillon_pdf"],
            "brouillon_pdf": ["envoye"],
            "envoye": ["receive"],
            "receive": [],
        }
        self.definition = WorkflowDefinition(
            name="Test",
            state_schema=self.schema,
            initial_state="brouillon",
        )

    def test_creation(self):
        inst = WorkflowInstance(
            workflow_id=self.definition.id,
            definition=self.definition,
        )
        self.assertEqual(inst.current_state, "brouillon")
        self.assertEqual(inst.workflow_id, self.definition.id)

    def test_creation_avec_etat_defini(self):
        inst = WorkflowInstance(
            workflow_id=self.definition.id,
            definition=self.definition,
            current_state="brouillon_pdf",
        )
        self.assertEqual(inst.current_state, "brouillon_pdf")

    def test_transition(self):
        inst = WorkflowInstance(
            workflow_id=self.definition.id,
            definition=self.definition,
        )
        inst.transition("brouillon_pdf", "admin")
        self.assertEqual(inst.current_state, "brouillon_pdf")

    def test_transition_refusee(self):
        inst = WorkflowInstance(
            workflow_id=self.definition.id,
            definition=self.definition,
        )
        with self.assertRaises(WorkflowError):
            inst.transition("receive", "admin")

    def test_to_dict(self):
        inst = WorkflowInstance(
            workflow_id=self.definition.id,
            definition=self.definition,
            metadata={"key": "value"},
        )
        d = inst.to_dict()
        self.assertEqual(d["workflow_id"], self.definition.id)
        self.assertEqual(d["current_state"], "brouillon")
        self.assertEqual(d["metadata"]["key"], "value")

    def test_repr(self):
        inst = WorkflowInstance(
            workflow_id=self.definition.id,
            definition=self.definition,
        )
        self.assertIn("WorkflowInstance", repr(inst))


class TestWorkflowEngine(unittest.TestCase):
    """Tests du moteur de workflow."""

    def setUp(self):
        self.engine = WorkflowEngine()
        self.schema = {
            "brouillon": ["brouillon_pdf"],
            "brouillon_pdf": ["envoye"],
            "envoye": ["receive"],
            "receive": [],
        }
        self.definition = WorkflowDefinition(
            name="Test workflow",
            state_schema=self.schema,
            initial_state="brouillon",
        )
        self.engine.register_definition(self.definition)

    def test_register_definition(self):
        self.assertIn(self.definition.id, self.engine.definitions)

    def test_create_instance(self):
        inst = self.engine.create_instance(self.definition.id)
        self.assertEqual(inst.current_state, "brouillon")

    def test_create_instance_unknown(self):
        with self.assertRaises(WorkflowError):
            self.engine.create_instance("inconnu")

    def test_transition_successful(self):
        inst = self.engine.create_instance(self.definition.id)
        self.engine.transition(inst, "brouillon_pdf", "admin")
        self.assertEqual(inst.current_state, "brouillon_pdf")

    def test_transition_refusee(self):
        inst = self.engine.create_instance(self.definition.id)
        with self.assertRaises(WorkflowError):
            self.engine.transition(inst, "receive", "admin")

    def test_hook_execution(self):
        called = []
        def hook(inst, acteur):
            called.append((inst.current_state, acteur))

        self.engine.register_hook("brouillon_pdf", hook)
        inst = self.engine.create_instance(self.definition.id)
        self.engine.transition(inst, "brouillon_pdf", "admin")

        self.assertEqual(len(called), 1)
        self.assertEqual(called[0][0], "brouillon_pdf")

    def test_no_hook_on_unknown_state(self):
        inst = self.engine.create_instance(self.definition.id)
        self.engine.transition(inst, "brouillon_pdf", "admin")
        # Pas de hook enregistré pour "envoye" (mais c'est une transition valide)
        self.engine.transition(inst, "envoye", "admin")


class TestWorkflowError(unittest.TestCase):
    """Tests de l'erreur WorkflowError."""

    def test_error_message(self):
        with self.assertRaises(WorkflowError) as ctx:
            raise WorkflowError("oups")
        self.assertEqual(str(ctx.exception), "oups")


if __name__ == "__main__":
    unittest.main()
