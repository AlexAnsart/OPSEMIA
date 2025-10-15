"""Application Flask principale pour l'API OPSEMIA.

Expose toutes les routes pour l'indexation, la recherche et la gestion des données.
"""

from __future__ import annotations

import sys
from pathlib import Path

from flask import Flask, jsonify, render_template
from flask_cors import CORS

# Ajouter le répertoire racine au path pour les imports
racine_projet = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(racine_projet))

from src.backend.api.routes_config import bp_config
from src.backend.api.routes_conversations import bp_conversations
from src.backend.api.routes_donnees import bp_donnees
from src.backend.api.routes_indexation import bp_indexation
from src.backend.api.routes_recherche import bp_recherche


def creer_app() -> Flask:
    """Crée et configure l'application Flask.

    Returns:
        Application Flask configurée avec tous les blueprints
    """
    # Configurer Flask avec les dossiers frontend
    app = Flask(
        __name__,
        template_folder=str(racine_projet / "src" / "frontend" / "templates"),
        static_folder=str(racine_projet / "src" / "frontend" / "static")
    )
    
    # Configuration CORS (permet les requêtes depuis n'importe quelle origine)
    CORS(app)
    
    # Configuration Flask
    app.config["JSON_AS_ASCII"] = False  # Support UTF-8 pour les caractères français
    app.config["JSON_SORT_KEYS"] = False  # Conserver l'ordre des clés JSON
    
    # Enregistrer les blueprints API
    app.register_blueprint(bp_indexation)
    app.register_blueprint(bp_recherche)
    app.register_blueprint(bp_donnees)
    app.register_blueprint(bp_conversations)
    app.register_blueprint(bp_config)
    
    # Routes frontend (interface web)
    @app.route("/", methods=["GET"])
    def index():
        """Page principale - Recherche sémantique."""
        return render_template("index.html")
    
    @app.route("/gestion", methods=["GET"])
    def gestion():
        """Page de gestion et configuration."""
        return render_template("gestion.html")
    
    @app.route("/conversations", methods=["GET"])
    def conversations():
        """Page de visualisation des conversations."""
        return render_template("conversations.html")
    
    # Route API documentation (JSON)
    @app.route("/api", methods=["GET"])
    def api_documentation():
        """Documentation de l'API (format JSON)."""
        return jsonify({
            "nom": "OPSEMIA API",
            "description": "API REST pour le moteur de recherche sémantique",
            "version": "1.0.0",
            "endpoints": {
                "indexation": [
                    "POST /api/load - Charger un fichier CSV (retourne task_id)",
                    "GET /api/load/progress/<task_id> - Stream SSE pour la progression",
                    "GET /api/load/status/<task_id> - Statut d'une tâche (polling)",
                    "POST /api/load_dossier - Charger tous les CSV d'un dossier"
                ],
                "recherche": [
                    "POST /api/search - Recherche sémantique avec filtres"
                ],
                "donnees": [
                    "GET /api/message/<id> - Obtenir un message spécifique",
                    "GET /api/context/<id> - Obtenir le contexte d'un message"
                ],
                "configuration": [
                    "GET /api/config - Obtenir la configuration",
                    "POST /api/config - Modifier la configuration",
                    "GET /api/stats - Statistiques d'indexation",
                    "GET /api/collections - Lister les collections",
                    "GET /api/health - Vérifier la santé de l'API"
                ]
            }
        }), 200
    
    # Gestion des erreurs 404
    @app.errorhandler(404)
    def non_trouve(e):
        """Gestion des routes non trouvées."""
        return jsonify({
            "succes": False,
            "erreur": "Route non trouvée",
            "message": "Consultez GET / pour la liste des endpoints disponibles"
        }), 404
    
    # Gestion des erreurs 500
    @app.errorhandler(500)
    def erreur_serveur(e):
        """Gestion des erreurs serveur."""
        return jsonify({
            "succes": False,
            "erreur": "Erreur serveur interne",
            "message": str(e)
        }), 500
    
    return app


def demarrer_serveur(host: str = "127.0.0.1", port: int = 5000, debug: bool = True) -> None:
    """Démarre le serveur Flask.

    Args:
        host: Adresse d'écoute (défaut: localhost uniquement)
        port: Port d'écoute (défaut: 5000)
        debug: Mode debug (défaut: True)
    """
    app = creer_app()
    
    print("=" * 70)
    print("OPSEMIA - Demarrage du serveur")
    print("=" * 70)
    print(f"Interface web: http://{host}:{port}")
    print(f"Recherche: http://{host}:{port}/")
    print(f"Gestion: http://{host}:{port}/gestion")
    print(f"API JSON: http://{host}:{port}/api")
    print(f"Mode debug: {'Active' if debug else 'Desactive'}")
    print("=" * 70)
    print("\nDemarrage en cours...\n")
    
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    demarrer_serveur()

