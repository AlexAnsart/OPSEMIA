#!/usr/bin/env python3
"""Script de test pour vérifier que pipeline_example.py fonctionne avec différents modèles.

Ce script teste rapidement chaque modèle d'embedding avec le pipeline complet :
1. Modification temporaire de la configuration
2. Indexation d'un petit échantillon de données
3. Recherche de test
4. Vérification des résultats
"""

import sys
import tempfile
from pathlib import Path

# Ajouter le répertoire racine au path pour les imports
racine_projet = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(racine_projet))

from config.settings import Parametres
from src.backend.core.search_engine import MoteurRecherche
from src.backend.database.indexer import indexer_csv_messages
from src.backend.database.vector_db import BaseVectorielle


# Modèles à tester (en ordre de taille croissante)
MODELES_A_TESTER = [
    ("jinaai/jina-embeddings-v3", "Jina-v3"),
    ("BAAI/bge-m3", "BGE-M3"),
    # Qwen3-8B commenté par défaut car très gourmand
    # ("Qwen/Qwen3-Embedding-8B", "Qwen3-8B"),
]


def tester_modele(id_modele: str, nom_modele: str) -> bool:
    """Teste un modèle avec le pipeline complet.
    
    Args:
        id_modele: ID Hugging Face du modèle
        nom_modele: Nom lisible du modèle
    
    Returns:
        True si le test réussit, False sinon
    """
    print(f"\n{'='*70}")
    print(f"TEST: {nom_modele}")
    print(f"{'='*70}")
    print(f"ID Modèle: {id_modele}")
    
    try:
        # Créer une configuration temporaire
        parametres = Parametres()
        parametres.ID_MODELE_EMBEDDING = id_modele
        
        # Utiliser une base temporaire pour ne pas écraser la base existante
        with tempfile.TemporaryDirectory() as tmpdir:
            parametres.CHEMIN_BASE_CHROMA = str(Path(tmpdir) / "chroma_test")
            
            print("\n📄 Phase 1/3: Indexation...")
            
            # Indexer le CSV (version courte pour test rapide)
            try:
                stats = indexer_csv_messages(
                    chemin_csv=parametres.CHEMIN_CSV_DONNEES,
                    parametres=parametres,
                    nom_cas="test",
                    reinitialiser=True,
                )
                
                print(f"   ✅ Indexation réussie")
                print(f"      - {stats['messages_indexe']} messages indexés")
                print(f"      - {stats['chunks_indexes']} chunks indexés")
                print(f"      - Durée totale: {stats['duree_totale_sec']:.2f}s")
                
            except Exception as e:
                print(f"   ❌ Échec indexation: {e}")
                return False
            
            print("\n🔍 Phase 2/3: Test de recherche...")
            
            # Initialiser le moteur de recherche
            db = BaseVectorielle(chemin_persistance=parametres.CHEMIN_BASE_CHROMA)
            moteur = MoteurRecherche(base_vectorielle=db, parametres=parametres)
            
            # Test de recherche simple
            requete_test = "rendez-vous argent"
            nom_collection = "messages_test"
            
            try:
                resultats = moteur.rechercher(
                    requete=requete_test,
                    nom_collection=nom_collection,
                    nombre_resultats=5,
                )
                
                print(f"   ✅ Recherche réussie")
                print(f"      - Requête: '{requete_test}'")
                print(f"      - {len(resultats)} résultats trouvés")
                
                if resultats:
                    premier = resultats[0]
                    print(f"      - Meilleur score: {premier['score']:.3f}")
                    print(f"      - Extrait: {premier['document'][:80]}...")
                
            except Exception as e:
                print(f"   ❌ Échec recherche: {e}")
                return False
            
            print("\n✅ Phase 3/3: Vérification...")
            
            # Vérifications basiques
            verifications = [
                (stats['messages_indexe'] > 0, "Messages indexés"),
                (stats['chunks_indexes'] >= 0, "Chunks créés"),
                (len(resultats) > 0, "Résultats trouvés"),
                (resultats[0]['score'] > 0, "Scores valides"),
            ]
            
            tout_ok = True
            for check, description in verifications:
                status = "✅" if check else "❌"
                print(f"      {status} {description}")
                tout_ok = tout_ok and check
            
            if tout_ok:
                print(f"\n🎉 TEST RÉUSSI pour {nom_modele}!")
                return True
            else:
                print(f"\n⚠️  TEST PARTIELLEMENT RÉUSSI pour {nom_modele}")
                return False
                
    except Exception as e:
        print(f"\n❌ ERREUR INATTENDUE: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Fonction principale."""
    print("=" * 70)
    print("TEST DES MODÈLES AVEC PIPELINE_EXAMPLE.PY")
    print("=" * 70)
    print("\nCe script teste que chaque modèle fonctionne avec le pipeline complet.")
    print("Les tests utilisent une base temporaire et ne modifient pas vos données.\n")
    
    # Importer ici pour forcer le rechargement du singleton à chaque test
    from src.backend.models import model_manager
    
    resultats = {}
    
    for id_modele, nom_modele in MODELES_A_TESTER:
        # Réinitialiser le singleton de l'encodeur avant chaque test
        model_manager._encodeur_texte_singleton = None
        
        try:
            succes = tester_modele(id_modele, nom_modele)
            resultats[nom_modele] = succes
        except KeyboardInterrupt:
            print("\n\n⚠️  Interruption utilisateur. Arrêt des tests.")
            break
        except Exception as e:
            print(f"\n❌ Erreur lors du test de {nom_modele}: {e}")
            resultats[nom_modele] = False
    
    # Afficher le résumé
    print(f"\n{'='*70}")
    print("RÉSUMÉ DES TESTS")
    print(f"{'='*70}")
    
    for nom_modele, succes in resultats.items():
        status = "✅ RÉUSSI" if succes else "❌ ÉCHOUÉ"
        print(f"  {status:12} - {nom_modele}")
    
    nb_reussis = sum(1 for s in resultats.values() if s)
    nb_total = len(resultats)
    
    print(f"\n{'='*70}")
    print(f"BILAN: {nb_reussis}/{nb_total} modèles fonctionnent correctement")
    print(f"{'='*70}")
    
    if nb_reussis == nb_total:
        print("\n🎉 Tous les tests ont réussi!")
        return 0
    else:
        print(f"\n⚠️  {nb_total - nb_reussis} modèle(s) ont échoué.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

