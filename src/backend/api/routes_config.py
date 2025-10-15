"""Routes API pour la configuration et les statistiques."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

from flask import Blueprint, jsonify, request

# Ajouter le répertoire racine au path pour les imports
racine_projet = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(racine_projet))

from config.settings import Parametres, obtenir_parametres, recharger_parametres, MODELES_DISPONIBLES
from src.backend.database.vector_db import BaseVectorielle

# Blueprint pour les routes de configuration
bp_config = Blueprint("config", __name__, url_prefix="/api")


@bp_config.route("/config", methods=["GET"])
def obtenir_config() -> tuple[Dict[str, Any], int]:
    """Obtient la configuration actuelle du système.

    Returns:
        JSON avec tous les paramètres de configuration
    """
    try:
        parametres = obtenir_parametres()
        
        config = {
            "encodage": {
                "modele": parametres.ID_MODELE_EMBEDDING,
                "peripherique": parametres.PERIPHERIQUE_EMBEDDING,
                "modeles_disponibles": MODELES_DISPONIBLES
            },
            "chunking": {
                "taille_fenetre": parametres.TAILLE_FENETRE_CHUNK,
                "overlap": parametres.OVERLAP_FENETRE_CHUNK
            },
            "base_vectorielle": {
                "chemin": parametres.CHEMIN_BASE_CHROMA,
                "collection_messages": parametres.NOM_COLLECTION_MESSAGES,
                "collection_chunks": parametres.NOM_COLLECTION_CHUNKS
            },
            "recherche": {
                "methode": parametres.METHODE_RECHERCHE,
                "nombre_resultats": parametres.NOMBRE_RESULTATS_RECHERCHE,
                "exclure_bruit_par_defaut": parametres.EXCLURE_BRUIT_PAR_DEFAUT,
                "seuil_distance_max": parametres.SEUIL_DISTANCE_MAX
            }
        }
        
        return jsonify({
            "succes": True,
            "configuration": config
        }), 200
        
    except Exception as e:
        return jsonify({
            "succes": False,
            "erreur": str(e)
        }), 500


@bp_config.route("/config", methods=["POST"])
def modifier_config() -> tuple[Dict[str, Any], int]:
    """Modifie la configuration du système de manière permanente.

    Body JSON attendu:
        {
            "id_modele_embedding": "BAAI/bge-m3",
            "peripherique_embedding": "auto",
            "taille_fenetre_chunk": 5,
            "overlap_fenetre_chunk": 2,
            "methode_recherche": "ANN",
            "nombre_resultats_recherche": 15,
            "exclure_bruit_par_defaut": true,
            "seuil_distance_max": 0.5
        }

    Returns:
        JSON avec confirmation et nouveaux paramètres
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "succes": False,
                "erreur": "Corps JSON requis"
            }), 400
        
        # Obtenir les paramètres actuels
        parametres = obtenir_parametres()
        
        # Sauvegarder les modifications dans le JSON
        parametres.sauvegarder(data)
        
        # Recharger les paramètres
        recharger_parametres()
        
        modifs = list(data.keys())
        
        # Déterminer si un redémarrage est nécessaire
        redemarrage_requis = any(k in data for k in [
            "id_modele_embedding",
            "peripherique_embedding",
            "taille_fenetre_chunk",
            "overlap_fenetre_chunk"
        ])
        
        reponse = {
            "succes": True,
            "message": f"{len(modifs)} paramètre(s) modifié(s) et sauvegardé(s): {', '.join(modifs)}",
            "modifications": data
        }
        
        if redemarrage_requis:
            reponse["avertissement"] = "⚠️ Redémarrage du serveur requis pour appliquer certains changements (modèle d'embedding, chunking)"
        
        return jsonify(reponse), 200
        
    except Exception as e:
        return jsonify({
            "succes": False,
            "erreur": str(e)
        }), 500


@bp_config.route("/stats", methods=["GET"])
def obtenir_stats() -> tuple[Dict[str, Any], int]:
    """Obtient les statistiques d'indexation de toutes les collections.

    Returns:
        JSON avec statistiques détaillées
    """
    try:
        parametres = obtenir_parametres()
        db = BaseVectorielle(parametres.CHEMIN_BASE_CHROMA)
        
        # Récupérer toutes les collections
        collections = db.client.list_collections()
        
        stats_collections = []
        total_documents = 0
        
        for collection_info in collections:
            nom = collection_info.name
            count = db.compter_documents(nom)
            total_documents += count
            
            stats_collections.append({
                "nom": nom,
                "nombre_documents": count,
                "metadata": collection_info.metadata
            })
        
        return jsonify({
            "succes": True,
            "statistiques": {
                "nombre_collections": len(collections),
                "total_documents": total_documents,
                "collections": stats_collections,
                "modele_embedding": parametres.ID_MODELE_EMBEDDING,
                "methode_recherche": parametres.METHODE_RECHERCHE
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "succes": False,
            "erreur": str(e)
        }), 500


@bp_config.route("/collections", methods=["GET"])
def lister_collections() -> tuple[Dict[str, Any], int]:
    """Liste toutes les collections disponibles dans ChromaDB.

    Returns:
        JSON avec liste des collections et leurs métadonnées
    """
    try:
        parametres = obtenir_parametres()
        db = BaseVectorielle(parametres.CHEMIN_BASE_CHROMA)
        
        collections = db.client.list_collections()
        
        liste_collections = [
            {
                "nom": col.name,
                "nombre_documents": db.compter_documents(col.name),
                "metadata": col.metadata
            }
            for col in collections
        ]
        
        return jsonify({
            "succes": True,
            "nombre_collections": len(liste_collections),
            "collections": liste_collections
        }), 200
        
    except Exception as e:
        return jsonify({
            "succes": False,
            "erreur": str(e)
        }), 500


@bp_config.route("/health", methods=["GET"])
def verifier_sante() -> tuple[Dict[str, Any], int]:
    """Vérifie que l'API fonctionne correctement.

    Returns:
        JSON avec statut de santé
    """
    try:
        parametres = obtenir_parametres()
        db = BaseVectorielle(parametres.CHEMIN_BASE_CHROMA)
        
        # Vérifier la connexion à ChromaDB
        collections = db.client.list_collections()
        
        return jsonify({
            "succes": True,
            "statut": "OK",
            "base_vectorielle": "connectée",
            "nombre_collections": len(collections)
        }), 200
        
    except Exception as e:
        return jsonify({
            "succes": False,
            "statut": "ERREUR",
            "erreur": str(e)
        }), 500

