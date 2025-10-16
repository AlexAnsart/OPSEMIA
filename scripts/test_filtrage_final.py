"""Test final du filtrage par direction après correction."""

import sys
from pathlib import Path

# Ajouter le répertoire racine au path
racine_projet = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(racine_projet))

from config.settings import obtenir_parametres
from src.backend.core.search_engine import MoteurRecherche
from src.backend.database.vector_db import BaseVectorielle

# Initialiser
parametres = obtenir_parametres()
db = BaseVectorielle(parametres.CHEMIN_BASE_CHROMA)
moteur = MoteurRecherche(db, parametres)

print("=== TEST FILTRAGE DIRECTION APRÈS CORRECTION ===\n")

# Test 1: Recherche SANS filtre
print("1️⃣  Recherche SANS filtre:")
resultats_sans = moteur.rechercher(
    requete="rendez-vous",
    nom_collection="messages",
    filtres=None,
    nombre_resultats=10,
    exclure_bruit=True
)
print(f"   Résultats: {len(resultats_sans)}")
if resultats_sans:
    directions = [r["metadata"]["direction"] for r in resultats_sans[:5]]
    print(f"   Directions (5 premiers): {directions}")

# Test 2: Recherche avec filtre INCOMING uniquement
print("\n2️⃣  Recherche avec filtre INCOMING (+ exclure_bruit=True):")
resultats_incoming = moteur.rechercher(
    requete="rendez-vous",
    nom_collection="messages",
    filtres={"direction": "incoming"},
    nombre_resultats=10,
    exclure_bruit=True
)
print(f"   Résultats: {len(resultats_incoming)}")
if resultats_incoming:
    directions = [r["metadata"]["direction"] for r in resultats_incoming[:5]]
    print(f"   Directions (5 premiers): {directions}")
    # Vérifier qu'on a bien QUE des incoming
    all_incoming = all(r["metadata"]["direction"] == "incoming" for r in resultats_incoming)
    print(f"   ✅ Tous incoming: {all_incoming}")

# Test 3: Recherche avec filtre OUTGOING uniquement
print("\n3️⃣  Recherche avec filtre OUTGOING (+ exclure_bruit=True):")
resultats_outgoing = moteur.rechercher(
    requete="rendez-vous",
    nom_collection="messages",
    filtres={"direction": "outgoing"},
    nombre_resultats=10,
    exclure_bruit=True
)
print(f"   Résultats: {len(resultats_outgoing)}")
if resultats_outgoing:
    directions = [r["metadata"]["direction"] for r in resultats_outgoing[:5]]
    print(f"   Directions (5 premiers): {directions}")
    # Vérifier qu'on a bien QUE des outgoing
    all_outgoing = all(r["metadata"]["direction"] == "outgoing" for r in resultats_outgoing)
    print(f"   ✅ Tous outgoing: {all_outgoing}")

# Test 4: Recherche avec filtre direction + temporel
print("\n4️⃣  Recherche avec filtre INCOMING + période temporelle:")
resultats_combo = moteur.rechercher(
    requete="rendez-vous",
    nom_collection="messages",
    filtres={
        "$and": [
            {"timestamp": {"$gte": "2010-03-01"}},
            {"timestamp": {"$lte": "2010-04-01"}},
            {"direction": "incoming"}
        ]
    },
    nombre_resultats=10,
    exclure_bruit=True
)
print(f"   Résultats: {len(resultats_combo)}")
if resultats_combo:
    directions = [r["metadata"]["direction"] for r in resultats_combo[:5]]
    timestamps = [r["metadata"]["timestamp"][:10] for r in resultats_combo[:5]]
    print(f"   Directions (5 premiers): {directions}")
    print(f"   Timestamps (5 premiers): {timestamps}")

print("\n=== RÉSUMÉ ===")
print(f"✅ Sans filtre: {len(resultats_sans)} résultats")
print(f"✅ Incoming seulement: {len(resultats_incoming)} résultats")
print(f"✅ Outgoing seulement: {len(resultats_outgoing)} résultats")
print(f"✅ Incoming + période: {len(resultats_combo)} résultats")

if len(resultats_incoming) > 0 and len(resultats_outgoing) > 0:
    print("\n🎉 SUCCÈS ! Le filtrage par direction fonctionne correctement !")
else:
    print("\n❌ ÉCHEC : Le filtrage ne retourne pas de résultats")

