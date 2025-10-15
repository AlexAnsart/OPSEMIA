#!/usr/bin/env python3
"""Script pour télécharger et pré-cacher le modèle BGE-M3.

Ce script télécharge le modèle BGE-M3 depuis Hugging Face et le met en cache
pour éviter le téléchargement lors du premier usage de l'application.
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
from config.settings import obtenir_parametres


def telecharger_modele_bge():
    """Télécharge et met en cache le modèle BGE-M3 configuré."""
    parametres = obtenir_parametres()
    id_modele = parametres.ID_MODELE_EMBEDDING
    
    print(f"Téléchargement du modèle {id_modele}...")
    print("Cela peut prendre plusieurs minutes (modèle ~2.2GB)...")
    
    try:
        # Le téléchargement se fait automatiquement lors de l'instanciation
        modele = SentenceTransformer(id_modele)
        
        # Test rapide pour vérifier que le modèle fonctionne
        texte_test = "Test du modèle BGE-M3"
        embedding = modele.encode([texte_test], normalize_embeddings=True)
        
        print(f"✅ Modèle téléchargé avec succès!")
        print(f"   - ID: {id_modele}")
        print(f"   - Dimensions: {modele.get_sentence_embedding_dimension()}")
        print(f"   - Cache: {modele._modules['0'].auto_model.config.name_or_path}")
        print(f"   - Test embedding: {embedding.shape}")
        
    except Exception as e:
        print(f"❌ Erreur lors du téléchargement: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("=== Téléchargement du modèle BGE-M3 ===")
    succes = telecharger_modele_bge()
    
    if succes:
        print("\n🎉 Le modèle est maintenant prêt à être utilisé!")
        print("Vous pouvez lancer l'application sans attendre le téléchargement.")
    else:
        print("\n💥 Échec du téléchargement. Vérifiez votre connexion internet.")
        sys.exit(1)
