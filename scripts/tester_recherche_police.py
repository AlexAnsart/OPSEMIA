"""Script de test rapide pour vérifier la recherche "police"."""

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
    """Test rapide de la recherche "police"."""
    print("=" * 70)
    print("TEST RECHERCHE 'police'")
    print("=" * 70)
    
    # Initialiser
    parametres = obtenir_parametres()
    db = BaseVectorielle(chemin_persistance=parametres.CHEMIN_BASE_CHROMA)
    moteur = MoteurRecherche(base_vectorielle=db, parametres=parametres)
    
    # Collection
    nom_collection = "messages_cas1"
    
    print(f"\nCollection: {nom_collection}")
    print(f"Modele: {parametres.ID_MODELE_EMBEDDING}")
    print(f"Methode: {parametres.METHODE_RECHERCHE}")
    
    # Test 1: Recherche "police" AVEC exclusion du bruit
    print("\n" + "=" * 70)
    print("TEST 1: Recherche 'police' AVEC exclusion du bruit")
    print("=" * 70)
    
    resultats_avec_filtre = moteur.rechercher(
        requete="police",
        nom_collection=nom_collection,
        nombre_resultats=10,
        exclure_bruit=True,
    )
    
    print(f"OK - {len(resultats_avec_filtre)} resultat(s) trouve(s)")
    
    if resultats_avec_filtre:
        for i, res in enumerate(resultats_avec_filtre[:3], 1):
            print(f"\n{i}. Score: {res['score']:.3f}")
            print(f"   Document: {res['document'][:100]}...")
            print(f"   Metadata: {res['metadata']}")
    
    # Test 2: Recherche "police" SANS exclusion du bruit
    print("\n" + "=" * 70)
    print("TEST 2: Recherche 'police' SANS exclusion du bruit")
    print("=" * 70)
    
    resultats_sans_filtre = moteur.rechercher(
        requete="police",
        nom_collection=nom_collection,
        nombre_resultats=10,
        exclure_bruit=False,
    )
    
    print(f"OK - {len(resultats_sans_filtre)} resultat(s) trouve(s)")
    
    if resultats_sans_filtre:
        for i, res in enumerate(resultats_sans_filtre[:3], 1):
            print(f"\n{i}. Score: {res['score']:.3f}")
            print(f"   Document: {res['document'][:100]}...")
            print(f"   Metadata: {res['metadata']}")
    
    # Vérifier si le message "nique la police" est présent
    print("\n" + "=" * 70)
    print("VÉRIFICATION: Message 'nique la police'")
    print("=" * 70)
    
    message_trouve = False
    for res in resultats_sans_filtre:
        if "police" in res['document'].lower():
            print(f"OK - Trouve: {res['document']}")
            print(f"   Score: {res['score']:.3f}")
            print(f"   ID: {res['id']}")
            message_trouve = True
            break
    
    if not message_trouve:
        print("ERREUR - Message 'nique la police' non trouve dans les resultats")


if __name__ == "__main__":
    main()

