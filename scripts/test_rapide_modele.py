#!/usr/bin/env python3
"""Script de test rapide pour un seul modèle.

Permet de tester rapidement un modèle sans exécuter tout le benchmark.
Utile pour le développement et le débogage.

Usage:
    python test_rapide_modele.py [nom_modele]
    
Exemples:
    python test_rapide_modele.py jina
    python test_rapide_modele.py bge
    python test_rapide_modele.py solon
    python test_rapide_modele.py qwen  # Nécessite DEEPINFRA_TOKEN
"""

import sys
import time
from pathlib import Path

# Ajouter le répertoire racine au path
racine_projet = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(racine_projet))

from sentence_transformers import SentenceTransformer
import numpy as np


# Modèles disponibles
MODELES = {
    "jina": {
        "id": "jinaai/jina-embeddings-v3",
        "nom": "Jina-v3",
        "trust_remote": True,
    },
    "solon": {
        "id": "OrdalieTech/Solon-embeddings-large-0.1",
        "nom": "Solon-large",
        "trust_remote": False,
    },
    "bge": {
        "id": "BAAI/bge-m3",
        "nom": "BGE-M3",
        "trust_remote": False,
    },
}


def tester_modele(nom_court: str):
    """Teste rapidement un modèle.
    
    Args:
        nom_court: Nom court du modèle (jina, bge, solon, qwen)
    """
    if nom_court not in MODELES:
        print(f"❌ Modèle '{nom_court}' inconnu")
        print(f"   Modèles disponibles: {', '.join(MODELES.keys())}")
        return
    
    modele_info = MODELES[nom_court]
    
    print("="*70)
    print(f"TEST RAPIDE - {modele_info['nom']}")
    print("="*70)
    print(f"ID: {modele_info['id']}")
    print()
    
    # Chargement
    print("⏳ Chargement du modèle...")
    debut = time.time()
    try:
        if modele_info['trust_remote']:
            modele = SentenceTransformer(modele_info['id'], trust_remote_code=True)
        else:
            modele = SentenceTransformer(modele_info['id'])
    except Exception as e:
        print(f"❌ Erreur chargement: {e}")
        print("\n💡 Conseil: Télécharger d'abord le modèle:")
        print(f"   python scripts/telecharger_modele_{nom_court}.py")
        return
    
    duree_chargement = time.time() - debut
    print(f"✅ Chargé en {duree_chargement:.2f}s")
    print(f"   Dimensions: {modele.get_sentence_embedding_dimension()}")
    print()
    
    # Test encodage simple
    print("⏳ Test encodage message simple...")
    texte_test = "Le produit est prêt pour la livraison. Qualité 99.1%"
    
    debut = time.time()
    embedding = modele.encode([texte_test], normalize_embeddings=True, show_progress_bar=False)[0]
    duree = time.time() - debut
    
    print(f"✅ Message encodé en {duree*1000:.2f}ms")
    print(f"   Dimension: {len(embedding)}")
    print(f"   Premiers éléments: {embedding[:5]}")
    print()
    
    # Test encodage batch
    print("⏳ Test encodage batch (100 messages)...")
    messages_test = [texte_test] * 100
    
    debut = time.time()
    embeddings_batch = modele.encode(messages_test, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
    duree_batch = time.time() - debut
    
    print(f"✅ Batch encodé en {duree_batch:.2f}s")
    print(f"   Débit: {100/duree_batch:.1f} messages/s")
    print(f"   Estimation 1000 msgs: {duree_batch*10:.1f}s")
    print()
    
    # Test similarité
    print("⏳ Test recherche de similarité...")
    requete = "livraison qualité produit"
    corpus = [
        "Le produit est prêt pour la livraison. Qualité 99.1%",
        "Salut, on se voit demain ?",
        "Production terminée, rendement excellent",
        "Pizza promotion 2 achetées 1 offerte",
        "Livraison effectuée mission accomplie",
    ]
    
    emb_requete = modele.encode([requete], normalize_embeddings=True, show_progress_bar=False)[0]
    emb_corpus = modele.encode(corpus, normalize_embeddings=True, show_progress_bar=False)
    
    # Calcul similarités
    similarites = np.dot(emb_corpus, emb_requete)
    indices_tries = np.argsort(-similarites)
    
    print(f"✅ Requête: '{requete}'")
    print(f"   Top 3 résultats:")
    for i, idx in enumerate(indices_tries[:3], 1):
        print(f"   {i}. [{similarites[idx]:.3f}] {corpus[idx][:50]}...")
    print()
    
    # Résumé
    print("="*70)
    print("✅ TEST RÉUSSI")
    print("="*70)
    print(f"Résumé {modele_info['nom']}:")
    print(f"  - Chargement: {duree_chargement:.2f}s")
    print(f"  - Encodage simple: {duree*1000:.2f}ms")
    print(f"  - Débit batch: {100/duree_batch:.1f} msg/s")
    print(f"  - Recherche: Fonctionne correctement")
    print()
    print("💡 Pour le benchmark complet:")
    print("   python scripts/benchmark_complet_opsemia.py")
    print("="*70)


def main():
    """Fonction principale."""
    if len(sys.argv) < 2:
        print("Usage: python test_rapide_modele.py [modele]")
        print()
        print("Modèles disponibles:")
        for nom, info in MODELES.items():
            print(f"  - {nom:<8} : {info['nom']}")
        print()
        print("Exemple:")
        print("  python test_rapide_modele.py jina")
        sys.exit(1)
    
    nom_modele = sys.argv[1].lower()
    tester_modele(nom_modele)


if __name__ == "__main__":
    main()

