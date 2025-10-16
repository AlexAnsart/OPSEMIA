#!/usr/bin/env python3
"""Script de nettoyage des fichiers temporaires du benchmark.

Supprime les collections ChromaDB temporaires créées pendant le benchmark.
Utile si le benchmark a été interrompu et que les collections n'ont pas été
nettoyées automatiquement.

Usage:
    python nettoyer_benchmark.py [--force]
"""

import shutil
import sys
from pathlib import Path

# Ajouter le répertoire racine au path
racine_projet = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(racine_projet))

CHEMIN_DB_BENCHMARK = racine_projet / "data" / "benchmark_temp"


def obtenir_taille_dossier(chemin: Path) -> float:
    """Calcule la taille d'un dossier en MB.
    
    Args:
        chemin: Chemin vers le dossier
        
    Returns:
        Taille en MB
    """
    if not chemin.exists():
        return 0.0
    
    taille_bytes = sum(
        f.stat().st_size 
        for f in chemin.rglob('*') 
        if f.is_file()
    )
    return taille_bytes / (1024 * 1024)


def lister_collections_temporaires() -> list:
    """Liste les collections temporaires du benchmark.
    
    Returns:
        Liste des noms de collections trouvées
    """
    if not CHEMIN_DB_BENCHMARK.exists():
        return []
    
    try:
        from src.backend.database.vector_db import BaseVectorielle
        
        db = BaseVectorielle(chemin_persistance=CHEMIN_DB_BENCHMARK)
        collections = db.client.list_collections()
        
        # Filtrer les collections de benchmark
        collections_benchmark = [
            col.name for col in collections 
            if col.name.startswith('benchmark_')
        ]
        
        return collections_benchmark
    except Exception as e:
        print(f"⚠️  Erreur lors de la liste des collections: {e}")
        return []


def nettoyer(force: bool = False):
    """Nettoie les fichiers temporaires du benchmark.
    
    Args:
        force: Si True, supprime sans confirmation
    """
    print("="*70)
    print("NETTOYAGE DES FICHIERS TEMPORAIRES DU BENCHMARK")
    print("="*70)
    
    if not CHEMIN_DB_BENCHMARK.exists():
        print("\n✅ Aucun fichier temporaire trouvé")
        print(f"   Dossier inexistant: {CHEMIN_DB_BENCHMARK}")
        return
    
    # Statistiques
    taille_mb = obtenir_taille_dossier(CHEMIN_DB_BENCHMARK)
    collections = lister_collections_temporaires()
    
    print(f"\n📁 Dossier temporaire: {CHEMIN_DB_BENCHMARK}")
    print(f"   Taille: {taille_mb:.2f} MB")
    
    if collections:
        print(f"\n🗄️  Collections temporaires trouvées ({len(collections)}):")
        for col in collections:
            print(f"   - {col}")
    else:
        print(f"\n📦 Aucune collection ChromaDB détectée")
    
    # Confirmation
    if not force:
        print("\n⚠️  Cette action va supprimer tous les fichiers temporaires du benchmark.")
        reponse = input("   Continuer? (oui/non): ").strip().lower()
        
        if reponse not in ['oui', 'o', 'yes', 'y']:
            print("\n❌ Annulation du nettoyage")
            return
    
    # Suppression
    print("\n🗑️  Suppression des fichiers temporaires...")
    try:
        shutil.rmtree(CHEMIN_DB_BENCHMARK)
        print(f"   ✅ {taille_mb:.2f} MB libérés")
        print(f"   ✅ {len(collections)} collection(s) supprimée(s)")
    except Exception as e:
        print(f"   ❌ Erreur lors de la suppression: {e}")
        return
    
    print("\n" + "="*70)
    print("✅ NETTOYAGE TERMINÉ")
    print("="*70)
    print("\n💡 Les fichiers temporaires seront automatiquement recréés")
    print("   lors de la prochaine exécution du benchmark.")


def main():
    """Fonction principale."""
    force = '--force' in sys.argv or '-f' in sys.argv
    
    if '--help' in sys.argv or '-h' in sys.argv:
        print("Usage: python nettoyer_benchmark.py [OPTIONS]")
        print()
        print("Options:")
        print("  --force, -f    Supprimer sans confirmation")
        print("  --help, -h     Afficher cette aide")
        print()
        print("Description:")
        print("  Supprime les collections ChromaDB temporaires créées pendant")
        print("  le benchmark. Utile si le benchmark a été interrompu.")
        print()
        print("Exemples:")
        print("  python nettoyer_benchmark.py          # Avec confirmation")
        print("  python nettoyer_benchmark.py --force  # Sans confirmation")
        return
    
    nettoyer(force=force)


if __name__ == "__main__":
    main()

