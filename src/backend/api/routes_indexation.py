"""Routes API pour l'indexation de CSV dans ChromaDB."""

from __future__ import annotations

import json
import logging
import psutil
import sys
import threading
import uuid
from pathlib import Path
from typing import Any, Dict

from flask import Blueprint, Response, jsonify, request, stream_with_context

# Ajouter le répertoire racine au path pour les imports
racine_projet = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(racine_projet))

from config.settings import obtenir_parametres
from src.backend.database.indexer import indexer_csv_messages
from src.backend.models.model_manager import obtenir_encodeur_texte

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Blueprint pour les routes d'indexation
bp_indexation = Blueprint("indexation", __name__, url_prefix="/api")

# Stockage des tâches d'indexation en cours
_taches_indexation: Dict[str, Dict[str, Any]] = {}
_taches_lock = threading.Lock()


@bp_indexation.route("/load", methods=["POST"])
def charger_csv() -> tuple[Dict[str, Any], int]:
    """Charge et indexe un fichier CSV de messages dans ChromaDB.

    Cette route lance l'indexation en arrière-plan et retourne immédiatement
    un ID de tâche. Utilisez /api/load/progress/<task_id> pour suivre la progression.

    Body JSON attendu:
        {
            "chemin_csv": "/chemin/vers/fichier.csv",  # Requis
            "nom_cas": "cas1",                          # Optionnel
            "reinitialiser": false                      # Optionnel (défaut: false)
        }

    Returns:
        JSON avec ID de tâche pour le suivi SSE
    """
    logger.info("📥 POST /api/load - Requête d'indexation reçue")
    try:
        # Récupérer les paramètres de la requête
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
        with _taches_lock:
            _taches_indexation[task_id] = {
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
            with _taches_lock:
                if task_id in _taches_indexation:
                    _taches_indexation[task_id]["progression"] = pct
                    _taches_indexation[task_id]["etape"] = etape
                    _taches_indexation[task_id]["message"] = msg
                    _taches_indexation[task_id]["evenements"].append({
                        "etape": etape,
                        "progression": pct,
                        "message": msg
                    })
        
        # IMPORTANT: Précharger le modèle d'embedding AVANT de lancer le thread
        # pour éviter de bloquer le serveur Flask pendant 15-30s (surtout avec Qwen3)
        
        # 1. Vérifier la RAM disponible
        mem = psutil.virtual_memory()
        ram_disponible_gb = mem.available / (1024**3)
        ram_totale_gb = mem.total / (1024**3)
        ram_utilisee_pct = mem.percent
        
        logger.info(f"💾 RAM système:")
        logger.info(f"   • Total: {ram_totale_gb:.1f} GB")
        logger.info(f"   • Disponible: {ram_disponible_gb:.1f} GB")
        logger.info(f"   • Utilisée: {ram_utilisee_pct:.1f}%")
        
        # Obtenir le modèle configuré
        parametres = obtenir_parametres()
        modele_id = parametres.ID_MODELE_EMBEDDING
        
        # Estimer la RAM requise selon le modèle
        ram_requise = {
            "OrdalieTech/Solon-embeddings-large-0.1": 2.0,
            "jinaai/jina-embeddings-v3": 3.0,
            "BAAI/bge-m3": 3.5,
            "Qwen/Qwen3-Embedding-8B": 10.0,  # 8GB modèle + 2GB overhead
        }
        ram_necessaire = ram_requise.get(modele_id, 2.0)
        
        logger.info(f"🧠 Modèle à charger: {modele_id}")
        logger.info(f"   • RAM estimée nécessaire: {ram_necessaire:.1f} GB")
        
        # Avertissement si RAM semble faible (sans bloquer)
        if ram_disponible_gb < ram_necessaire:
            logger.warning(
                f"⚠️ RAM disponible ({ram_disponible_gb:.1f} GB) inférieure à "
                f"l'estimation pour {modele_id} ({ram_necessaire:.1f} GB). "
                f"Tentative de chargement quand même..."
            )
        
        # Tenter le chargement du modèle
        try:
            logger.info(f"🔄 Préchargement du modèle d'embedding...")
            logger.info(f"   ⏳ Ceci peut prendre 15-60 secondes pour les gros modèles...")
            
            encodeur = obtenir_encodeur_texte()
            
            # Vérifier la RAM après chargement
            mem_apres = psutil.virtual_memory()
            ram_utilisee_chargement = (mem.available - mem_apres.available) / (1024**3)
            
            logger.info(f"✅ Modèle préchargé: {encodeur.id_modele} (dim={encodeur.dimension_embedding})")
            logger.info(f"   • RAM utilisée pour le chargement: {ram_utilisee_chargement:.2f} GB")
            logger.info(f"   • RAM disponible restante: {mem_apres.available / (1024**3):.1f} GB")
            
        except MemoryError as e:
            logger.error(f"❌ Erreur: Mémoire insuffisante!")
            message_erreur = (
                f"Mémoire RAM insuffisante pour charger {modele_id}. "
                f"Utilisez un modèle plus léger (BGE-M3, Jina v3) ou libérez de la RAM."
            )
            with _taches_lock:
                if task_id in _taches_indexation:
                    _taches_indexation[task_id]["etat"] = "erreur"
                    _taches_indexation[task_id]["erreur"] = message_erreur
            return jsonify({
                "succes": False,
                "erreur": message_erreur
            }), 500
            
        except Exception as e:
            logger.error(f"❌ Erreur préchargement modèle: {e}", exc_info=True)
            with _taches_lock:
                if task_id in _taches_indexation:
                    _taches_indexation[task_id]["etat"] = "erreur"
                    _taches_indexation[task_id]["erreur"] = f"Impossible de charger le modèle: {str(e)}"
            return jsonify({
                "succes": False,
                "erreur": f"Impossible de charger le modèle d'embedding: {str(e)}"
            }), 500
        
        # Fonction d'indexation dans un thread
        def run_indexation():
            try:
                logger.info(f"🚀 Début indexation tâche {task_id}: {chemin_csv}")
                parametres = obtenir_parametres()
                stats = indexer_csv_messages(
                    chemin_csv=chemin_csv,
                    parametres=parametres,
                    nom_cas=nom_cas,
                    reinitialiser=reinitialiser,
                    progress_callback=on_progress
                )
                
                with _taches_lock:
                    if task_id in _taches_indexation:
                        _taches_indexation[task_id]["etat"] = "termine"
                        _taches_indexation[task_id]["statistiques"] = stats
                        logger.info(f"✅ Indexation terminée tâche {task_id}")
                        
            except Exception as e:
                logger.error(f"❌ Erreur indexation tâche {task_id}: {e}", exc_info=True)
                with _taches_lock:
                    if task_id in _taches_indexation:
                        _taches_indexation[task_id]["etat"] = "erreur"
                        _taches_indexation[task_id]["erreur"] = str(e)
        
        # Lancer le thread
        thread = threading.Thread(target=run_indexation, daemon=True)
        thread.start()
        
        return jsonify({
            "succes": True,
            "task_id": task_id,
            "message": "Indexation démarrée. Utilisez /api/load/progress/{task_id} pour suivre la progression."
        }), 202  # 202 Accepted
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du démarrage de l'indexation: {e}", exc_info=True)
        return jsonify({
            "succes": False,
            "erreur": str(e)
        }), 500


@bp_indexation.route("/load/progress/<task_id>", methods=["GET"])
def suivre_progression(task_id: str):
    """Stream SSE pour suivre la progression d'une tâche d'indexation.
    
    Args:
        task_id: ID de la tâche retourné par /api/load
        
    Returns:
        Stream SSE avec événements de progression
    """
    logger.info(f"📡 GET /api/load/progress/{task_id} - Client SSE connecté")
    logger.info(f"   Tâches actives: {list(_taches_indexation.keys())}")
    
    def generate():
        """Génère les événements SSE pour la progression."""
        import time
        
        logger.info(f"📡 Client connecté pour SSE task {task_id}")
        derniere_progression = -1
        
        while True:
            with _taches_lock:
                if task_id not in _taches_indexation:
                    # Tâche introuvable
                    yield f"event: error\ndata: {json.dumps({'erreur': 'Tâche introuvable'})}\n\n"
                    break
                
                tache = _taches_indexation[task_id]
                
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
                            "message": "Indexation terminée avec succès"
                        }
                        yield f"event: complete\ndata: {json.dumps(event_data)}\n\n"
                        logger.info(f"✅ SSE terminé pour task {task_id}")
                    else:
                        event_data = {
                            "etat": "erreur",
                            "erreur": tache["erreur"],
                            "message": f"Erreur: {tache['erreur']}"
                        }
                        yield f"event: error\ndata: {json.dumps(event_data)}\n\n"
                        logger.error(f"❌ SSE erreur pour task {task_id}: {tache['erreur']}")
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


@bp_indexation.route("/load/status/<task_id>", methods=["GET"])
def obtenir_statut_tache(task_id: str) -> tuple[Dict[str, Any], int]:
    """Obtient le statut actuel d'une tâche d'indexation (alternative à SSE).
    
    Args:
        task_id: ID de la tâche
        
    Returns:
        JSON avec le statut de la tâche
    """
    logger.info(f"📊 GET /api/load/status/{task_id} - Vérification statut")
    with _taches_lock:
        if task_id not in _taches_indexation:
            return jsonify({
                "succes": False,
                "erreur": "Tâche introuvable"
            }), 404
        
        tache = _taches_indexation[task_id]
        return jsonify({
            "succes": True,
            "etat": tache["etat"],
            "progression": tache["progression"],
            "etape": tache["etape"],
            "message": tache["message"],
            "statistiques": tache["statistiques"],
            "erreur": tache["erreur"]
        }), 200


@bp_indexation.route("/load_dossier", methods=["POST"])
def charger_dossier() -> tuple[Dict[str, Any], int]:
    """Charge et indexe tous les CSV d'un dossier (sms.csv, email.csv, etc.).

    Body JSON attendu:
        {
            "chemin_dossier": "/chemin/vers/dossier/",  # Requis
            "nom_cas": "cas1",                           # Optionnel
            "reinitialiser": false                       # Optionnel
        }

    Returns:
        JSON avec statistiques d'indexation pour chaque fichier
    """
    try:
        data = request.get_json()
        
        if not data or "chemin_dossier" not in data:
            return jsonify({
                "succes": False,
                "erreur": "Le champ 'chemin_dossier' est requis"
            }), 400
        
        chemin_dossier = Path(data["chemin_dossier"])
        nom_cas = data.get("nom_cas", None)
        reinitialiser = data.get("reinitialiser", False)
        
        if not chemin_dossier.exists() or not chemin_dossier.is_dir():
            return jsonify({
                "succes": False,
                "erreur": f"Le dossier '{chemin_dossier}' n'existe pas"
            }), 404
        
        # Chercher les fichiers CSV dans le dossier
        fichiers_csv = list(chemin_dossier.glob("*.csv"))
        
        if not fichiers_csv:
            return jsonify({
                "succes": False,
                "erreur": f"Aucun fichier CSV trouvé dans '{chemin_dossier}'"
            }), 404
        
        # Indexer chaque fichier
        resultats = {}
        parametres = obtenir_parametres()
        
        for fichier in fichiers_csv:
            try:
                # Utiliser le nom du fichier (sans extension) comme suffixe du cas
                nom_fichier = fichier.stem
                nom_complet = f"{nom_cas}_{nom_fichier}" if nom_cas else nom_fichier
                
                stats = indexer_csv_messages(
                    chemin_csv=fichier,
                    parametres=parametres,
                    nom_cas=nom_complet,
                    reinitialiser=reinitialiser,
                )
                resultats[nom_fichier] = {
                    "succes": True,
                    "statistiques": stats
                }
            except Exception as e:
                resultats[nom_fichier] = {
                    "succes": False,
                    "erreur": str(e)
                }
        
        return jsonify({
            "succes": True,
            "resultats": resultats,
            "message": f"{len(fichiers_csv)} fichiers traités"
        }), 200
        
    except Exception as e:
        return jsonify({
            "succes": False,
            "erreur": str(e)
        }), 500

