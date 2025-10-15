"""Configuration centralisée pour OPSEMIA.

Tous les paramètres configurables chargés depuis settings.json.
Les modifications via l'interface web sont persistées dans ce fichier JSON.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# Chemin vers le fichier de configuration JSON
CHEMIN_CONFIG_JSON = Path(__file__).parent / "settings.json"

# Modèles d'embedding disponibles
MODELES_DISPONIBLES = [
    {
        "id": "BAAI/bge-m3",
        "nom": "BGE-M3",
        "description": "Modèle multilingue performant (~2.2GB)",
        "dimensions": 1024
    },
    {
        "id": "jinaai/jina-embeddings-v3",
        "nom": "Jina Embeddings v3",
        "description": "Optimisé pour la recherche multilingue",
        "dimensions": 1024
    },
    {
        "id": "Qwen/Qwen3-Embedding-8B",
        "nom": "Qwen3 Embedding 8B",
        "description": "Modèle très performant mais volumineux (~8GB)",
        "dimensions": 8192
    },
    {
        "id": "OrdalieTech/Solon-embeddings-large-0.1",
        "nom": "Solon Embeddings Large",
        "description": "Modèle français optimisé",
        "dimensions": 1024
    }
]


class Parametres:
    """Paramètres de configuration pour OPSEMIA.

    Chargés depuis settings.json et modifiables via l'interface web.
    """

    def __init__(self):
        """Initialise les paramètres en chargeant le fichier JSON."""
        self._charger_config()

    def _charger_config(self) -> None:
        """Charge la configuration depuis le fichier JSON."""
        if not CHEMIN_CONFIG_JSON.exists():
            # Créer la configuration par défaut
            self._creer_config_defaut()

        with open(CHEMIN_CONFIG_JSON, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Charger les paramètres depuis le JSON
        encodage = config.get("encodage", {})
        chunking = config.get("chunking", {})
        base_vectorielle = config.get("base_vectorielle", {})
        recherche = config.get("recherche", {})
        donnees = config.get("donnees", {})

        # ENCODAGE
        self.ID_MODELE_EMBEDDING = encodage.get("id_modele_embedding", "BAAI/bge-m3")
        self.PERIPHERIQUE_EMBEDDING = encodage.get("peripherique_embedding", "auto")

        # CHUNKING
        self.TAILLE_FENETRE_CHUNK = chunking.get("taille_fenetre_chunk", 1)
        self.OVERLAP_FENETRE_CHUNK = chunking.get("overlap_fenetre_chunk", 1)

        # BASE VECTORIELLE
        chemin_relatif = base_vectorielle.get("chemin_base_chroma", "data/chroma_db")
        if Path(chemin_relatif).is_absolute():
            self.CHEMIN_BASE_CHROMA = str(chemin_relatif)
        else:
            self.CHEMIN_BASE_CHROMA = str(
                Path(__file__).resolve().parents[1] / chemin_relatif
            )
        self.NOM_COLLECTION_MESSAGES = base_vectorielle.get("nom_collection_messages", "messages")
        self.NOM_COLLECTION_CHUNKS = base_vectorielle.get("nom_collection_chunks", "message_chunks")

        # RECHERCHE
        self.METHODE_RECHERCHE = recherche.get("methode_recherche", "KNN")
        self.NOMBRE_RESULTATS_RECHERCHE = recherche.get("nombre_resultats_recherche", 10)
        self.EXCLURE_BRUIT_PAR_DEFAUT = recherche.get("exclure_bruit_par_defaut", False)
        self.SEUIL_DISTANCE_MAX = recherche.get("seuil_distance_max", None)

        # DONNÉES
        chemin_csv = donnees.get("chemin_csv_donnees", "Cas/Cas1/sms.csv")
        if Path(chemin_csv).is_absolute():
            self.CHEMIN_CSV_DONNEES = str(chemin_csv)
        else:
            self.CHEMIN_CSV_DONNEES = str(
                Path(__file__).resolve().parents[1] / chemin_csv
            )

    def _creer_config_defaut(self) -> None:
        """Crée le fichier de configuration par défaut."""
        config_defaut = {
            "encodage": {
                "id_modele_embedding": "BAAI/bge-m3",
                "peripherique_embedding": "auto"
            },
            "chunking": {
                "taille_fenetre_chunk": 1,
                "overlap_fenetre_chunk": 1
            },
            "base_vectorielle": {
                "chemin_base_chroma": "data/chroma_db",
                "nom_collection_messages": "messages",
                "nom_collection_chunks": "message_chunks"
            },
            "recherche": {
                "methode_recherche": "KNN",
                "nombre_resultats_recherche": 10,
                "exclure_bruit_par_defaut": False,
                "seuil_distance_max": None
            },
            "donnees": {
                "chemin_csv_donnees": "Cas/Cas1/sms.csv"
            }
        }

        with open(CHEMIN_CONFIG_JSON, 'w', encoding='utf-8') as f:
            json.dump(config_defaut, f, indent=2, ensure_ascii=False)

    def sauvegarder(self, modifications: dict[str, Any]) -> None:
        """Sauvegarde les modifications dans le fichier JSON.

        Args:
            modifications: Dictionnaire des paramètres à modifier
        """
        # Charger la config actuelle
        with open(CHEMIN_CONFIG_JSON, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Appliquer les modifications
        if "id_modele_embedding" in modifications:
            config["encodage"]["id_modele_embedding"] = modifications["id_modele_embedding"]
            self.ID_MODELE_EMBEDDING = modifications["id_modele_embedding"]

        if "peripherique_embedding" in modifications:
            config["encodage"]["peripherique_embedding"] = modifications["peripherique_embedding"]
            self.PERIPHERIQUE_EMBEDDING = modifications["peripherique_embedding"]

        if "taille_fenetre_chunk" in modifications:
            config["chunking"]["taille_fenetre_chunk"] = int(modifications["taille_fenetre_chunk"])
            self.TAILLE_FENETRE_CHUNK = int(modifications["taille_fenetre_chunk"])

        if "overlap_fenetre_chunk" in modifications:
            config["chunking"]["overlap_fenetre_chunk"] = int(modifications["overlap_fenetre_chunk"])
            self.OVERLAP_FENETRE_CHUNK = int(modifications["overlap_fenetre_chunk"])

        if "methode_recherche" in modifications:
            config["recherche"]["methode_recherche"] = modifications["methode_recherche"]
            self.METHODE_RECHERCHE = modifications["methode_recherche"]

        if "nombre_resultats_recherche" in modifications:
            config["recherche"]["nombre_resultats_recherche"] = int(modifications["nombre_resultats_recherche"])
            self.NOMBRE_RESULTATS_RECHERCHE = int(modifications["nombre_resultats_recherche"])

        if "exclure_bruit_par_defaut" in modifications:
            config["recherche"]["exclure_bruit_par_defaut"] = bool(modifications["exclure_bruit_par_defaut"])
            self.EXCLURE_BRUIT_PAR_DEFAUT = bool(modifications["exclure_bruit_par_defaut"])

        if "seuil_distance_max" in modifications:
            config["recherche"]["seuil_distance_max"] = modifications["seuil_distance_max"]
            self.SEUIL_DISTANCE_MAX = modifications["seuil_distance_max"]

        # Sauvegarder dans le fichier
        with open(CHEMIN_CONFIG_JSON, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)


# Instance globale des paramètres
_parametres_instance = None


def obtenir_parametres() -> Parametres:
    """Retourne l'instance singleton des paramètres."""
    global _parametres_instance
    if _parametres_instance is None:
        _parametres_instance = Parametres()
    return _parametres_instance


def recharger_parametres() -> Parametres:
    """Recharge les paramètres depuis le fichier JSON."""
    global _parametres_instance
    _parametres_instance = Parametres()
    return _parametres_instance
