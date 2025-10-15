#!/usr/bin/env python3
"""Script pour télécharger et pré-cacher le modèle Jina-embeddings-v3.

Ce script télécharge le modèle Jina-embeddings-v3 depuis Hugging Face et le met en cache
pour éviter le téléchargement lors du premier usage de l'application.

Jina-embeddings-v3 est un modèle multilingue optimisé pour la recherche et la récupération
d'informations.
"""

import io
import sys
from pathlib import Path

# Forcer UTF-8 pour la sortie console (nécessaire pour les emojis sur Windows)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ajouter le répertoire racine au path pour les imports
racine_projet = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(racine_projet))

from sentence_transformers import SentenceTransformer


def telecharger_modele_jina():
    """Télécharge et met en cache le modèle Jina-embeddings-v3."""
    id_modele = "jinaai/jina-embeddings-v3"
    
    print(f"Téléchargement du modèle {id_modele}...")
    print("Cela peut prendre plusieurs minutes selon votre connexion...")
    
    try:
        # Le téléchargement se fait automatiquement lors de l'instanciation
        modele = SentenceTransformer(id_modele, trust_remote_code=True)
        
        # Test rapide pour vérifier que le modèle fonctionne
        texte_test = "Test du modèle Jina-embeddings-v3"
        embedding = modele.encode([texte_test], normalize_embeddings=True)
        
        print(f"✅ Modèle téléchargé avec succès!")
        print(f"   - ID: {id_modele}")
        print(f"   - Dimensions: {modele.get_sentence_embedding_dimension()}")
        print(f"   - Test embedding: {embedding.shape}")
        
    except Exception as e:
        print(f"❌ Erreur lors du téléchargement: {e}")
        print("\n💡 Suggestions:")
        print("   - Vérifiez votre connexion internet")
        print("   - Assurez-vous d'avoir assez d'espace disque")
        print("   - Vérifiez que transformers est à jour: pip install --upgrade transformers")
        return False
    
    return True


if __name__ == "__main__":
    print("=== Téléchargement du modèle Jina-embeddings-v3 ===")
    succes = telecharger_modele_jina()
    
    if succes:
        print("\n🎉 Le modèle est maintenant prêt à être utilisé!")
        print("Configurez-le dans config/settings.py:")
        print('   ID_MODELE_EMBEDDING = "jinaai/jina-embeddings-v3"')
    else:
        print("\n💥 Échec du téléchargement.")
        sys.exit(1)

