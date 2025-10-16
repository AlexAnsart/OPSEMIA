"""Script de debug pour tester le filtrage par direction."""

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

# Nom de la collection à tester
nom_collection = "messages"

print(f"=== DEBUG FILTRAGE DIRECTION ===")
print(f"Collection: {nom_collection}")

# 1. Compter le nombre total de documents
try:
    total = db.compter_documents(nom_collection)
    print(f"\n1. Nombre total de documents: {total}")
except Exception as e:
    print(f"\n❌ Erreur: {e}")
    sys.exit(1)

# 2. Récupérer quelques documents pour voir la structure
print(f"\n2. Échantillon de documents (premiers 5):")
try:
    collection = db.client.get_collection(nom_collection)
    resultats = collection.get(limit=5, include=["metadatas", "documents"])
    
    for i, (doc, meta) in enumerate(zip(resultats["documents"], resultats["metadatas"])):
        print(f"\n   Document {i+1}:")
        print(f"      direction: {meta.get('direction', 'ABSENT')}")
        print(f"      is_noise: {meta.get('is_noise', 'ABSENT')}")
        print(f"      type: {meta.get('type', 'ABSENT')}")
        print(f"      timestamp: {meta.get('timestamp', 'ABSENT')[:19] if meta.get('timestamp') else 'ABSENT'}")
        print(f"      message: {doc[:80]}...")
except Exception as e:
    print(f"   ❌ Erreur: {e}")

# 3. Compter les messages par direction
print(f"\n3. Comptage par direction:")

# Incoming
try:
    collection = db.client.get_collection(nom_collection)
    
    # Test avec filtre simple
    resultats_incoming = collection.get(
        where={"direction": "incoming"},
        limit=10000,
        include=["metadatas"]
    )
    nb_incoming = len(resultats_incoming["ids"])
    print(f"   Messages 'incoming' (filtre simple): {nb_incoming}")
    
    # Afficher quelques exemples
    if nb_incoming > 0:
        print(f"   Exemples (3 premiers):")
        for i, meta in enumerate(resultats_incoming["metadatas"][:3]):
            print(f"      - direction={meta.get('direction')}, is_noise={meta.get('is_noise')}")
except Exception as e:
    print(f"   ❌ Erreur incoming: {e}")
    import traceback
    traceback.print_exc()

# Outgoing
try:
    resultats_outgoing = collection.get(
        where={"direction": "outgoing"},
        limit=10000,
        include=["metadatas"]
    )
    nb_outgoing = len(resultats_outgoing["ids"])
    print(f"   Messages 'outgoing' (filtre simple): {nb_outgoing}")
    
    # Afficher quelques exemples
    if nb_outgoing > 0:
        print(f"   Exemples (3 premiers):")
        for i, meta in enumerate(resultats_outgoing["metadatas"][:3]):
            print(f"      - direction={meta.get('direction')}, is_noise={meta.get('is_noise')}")
except Exception as e:
    print(f"   ❌ Erreur outgoing: {e}")
    import traceback
    traceback.print_exc()

# 4. Test avec filtre combiné (direction + is_noise)
print(f"\n4. Test filtre combiné (direction + is_noise=False):")
try:
    # Test avec $and
    resultats_and = collection.get(
        where={
            "$and": [
                {"direction": "incoming"},
                {"is_noise": False}
            ]
        },
        limit=10000,
        include=["metadatas"]
    )
    nb_and = len(resultats_and["ids"])
    print(f"   Avec $and: {nb_and} résultats")
    
    # Test sans $and (dict simple)
    resultats_simple = collection.get(
        where={
            "direction": "incoming",
            "is_noise": False
        },
        limit=10000,
        include=["metadatas"]
    )
    nb_simple = len(resultats_simple["ids"])
    print(f"   Sans $and (dict simple): {nb_simple} résultats")
    
except Exception as e:
    print(f"   ❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

# 5. Test de recherche vectorielle avec filtre
print(f"\n5. Test recherche vectorielle avec filtre direction:")
from src.backend.models.model_manager import obtenir_encodeur_texte

encodeur = obtenir_encodeur_texte()
requete = "rendez-vous"
embedding_requete = encodeur.encoder([requete])[0].tolist()

try:
    # Sans filtre
    resultats_sans = collection.query(
        query_embeddings=[embedding_requete],
        n_results=10,
        include=["metadatas", "documents", "distances"]
    )
    print(f"   Sans filtre: {len(resultats_sans['ids'][0])} résultats")
    
    # Avec filtre incoming
    resultats_incoming = collection.query(
        query_embeddings=[embedding_requete],
        n_results=10,
        where={"direction": "incoming"},
        include=["metadatas", "documents", "distances"]
    )
    print(f"   Avec filtre 'incoming': {len(resultats_incoming['ids'][0])} résultats")
    if len(resultats_incoming['ids'][0]) > 0:
        print(f"      Premier résultat: direction={resultats_incoming['metadatas'][0][0].get('direction')}")
    
    # Avec filtre outgoing
    resultats_outgoing = collection.query(
        query_embeddings=[embedding_requete],
        n_results=10,
        where={"direction": "outgoing"},
        include=["metadatas", "documents", "distances"]
    )
    print(f"   Avec filtre 'outgoing': {len(resultats_outgoing['ids'][0])} résultats")
    if len(resultats_outgoing['ids'][0]) > 0:
        print(f"      Premier résultat: direction={resultats_outgoing['metadatas'][0][0].get('direction')}")
    
except Exception as e:
    print(f"   ❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

print(f"\n=== FIN DEBUG ===")

