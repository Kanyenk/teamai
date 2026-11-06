#!/usr/bin/env bash
# Smoke test du générateur de modules.
# Génère un module fictif avec valeurs string piégeuses, lance ses tests, puis nettoie.
set -e

MODULE="smoketest"
SPEC="scripts/modules/${MODULE}.json"

# Valeurs piégeuses : espaces, tirets, apostrophe.
cat > "$SPEC" << 'JSONEOF'
{
  "entity": "SmokeTest",
  "table": "smoke_tests",
  "prefix": "smk",
  "plural": "smoke-tests",
  "fields": [
    {"name": "organisation_id", "type": "str", "required": true, "test_value": "org-1"},
    {"name": "label", "type": "str", "required": true, "test_value": "Test avec espaces et tirets - A-01"},
    {"name": "note", "type": "str", "required": false, "default": "", "test_value": "Note avec apostrophe d'essai"},
    {"name": "quantity", "type": "int", "required": true, "test_value": 5}
  ]
}
JSONEOF

echo "=== Smoke test : génération du module $MODULE ==="
bash scripts/new_module.sh "$MODULE" "$SPEC"

echo "=== Smoke test : lancement des tests du module ==="
python3 -m unittest tests/test_${MODULE}.py tests/test_${MODULE}_repository.py tests/test_${MODULE}_service.py tests/test_${MODULE}_http_api.py -v

echo "=== Smoke test : nettoyage ==="
# Restaurer les fichiers partagés modifiés par le générateur.
git checkout -- engine/http.py README.md
# Supprimer les fichiers générés.
rm -f engine/${MODULE}.py engine/${MODULE}_repository.py engine/${MODULE}_service.py \
      tests/test_${MODULE}.py tests/test_${MODULE}_repository.py tests/test_${MODULE}_service.py tests/test_${MODULE}_http_api.py \
      docs/api_${MODULE}.md "$SPEC"

echo "=== Smoke test : terminé avec succès ==="
