"""Routes API pour la gestion des images (indexation, visualisation, galerie)."""

from __future__ import annotations

import base64
import json
import logging
import sys
import threading
import uuid
from pathlib import Path
from typing import Any, Dict, List

from flask import Blueprint, Response, jsonify, request, send_file, stream_with_context

# Ajouter le répertoire racine au path pour les imports
racine_projet = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(racine_projet))

from config.settings import obtenir_parametres
import os
from urllib.parse import unquote
from src.backend.database.image_indexer import indexer_csv_images
from src.backend.database.vector_db import BaseVectorielle

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Blueprint pour les routes d'images
bp_images = Blueprint("images", __name__, url_prefix="/api")

# Stockage des tâches d'indexation d'images
_taches_images: Dict[str, Dict[str, Any]] = {}
_taches_images_lock = threading.Lock()


@bp_images.route("/load_images", methods=["POST"])
def charger_images() -> tuple[Dict[str, Any], int]:
    """Charge et indexe un fichier CSV d'images dans ChromaDB.
    
    Cette route lance l'indexation en arrière-plan et retourne immédiatement
    un ID de tâche. Utilisez /api/load_images/progress/<task_id> pour suivre la progression.
    
    Body JSON attendu:
        {
            "chemin_csv": "Cas/Cas4/images.csv",  # Requis
            "nom_cas": "cas4",                     # Optionnel
            "reinitialiser": false                 # Optionnel
        }
        
    Returns:
        JSON avec ID de tâche pour le suivi SSE
    """
    logger.info("📥 POST /api/load_images - Requête d'indexation d'images reçue")
    try:
        # Récupérer les paramètres
        data = request.get_json()
        logger.info(f"   Données reçues: {data}")
        
        if not data or "chemin_csv" not in data:
            return jsonify({
                "succes": False,
                "erreur": "Le champ 'chemin_csv' est requis"
            }), 400
        
        chemin_csv = data["chemin_csv"]
        nom_cas = data.get("nom_cas", None)
        reinitialiser = data.get("reinitialiser", False)
        
        # Vérifier que le fichier existe
        if not Path(chemin_csv).exists():
            return jsonify({
                "succes": False,
                "erreur": f"Le fichier '{chemin_csv}' n'existe pas"
            }), 404
        
        # Créer une nouvelle tâche
        task_id = str(uuid.uuid4())
        with _taches_images_lock:
            _taches_images[task_id] = {
                "etat": "en_cours",
                "progression": 0,
                "etape": "initialisation",
                "message": "Démarrage...",
                "statistiques": None,
                "erreur": None,
                "evenements": []
            }
        
        # Fonction de callback pour la progression
        def on_progress(etape: str, pct: float, msg: str):
            with _taches_images_lock:
                if task_id in _taches_images:
                    _taches_images[task_id]["progression"] = pct
                    _taches_images[task_id]["etape"] = etape
                    _taches_images[task_id]["message"] = msg
                    _taches_images[task_id]["evenements"].append({
                        "etape": etape,
                        "progression": pct,
                        "message": msg
                    })
        
        # Fonction d'indexation dans un thread
        def run_indexation():
            try:
                logger.info(f"🚀 Début indexation images tâche {task_id}: {chemin_csv}")
                parametres = obtenir_parametres()
                stats = indexer_csv_images(
                    chemin_csv=chemin_csv,
                    parametres=parametres,
                    nom_cas=nom_cas,
                    reinitialiser=reinitialiser,
                    progress_callback=on_progress
                )
                
                with _taches_images_lock:
                    if task_id in _taches_images:
                        _taches_images[task_id]["etat"] = "termine"
                        _taches_images[task_id]["statistiques"] = stats
                        logger.info(f"✅ Indexation images terminée tâche {task_id}")
                        
            except Exception as e:
                logger.error(f"❌ Erreur indexation images tâche {task_id}: {e}", exc_info=True)
                with _taches_images_lock:
                    if task_id in _taches_images:
                        _taches_images[task_id]["etat"] = "erreur"
                        _taches_images[task_id]["erreur"] = str(e)
        
        # Lancer le thread
        thread = threading.Thread(target=run_indexation, daemon=True)
        thread.start()
        
        return jsonify({
            "succes": True,
            "task_id": task_id,
            "message": "Indexation d'images démarrée. Utilisez /api/load_images/progress/{task_id} pour suivre la progression."
        }), 202  # 202 Accepted
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du démarrage de l'indexation d'images: {e}", exc_info=True)
        return jsonify({
            "succes": False,
            "erreur": str(e)
        }), 500


@bp_images.route("/load_images/progress/<task_id>", methods=["GET"])
def suivre_progression_images(task_id: str):
    """Stream SSE pour suivre la progression d'une tâche d'indexation d'images.
    
    Args:
        task_id: ID de la tâche retourné par /api/load_images
        
    Returns:
        Stream SSE avec événements de progression
    """
    logger.info(f"📡 GET /api/load_images/progress/{task_id} - Client SSE connecté")
    
    def generate():
        """Génère les événements SSE pour la progression."""
        import time
        
        logger.info(f"📡 Client connecté pour SSE images task {task_id}")
        derniere_progression = -1
        
        while True:
            with _taches_images_lock:
                if task_id not in _taches_images:
                    # Tâche introuvable
                    yield f"event: error\ndata: {json.dumps({'erreur': 'Tâche introuvable'})}\n\n"
                    break
                
                tache = _taches_images[task_id]
                
                # Envoyer un événement seulement si la progression a changé
                if tache["progression"] != derniere_progression:
                    event_data = {
                        "etat": tache["etat"],
                        "progression": tache["progression"],
                        "etape": tache["etape"],
                        "message": tache["message"]
                    }
                    
                    yield f"data: {json.dumps(event_data)}\n\n"
                    derniere_progression = tache["progression"]
                
                # Si terminé ou erreur, envoyer l'événement final et fermer
                if tache["etat"] in ["termine", "erreur"]:
                    if tache["etat"] == "termine":
                        event_data = {
                            "etat": "termine",
                            "progression": 100,
                            "statistiques": tache["statistiques"],
                            "message": "Indexation d'images terminée avec succès"
                        }
                        yield f"event: complete\ndata: {json.dumps(event_data)}\n\n"
                        logger.info(f"✅ SSE images terminé pour task {task_id}")
                    else:
                        event_data = {
                            "etat": "erreur",
                            "erreur": tache["erreur"],
                            "message": f"Erreur: {tache['erreur']}"
                        }
                        yield f"event: error\ndata: {json.dumps(event_data)}\n\n"
                        logger.error(f"❌ SSE images erreur pour task {task_id}: {tache['erreur']}")
                    break
            
            time.sleep(0.5)  # Poll toutes les 500ms
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


@bp_images.route("/images/galerie", methods=["GET"])
def obtenir_galerie() -> tuple[Dict[str, Any], int]:
    """Obtient toutes les images d'une collection pour la galerie.
    
    Query params:
        collection: Nom de la collection (défaut: "images")
        limite: Nombre maximum d'images (défaut: 1000)
        tri: "chronologique" ou "nom" (défaut: "chronologique")
        
    Returns:
        JSON avec liste d'images et métadonnées
    """
    try:
        # Paramètres de la requête
        collection = request.args.get("collection", "images")
        limite = int(request.args.get("limite", "1000"))
        tri = request.args.get("tri", "chronologique")
        
        # Récupérer toutes les images de la collection
        parametres = obtenir_parametres()
        db = BaseVectorielle(parametres.CHEMIN_BASE_CHROMA)
        
        try:
            collection_obj = db.client.get_collection(name=collection)
        except Exception:
            return jsonify({
                "succes": False,
                "erreur": f"Collection '{collection}' introuvable"
            }), 404
        
        # Récupérer tous les documents
        count = collection_obj.count()
        if count == 0:
            return jsonify({
                "succes": True,
                "nombre_images": 0,
                "images": []
            }), 200
        
        resultats_bruts = collection_obj.get(
            limit=min(limite, count),
            include=["metadatas", "documents"]
        )
        
        # Formatter les images
        images = []
        for i in range(len(resultats_bruts["ids"])):
            image_data = {
                "id": resultats_bruts["ids"][i],
                "metadata": resultats_bruts["metadatas"][i] if resultats_bruts["metadatas"] else {},
                "description": resultats_bruts["documents"][i] if resultats_bruts["documents"] else "",
            }
            images.append(image_data)
        
        # Trier les images
        if tri == "chronologique":
            # Trier par timestamp (plus récent d'abord)
            images.sort(
                key=lambda x: x["metadata"].get("timestamp", ""),
                reverse=True
            )
        elif tri == "nom":
            # Trier par nom alphabétique
            images.sort(
                key=lambda x: x["metadata"].get("nom_image", "")
            )
        
        return jsonify({
            "succes": True,
            "nombre_images": len(images),
            "images": images
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la galerie: {e}", exc_info=True)
        return jsonify({
            "succes": False,
            "erreur": str(e)
        }), 500


@bp_images.route("/images/servir/<path:chemin_image>", methods=["GET"])
def servir_image(chemin_image: str):
    """Sert une image depuis le système de fichiers.
    
    Args:
        chemin_image: Chemin relatif ou absolu de l'image
        
    Returns:
        Fichier image ou erreur 404
    """
    try:
        # Décoder et normaliser le chemin (gérer les backslashes Windows)
        chemin_str = unquote(chemin_image)
        # Remplacer les antislashs par des slashs OS
        chemin_str = chemin_str.replace("\\", "/")

        candidats = []

        # 1) Chemin tel quel
        candidats.append(Path(chemin_str))

        # 2) Relatif à la racine du projet
        candidats.append(racine_projet / chemin_str)

        # 3) Relatif au dossier Cas/
        candidats.append(racine_projet / "Cas" / chemin_str)

        # 4) Recherche par nom de fichier dans Cas/** si toujours introuvable
        chemin_trouve = None
        for c in candidats:
            if c.exists() and c.is_file():
                chemin_trouve = c
                break

        if chemin_trouve is None:
            try:
                base_cas = racine_projet / "Cas"
                if base_cas.exists():
                    # Rechercher d'abord par chemin relatif 'Images/...'
                    # Puis fallback par nom de fichier uniquement
                    try_path_suffix = Path(chemin_str)
                    # Essayer de retrouver un chemin qui se termine par ce suffixe
                    suffix_norm = os.path.join(*try_path_suffix.parts)
                    for p in base_cas.rglob(try_path_suffix.name):
                        # Choisir le premier match
                        chemin_trouve = p
                        break
            except Exception:
                chemin_trouve = None

        if chemin_trouve is None or not chemin_trouve.exists():
            return jsonify({
                "succes": False,
                "erreur": f"Image non trouvée: {chemin_image}"
            }), 404

        # Déterminer un mimetype simple selon l'extension
        ext = chemin_trouve.suffix.lower()
        if ext in {".jpg", ".jpeg"}:
            mimetype = 'image/jpeg'
        elif ext in {".png"}:
            mimetype = 'image/png'
        elif ext in {".webp"}:
            mimetype = 'image/webp'
        elif ext in {".gif"}:
            mimetype = 'image/gif'
        else:
            mimetype = 'application/octet-stream'

        return send_file(str(chemin_trouve), mimetype=mimetype)

    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'image: {e}")
        return jsonify({
            "succes": False,
            "erreur": str(e)
        }), 500


