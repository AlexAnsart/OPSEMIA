#!/usr/bin/env python3
"""Script de validation du système de benchmark.

Vérifie que tous les composants sont prêts avant d'exécuter le benchmark complet.
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire racine au path
racine_projet = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(racine_projet))

# Charger les variables d'environnement depuis .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv non installé, impossible de charger .env automatiquement")
    print("   Installation: pip install python-dotenv")


def verifier_fichiers():
    """Vérifie que tous les fichiers nécessaires existent."""
    print("📁 Vérification des fichiers...")
    
    fichiers_requis = [
        racine_projet / "Cas" / "Cas4" / "sms.csv",
        racine_projet / "Cas" / "Cas4" / "images.csv",
        racine_projet / "scripts" / "donnees_benchmark_opsemia.py",
        racine_projet / "scripts" / "benchmark_complet_opsemia.py",
    ]
    
    dossiers_requis = [
        racine_projet / "Cas" / "Cas4" / "Images",
        racine_projet / "Docs Projet",
    ]
    
    erreurs = []
    
    for fichier in fichiers_requis:
        if not fichier.exists():
            erreurs.append(f"❌ Fichier manquant: {fichier}")
        else:
            print(f"   ✓ {fichier.name}")
    
    for dossier in dossiers_requis:
        if not dossier.exists():
            erreurs.append(f"❌ Dossier manquant: {dossier}")
        else:
            nb_fichiers = len(list(dossier.glob("*")))
            print(f"   ✓ {dossier.name}/ ({nb_fichiers} fichiers)")
    
    return erreurs


def verifier_dependances():
    """Vérifie que les dépendances Python sont installées."""
    print("\n📦 Vérification des dépendances...")
    
    dependances = [
        ("numpy", "numpy"),
        ("sentence_transformers", "sentence-transformers"),
        ("PIL", "Pillow"),
        ("transformers", "transformers"),
        ("requests", "requests"),
        ("chromadb", "chromadb"),
    ]
    
    erreurs = []
    
    for module, package in dependances:
        try:
            __import__(module)
            print(f"   ✓ {package}")
        except ImportError:
            erreurs.append(f"❌ Package manquant: {package}")
            erreurs.append(f"   Installation: pip install {package}")
    
    return erreurs


def verifier_configuration():
    """Vérifie la configuration."""
    print("\n⚙️  Vérification de la configuration...")
    
    erreurs = []
    
    # Vérifier fichier .env
    chemin_env = racine_projet / ".env"
    print(f"\n   🔍 Débogage .env:")
    print(f"      Racine projet: {racine_projet}")
    print(f"      Fichier .env attendu: {chemin_env}")
    print(f"      Fichier .env existe: {chemin_env.exists()}")
    
    if chemin_env.exists():
        print(f"      Taille .env: {chemin_env.stat().st_size} octets")
        # Lire le contenu (masqué)
        try:
            with open(chemin_env, 'r') as f:
                contenu = f.read()
                if "DEEPINFRA_TOKEN" in contenu:
                    print(f"      ✓ Variable DEEPINFRA_TOKEN trouvée dans .env")
                else:
                    print(f"      ⚠️  Variable DEEPINFRA_TOKEN absente du .env")
        except Exception as e:
            print(f"      ⚠️  Erreur lecture .env: {e}")
    
    # Vérifier clé API
    deepinfra_token = os.getenv("DEEPINFRA_TOKEN")
    print(f"      os.getenv('DEEPINFRA_TOKEN'): {'***' + deepinfra_token[-10:] if deepinfra_token else 'None'}")
    
    if not deepinfra_token:
        erreurs.append("⚠️  DEEPINFRA_TOKEN non configuré dans les variables d'environnement")
        erreurs.append("   Créer un fichier .env à la racine avec: DEEPINFRA_TOKEN=votre_clé")
        erreurs.append(f"   Ou définir la variable: export DEEPINFRA_TOKEN=votre_clé")
    else:
        cle_masquee = deepinfra_token[:10] + "..." + deepinfra_token[-5:] if len(deepinfra_token) > 15 else "***"
        print(f"   ✓ DEEPINFRA_TOKEN configuré: {cle_masquee}")
    
    # Vérifier imports projet
    try:
        from config.settings import obtenir_parametres
        parametres = obtenir_parametres()
        print(f"   ✓ Configuration OPSEMIA chargée")
        print(f"      Modèle actuel: {parametres.ID_MODELE_EMBEDDING}")
    except Exception as e:
        erreurs.append(f"❌ Erreur chargement config: {e}")
    
    return erreurs


def verifier_dataset_benchmark():
    """Vérifie le dataset de benchmark."""
    print("\n🎯 Vérification du dataset de benchmark...")
    
    erreurs = []
    
    try:
        from scripts.donnees_benchmark_opsemia import (
            obtenir_requetes_messages,
            obtenir_requetes_images,
        )
        
        requetes_messages = obtenir_requetes_messages()
        requetes_images = obtenir_requetes_images()
        
        print(f"   ✓ {len(requetes_messages)} requêtes messages")
        print(f"   ✓ {len(requetes_images)} requêtes images")
        
        # Vérifier requêtes images complétées
        requetes_non_completees = sum(
            1 for req, _, _ in requetes_images 
            if "[REQUETE_A_COMPLETER]" in req
        )
        
        if requetes_non_completees > 0:
            erreurs.append(f"⚠️  {requetes_non_completees} requêtes images non complétées")
            erreurs.append("   Éditer scripts/donnees_benchmark_opsemia.py")
        else:
            print(f"   ✓ Toutes les requêtes images sont complétées")
        
        # Vérifier format
        for i, (req, ids, diff) in enumerate(requetes_messages[:3]):
            if not req or not ids or diff not in ["facile", "moyen", "difficile"]:
                erreurs.append(f"❌ Requête message {i+1} mal formatée")
        
        print(f"   ✓ Format du dataset valide")
        
    except Exception as e:
        erreurs.append(f"❌ Erreur chargement dataset: {e}")
    
    return erreurs


def verifier_espace_disque():
    """Vérifie l'espace disque disponible."""
    print("\n💾 Vérification de l'espace disque...")
    
    erreurs = []
    
    try:
        import shutil
        stat = shutil.disk_usage(racine_projet)
        
        gb_disponible = stat.free / (1024**3)
        gb_total = stat.total / (1024**3)
        
        print(f"   Espace disponible: {gb_disponible:.1f} GB / {gb_total:.1f} GB")
        
        if gb_disponible < 10:
            erreurs.append(f"⚠️  Espace disque faible: {gb_disponible:.1f} GB")
            erreurs.append("   Recommandé: au moins 10 GB pour les modèles")
        else:
            print(f"   ✓ Espace disque suffisant")
        
    except Exception as e:
        erreurs.append(f"⚠️  Impossible de vérifier l'espace disque: {e}")
    
    return erreurs


def afficher_estimation_temps():
    """Affiche une estimation du temps d'exécution."""
    print("\n⏱️  Estimation du temps d'exécution:")
    print("   - Calcul des durées: ~5-10 minutes")
    print("   - Modèles locaux (×3): ~15-30 minutes")
    print("   - Qwen3-8B via API: ~20-30 minutes")
    print("   - Total estimé: ~40-70 minutes")
    print("\n   💡 Conseils:")
    print("   - Exécuter pendant une pause")
    print("   - Vérifier la connexion Internet (pour API)")
    print("   - GPU recommandé pour les modèles locaux")


def main():
    """Fonction principale de validation."""
    print("="*80)
    print("VALIDATION DU SYSTÈME DE BENCHMARK OPSEMIA")
    print("="*80)
    
    toutes_erreurs = []
    
    # Vérifications
    toutes_erreurs.extend(verifier_fichiers())
    toutes_erreurs.extend(verifier_dependances())
    toutes_erreurs.extend(verifier_configuration())
    toutes_erreurs.extend(verifier_dataset_benchmark())
    toutes_erreurs.extend(verifier_espace_disque())
    
    # Afficher estimation
    afficher_estimation_temps()
    
    # Résumé
    print("\n" + "="*80)
    if toutes_erreurs:
        print("❌ VALIDATION ÉCHOUÉE")
        print("="*80)
        print("\nErreurs et avertissements:")
        for erreur in toutes_erreurs:
            print(f"  {erreur}")
        print("\n💡 Corrigez les erreurs avant d'exécuter le benchmark.")
    else:
        print("✅ VALIDATION RÉUSSIE")
        print("="*80)
        print("\n🚀 Le système est prêt pour le benchmark!")
        print("\nPour lancer le benchmark complet:")
        print("   python scripts/benchmark_complet_opsemia.py")
        print("\nPour visualiser le dataset:")
        print("   python scripts/afficher_dataset_benchmark.py")
    
    print("="*80)
    
    return len(toutes_erreurs)


if __name__ == "__main__":
    exit_code = main()
    sys.exit(0 if exit_code == 0 else 1)

