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
from src.backend.models.model_manager import recharger_encodeur_texte, obtenir_id_modele_actuel

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
            },
            "images": {
                "longueur_min_description": parametres.LONGUEUR_MIN_DESCRIPTION_IMAGE,
                "longueur_max_description": parametres.LONGUEUR_MAX_DESCRIPTION_IMAGE,
                "num_beams": parametres.NUM_BEAMS_DESCRIPTION_IMAGE,
                "temperature": parametres.TEMPERATURE_DESCRIPTION_IMAGE
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
            "seuil_distance_max": 0.5,
            "longueur_min_description_image": 30,
            "longueur_max_description_image": 150,
            "num_beams_description_image": 15,
            "temperature_description_image": 0.3
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
        id_modele_avant = parametres.ID_MODELE_EMBEDDING
        peripherique_avant = parametres.PERIPHERIQUE_EMBEDDING
        
        # Sauvegarder les modifications dans le JSON
        parametres.sauvegarder(data)
        
        # Recharger les paramètres
        parametres_nouveaux = recharger_parametres()
        
        modifs = list(data.keys())
        
        # Vérifier si le modèle d'embedding ou le périphérique a changé
        modele_change = "id_modele_embedding" in data and data["id_modele_embedding"] != id_modele_avant
        peripherique_change = "peripherique_embedding" in data and data["peripherique_embedding"] != peripherique_avant
        
        # Recharger l'encodeur si nécessaire (automatique, sans redémarrage)
        if modele_change or peripherique_change:
            try:
                print(f"🔄 Rechargement du modèle d'embedding: {parametres_nouveaux.ID_MODELE_EMBEDDING} ({parametres_nouveaux.PERIPHERIQUE_EMBEDDING})")
                recharger_encodeur_texte()
                print(f"✅ Modèle rechargé avec succès")
            except Exception as e:
                print(f"❌ Erreur lors du rechargement du modèle: {e}")
                # Restaurer les anciens paramètres si le rechargement échoue
                parametres.sauvegarder({
                    "id_modele_embedding": id_modele_avant,
                    "peripherique_embedding": peripherique_avant
                })
                recharger_parametres()
                return jsonify({
                    "succes": False,
                    "erreur": f"Impossible de charger le modèle {data.get('id_modele_embedding')}: {str(e)}"
                }), 500
        
        # Déterminer si un redémarrage est nécessaire (uniquement pour chunking maintenant)
        redemarrage_requis = any(k in data for k in [
            "taille_fenetre_chunk",
            "overlap_fenetre_chunk"
        ])
        
        reponse = {
            "succes": True,
            "message": f"{len(modifs)} paramètre(s) modifié(s) et sauvegardé(s): {', '.join(modifs)}",
            "modifications": data
        }
        
        if modele_change or peripherique_change:
            reponse["info"] = f"✅ Modèle rechargé automatiquement: {parametres_nouveaux.ID_MODELE_EMBEDDING}"
        
        if redemarrage_requis:
            reponse["avertissement"] = "⚠️ Redémarrage du serveur requis pour appliquer les changements de chunking (taille fenêtre, overlap)"
        
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


@bp_config.route("/collections/<nom_collection>", methods=["DELETE"])
def supprimer_collection(nom_collection: str) -> tuple[Dict[str, Any], int]:
    """Supprime une collection de ChromaDB.

    Args:
        nom_collection: Nom de la collection à supprimer

    Returns:
        JSON avec confirmation
    """
    try:
        parametres = obtenir_parametres()
        db = BaseVectorielle(parametres.CHEMIN_BASE_CHROMA)
        
        # Vérifier si la collection existe
        collections = db.client.list_collections()
        collection_existe = any(col.name == nom_collection for col in collections)
        
        if not collection_existe:
            return jsonify({
                "succes": False,
                "erreur": f"Collection '{nom_collection}' introuvable"
            }), 404
        
        # Supprimer la collection
        db.supprimer_collection(nom_collection)
        
        return jsonify({
            "succes": True,
            "message": f"Collection '{nom_collection}' supprimée avec succès"
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

