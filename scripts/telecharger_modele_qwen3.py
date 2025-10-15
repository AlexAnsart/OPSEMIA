#!/usr/bin/env python3
"""Script pour télécharger et pré-cacher le modèle Qwen3-Embedding-8B.

Ce script télécharge le modèle Qwen3-Embedding-8B depuis Hugging Face et le met en cache
pour éviter le téléchargement lors du premier usage de l'application.

ATTENTION: Ce modèle est volumineux (~8GB). Assurez-vous d'avoir suffisamment d'espace disque
et de mémoire GPU/RAM disponible.
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


def telecharger_modele_qwen3():
    """Télécharge et met en cache le modèle Qwen3-Embedding-8B."""
    id_modele = "Qwen/Qwen3-Embedding-8B"
    
    print(f"Téléchargement du modèle {id_modele}...")
    print("⚠️  ATTENTION: Ce modèle fait ~8GB et nécessite beaucoup de RAM/VRAM")
    print("Cela peut prendre 10-30 minutes selon votre connexion...")
    
    try:
        # Le téléchargement se fait automatiquement lors de l'instanciation
        modele = SentenceTransformer(id_modele)
        
        # Test rapide pour vérifier que le modèle fonctionne
        texte_test = "Test du modèle Qwen3-Embedding-8B"
        embedding = modele.encode([texte_test], normalize_embeddings=True)
        
        print(f"✅ Modèle téléchargé avec succès!")
        print(f"   - ID: {id_modele}")
        print(f"   - Dimensions: {modele.get_sentence_embedding_dimension()}")
        print(f"   - Test embedding: {embedding.shape}")
        
    except Exception as e:
        print(f"❌ Erreur lors du téléchargement: {e}")
        print("\n💡 Suggestions:")
        print("   - Vérifiez votre connexion internet")
        print("   - Assurez-vous d'avoir assez d'espace disque (~8GB)")
        print("   - Vérifiez que transformers est à jour: pip install --upgrade transformers")
        return False
    
    return True


if __name__ == "__main__":
    print("=== Téléchargement du modèle Qwen3-Embedding-8B ===")
    succes = telecharger_modele_qwen3()
    
    if succes:
        print("\n🎉 Le modèle est maintenant prêt à être utilisé!")
        print("Configurez-le dans config/settings.py:")
        print('   ID_MODELE_EMBEDDING = "Qwen/Qwen3-Embedding-8B"')
    else:
        print("\n💥 Échec du téléchargement.")
        sys.exit(1)

