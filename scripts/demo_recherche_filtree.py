"""Script de démonstration du moteur de recherche avec filtres.

Ce script illustre l'utilisation programmatique du moteur de recherche avec
différents types de filtres (temporel, géographique, exclusion bruit).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ajouter le répertoire racine au path pour les imports
racine_projet = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(racine_projet))

from config.settings import obtenir_parametres
from src.backend.core.filters import (
    combiner_filtres,
    creer_filtre_exclusion_bruit,
    creer_filtre_geographique,
    creer_filtre_temporel,
)
from src.backend.core.search_engine import MoteurRecherche
from src.backend.database.vector_db import BaseVectorielle


def afficher_resultats(resultats: list, titre: str) -> None:
    """Affiche les résultats de recherche de manière formatée.

    Args:
        resultats: Liste de résultats de recherche
        titre: Titre à afficher
    """
    print(f"\n{'='*70}")
    print(f"  {titre}")
    print(f"{'='*70}")
    
    if not resultats:
        print("❌ Aucun résultat trouvé.")
        return
    
    print(f"✅ {len(resultats)} résultat(s) trouvé(s):\n")
    
    for i, res in enumerate(resultats, 1):
        score = res["score"]
        texte = res["document"][:120]
        metadata = res["metadata"]
        
        timestamp = metadata.get("timestamp", "N/A")
        contact = metadata.get("contact_name") or metadata.get("from", "N/A")
        is_noise = metadata.get("is_noise", False)
        
        print(f"{i}. [Score: {score:.3f}] {'🔇 BRUIT' if is_noise else ''}")
        print(f"   📅 {timestamp} | 👤 {contact}")
        print(f"   💬 {texte}{'...' if len(res['document']) > 120 else ''}\n")


def demo_recherche_simple(moteur: MoteurRecherche) -> None:
    """Démonstration d'une recherche simple sans filtre."""
    print("\n" + "🔍 DÉMONSTRATION 1: Recherche simple".center(70, "="))
    
    resultats = moteur.rechercher(
        requete="rendez-vous",
        nom_collection="messages_cas1",
        nombre_resultats=5,
        exclure_bruit=False,  # On inclut tout pour la démo
    )
    
    afficher_resultats(resultats, "Recherche: 'rendez-vous'")


def demo_recherche_avec_exclusion_bruit(moteur: MoteurRecherche) -> None:
    """Démonstration avec exclusion du bruit."""
    print("\n" + "🔍 DÉMONSTRATION 2: Recherche avec exclusion du bruit".center(70, "="))
    
    # Recherche AVEC bruit
    resultats_avec_bruit = moteur.rechercher(
        requete="promo offre",
        nom_collection="messages_cas1",
        nombre_resultats=5,
        exclure_bruit=False,
    )
    
    afficher_resultats(resultats_avec_bruit, "Recherche 'promo offre' (AVEC bruit)")
    
    # Recherche SANS bruit
    resultats_sans_bruit = moteur.rechercher(
        requete="promo offre",
        nom_collection="messages_cas1",
        nombre_resultats=5,
        exclure_bruit=True,
    )
    
    afficher_resultats(resultats_sans_bruit, "Recherche 'promo offre' (SANS bruit)")


def demo_recherche_filtre_temporel(moteur: MoteurRecherche) -> None:
    """Démonstration avec filtre temporel."""
    print("\n" + "🔍 DÉMONSTRATION 3: Recherche avec filtre temporel".center(70, "="))
    
    # Créer un filtre temporel (exemple: mars 2024)
    filtre_mars = creer_filtre_temporel(
        timestamp_debut="2024-03-01",
        timestamp_fin="2024-03-31"
    )
    
    resultats = moteur.rechercher(
        requete="message",
        nom_collection="messages_cas1",
        filtres=filtre_mars,
        nombre_resultats=5,
    )
    
    afficher_resultats(resultats, "Recherche dans Mars 2024 uniquement")


def demo_recherche_filtres_combines(moteur: MoteurRecherche) -> None:
    """Démonstration avec combinaison de filtres."""
    print("\n" + "🔍 DÉMONSTRATION 4: Filtres combinés".center(70, "="))
    
    # Combiner filtre temporel + exclusion bruit
    filtre_combine = combiner_filtres(
        creer_filtre_temporel(timestamp_debut="2024-03-01"),
        creer_filtre_exclusion_bruit(exclure=True)
    )
    
    resultats = moteur.rechercher(
        requete="transfert",
        nom_collection="messages_cas1",
        filtres=filtre_combine,
        nombre_resultats=5,
    )
    
    afficher_resultats(resultats, "Recherche 'transfert' (Mars 2024 + sans bruit)")


def main() -> None:
    """Fonction principale de démonstration."""
    print("\n" + "="*70)
    print("OPSEMIA - Démonstration du Moteur de Recherche avec Filtres".center(70))
    print("="*70)
    
    # Initialisation
    parametres = obtenir_parametres()
    db = BaseVectorielle(chemin_persistance=parametres.CHEMIN_BASE_CHROMA)
    moteur = MoteurRecherche(base_vectorielle=db, parametres=parametres)
    
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
    
    print(f"\n📚 Collection: {nom_collection} ({count} documents)")
    print(f"🧠 Modèle: {parametres.ID_MODELE_EMBEDDING}")
    print(f"⚙️  Méthode: {parametres.METHODE_RECHERCHE}")
    
    # Lancer les démonstrations
    demo_recherche_simple(moteur)
    demo_recherche_avec_exclusion_bruit(moteur)
    demo_recherche_filtre_temporel(moteur)
    demo_recherche_filtres_combines(moteur)
    
    print("\n" + "="*70)
    print("✅ Démonstration terminée!")
    print("="*70)
    print("\nPour une recherche interactive, lancez:")
    print("  python src/backend/core/pipeline_example.py --search")
    print()


if __name__ == "__main__":
    main()

