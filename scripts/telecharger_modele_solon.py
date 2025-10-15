#!/usr/bin/env python3
"""Script pour télécharger et pré-cacher le modèle Solon-embeddings-large-0.1.

Ce script télécharge le modèle Solon-embeddings-large depuis Hugging Face et le met en cache
pour éviter le téléchargement lors du premier usage de l'application.

⚠️  ATTENTION: L'ID exact du modèle doit être vérifié sur Hugging Face.
Les IDs possibles testés:
- OrdalieTech/Solon-embeddings-large-0.1
- OrdalieTech/Solon-embeddings-large
"""

import sys
from pathlib import Path

# Ajouter le répertoire racine au path pour les imports
racine_projet = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(racine_projet))

from sentence_transformers import SentenceTransformer


def telecharger_modele_solon():
    """Télécharge et met en cache le modèle Solon-embeddings-large."""
    # IDs possibles à tester dans l'ordre
    ids_possibles = [
        "OrdalieTech/Solon-embeddings-large-0.1",
        "OrdalieTech/Solon-embeddings-large",
        "Solon-embeddings-large-0.1",
    ]
    
    for id_modele in ids_possibles:
        print(f"\n🔍 Tentative avec: {id_modele}...")
        
        try:
            # Le téléchargement se fait automatiquement lors de l'instanciation
            modele = SentenceTransformer(id_modele, trust_remote_code=True)
            
            # Test rapide pour vérifier que le modèle fonctionne
            texte_test = "Test du modèle Solon-embeddings-large"
            embedding = modele.encode([texte_test], normalize_embeddings=True)
            
            print(f"✅ Modèle téléchargé avec succès!")
            print(f"   - ID: {id_modele}")
            print(f"   - Dimensions: {modele.get_sentence_embedding_dimension()}")
            print(f"   - Test embedding: {embedding.shape}")
            
            return True, id_modele
            
        except Exception as e:
            print(f"❌ Échec avec {id_modele}: {str(e)[:100]}")
            continue
    
    print("\n💥 Aucun ID de modèle n'a fonctionné.")
    print("\n💡 Suggestions:")
    print("   1. Recherchez 'Solon-embeddings' sur https://huggingface.co/models")
    print("   2. Vérifiez le nom exact du modèle")
    print("   3. Assurez-vous que le modèle est public et accessible")
    return False, None


if __name__ == "__main__":
    print("=== Téléchargement du modèle Solon-embeddings-large ===")
    succes, id_trouve = telecharger_modele_solon()
    
    if succes:
        print("\n🎉 Le modèle est maintenant prêt à être utilisé!")
        print("Configurez-le dans config/settings.py:")
        print(f'   ID_MODELE_EMBEDDING = "{id_trouve}"')
    else:
        print("\n💥 Échec du téléchargement.")
        print("Veuillez vérifier le nom du modèle et réessayer.")
        sys.exit(1)

