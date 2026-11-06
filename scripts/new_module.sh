#!/usr/bin/env bash
# scripts/new_module.sh — génère un module CRUD complet (entité, repo, service, HTTP, tests, doc, README)
# Usage: bash scripts/new_module.sh <module> <spec.json> [--commit]
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: bash scripts/new_module.sh <module> <spec.json> [--commit]"
  exit 1
fi

MODULE="$1"
SPEC="$2"
COMMIT="${3:-}"

echo "=== Génération du module: $MODULE ==="

python3 - "$MODULE" "$SPEC" <<'PYEOF'
import json, sys
from pathlib import Path

module = sys.argv[1]
spec = json.loads(Path(sys.argv[2]).read_text())

entity = spec.get("entity") or module.replace("_", " ").title().replace(" ", "")
table = spec.get("table") or module + "s"
prefix = spec.get("prefix") or module[:3]
plural = spec.get("plural") or table
fields = spec["fields"]

def default_repr(f):
    if "default" in f:
        return f["default"]
    return '""' if f["type"] == "str" else "0" if f["type"] == "int" else "0.0" if f["type"] == "float" else "False"

def test_value(f):
    return f.get("test_value") or default_repr(f)

def cast_expr(f, var):
    t = f["type"]
    if t == "int":
        return f'int({var}["{f["name"]}"])'
    if t == "float":
        return f'float({var}["{f["name"]}"])'
    return f'{var}["{f["name"]}"]'

org_test = next((test_value(f) for f in fields if f["name"] == "organisation_id"), '"test"')

# ─── Entité ───
entity_fields = []
for f in fields:
    if f.get("required"):
        entity_fields.append(f"    {f['name']}: {f['type']}")
    else:
        entity_fields.append(f"    {f['name']}: {f['type']} = {default_repr(f)}")
entity_fields.append('    id: str = field(default_factory=lambda: f"%s-{uuid.uuid4().hex[:12]}")' % prefix)
entity_fields.append('    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))')
entity_fields.append('    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))')

validations = []
for f in fields:
    if not f.get("required"):
        continue
    n, t = f["name"], f["type"]
    if t == "str":
        validations.append(f'        if not self.{n} or not isinstance(self.{n}, str):\n            raise ValueError("{n} requis et non vide")')
    elif t == "int":
        if f.get("min", 0) == 0:
            validations.append(f'        if not isinstance(self.{n}, int) or self.{n} < 0:\n            raise ValueError("{n} doit être un entier positif ou nul")')
        else:
            validations.append(f'        if not isinstance(self.{n}, int) or self.{n} == 0:\n            raise ValueError("{n} doit être un entier non nul")')
    elif t == "float":
        validations.append(f'        if not isinstance(self.{n}, (int, float)) or self.{n} < 0:\n            raise ValueError("{n} doit être un nombre positif ou nul")')

entity_code = f'''"""Entité {entity}."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass
class {entity}:
    """Représente un(e) {module.replace('_',' ')}."""

{chr(10).join(entity_fields)}

    def __post_init__(self) -> None:
{chr(10).join(validations) if validations else "        pass"}

    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'entité en dictionnaire."""
        return {{
            "id": self.id,
{chr(10).join(f'            "{f["name"]}": self.{f["name"]},' for f in fields)}
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }}

    def __repr__(self) -> str:
        return f"<{entity} {{self.id}}>"
'''
Path(f"engine/{module}.py").write_text(entity_code)

# ─── Repository ───
cols = [f["name"] for f in fields]
all_cols = ["id"] + cols + ["created_at", "updated_at"]
placeholders = ", ".join("?" * len(all_cols))
insert_cols = ", ".join(all_cols)

col_defs = []
for c in all_cols:
    if c == "id":
        col_defs.append("                    id TEXT PRIMARY KEY")
    elif c in ("created_at", "updated_at"):
        col_defs.append(f"                    {c} TEXT NOT NULL")
    else:
        fdef = next(x for x in fields if x["name"] == c)
        if fdef.get("required"):
            col_defs.append(f"                    {c} TEXT NOT NULL")
        else:
            col_defs.append(f"                    {c} TEXT")
create_cols = ",\n".join(col_defs)

repo_code = f'''"""Repository {entity}."""
from __future__ import annotations

import sqlite3
from typing import List, Optional

from engine.{module} import {entity}


class {entity}Repository:
    """Accès SQLite aux {table}."""

    def __init__(self, db_path: str = "data/teamai.db") -> None:
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS {table} (
{create_cols}
                )
                """
            )

    def create(self, obj: {entity}) -> {entity}:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO {table} ({insert_cols}) VALUES ({placeholders})",
                ({chr(10).join(f'                    obj.{c},' for c in all_cols)}                ),
            )
        return obj

    def get(self, obj_id: str) -> Optional[{entity}]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM {table} WHERE id = ?", (obj_id,)).fetchone()
        if row is None:
            return None
        return {entity}(
{chr(10).join(f'            {f["name"]}={cast_expr(f, "row")},' for f in fields)}
            id=row["id"],
        )

    def list(self, organisation_id: str) -> List[{entity}]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM {table} WHERE organisation_id = ? ORDER BY created_at DESC",
                (organisation_id,),
            ).fetchall()
        return [
            {entity}(
{chr(10).join(f'                {f["name"]}={cast_expr(f, "r")},' for f in fields)}
                id=r["id"],
            )
            for r in rows
        ]

    def delete(self, obj_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("DELETE FROM {table} WHERE id = ?", (obj_id,))
            return cur.rowcount > 0
'''
Path(f"engine/{module}_repository.py").write_text(repo_code)

# ─── Service ───
service_code = f'''"""Service {entity}."""
from __future__ import annotations

from typing import Optional

from engine.{module} import {entity}
from engine.{module}_repository import {entity}Repository


class {entity}Service:
    """Orchestre la création et la consultation des {table}."""

    def __init__(self, repo: {entity}Repository) -> None:
        self.repo = repo

    def create(self, **kwargs) -> {entity}:
        obj = {entity}(**kwargs)
        return self.repo.create(obj)

    def get(self, obj_id: str) -> Optional[{entity}]:
        return self.repo.get(obj_id)

    def list(self, organisation_id: str):
        return self.repo.list(organisation_id)

    def delete(self, obj_id: str) -> bool:
        return self.repo.delete(obj_id)
'''
Path(f"engine/{module}_service.py").write_text(service_code)

# ─── Patch HTTP ───
http_path = Path("engine/http.py")
http_src = http_path.read_text()
route_check = f'segments[3] == "{plural}"'
if route_check not in http_src:
    get_code = f'''            if len(segments) >= 4 and segments[3] == "{plural}":
                from engine.{module}_repository import {entity}Repository
                repo = {entity}Repository(self.store.db_path)
                obj_id = segments[4] if len(segments) > 4 else None
                if obj_id:
                    obj = repo.get(obj_id)
                    if obj is None:
                        return self._send_error(404, "{entity} not found")
                    self._send_json(200, {{"item": obj.to_dict()}})
                    return
                from urllib.parse import parse_qs
                query = parse_qs(urlparse(self.path).query)
                org_id = query.get("organisation_id", [None])[0]
                if not org_id:
                    return self._send_error(400, "organisation_id requis")
                items = repo.list(org_id)
                self._send_json(200, {{"items": [o.to_dict() for o in items]}})
                return
'''
    post_code = f'''            if len(segments) >= 4 and segments[3] == "{plural}":
                from engine.{module}_repository import {entity}Repository
                from engine.{module} import {entity}
                repo = {entity}Repository(self.store.db_path)
                obj_id = segments[4] if len(segments) > 4 else None
                if obj_id:
                    return self._send_error(404, "{entity} not found")
                try:
                    obj = {entity}(
{chr(10).join(f'                        {f["name"]}=body.get("{f["name"]}", {default_repr(f)}),' for f in fields)}
                    )
                    result = repo.create(obj)
                except ValueError as e:
                    return self._send_error(400, str(e))
                self._send_json(201, {{"item": result.to_dict()}})
                return
'''
    seg = '            segments = [s for s in path.split("/") if s]\n'
    gi = http_src.find("def _handle_wms_get(self, path: str):")
    gi_seg = http_src.find(seg, gi)
    http_src = http_src[:gi_seg+len(seg)] + get_code + http_src[gi_seg+len(seg):]
    pi = http_src.find("def _handle_wms_post(self, path: str):")
    pi_seg = http_src.find(seg, pi)
    http_src = http_src[:pi_seg+len(seg)] + post_code + http_src[pi_seg+len(seg):]
    http_path.write_text(http_src)
    print("HTTP patch appliqué")
else:
    print("HTTP déjà patché, skip")

# ─── Tests entité ───
entity_tests = [f'''    def test_creation_valide(self):
        """Création valide doit passer sans erreur."""
        obj = {entity}(**self._defaults())
        self.assertTrue(obj.id.startswith("{prefix}"))
''']
for f in fields:
    if not f.get("required"):
        continue
    if f["type"] == "str":
        entity_tests.append(f'''    def test_{f["name"]}_manquant(self):
        with self.assertRaises(ValueError):
            {entity}(**{{**self._defaults(), "{f['name']}": ""}})
''')
    elif f["type"] == "int":
        entity_tests.append(f'''    def test_{f["name"]}_invalide(self):
        with self.assertRaises(ValueError):
            {entity}(**{{**self._defaults(), "{f['name']}": -1}})
''')
entity_tests.append(f'''    def test_to_dict(self):
        obj = {entity}(**self._defaults())
        d = obj.to_dict()
        self.assertEqual(d["id"], obj.id)

    def test_repr(self):
        obj = {entity}(**self._defaults())
        self.assertIn("{prefix}-", repr(obj))

    @staticmethod
    def _defaults():
        return {{
{chr(10).join(f'            "{f["name"]}": {test_value(f)},' for f in fields)}        }}
''')
test_entity = f'''"""Tests unitaires de l'entité {entity}."""
import unittest
from engine.{module} import {entity}


class Test{entity}Entity(unittest.TestCase):
{chr(10).join(entity_tests)}

if __name__ == "__main__":
    unittest.main()
'''
Path(f"tests/test_{module}.py").write_text(test_entity)

# ─── Tests repository ───
test_repo = f'''"""Tests unitaires du repository {entity}."""
import os, tempfile, unittest
from engine.{module} import {entity}
from engine.{module}_repository import {entity}Repository


class Test{entity}Repository(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.repo = {entity}Repository(db_path=self.db_path)

    def tearDown(self):
        os.unlink(self.db_path)

    @staticmethod
    def _defaults():
        return {{
{chr(10).join(f'            "{f["name"]}": {test_value(f)},' for f in fields)}        }}

    def _make(self, **kw):
        return {entity}(**{{**self._defaults(), **kw}})

    def test_create_and_get(self):
        obj = self._make()
        self.repo.create(obj)
        self.assertIsNotNone(self.repo.get(obj.id))

    def test_get_non_existant(self):
        self.assertIsNone(self.repo.get("{prefix}-inexistant"))

    def test_list(self):
        self.repo.create(self._make())
        self.repo.create(self._make())
        self.assertEqual(len(self.repo.list({org_test})), 2)

    def test_list_empty(self):
        self.assertEqual(len(self.repo.list("inconnu")), 0)

    def test_delete(self):
        obj = self._make()
        self.repo.create(obj)
        self.assertTrue(self.repo.delete(obj.id))
        self.assertIsNone(self.repo.get(obj.id))

    def test_delete_non_existant(self):
        self.assertFalse(self.repo.delete("{prefix}-inexistant"))


if __name__ == "__main__":
    unittest.main()
'''
Path(f"tests/test_{module}_repository.py").write_text(test_repo)

# ─── Tests service ───
test_service = f'''"""Tests unitaires du service {entity}."""
import os, tempfile, unittest
from engine.{module}_repository import {entity}Repository
from engine.{module}_service import {entity}Service


class Test{entity}Service(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.repo = {entity}Repository(db_path=self.db_path)
        self.service = {entity}Service(self.repo)

    def tearDown(self):
        os.unlink(self.db_path)

    @staticmethod
    def _defaults():
        return {{
{chr(10).join(f'            "{f["name"]}": {test_value(f)},' for f in fields)}        }}

    def test_create(self):
        obj = self.service.create(**self._defaults())
        self.assertIsNotNone(self.service.get(obj.id))

    def test_get_inexistant(self):
        self.assertIsNone(self.service.get("{prefix}-inexistant"))

    def test_list(self):
        self.service.create(**self._defaults())
        self.service.create(**self._defaults())
        self.assertEqual(len(self.service.list({org_test})), 2)

    def test_delete(self):
        obj = self.service.create(**self._defaults())
        self.assertTrue(self.service.delete(obj.id))
        self.assertIsNone(self.service.get(obj.id))

    def test_delete_inexistant(self):
        self.assertFalse(self.service.delete("{prefix}-inexistant"))


if __name__ == "__main__":
    unittest.main()
'''
Path(f"tests/test_{module}_service.py").write_text(test_service)

# ─── Tests HTTP ───
test_http = f'''"""Tests HTTP des {table} (http.server)."""
import json, os, tempfile, threading, unittest, urllib.error, urllib.request
from http.server import HTTPServer
from types import SimpleNamespace
from engine.http import make_app
from engine.{module}_repository import {entity}Repository
from engine.{module}_service import {entity}Service


class Test{entity}HttpApi(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.repo = {entity}Repository(db_path=self.db_path)
        self.service = {entity}Service(self.repo)
        store = SimpleNamespace(db_path=self.db_path)
        handler = make_app(store, auth=None)
        self.server = HTTPServer(("127.0.0.1", 0), handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{{self.port}}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        os.unlink(self.db_path)

    def _request(self, method, path, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method, headers={{"Content-Type": "application/json"}})
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())

    def _create(self, **overrides):
        payload = {{
{chr(10).join(f'            "{f["name"]}": {test_value(f)},' for f in fields)}        }}
        payload.update(overrides)
        return self._request("POST", "/api/v1/wms/{plural}", payload)

    def test_create(self):
        status, body = self._create()
        self.assertEqual(status, 201)
        self.assertIn("item", body)

    def test_list(self):
        self._create()
        status, body = self._request("GET", "/api/v1/wms/{plural}?organisation_id={org_test.strip(chr(34))}")
        self.assertEqual(status, 200)
        self.assertEqual(len(body["items"]), 1)

    def test_list_missing_org(self):
        status, _ = self._request("GET", "/api/v1/wms/{plural}")
        self.assertEqual(status, 400)

    def test_get(self):
        _, body = self._create()
        obj_id = body["item"]["id"]
        status, body = self._request("GET", f"/api/v1/wms/{plural}/{{obj_id}}")
        self.assertEqual(status, 200)

    def test_get_not_found(self):
        status, _ = self._request("GET", "/api/v1/wms/{plural}/{prefix}-inexistant")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
'''
Path(f"tests/test_{module}_http_api.py").write_text(test_http)

# ─── Doc API ───
fields_doc = chr(10).join(f'  "{f["name"]}": {test_value(f)},' for f in fields)
doc = f'''# API {entity} ({module.replace('_',' ').title()})

## Endpoints

### POST /api/v1/wms/{plural}
Créer un(e) {module.replace('_',' ')}.

**Corps de requête :**
```json
{{
{fields_doc}
}}
```

**Réponse (201) :** `{{"item": {{...}}}}`

### GET /api/v1/wms/{plural}
Lister par organisation. **Paramètre :** `organisation_id` (requis).

**Réponse (200) :** `{{"items": [...]}}`

### GET /api/v1/wms/{plural}/{{id}}
Consulter. **Réponse (200/404).**

## Codes HTTP

| Code | Signification |
|---|---|
| 201 | Créé |
| 200 | Consulté/listé |
| 400 | Champ manquant/invalide |
| 404 | Introuvable |

## Authentification

Header `Authorization: Bearer <token>`.
'''
Path(f"docs/api_{module}.md").write_text(doc)

# ─── README ───
readme = Path("README.md")
if f"API {entity}" not in readme.read_text():
    readme_section = f'''
## API {entity} ({module.replace('_',' ').title()})

La documentation est disponible dans [docs/api_{module}.md](docs/api_{module}.md).

- POST /api/v1/wms/{plural} : créer (201).
- GET /api/v1/wms/{plural} : lister (200).
- GET /api/v1/wms/{plural}/{{id}} : consulter (200/404).
'''
    readme.write_text(readme.read_text() + readme_section)

print("Génération terminée.")
PYEOF

# Vérifier la syntaxe de tous les fichiers générés.
python3 -m py_compile "engine/${MODULE}.py" "engine/${MODULE}_repository.py" "engine/${MODULE}_service.py" "engine/http.py" "tests/test_${MODULE}.py" "tests/test_${MODULE}_repository.py" "tests/test_${MODULE}_service.py" "tests/test_${MODULE}_http_api.py" && echo "syntaxe OK"

# Lancer les tests du module.
python3 -m unittest "tests/test_${MODULE}.py" "tests/test_${MODULE}_repository.py" "tests/test_${MODULE}_service.py" "tests/test_${MODULE}_http_api.py" -v 2>&1 | tee "/tmp/${MODULE}_tests.log"
tail -10 "/tmp/${MODULE}_tests.log"

# Lancer la suite complète.
python3 -W error::ResourceWarning -m unittest discover -s tests -v 2>&1 | tee "/tmp/${MODULE}_full_tests.log"
tail -10 "/tmp/${MODULE}_full_tests.log"
grep -n "ResourceWarning\|unclosed" "/tmp/${MODULE}_full_tests.log" || echo "aucun warning socket"
grep -n "^FAIL\|^ERROR\|^FAILED" "/tmp/${MODULE}_full_tests.log" || true

# Commit si demandé.
if [ "$COMMIT" = "--commit" ]; then
  git add "engine/${MODULE}.py" "engine/${MODULE}_repository.py" "engine/${MODULE}_service.py" "engine/http.py" "tests/test_${MODULE}.py" "tests/test_${MODULE}_repository.py" "tests/test_${MODULE}_service.py" "tests/test_${MODULE}_http_api.py" "docs/api_${MODULE}.md" README.md
  git commit -m "feat(wms): add ${MODULE} module

- Entité ${MODULE} avec validation.
- Repository CRUD SQLite.
- Service logique métier.
- Endpoints HTTP intégrés au dispatch.
- Tests unitaires + HTTP.
- Documentation API + README."
  git log --oneline -1
  git status --short
fi
