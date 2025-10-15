"""Script de test pour valider que l'interface frontend fonctionne correctement."""

from __future__ import annotations

import sys
from pathlib import Path

# Ajouter le répertoire racine au path
racine_projet = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(racine_projet))

from config.settings import obtenir_parametres
from src.backend.core.search_engine import MoteurRecherche
from src.backend.database.vector_db import BaseVectorielle


def main():
    """Tests de validation de l'interface."""
    print("=" * 70)
    print("VALIDATION INTERFACE FRONTEND")
    print("=" * 70)
    
    parametres = obtenir_parametres()
    db = BaseVectorielle(chemin_persistance=parametres.CHEMIN_BASE_CHROMA)
    moteur = MoteurRecherche(base_vectorielle=db, parametres=parametres)
    
    # Test 1: Lister les collections
    print("\n[TEST 1] Lister les collections")
    print("-" * 70)
    collections_raw = db.client.list_collections()
    collections = [
        {
            "nom": col.name,
            "nombre_documents": db.compter_documents(col.name),
            "metadata": col.metadata
        }
        for col in collections_raw
    ]
    
    for col in collections:
        print(f"  - {col['nom']} ({col['nombre_documents']} docs)")
    
    # Filtrer comme le frontend
    collections_messages = [c for c in collections if 'chunk' not in c['nom']]
    print(f"\nCollections messages (sans chunks): {[c['nom'] for c in collections_messages]}")
    
    if not collections_messages:
        print("ERREUR: Aucune collection de messages trouvee!")
        return
    
    collection_par_defaut = collections_messages[0]['nom']
    print(f"Collection par defaut selectionnee: {collection_par_defaut}")
    
    # Test 2: Recherche "police" AVEC exclusion du bruit
    print("\n[TEST 2] Recherche 'police' avec exclusion du bruit")
    print("-" * 70)
    
    resultats = moteur.rechercher(
        requete="police",
        nom_collection=collection_par_defaut,
        nombre_resultats=10,
        exclure_bruit=True,
    )
    
    print(f"Nombre de resultats: {len(resultats)}")
    
    if resultats:
        premier = resultats[0]
        print(f"\nPremier resultat:")
        print(f"  ID: {premier['id']}")
        print(f"  Score: {premier['score']:.3f}")
        print(f"  Document: {premier['document'][:100]}...")
        print(f"  is_noise: {premier['metadata'].get('is_noise')}")
        
        # Vérifier si "police" est bien présent
        if "police" in premier['document'].lower():
            print("\n  OK - Le message contient bien 'police'")
        else:
            print("\n  ATTENTION - Le premier resultat ne contient pas 'police'")
    else:
        print("\nERREUR: Aucun resultat trouve!")
        print("Le frontend devrait afficher: 'Aucun resultat trouve'")
    
    # Test 3: Recherche "police" SANS exclusion du bruit
    print("\n[TEST 3] Recherche 'police' sans exclusion du bruit")
    print("-" * 70)
    
    resultats2 = moteur.rechercher(
        requete="police",
        nom_collection=collection_par_defaut,
        nombre_resultats=10,
        exclure_bruit=False,
    )
    
    print(f"Nombre de resultats: {len(resultats2)}")
    
    if resultats2:
        premier = resultats2[0]
        print(f"\nPremier resultat:")
        print(f"  ID: {premier['id']}")
        print(f"  Score: {premier['score']:.3f}")
        print(f"  Document: {premier['document'][:100]}...")
    
    # Résumé
    print("\n" + "=" * 70)
    print("RESUME")
    print("=" * 70)
    print(f"Collection par defaut: {collection_par_defaut}")
    print(f"Resultats avec filtre bruit: {len(resultats)}")
    print(f"Resultats sans filtre bruit: {len(resultats2)}")
    
    if len(resultats) > 0 and len(resultats2) > 0:
        print("\nOK - Le frontend devrait fonctionner correctement!")
    else:
        print("\nATTENTION - Verifier la configuration!")


if __name__ == "__main__":
    main()

