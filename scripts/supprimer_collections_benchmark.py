#!/usr/bin/env python3
"""Supprime toutes les collections de benchmark pour forcer une réindexation complète."""

import sys
from pathlib import Path

racine_projet = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(racine_projet))

from src.backend.database.vector_db import BaseVectorielle

CHEMIN_DB_BENCHMARK = racine_projet / "data" / "benchmark_temp"

def main():
    db = BaseVectorielle(chemin_persistance=CHEMIN_DB_BENCHMARK)
    
    collections = [col.name for col in db.client.list_collections() if col.name.startswith("benchmark_")]
    
    print(f"🗑️  Suppression de {len(collections)} collection(s)...")
    
    for nom in collections:
        print(f"   - {nom}")
        db.supprimer_collection(nom)
    
    print(f"✅ Suppression terminée")

if __name__ == "__main__":
    main()

