#!/usr/bin/env python3
"""Script pour afficher les statistiques et exemples du dataset de benchmark.

Utilisation:
    python afficher_dataset_benchmark.py
"""

import sys
from pathlib import Path

# Ajouter le répertoire racine au path
racine_projet = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(racine_projet))

from scripts.donnees_benchmark_opsemia import (
    obtenir_requetes_messages,
    obtenir_requetes_images,
    afficher_statistiques_dataset,
)


def afficher_exemples_requetes(nombre: int = 15):
    """Affiche des exemples de requêtes de chaque catégorie.
    
    Args:
        nombre: Nombre total d'exemples à afficher
    """
    print("\n" + "="*80)
    print("EXEMPLES DE REQUÊTES PAR CATÉGORIE")
    print("="*80)
    
    # Catégories de requêtes
    categories = {
        "Production/Qualité": [0, 9],
        "Transactions financières": [10, 24],
        "Rendez-vous/Livraisons": [25, 36],
        "Sécurité/Surveillance": [37, 49],
        "Enquêtes/Risques": [50, 59],
        "Négociations/Affaires": [60, 71],
        "Relations personnages": [72, 81],
        "Spam/Commercial": [82, 89],
    }
    
    requetes_messages = obtenir_requetes_messages()
    
    for categorie, (debut, fin) in categories.items():
        print(f"\n### {categorie}")
        print("-" * 80)
        
        # Afficher 2 exemples par catégorie
        for i in range(debut, min(debut + 2, fin + 1)):
            if i < len(requetes_messages):
                requete, ids_attendus, difficulte = requetes_messages[i]
                print(f"\n{i+1}. [{difficulte.upper()}] {requete}")
                print(f"   Attendus: {', '.join(ids_attendus[:3])}{'...' if len(ids_attendus) > 3 else ''}")


def afficher_requetes_images():
    """Affiche les requêtes images à compléter."""
    print("\n" + "="*80)
    print("REQUÊTES IMAGES (À COMPLÉTER)")
    print("="*80)
    
    print("\n⚠️  Les requêtes suivantes doivent être complétées avec des descriptions")
    print("    textuelles appropriées basées sur le contenu réel des images.\n")
    
    requetes_images = obtenir_requetes_images()
    
    for i, (requete, ids_attendus, difficulte) in enumerate(requetes_images, 1):
        print(f"{i}. [{difficulte.upper()}] Images attendues: {', '.join(ids_attendus)}")
        print(f"   Requête actuelle: {requete}")
        print()


def afficher_analyse_difficulte():
    """Affiche une analyse de la répartition par difficulté."""
    print("\n" + "="*80)
    print("ANALYSE DE LA DIFFICULTÉ DES REQUÊTES")
    print("="*80)
    
    requetes_messages = obtenir_requetes_messages()
    requetes_images = obtenir_requetes_images()
    
    difficultes = {
        "facile": {"messages": [], "images": []},
        "moyen": {"messages": [], "images": []},
        "difficile": {"messages": [], "images": []},
    }
    
    # Compter messages
    for requete, ids, diff in requetes_messages:
        difficultes[diff]["messages"].append((requete, ids))
    
    # Compter images
    for requete, ids, diff in requetes_images:
        difficultes[diff]["images"].append((requete, ids))
    
    # Afficher
    for niveau in ["facile", "moyen", "difficile"]:
        nb_msg = len(difficultes[niveau]["messages"])
        nb_img = len(difficultes[niveau]["images"])
        total = nb_msg + nb_img
        pct = (total / (len(requetes_messages) + len(requetes_images))) * 100
        
        print(f"\n### {niveau.upper()}")
        print(f"  - Messages: {nb_msg}")
        print(f"  - Images: {nb_img}")
        print(f"  - Total: {total} ({pct:.1f}%)")
        
        if niveau == "facile":
            print("  - Caractéristiques: Termes exacts, concepts simples")
        elif niveau == "moyen":
            print("  - Caractéristiques: Synonymes, concepts combinés")
        else:
            print("  - Caractéristiques: Sémantique complexe, plusieurs concepts")


def afficher_couverture_dataset():
    """Affiche la couverture du dataset par les requêtes."""
    print("\n" + "="*80)
    print("COUVERTURE DU DATASET")
    print("="*80)
    
    requetes_messages = obtenir_requetes_messages()
    
    # Compter les documents uniques référencés
    docs_references = set()
    for _, ids_attendus, _ in requetes_messages:
        docs_references.update(ids_attendus)
    
    print(f"\n📊 Statistiques de couverture:")
    print(f"  - Total requêtes messages: {len(requetes_messages)}")
    print(f"  - Documents uniques référencés: {len(docs_references)}")
    print(f"  - Moyenne docs/requête: {sum(len(ids) for _, ids, _ in requetes_messages) / len(requetes_messages):.1f}")
    
    # Distribution du nombre de résultats attendus
    distribution = {}
    for _, ids_attendus, _ in requetes_messages:
        nb = len(ids_attendus)
        distribution[nb] = distribution.get(nb, 0) + 1
    
    print(f"\n📈 Distribution du nombre de résultats attendus:")
    for nb in sorted(distribution.keys()):
        count = distribution[nb]
        print(f"  - {nb} résultat{'s' if nb > 1 else ''}: {count} requête{'s' if count > 1 else ''}")


def main():
    """Fonction principale."""
    print("="*80)
    print("DATASET DE BENCHMARK OPSEMIA - VISUALISATION")
    print("="*80)
    
    # Statistiques globales
    afficher_statistiques_dataset()
    
    # Exemples de requêtes
    afficher_exemples_requetes()
    
    # Requêtes images
    afficher_requetes_images()
    
    # Analyse difficulté
    afficher_analyse_difficulte()
    
    # Couverture
    afficher_couverture_dataset()
    
    print("\n" + "="*80)
    print("✅ Visualisation terminée")
    print("="*80)
    print("\n💡 Pour exécuter le benchmark complet:")
    print("   python benchmark_complet_opsemia.py")
    print("\n📖 Pour plus d'informations:")
    print("   cat README_BENCHMARK.md")
    print("="*80)


if __name__ == "__main__":
    main()

