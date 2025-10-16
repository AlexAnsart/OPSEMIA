"""Script pour lister toutes les collections disponibles."""

import sys
from pathlib import Path

# Ajouter le répertoire racine au path
racine_projet = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(racine_projet))

from config.settings import obtenir_parametres
from src.backend.database.vector_db import BaseVectorielle

# Initialiser
parametres = obtenir_parametres()
db = BaseVectorielle(parametres.CHEMIN_BASE_CHROMA)

print("=== COLLECTIONS DISPONIBLES ===\n")

# Utiliser l'API ChromaDB directement
collections = db.client.list_collections()

if not collections:
    print("Aucune collection trouvée.")
else:
    for col in collections:
        nom = col.name
        nb_docs = col.count()
        print(f"📁 {nom}")
        print(f"   Documents: {nb_docs}")
        
        # Afficher un échantillon de métadonnées
        try:
            resultats = col.get(limit=2, include=["metadatas"])
            
            if resultats["metadatas"]:
                print(f"   Métadonnées échantillon:")
                meta = resultats["metadatas"][0]
                for cle in sorted(meta.keys()):
                    valeur = meta[cle]
                    if isinstance(valeur, str) and len(valeur) > 50:
                        valeur = valeur[:50] + "..."
                    print(f"      • {cle}: {valeur}")
        except Exception as e:
            print(f"   ⚠️ Erreur lecture métadonnées: {e}")
        
        print()

print("=" * 40)
