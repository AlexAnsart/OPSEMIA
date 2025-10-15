"""Script de comparaison entre ANN (HNSW) et KNN (exact) pour la recherche.

Ce script montre les différences de performance et de résultats entre les deux méthodes.
"""

from __future__ import annotations

import io
import sys
import time
from pathlib import Path

# Forcer UTF-8 pour la sortie console (nécessaire pour les emojis sur Windows)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ajouter le répertoire racine au path pour les imports
racine_projet = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(racine_projet))

from config.settings import obtenir_parametres
from src.backend.core.search_engine import MoteurRecherche
from src.backend.database.vector_db import BaseVectorielle


def comparer_methodes(requete: str, nom_collection: str = "messages_cas1") -> None:
    """Compare les résultats et performances d'ANN vs KNN.

    Args:
        requete: Requête de recherche
        nom_collection: Nom de la collection
    """
    parametres = obtenir_parametres()
    db = BaseVectorielle(chemin_persistance=parametres.CHEMIN_BASE_CHROMA)
    
    # Créer une copie des paramètres pour ANN
    class ParametresANN:
        def __init__(self, params_orig):
            for attr in dir(params_orig):
                if not attr.startswith('_'):
                    setattr(self, attr, getattr(params_orig, attr))
            self.METHODE_RECHERCHE = "ANN"
    
    # Créer une copie des paramètres pour KNN
    class ParametresKNN:
        def __init__(self, params_orig):
            for attr in dir(params_orig):
                if not attr.startswith('_'):
                    setattr(self, attr, getattr(params_orig, attr))
            self.METHODE_RECHERCHE = "KNN"
    
    params_ann = ParametresANN(parametres)
    params_knn = ParametresKNN(parametres)
    
    moteur_ann = MoteurRecherche(db, params_ann)
    moteur_knn = MoteurRecherche(db, params_knn)
    
    print("\n" + "="*70)
    print(f"  COMPARAISON ANN vs KNN")
    print("="*70)
    print(f"Requête: '{requete}'")
    print(f"Collection: {nom_collection}")
    print(f"Top K: {parametres.NOMBRE_RESULTATS_RECHERCHE}")
    
    # Test ANN
    print("\n" + "-"*70)
    print("🚀 ANN (HNSW) - Approximation rapide")
    print("-"*70)
    debut = time.time()
    resultats_ann = moteur_ann.rechercher(requete, nom_collection, nombre_resultats=5)
    duree_ann = time.time() - debut
    
    print(f"⏱️  Durée: {duree_ann*1000:.2f}ms")
    print(f"📊 Résultats: {len(resultats_ann)}\n")
    
    for i, res in enumerate(resultats_ann[:5], 1):
        print(f"{i}. [Score: {res['score']:.4f}] ID: {res['id']}")
        print(f"   💬 {res['document'][:80]}...\n")
    
    # Test KNN
    print("-"*70)
    print("🎯 KNN (Exact) - Brute-force précis")
    print("-"*70)
    debut = time.time()
    resultats_knn = moteur_knn.rechercher(requete, nom_collection, nombre_resultats=5)
    duree_knn = time.time() - debut
    
    print(f"⏱️  Durée: {duree_knn*1000:.2f}ms")
    print(f"📊 Résultats: {len(resultats_knn)}\n")
    
    for i, res in enumerate(resultats_knn[:5], 1):
        print(f"{i}. [Score: {res['score']:.4f}] ID: {res['id']}")
        print(f"   💬 {res['document'][:80]}...\n")
    
    # Comparaison
    print("-"*70)
    print("📊 COMPARAISON")
    print("-"*70)
    print(f"🚀 ANN: {duree_ann*1000:.2f}ms")
    print(f"🎯 KNN: {duree_knn*1000:.2f}ms")
    print(f"⚡ Ratio: KNN est {duree_knn/duree_ann:.1f}x {'plus lent' if duree_knn > duree_ann else 'plus rapide'} que ANN")
    
    # Vérifier la concordance des résultats
    ids_ann = set(r['id'] for r in resultats_ann)
    ids_knn = set(r['id'] for r in resultats_knn)
    concordance = len(ids_ann & ids_knn) / len(ids_ann) * 100 if ids_ann else 0
    
    print(f"✅ Concordance des résultats: {concordance:.1f}%")
    
    if concordance < 100:
        print(f"⚠️  Différences détectées (normal avec ANN)")
        print(f"   - IDs uniquement dans ANN: {ids_ann - ids_knn}")
        print(f"   - IDs uniquement dans KNN: {ids_knn - ids_ann}")
    else:
        print(f"✅ Résultats identiques (rare avec ANN)")
    
    print("="*70 + "\n")


def main() -> None:
    """Fonction principale."""
    parametres = obtenir_parametres()
    db = BaseVectorielle(chemin_persistance=parametres.CHEMIN_BASE_CHROMA)
    
    # Vérifier que la collection existe
    nom_collection = "messages_cas1"
    try:
        count = db.compter_documents(nom_collection)
        if count == 0:
            print(f"\n❌ La collection '{nom_collection}' est vide ou n'existe pas.")
            print("   Veuillez d'abord indexer les données:")
            print("   python src/backend/core/pipeline_example.py")
            return
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return
    
    print("\n" + "="*70)
    print("OPSEMIA - Comparaison ANN vs KNN".center(70))
    print("="*70)
    print(f"\n📚 Collection: {nom_collection} ({count} documents)")
    
    # Tester plusieurs requêtes
    requetes = [
        "rendez-vous argent",
        "transfert",
        "contact téléphone",
    ]
    
    for requete in requetes:
        comparer_methodes(requete, nom_collection)
        input("Appuyez sur Entrée pour continuer...")
    
    print("\n✅ Comparaison terminée!")
    print("\n💡 Observations:")
    print("  - ANN est plus rapide mais peut manquer certains résultats")
    print("  - KNN est exact mais plus lent (négligeable sur petites bases)")
    print("  - Pour 275 messages, la différence est minime")
    print("  - Pour >10K messages, ANN devient indispensable\n")


if __name__ == "__main__":
    main()

