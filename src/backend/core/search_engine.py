"""Moteur de recherche sémantique avec support des filtres et ranking."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ajouter le répertoire racine au path pour les imports
racine_projet = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(racine_projet))

from config.settings import Parametres
from src.backend.core.filters import combiner_filtres
from src.backend.database.vector_db import BaseVectorielle
from src.backend.models.model_manager import obtenir_encodeur_texte


class MoteurRecherche:
    """Moteur de recherche sémantique avec filtrage et ranking.

    Gère l'encodage des requêtes, l'application des filtres et la recherche
    dans ChromaDB avec support ANN ou KNN.
    """

    def __init__(
        self,
        base_vectorielle: BaseVectorielle,
        parametres: Parametres,
    ) -> None:
        """Initialise le moteur de recherche.

        Args:
            base_vectorielle: Instance de la base vectorielle
            parametres: Paramètres de configuration
        """
        self.db = base_vectorielle
        self.parametres = parametres
        self.encodeur = obtenir_encodeur_texte()

    def rechercher(
        self,
        requete: str,
        nom_collection: str,
        filtres: Optional[Dict[str, Any]] = None,
        nombre_resultats: Optional[int] = None,
        exclure_bruit: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """Recherche sémantique dans une collection avec filtres optionnels.

        Args:
            requete: Texte de la requête utilisateur
            nom_collection: Nom de la collection à rechercher
            filtres: Filtres ChromaDB optionnels (dict) - peut contenir des filtres temporels
            nombre_resultats: Nombre de résultats à retourner (utilise config par défaut si None)
            exclure_bruit: Exclure les messages de bruit (utilise config par défaut si None)

        Returns:
            Liste de résultats avec métadonnées, texte et score de similarité

        Exemple:
            >>> moteur = MoteurRecherche(db, parametres)
            >>> resultats = moteur.rechercher("rendez-vous argent", "messages_cas1")
            >>> for res in resultats:
            >>>     print(f"{res['score']:.3f} - {res['document'][:50]}")
        """
        # Paramètres par défaut
        k = nombre_resultats or self.parametres.NOMBRE_RESULTATS_RECHERCHE
        exclure = exclure_bruit if exclure_bruit is not None else self.parametres.EXCLURE_BRUIT_PAR_DEFAUT

        # Extraire les filtres temporels (post-processing) et construire filtres ChromaDB
        filtres_temporels = self._extraire_filtres_temporels(filtres or {})
        filtres_chromadb = self._construire_filtres_chromadb(filtres or {}, exclure)

        # Encoder la requête
        embedding_requete = self.encodeur.encoder([requete])[0].tolist()

        # Augmenter le nombre de résultats si on a des filtres post-processing
        k_recherche = k * 3 if filtres_temporels else k

        # Rechercher dans ChromaDB avec la méthode configurée
        resultats = self.db.rechercher(
            nom_collection=nom_collection,
            embedding_requete=embedding_requete,
            nombre_resultats=k_recherche,
            filtres=filtres_chromadb if filtres_chromadb else None,
            methode=self.parametres.METHODE_RECHERCHE,
        )

        # Appliquer filtres temporels en post-processing
        if filtres_temporels:
            resultats = self._filtrer_temporel_post(resultats, filtres_temporels)
            resultats = resultats[:k]  # Limiter au nombre demandé

        return resultats

    def rechercher_multi_collections(
        self,
        requete: str,
        noms_collections: List[str],
        filtres: Optional[Dict[str, Any]] = None,
        nombre_resultats: Optional[int] = None,
        exclure_bruit: Optional[bool] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Recherche dans plusieurs collections simultanément.

        Args:
            requete: Texte de la requête utilisateur
            noms_collections: Liste des collections à rechercher
            filtres: Filtres ChromaDB optionnels
            nombre_resultats: Nombre de résultats par collection
            exclure_bruit: Exclure les messages de bruit

        Returns:
            Dictionnaire {nom_collection: liste_resultats}
        """
        resultats_multi = {}
        
        for nom_collection in noms_collections:
            try:
                resultats = self.rechercher(
                    requete=requete,
                    nom_collection=nom_collection,
                    filtres=filtres,
                    nombre_resultats=nombre_resultats,
                    exclure_bruit=exclure_bruit,
                )
                resultats_multi[nom_collection] = resultats
            except Exception as e:
                # Collection n'existe pas ou erreur
                print(f"⚠️  Erreur lors de la recherche dans {nom_collection}: {e}")
                resultats_multi[nom_collection] = []

        return resultats_multi

    def _extraire_filtres_temporels(self, filtres: Dict[str, Any]) -> Dict[str, Any]:
        """Extrait les filtres temporels pour post-processing.

        Args:
            filtres: Dictionnaire de filtres (peut contenir $and avec timestamp)

        Returns:
            Dictionnaire avec timestamp_debut et timestamp_fin si présents
        """
        filtres_temps = {}
        
        # Vérifier si on a une structure $and avec timestamps
        if "$and" in filtres:
            for condition in filtres["$and"]:
                if "timestamp" in condition:
                    ts_cond = condition["timestamp"]
                    if "$gte" in ts_cond:
                        filtres_temps["debut"] = ts_cond["$gte"]
                    if "$lte" in ts_cond:
                        filtres_temps["fin"] = ts_cond["$lte"]
        
        # Vérifier si on a un timestamp simple
        elif "timestamp" in filtres:
            ts_cond = filtres["timestamp"]
            if isinstance(ts_cond, dict):
                if "$gte" in ts_cond:
                    filtres_temps["debut"] = ts_cond["$gte"]
                if "$lte" in ts_cond:
                    filtres_temps["fin"] = ts_cond["$lte"]
        
        return filtres_temps

    def _construire_filtres_chromadb(self, filtres: Dict[str, Any], exclure_bruit: bool) -> Dict[str, Any]:
        """Construit les filtres ChromaDB (sans les temporels).

        Args:
            filtres: Dictionnaire de filtres complet
            exclure_bruit: Si True, ajoute le filtre d'exclusion du bruit

        Returns:
            Filtres ChromaDB compatibles (sans comparaisons temporelles)
        """
        filtres_chromadb = {}
        
        # Ajouter filtres non-temporels (direction, GPS approximatif, etc.)
        for cle, valeur in filtres.items():
            if cle not in ["$and", "timestamp", "timestamp_debut", "timestamp_fin"]:
                filtres_chromadb[cle] = valeur
        
        # Ajouter filtre d'exclusion du bruit
        if exclure_bruit:
            filtres_chromadb["is_noise"] = False
        
        return filtres_chromadb

    def _filtrer_temporel_post(self, resultats: List[Dict[str, Any]], filtres_temps: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filtre les résultats par timestamp en post-processing.

        Args:
            resultats: Liste de résultats de ChromaDB
            filtres_temps: Dict avec "debut" et/ou "fin"

        Returns:
            Résultats filtrés
        """
        resultats_filtres = []
        
        for res in resultats:
            timestamp = res.get("metadata", {}).get("timestamp", "")
            
            if not timestamp:
                continue
            
            # Vérifier si dans la plage temporelle
            dans_plage = True
            
            if "debut" in filtres_temps:
                dans_plage = dans_plage and (timestamp >= filtres_temps["debut"])
            
            if "fin" in filtres_temps:
                dans_plage = dans_plage and (timestamp <= filtres_temps["fin"])
            
            if dans_plage:
                resultats_filtres.append(res)
        
        return resultats_filtres

