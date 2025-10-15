"""Routes API pour l'indexation de CSV dans ChromaDB."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

from flask import Blueprint, jsonify, request

# Ajouter le répertoire racine au path pour les imports
racine_projet = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(racine_projet))

from config.settings import obtenir_parametres
from src.backend.database.indexer import indexer_csv_messages

# Blueprint pour les routes d'indexation
bp_indexation = Blueprint("indexation", __name__, url_prefix="/api")


@bp_indexation.route("/load", methods=["POST"])
def charger_csv() -> tuple[Dict[str, Any], int]:
    """Charge et indexe un fichier CSV de messages dans ChromaDB.

    Body JSON attendu:
        {
            "chemin_csv": "/chemin/vers/fichier.csv",  # Requis
            "nom_cas": "cas1",                          # Optionnel
            "reinitialiser": false                      # Optionnel (défaut: false)
        }

    Returns:
        JSON avec statistiques d'indexation et code HTTP 200 si succès
    """
    try:
        # Récupérer les paramètres de la requête
        data = request.get_json()
        
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
        
        # Lancer l'indexation
        parametres = obtenir_parametres()
        stats = indexer_csv_messages(
            chemin_csv=chemin_csv,
            parametres=parametres,
            nom_cas=nom_cas,
            reinitialiser=reinitialiser,
        )
        
        return jsonify({
            "succes": True,
            "statistiques": stats,
            "message": f"Indexation terminée: {stats['messages_indexe']} messages, {stats['chunks_indexes']} chunks"
        }), 200
        
    except Exception as e:
        return jsonify({
            "succes": False,
            "erreur": str(e)
        }), 500


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

