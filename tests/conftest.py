"""Fixtures partagées pour les tests du moteur XoHive (engine-api-v1)."""
from __future__ import annotations

import sys
from pathlib import Path

# Ajouter le répertoire racine au chemin d'imports
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import engine
import engine.api as api_mod
from engine.api import XoHiveError


@pytest.fixture(scope="module")
def doc_store():
    """DocumentStore en mémoire (état volatile, pas de persistance)."""
    from engine.documents import DocumentStore

    store = DocumentStore(org_id=1)
    return store


@pytest.fixture(scope="module")
def app_handlers():
    """Sous-ensemble de handlers HTTP pour les tests de route."""
    from engine.api import Handler

    return Handler
