#!/usr/bin/env python3
"""Génération du lot Pipeline CRM - branche feature/pipeline-crm."""
import subprocess
import os

def run(cmd, check=True):
    """Exécute une commande shell."""
    print(f"$ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}")
    return result

import sys
sys.path.insert(0, '.')

# Créer la branche feature/pipeline-crm
run("git checkout main")
run("git pull origin main")
run("git checkout -b feature/pipeline-crm", check=False)

print("\n=== Branche créée: feature/pipeline-crm ===")
print("Commence l'implémentation du module Pipeline CRM...")
