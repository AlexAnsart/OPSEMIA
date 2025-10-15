"""Routes API pour la visualisation et la gestion des conversations."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

from flask import Blueprint, jsonify, request

# Ajouter le répertoire racine au path pour les imports
racine_projet = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(racine_projet))

from config.settings import obtenir_parametres
from src.backend.database.vector_db import BaseVectorielle

# Blueprint pour les routes de conversations
bp_conversations = Blueprint("conversations", __name__, url_prefix="/api")


@bp_conversations.route("/conversations", methods=["GET"])
def lister_conversations() -> tuple[Dict[str, Any], int]:
    """Liste toutes les conversations disponibles (groupées par contact).

    Query params:
        collection: nom de la collection (défaut: messages_cas1)

    Returns:
        JSON avec la liste des conversations et statistiques
    """
    try:
        nom_collection = request.args.get("collection", "messages_cas1")
        
        parametres = obtenir_parametres()
        db = BaseVectorielle(parametres.CHEMIN_BASE_CHROMA)
        
        # Récupérer tous les messages
        collection = db.obtenir_ou_creer_collection(nom_collection)
        count = collection.count()
        
        if count == 0:
            return jsonify({
                "succes": True,
                "conversations": [],
                "total": 0
            }), 200
        
        tous_messages = collection.get(
            include=["documents", "metadatas"],
            limit=count
        )
        
        if not tous_messages["ids"]:
            return jsonify({
                "succes": True,
                "conversations": [],
                "total": 0
            }), 200
        
        # Grouper par contact
        conversations_map = {}
        
        for i, msg_id in enumerate(tous_messages["ids"]):
            metadata = tous_messages["metadatas"][i] if tous_messages["metadatas"] else {}
            document = tous_messages["documents"][i] if tous_messages["documents"] else ""
            
            # Identifier le contact (utiliser from ou to selon la direction)
            direction = metadata.get("direction", "")
            contact = metadata.get("from", "") if direction == "incoming" else metadata.get("to", "")
            contact_name = metadata.get("contact_name", contact)
            
            # Clé unique pour le contact
            cle_contact = contact or "inconnu"
            
            if cle_contact not in conversations_map:
                conversations_map[cle_contact] = {
                    "contact": contact,
                    "contact_name": contact_name,
                    "messages": [],
                    "dernier_message": None,
                    "dernier_timestamp": None,
                    "nombre_messages": 0
                }
            
            # Ajouter le message à la conversation
            timestamp = metadata.get("timestamp", "")
            conversations_map[cle_contact]["messages"].append({
                "id": msg_id,
                "document": document,
                "metadata": metadata,
                "timestamp": timestamp
            })
            
            # Mettre à jour le dernier message
            conversations_map[cle_contact]["nombre_messages"] += 1
            if not conversations_map[cle_contact]["dernier_timestamp"] or timestamp > conversations_map[cle_contact]["dernier_timestamp"]:
                conversations_map[cle_contact]["dernier_timestamp"] = timestamp
                conversations_map[cle_contact]["dernier_message"] = document[:100] + ("..." if len(document) > 100 else "")
        
        # Trier les conversations par date du dernier message (plus récent en premier)
        conversations_liste = list(conversations_map.values())
        conversations_liste.sort(key=lambda x: x["dernier_timestamp"] or "", reverse=True)
        
        # Ne pas retourner tous les messages dans cette route (juste les stats)
        conversations_resumees = []
        for conv in conversations_liste:
            conversations_resumees.append({
                "contact": conv["contact"],
                "contact_name": conv["contact_name"],
                "dernier_message": conv["dernier_message"],
                "dernier_timestamp": conv["dernier_timestamp"],
                "nombre_messages": conv["nombre_messages"]
            })
        
        return jsonify({
            "succes": True,
            "conversations": conversations_resumees,
            "total": len(conversations_resumees)
        }), 200
        
    except Exception as e:
        return jsonify({
            "succes": False,
            "erreur": str(e)
        }), 500


@bp_conversations.route("/conversation/<contact>", methods=["GET"])
def obtenir_conversation(contact: str) -> tuple[Dict[str, Any], int]:
    """Obtient tous les messages d'une conversation avec un contact spécifique.

    Args:
        contact: Numéro de téléphone ou identifiant du contact

    Query params:
        collection: nom de la collection (défaut: messages_cas1)

    Returns:
        JSON avec tous les messages de la conversation, triés chronologiquement
    """
    try:
        nom_collection = request.args.get("collection", "messages_cas1")
        
        parametres = obtenir_parametres()
        db = BaseVectorielle(parametres.CHEMIN_BASE_CHROMA)
        
        # Récupérer tous les messages
        collection = db.obtenir_ou_creer_collection(nom_collection)
        count = collection.count()
        
        if count == 0:
            return jsonify({
                "succes": False,
                "erreur": "Collection vide"
            }), 404
        
        tous_messages = collection.get(
            include=["documents", "metadatas"],
            limit=count
        )
        
        if not tous_messages["ids"]:
            return jsonify({
                "succes": False,
                "erreur": "Aucun message trouvé"
            }), 404
        
        # Filtrer les messages pour ce contact
        messages_conversation = []
        
        for i, msg_id in enumerate(tous_messages["ids"]):
            metadata = tous_messages["metadatas"][i] if tous_messages["metadatas"] else {}
            document = tous_messages["documents"][i] if tous_messages["documents"] else ""
            
            # Vérifier si le message appartient à cette conversation
            msg_from = metadata.get("from", "")
            msg_to = metadata.get("to", "")
            
            if contact in [msg_from, msg_to]:
                messages_conversation.append({
                    "id": msg_id,
                    "document": document,
                    "metadata": metadata,
                    "timestamp": metadata.get("timestamp", "")
                })
        
        # Trier chronologiquement
        messages_conversation.sort(key=lambda x: x["timestamp"] or "")
        
        # Informations du contact
        contact_info = {
            "contact": contact,
            "contact_name": messages_conversation[0]["metadata"].get("contact_name", contact) if messages_conversation else contact,
            "nombre_messages": len(messages_conversation)
        }
        
        return jsonify({
            "succes": True,
            "conversation": contact_info,
            "messages": messages_conversation
        }), 200
        
    except Exception as e:
        return jsonify({
            "succes": False,
            "erreur": str(e)
        }), 500


@bp_conversations.route("/conversation/<contact>/search", methods=["POST"])
def rechercher_dans_conversation(contact: str) -> tuple[Dict[str, Any], int]:
    """Recherche par mots-clés dans une conversation spécifique.

    Args:
        contact: Numéro de téléphone ou identifiant du contact

    Body JSON:
        query: Terme de recherche
        collection: nom de la collection

    Returns:
        JSON avec les messages correspondants
    """
    try:
        data = request.get_json()
        query = data.get("query", "").lower()
        nom_collection = data.get("collection", "messages_cas1")
        
        if not query:
            return jsonify({
                "succes": False,
                "erreur": "Requête vide"
            }), 400
        
        parametres = obtenir_parametres()
        db = BaseVectorielle(parametres.CHEMIN_BASE_CHROMA)
        
        # Récupérer tous les messages de la conversation
        collection = db.obtenir_ou_creer_collection(nom_collection)
        count = collection.count()
        
        tous_messages = collection.get(
            include=["documents", "metadatas"],
            limit=count if count > 0 else 10000
        )
        
        # Filtrer par contact et par mot-clé
        messages_trouves = []
        
        for i, msg_id in enumerate(tous_messages["ids"]):
            metadata = tous_messages["metadatas"][i] if tous_messages["metadatas"] else {}
            document = tous_messages["documents"][i] if tous_messages["documents"] else ""
            
            # Vérifier si le message appartient à cette conversation
            msg_from = metadata.get("from", "")
            msg_to = metadata.get("to", "")
            
            if contact in [msg_from, msg_to]:
                # Rechercher le terme dans le document
                if query in document.lower():
                    messages_trouves.append({
                        "id": msg_id,
                        "document": document,
                        "metadata": metadata,
                        "timestamp": metadata.get("timestamp", "")
                    })
        
        # Trier chronologiquement
        messages_trouves.sort(key=lambda x: x["timestamp"] or "")
        
        return jsonify({
            "succes": True,
            "resultats": messages_trouves,
            "total": len(messages_trouves)
        }), 200
        
    except Exception as e:
        return jsonify({
            "succes": False,
            "erreur": str(e)
        }), 500

