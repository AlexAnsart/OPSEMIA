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
        try:
            print(f"🔍 [SEARCH] Encodage requête: '{requete}' pour collection '{nom_collection}'")
            print(f"🔍 [SEARCH] Encodeur actuel: {type(self.encodeur).__name__}")
            print(f"🔍 [SEARCH] Modèle: {self.encodeur.id_modele if hasattr(self.encodeur, 'id_modele') else 'inconnu'}")
            embedding_requete = self.encodeur.encoder([requete])[0].tolist()
            print(f"🔍 [SEARCH] Embedding généré: dimension={len(embedding_requete)}")
        except Exception as e:
            print(f"❌ [SEARCH] Erreur lors de l'encodage de la requête: {e}")
            print(f"❌ [SEARCH] Type d'erreur: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            raise

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
    
    def rechercher_avec_filtrage_doublons(
        self,
        requete: str,
        noms_collections: List[str],
        filtres: Optional[Dict[str, Any]] = None,
        nombre_resultats: Optional[int] = None,
        exclure_bruit: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """Recherche dans plusieurs collections avec filtrage intelligent des doublons.
        
        Cette fonction combine les résultats de recherche provenant de collections
        de messages ET de chunks, en éliminant les doublons (un message peut apparaître
        à la fois comme message individuel et dans un chunk).
        
        Stratégie de déduplication:
        - Si un message apparaît dans les deux types de résultats, on garde celui avec le meilleur score
        - Les chunks sont identifiés par le champ metadata.type = "chunk"
        - On utilise les message_ids des chunks pour détecter les doublons
        
        Args:
            requete: Texte de la requête utilisateur
            noms_collections: Liste des collections à rechercher
            filtres: Filtres ChromaDB optionnels
            nombre_resultats: Nombre TOTAL de résultats à retourner (après déduplication)
            exclure_bruit: Exclure les messages de bruit
            
        Returns:
            Liste de résultats dédupliqués, triés par score décroissant
            
        Exemple:
            >>> moteur = MoteurRecherche(db, parametres)
            >>> # Rechercher dans messages ET chunks
            >>> resultats = moteur.rechercher_avec_filtrage_doublons(
            ...     "rendez-vous", 
            ...     ["messages_cas3", "message_chunks_cas3"]
            ... )
            >>> # Aucun doublon dans les résultats
        """
        # Rechercher avec un nombre augmenté pour compenser les doublons
        k_augmente = (nombre_resultats or self.parametres.NOMBRE_RESULTATS_RECHERCHE) * 2
        
        # Rechercher dans toutes les collections
        tous_resultats = []
        for nom_collection in noms_collections:
            try:
                resultats = self.rechercher(
                    requete=requete,
                    nom_collection=nom_collection,
                    filtres=filtres,
                    nombre_resultats=k_augmente,
                    exclure_bruit=exclure_bruit,
                )
                
                # Ajouter le nom de la collection source à chaque résultat
                for res in resultats:
                    res["collection_source"] = nom_collection
                
                tous_resultats.extend(resultats)
                
            except Exception as e:
                print(f"⚠️  Erreur lors de la recherche dans {nom_collection}: {e}")
                continue
        
        # Dédupliquer et fusionner
        resultats_dedupliques = self._dedupliquer_resultats(tous_resultats)
        
        # Trier par score décroissant
        resultats_dedupliques.sort(key=lambda r: r["score"], reverse=True)
        
        # Limiter au nombre demandé
        k_final = nombre_resultats or self.parametres.NOMBRE_RESULTATS_RECHERCHE
        return resultats_dedupliques[:k_final]
    
    def _dedupliquer_resultats(self, resultats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Déduplique les résultats en gardant le meilleur score pour chaque message unique.
        
        Logique:
        - Un message peut apparaître comme:
          1. Message individuel (type="message", id=message_id)
          2. Dans un ou plusieurs chunks (type="chunk", message_ids=[...])
        - Pour chaque message unique, on garde la meilleure occurrence
        - Pour les chunks, on garde le chunk complet (pas de décomposition)
        
        Args:
            resultats: Liste de tous les résultats (messages + chunks)
            
        Returns:
            Liste dédupliquée
        """
        # Map: message_id -> meilleur résultat pour ce message
        meilleurs_messages: Dict[str, Dict[str, Any]] = {}
        
        # Map: chunk_id -> chunk complet
        chunks_gardes: Dict[str, Dict[str, Any]] = {}
        
        for res in resultats:
            meta = res.get("metadata", {})
            type_resultat = meta.get("type", "message")
            
            if type_resultat == "chunk":
                # C'est un chunk - vérifier si ses messages sont déjà trouvés individuellement
                chunk_id = res.get("id")
                message_ids = meta.get("premier_message_id")  # On utilise le premier message comme clé
                
                if not message_ids:
                    # Chunk sans message_ids (ne devrait pas arriver) - on le garde quand même
                    chunks_gardes[chunk_id] = res
                    continue
                
                # Vérifier si le premier message du chunk a déjà un meilleur score en tant que message individuel
                if message_ids in meilleurs_messages:
                    # Comparer les scores
                    if res["score"] > meilleurs_messages[message_ids]["score"]:
                        # Le chunk a un meilleur score - remplacer le message par le chunk
                        del meilleurs_messages[message_ids]
                        chunks_gardes[chunk_id] = res
                    # Sinon, on garde le message individuel et on ignore le chunk
                else:
                    # Pas encore de message individuel - garder le chunk
                    chunks_gardes[chunk_id] = res
                    
            else:
                # C'est un message individuel
                message_id = res.get("id")
                
                if not message_id:
                    continue
                
                # Vérifier si ce message fait déjà partie d'un chunk gardé
                message_dans_chunk = False
                for chunk in chunks_gardes.values():
                    chunk_meta = chunk.get("metadata", {})
                    premier_msg = chunk_meta.get("premier_message_id")
                    if premier_msg == message_id:
                        # Ce message est le premier d'un chunk déjà gardé
                        if res["score"] > chunk["score"]:
                            # Le message individuel a un meilleur score - garder le message, retirer le chunk
                            chunk_id = chunk.get("id")
                            if chunk_id in chunks_gardes:
                                del chunks_gardes[chunk_id]
                            meilleurs_messages[message_id] = res
                        message_dans_chunk = True
                        break
                
                if not message_dans_chunk:
                    # Vérifier si on a déjà ce message (peut arriver si indexé 2 fois)
                    if message_id in meilleurs_messages:
                        # Garder le meilleur score
                        if res["score"] > meilleurs_messages[message_id]["score"]:
                            meilleurs_messages[message_id] = res
                    else:
                        # Nouveau message
                        meilleurs_messages[message_id] = res
        
        # Combiner messages et chunks gardés
        resultats_finaux = list(meilleurs_messages.values()) + list(chunks_gardes.values())
        
        return resultats_finaux

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
            filtres: Dictionnaire de filtres complet (peut contenir $and)
            exclure_bruit: Si True, ajoute le filtre d'exclusion du bruit

        Returns:
            Filtres ChromaDB compatibles (sans comparaisons temporelles)
            
        Note:
            ChromaDB nécessite que plusieurs conditions soient dans un $and.
            Un dict avec plusieurs clés {k1: v1, k2: v2} génère une erreur.
        """
        conditions = []
        
        # Si on a un $and, extraire les conditions non-temporelles
        if "$and" in filtres:
            for condition in filtres["$and"]:
                # Ignorer les conditions sur timestamp (post-processing)
                if "timestamp" not in condition:
                    conditions.append(condition)
        else:
            # Format simple : extraire chaque clé non-temporelle comme une condition
            for cle, valeur in filtres.items():
                if cle not in ["timestamp", "timestamp_debut", "timestamp_fin"]:
                    conditions.append({cle: valeur})
        
        # Ajouter le filtre d'exclusion du bruit si demandé
        if exclure_bruit:
            conditions.append({"is_noise": False})
        
        # Retourner selon le nombre de conditions
        if len(conditions) == 0:
            return {}
        elif len(conditions) == 1:
            # Une seule condition : retourner directement
            return conditions[0]
        else:
            # Plusieurs conditions : TOUJOURS utiliser $and
            return {"$and": conditions}

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

