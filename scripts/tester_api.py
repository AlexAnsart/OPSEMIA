"""Script de test et démonstration de l'API OPSEMIA.

Teste toutes les routes de l'API et vérifie leur bon fonctionnement.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any, Dict

import requests

# Configuration de l'API
API_URL = "http://127.0.0.1:5000"

# Ajouter le répertoire racine au path
racine_projet = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(racine_projet))


def tester_endpoint(
    nom: str,
    methode: str,
    endpoint: str,
    data: Dict[str, Any] | None = None,
    params: Dict[str, Any] | None = None,
) -> None:
    """Teste un endpoint de l'API et affiche le résultat.

    Args:
        nom: Nom descriptif du test
        methode: Méthode HTTP (GET, POST, etc.)
        endpoint: Chemin de l'endpoint
        data: Données JSON pour POST (optionnel)
        params: Paramètres de requête pour GET (optionnel)
    """
    print(f"\n{'='*70}")
    print(f"🧪 Test: {nom}")
    print(f"{'='*70}")
    print(f"   {methode} {endpoint}")
    
    if data:
        print(f"   Données: {data}")
    
    try:
        url = f"{API_URL}{endpoint}"
        
        if methode == "GET":
            response = requests.get(url, params=params)
        elif methode == "POST":
            response = requests.post(url, json=data)
        else:
            print(f"❌ Méthode {methode} non supportée")
            return
        
        print(f"\n   Statut: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Succès")
            result = response.json()
            print(f"   Réponse: {result}")
        else:
            print(f"   ❌ Échec")
            print(f"   Réponse: {response.text}")
    
    except Exception as e:
        print(f"   ❌ Erreur: {e}")


def executer_tests_complets() -> None:
    """Exécute une suite complète de tests sur l'API."""
    print("\n" + "="*70)
    print("🚀 OPSEMIA - Tests de l'API")
    print("="*70)
    print("⚠️  Assurez-vous que le serveur Flask est démarré sur http://127.0.0.1:5000")
    print("   Lancez: python src/backend/app.py")
    print("="*70)
    
    input("\nAppuyez sur Entrée pour commencer les tests...")
    
    # Test 1: Santé de l'API
    tester_endpoint(
        "Vérification de santé",
        "GET",
        "/api/health"
    )
    
    time.sleep(0.5)
    
    # Test 2: Liste des collections
    tester_endpoint(
        "Liste des collections",
        "GET",
        "/api/collections"
    )
    
    time.sleep(0.5)
    
    # Test 3: Statistiques
    tester_endpoint(
        "Statistiques d'indexation",
        "GET",
        "/api/stats"
    )
    
    time.sleep(0.5)
    
    # Test 4: Configuration actuelle
    tester_endpoint(
        "Configuration actuelle",
        "GET",
        "/api/config"
    )
    
    time.sleep(0.5)
    
    # Test 5: Recherche sémantique (nécessite des données indexées)
    tester_endpoint(
        "Recherche sémantique",
        "POST",
        "/api/search",
        data={
            "requete": "rendez-vous argent",
            "nom_collection": "messages_cas1",
            "nombre_resultats": 5,
            "exclure_bruit": True
        }
    )
    
    time.sleep(0.5)
    
    # Test 6: Recherche avec filtres temporels
    tester_endpoint(
        "Recherche avec filtre temporel",
        "POST",
        "/api/search",
        data={
            "requete": "transfert",
            "nom_collection": "messages_cas1",
            "nombre_resultats": 3,
            "filtres": {
                "timestamp_debut": "2025-01-01",
                "timestamp_fin": "2025-12-31"
            }
        }
    )
    
    time.sleep(0.5)
    
    # Test 7: Obtenir un message spécifique
    tester_endpoint(
        "Obtenir un message par ID",
        "GET",
        "/api/message/SM0447",
        params={"collection": "messages_cas1"}
    )
    
    time.sleep(0.5)
    
    # Test 8: Contexte d'un message
    tester_endpoint(
        "Contexte d'un message",
        "GET",
        "/api/context/SM0447",
        params={
            "collection": "messages_cas1",
            "fenetre_avant": 3,
            "fenetre_apres": 3
        }
    )
    
    print("\n" + "="*70)
    print("✅ Tests terminés!")
    print("="*70)


if __name__ == "__main__":
    executer_tests_complets()

