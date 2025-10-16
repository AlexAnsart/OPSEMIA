#!/usr/bin/env python3
"""Script de correction des IDs dans les collections de benchmark.

Corrige le format des IDs de msg_1 → msg_001 (avec padding)
sans réindexer complètement.
"""

import sys
from pathlib import Path

# Ajouter le répertoire racine au path
racine_projet = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(racine_projet))

from src.backend.database.vector_db import BaseVectorielle

# Chemin de la base temporaire
CHEMIN_DB_BENCHMARK = racine_projet / "data" / "benchmark_temp"


def corriger_id_message(ancien_id: str) -> str:
    """Corrige un ID de message pour ajouter le padding.
    
    msg_1 → msg_001
    msg_46 → msg_046
    msg_123 → msg_123 (déjà OK)
    img_1 → img_001
    """
    if not ancien_id:
        return ancien_id
    
    # Séparer le préfixe (msg_, img_) du numéro
    if "_" in ancien_id:
        prefixe, numero_str = ancien_id.rsplit("_", 1)
        try:
            numero = int(numero_str)
            # Padding à 3 chiffres
            return f"{prefixe}_{numero:03d}"
        except ValueError:
            # Pas un nombre, garder tel quel
            return ancien_id
    
    return ancien_id


def corriger_collection(db: BaseVectorielle, nom_collection: str):
    """Corrige les IDs d'une collection.
    
    Args:
        db: Instance de BaseVectorielle
        nom_collection: Nom de la collection à corriger
    """
    print(f"\n📦 Collection: {nom_collection}")
    
    try:
        collection = db.client.get_collection(name=nom_collection)
    except Exception as e:
        print(f"   ⚠️  Impossible d'accéder à la collection: {e}")
        return
    
    # Récupérer tous les documents
    print(f"   📥 Récupération des documents...")
    resultats = collection.get(include=["embeddings", "metadatas", "documents"])
    
    nb_docs = len(resultats["ids"])
    print(f"   📊 {nb_docs} documents trouvés")
    
    if nb_docs == 0:
        print(f"   ✓ Collection vide, rien à corriger")
        return
    
    # Vérifier s'il y a des IDs à corriger
    ids_a_corriger = []
    nouveaux_ids = []
    
    for ancien_id in resultats["ids"]:
        nouveau_id = corriger_id_message(ancien_id)
        if ancien_id != nouveau_id:
            ids_a_corriger.append(ancien_id)
        nouveaux_ids.append(nouveau_id)
    
    if not ids_a_corriger:
        print(f"   ✓ Tous les IDs sont déjà au bon format")
        return
    
    print(f"   🔧 {len(ids_a_corriger)} IDs à corriger")
    print(f"      Exemples: {ids_a_corriger[:3]}")
    print(f"      → {[corriger_id_message(id) for id in ids_a_corriger[:3]]}")
    
    # Supprimer l'ancienne collection
    print(f"   🗑️  Suppression de l'ancienne collection...")
    db.supprimer_collection(nom_collection)
    
    # Recréer avec les bons IDs
    print(f"   ✨ Recréation avec les IDs corrigés...")
    
    # Mettre à jour les métadonnées
    metadonnees_corrigees = []
    for i, meta in enumerate(resultats["metadatas"]):
        if meta and isinstance(meta, dict):
            meta_copy = meta.copy()
            # Corriger l'ID dans les métadonnées aussi
            if "id" in meta_copy:
                meta_copy["id"] = nouveaux_ids[i]
            metadonnees_corrigees.append(meta_copy)
        else:
            metadonnees_corrigees.append(meta)
    
    db.ajouter_messages(
        nom_collection=nom_collection,
        ids=nouveaux_ids,
        embeddings=resultats["embeddings"],
        metadonnees=metadonnees_corrigees,
        documents=resultats["documents"],
    )
    
    print(f"   ✅ Collection corrigée: {nb_docs} documents avec nouveaux IDs")


def main():
    """Fonction principale."""
    print("="*80)
    print("CORRECTION DES IDS DE BENCHMARK")
    print("="*80)
    
    # Connexion à la base
    db = BaseVectorielle(chemin_persistance=CHEMIN_DB_BENCHMARK)
    
    # Lister toutes les collections benchmark
    collections = [col.name for col in db.client.list_collections() if col.name.startswith("benchmark_")]
    
    print(f"\n🔍 {len(collections)} collection(s) de benchmark trouvée(s)")
    
    if not collections:
        print("\n⚠️  Aucune collection de benchmark à corriger")
        print("   Lancez d'abord le benchmark pour créer les collections")
        return
    
    for nom_collection in collections:
        corriger_collection(db, nom_collection)
    
    print("\n" + "="*80)
    print("✅ CORRECTION TERMINÉE")
    print("="*80)
    print(f"📊 {len(collections)} collection(s) traitée(s)")
    print("\n💡 Vous pouvez maintenant relancer le benchmark SANS --force")
    print("   python scripts/benchmark_complet_opsemia.py")
    print("="*80)


if __name__ == "__main__":
    main()

