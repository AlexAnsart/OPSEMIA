"""Routes API pour la recherche sémantique."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

from flask import Blueprint, jsonify, request

# Ajouter le répertoire racine au path pour les imports
racine_projet = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(racine_projet))

from config.settings import obtenir_parametres
from src.backend.core.filters import (
    combiner_filtres,
    creer_filtre_direction,
    creer_filtre_geographique,
    creer_filtre_temporel,
)
from src.backend.core.search_engine import MoteurRecherche
from src.backend.database.vector_db import BaseVectorielle

# Blueprint pour les routes de recherche
bp_recherche = Blueprint("recherche", __name__, url_prefix="/api")


@bp_recherche.route("/search", methods=["POST"])
def rechercher() -> tuple[Dict[str, Any], int]:
    """Recherche sémantique dans une collection avec filtres optionnels.

    Body JSON attendu:
        {
            "requete": "rendez-vous argent",      # Requis
            "nom_collection": "messages_cas1",    # Requis
            "nombre_resultats": 10,               # Optionnel
            "exclure_bruit": true,                # Optionnel
            "filtres": {                          # Optionnel
                "timestamp_debut": "2024-01-01",
                "timestamp_fin": "2024-12-31",
                "direction": "incoming",
                "gps_lat": 48.8566,
                "gps_lon": 2.3522,
                "rayon_km": 10
            }
        }

    Returns:
        JSON avec liste de résultats et leurs scores
    """
    try:
        data = request.get_json()
        
        if not data or "requete" not in data or "nom_collection" not in data:
            return jsonify({
                "succes": False,
                "erreur": "Les champs 'requete' et 'nom_collection' sont requis"
            }), 400
        
        requete = data["requete"]
        nom_collection = data["nom_collection"]
        nombre_resultats = data.get("nombre_resultats", None)
        exclure_bruit = data.get("exclure_bruit", None)
        filtres_data = data.get("filtres", {})
        
        # Construire les filtres ChromaDB
        filtres = _construire_filtres(filtres_data)
        
        # Initialiser le moteur de recherche
        parametres = obtenir_parametres()
        db = BaseVectorielle(parametres.CHEMIN_BASE_CHROMA)
        moteur = MoteurRecherche(db, parametres)
        
        # Effectuer la recherche
        resultats = moteur.rechercher(
            requete=requete,
            nom_collection=nom_collection,
            filtres=filtres if filtres else None,
            nombre_resultats=nombre_resultats,
            exclure_bruit=exclure_bruit,
        )
        
        # DEBUG: Logger les résultats
        print(f"\n=== RECHERCHE API ===")
        print(f"Requête: {requete}")
        print(f"Collection: {nom_collection}")
        print(f"Nombre résultats demandés: {nombre_resultats}")
        print(f"Exclure bruit: {exclure_bruit}")
        print(f"Filtres: {filtres}")
        print(f"Nombre de résultats trouvés: {len(resultats)}")
        if resultats:
            print(f"Premier résultat: {resultats[0]}")
        print(f"=====================\n")
        
        return jsonify({
            "succes": True,
            "nombre_resultats": len(resultats),
            "resultats": resultats
        }), 200
        
    except Exception as e:
        return jsonify({
            "succes": False,
            "erreur": str(e)
        }), 500


def _construire_filtres(filtres_data: Dict[str, Any]) -> Dict[str, Any]:
    """Construit un filtre ChromaDB à partir des données JSON.

    Args:
        filtres_data: Dictionnaire de filtres bruts

    Returns:
        Filtre ChromaDB combiné
    """
    liste_filtres = []
    
    # Filtre temporel
    if "timestamp_debut" in filtres_data or "timestamp_fin" in filtres_data:
        filtre_temps = creer_filtre_temporel(
            filtres_data.get("timestamp_debut"),
            filtres_data.get("timestamp_fin"),
        )
        if filtre_temps:
            liste_filtres.append(filtre_temps)
    
    # Filtre géographique
    if all(k in filtres_data for k in ["gps_lat", "gps_lon", "rayon_km"]):
        filtre_geo = creer_filtre_geographique(
            filtres_data["gps_lat"],
            filtres_data["gps_lon"],
            filtres_data["rayon_km"],
        )
        liste_filtres.append(filtre_geo)
    
    # Filtre direction
    if "direction" in filtres_data:
        filtre_dir = creer_filtre_direction(filtres_data["direction"])
        if filtre_dir:
            liste_filtres.append(filtre_dir)
    
    # Combiner tous les filtres
    if liste_filtres:
        return combiner_filtres(*liste_filtres)
    
    return {}

