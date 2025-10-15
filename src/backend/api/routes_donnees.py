"""Routes API pour l'accès aux données (messages, contexte, timeline)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

from flask import Blueprint, jsonify, request

# Ajouter le répertoire racine au path pour les imports
racine_projet = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(racine_projet))

from config.settings import obtenir_parametres
from src.backend.database.vector_db import BaseVectorielle

# Blueprint pour les routes d'accès aux données
bp_donnees = Blueprint("donnees", __name__, url_prefix="/api")


@bp_donnees.route("/message/<message_id>", methods=["GET"])
def obtenir_message(message_id: str) -> tuple[Dict[str, Any], int]:
    """Obtient un message spécifique par son ID.

    Args:
        message_id: ID du message à récupérer

    Query params:
        collection: nom de la collection (défaut: messages)

    Returns:
        JSON avec le message et ses métadonnées
    """
    try:
        nom_collection = request.args.get("collection", "messages")
        
        parametres = obtenir_parametres()
        db = BaseVectorielle(parametres.CHEMIN_BASE_CHROMA)
        
        # Récupérer le message par ID
        collection = db.obtenir_ou_creer_collection(nom_collection)
        resultats = collection.get(
            ids=[message_id],
            include=["documents", "metadatas"]
        )
        
        if not resultats["ids"] or len(resultats["ids"]) == 0:
            return jsonify({
                "succes": False,
                "erreur": f"Message '{message_id}' introuvable"
            }), 404
        
        return jsonify({
            "succes": True,
            "message": {
                "id": resultats["ids"][0],
                "document": resultats["documents"][0] if resultats["documents"] else "",
                "metadata": resultats["metadatas"][0] if resultats["metadatas"] else {}
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "succes": False,
            "erreur": str(e)
        }), 500


@bp_donnees.route("/context/<message_id>", methods=["GET"])
def obtenir_contexte(message_id: str) -> tuple[Dict[str, Any], int]:
    """Obtient un message avec son contexte (messages adjacents chronologiquement).

    Args:
        message_id: ID du message central

    Query params:
        collection: nom de la collection
        fenetre_avant: nombre de messages avant (défaut: 5)
        fenetre_apres: nombre de messages après (défaut: 5)

    Returns:
        JSON avec le message central et son contexte
    """
    try:
        nom_collection = request.args.get("collection", "messages")
        fenetre_avant = int(request.args.get("fenetre_avant", 5))
        fenetre_apres = int(request.args.get("fenetre_apres", 5))
        
        parametres = obtenir_parametres()
        db = BaseVectorielle(parametres.CHEMIN_BASE_CHROMA)
        
        # Récupérer tous les messages de la collection
        collection = db.obtenir_ou_creer_collection(nom_collection)
        count = collection.count()
        
        tous_messages = collection.get(
            include=["documents", "metadatas"],
            limit=count if count > 0 else 10000
        )
        
        if not tous_messages["ids"]:
            return jsonify({
                "succes": False,
                "erreur": "Collection vide"
            }), 404
        
        # Trouver l'index du message cible
        try:
            index_cible = tous_messages["ids"].index(message_id)
        except ValueError:
            return jsonify({
                "succes": False,
                "erreur": f"Message '{message_id}' introuvable"
            }), 404
        
        # Extraire le contexte
        index_debut = max(0, index_cible - fenetre_avant)
        index_fin = min(len(tous_messages["ids"]), index_cible + fenetre_apres + 1)
        
        contexte = _extraire_contexte(tous_messages, index_debut, index_fin, index_cible)
        
        return jsonify({
            "succes": True,
            "contexte": contexte
        }), 200
        
    except Exception as e:
        return jsonify({
            "succes": False,
            "erreur": str(e)
        }), 500


def _extraire_contexte(
    tous_messages: Dict[str, List],
    index_debut: int,
    index_fin: int,
    index_cible: int
) -> Dict[str, Any]:
    """Extrait le contexte autour d'un message."""
    messages_contexte = []
    
    for i in range(index_debut, index_fin):
        messages_contexte.append({
            "id": tous_messages["ids"][i],
            "document": tous_messages["documents"][i] if tous_messages["documents"] else "",
            "metadata": tous_messages["metadatas"][i] if tous_messages["metadatas"] else {},
            "est_cible": (i == index_cible)
        })
    
    return {
        "message_central": messages_contexte[index_cible - index_debut],
        "messages_avant": messages_contexte[:index_cible - index_debut],
        "messages_apres": messages_contexte[index_cible - index_debut + 1:],
        "total_contexte": len(messages_contexte)
    }

