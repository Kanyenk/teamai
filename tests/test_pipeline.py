"""Tests unitaires pour Pipeline et PipelineEngine."""

import unittest

from xohive.crm.domain.pipeline import (
    PipelineError,
    PipelineDefinition,
    PipelineInstance,
    PipelineEngine,
)


class TestPipelineDefinition(unittest.TestCase):
    """Tests de l'entité PipelineDefinition."""

    def setUp(self):
        self.schema = {
            "prospecting": ["qualifying"],
            "qualifying": ["proposition"],
            "proposition": ["negociation"],
            "negociation": ["closed"],
            "closed": [],
        }
        self.definition = PipelineDefinition(
            name="Pipeline commercial",
            stage_schema=self.schema,
            initial_stage="prospecting",
        )

    def test_creation(self):
        wf = PipelineDefinition(
            name="Test",
            stage_schema={"a": ["b"], "b": []},
            initial_stage="a",
        )
        self.assertTrue(wf.id.startswith("pipe-"))

    def test_creation_avec_id(self):
        wf = PipelineDefinition(
            id="custom",
            name="Test",
            stage_schema={"a": ["b"], "b": []},
            initial_stage="a",
        )
        self.assertEqual(wf.id, "custom")

    def test_creation_nom_vide(self):
        with self.assertRaises(PipelineError):
            PipelineDefinition(
                name="",
                stage_schema={"a": ["b"], "b": []},
                initial_stage="a",
            )

    def test_creation_stage_inconnu(self):
        with self.assertRaises(PipelineError):
            PipelineDefinition(
                name="Test",
                stage_schema={"a": ["b"], "b": []},
                initial_stage="inconnu",
            )

    def test_est_transition_valide(self):
        self.assertTrue(self.definition.est_transition_valide("prospecting", "qualifying"))
        self.assertFalse(self.definition.est_transition_valide("prospecting", "closed"))
        self.assertFalse(self.definition.est_transition_valide("negociation", "prospecting"))

    def test_get_next_stages(self):
        self.assertEqual(
            self.definition.get_next_stages("prospecting"),
            ["qualifying"],
        )
        self.assertEqual(self.definition.get_next_stages("closed"), [])

    def test_repr(self):
        self.assertIn("PipelineDefinition", repr(self.definition))


class TestPipelineInstance(unittest.TestCase):
    """Tests de l'entité PipelineInstance."""

    def setUp(self):
        self.schema = {
            "prospecting": ["qualifying"],
            "qualifying": ["proposition"],
            "proposition": ["negociation"],
            "negociation": ["closed"],
            "closed": [],
        }
        self.definition = PipelineDefinition(
            name="Test",
            stage_schema=self.schema,
            initial_stage="prospecting",
        )

    def test_creation_defaut(self):
        inst = PipelineInstance(
            pipeline_id=self.definition.id,
            definition=self.definition,
        )
        self.assertEqual(inst.stage, "prospecting")
        self.assertIsNotNone(inst.id)

    def test_creation_avec_stage(self):
        inst = PipelineInstance(
            pipeline_id=self.definition.id,
            definition=self.definition,
            stage="negociation",
        )
        self.assertEqual(inst.stage, "negociation")

    def test_creation_stage_inconnu(self):
        with self.assertRaises(PipelineError):
            PipelineInstance(
                pipeline_id=self.definition.id,
                definition=self.definition,
                stage="invalide",
            )

    def test_transition(self):
        inst = PipelineInstance(
            pipeline_id=self.definition.id,
            definition=self.definition,
        )
        inst.transition("qualifying", "admin")
        self.assertEqual(inst.stage, "qualifying")

    def test_transition_refusee(self):
        inst = PipelineInstance(
            pipeline_id=self.definition.id,
            definition=self.definition,
        )
        with self.assertRaises(PipelineError):
            inst.transition("closed", "admin")

    def test_to_dict(self):
        inst = PipelineInstance(
            pipeline_id=self.definition.id,
            definition=self.definition,
            metadata={"key": "value"},
        )
        d = inst.to_dict()
        self.assertEqual(d["pipeline_id"], self.definition.id)
        self.assertEqual(d["stage"], "prospecting")
        self.assertEqual(d["metadata"]["key"], "value")

    def test_repr(self):
        inst = PipelineInstance(
            pipeline_id=self.definition.id,
            definition=self.definition,
        )
        self.assertIn("PipelineInstance", repr(inst))


class TestPipelineEngine(unittest.TestCase):
    """Tests du moteur de pipeline."""

    def setUp(self):
        self.engine = PipelineEngine()
        self.schema = {
            "prospecting": ["qualifying"],
            "qualifying": ["proposition"],
            "proposition": ["negociation"],
            "negociation": ["closed"],
            "closed": [],
        }
        self.definition = PipelineDefinition(
            name="Test",
            stage_schema=self.schema,
            initial_stage="prospecting",
        )
        self.engine.register_definition(self.definition)

    def test_register_definition(self):
        self.assertIn(self.definition.id, self.engine.definitions)

    def test_create_instance(self):
        inst = self.engine.create_instance(self.definition.id)
        self.assertEqual(inst.stage, "prospecting")

    def test_create_instance_unknown(self):
        with self.assertRaises(PipelineError):
            self.engine.create_instance("inconnu")

    def test_transition_successful(self):
        inst = self.engine.create_instance(self.definition.id)
        self.engine.transition(inst, "qualifying", "admin")
        self.assertEqual(inst.stage, "qualifying")

    def test_transition_refusee(self):
        inst = self.engine.create_instance(self.definition.id)
        with self.assertRaises(PipelineError):
            self.engine.transition(inst, "closed", "admin")

    def test_hook_execution(self):
        called = []
        def hook(inst, acteur):
            called.append((inst.stage, acteur))

        self.engine.register_hook(self.definition.id, "qualifying", hook)
        inst = self.engine.create_instance(self.definition.id)
        self.engine.transition(inst, "qualifying", "admin")
        self.assertEqual(len(called), 1)
        self.assertEqual(called[0][0], "qualifying")

    def test_no_hook_on_unknown_stage(self):
        inst = self.engine.create_instance(self.definition.id)
        self.engine.transition(inst, "qualifying", "admin")
        # Pas de hook enregistré pour "proposition"
        self.engine.transition(inst, "proposition", "admin")


class TestPipelineError(unittest.TestCase):
    """Tests de l'erreur PipelineError."""

    def test_error_message(self):
        with self.assertRaises(PipelineError) as ctx:
            raise PipelineError("oups")
        self.assertEqual(str(ctx.exception), "oups")


if __name__ == "__main__":
    unittest.main()
