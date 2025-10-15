"""Wrapper ChromaDB pour la gestion de la base vectorielle."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
import numpy as np
from chromadb.config import Settings as ChromaSettings


class BaseVectorielle:
    """Gestionnaire de la base vectorielle ChromaDB avec backend SQLite.

    Gère les collections pour messages individuels et chunks de contexte.
    """

    def __init__(self, chemin_persistance: str | Path) -> None:
        """Initialise la connexion ChromaDB avec persistance SQLite.

        Args:
            chemin_persistance: Chemin vers le répertoire de stockage ChromaDB
        """
        self.chemin_persistance = Path(chemin_persistance)
        self.chemin_persistance.mkdir(parents=True, exist_ok=True)

        # Configuration ChromaDB avec backend SQLite
        self.client = chromadb.PersistentClient(
            path=str(self.chemin_persistance),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

    def obtenir_ou_creer_collection(
        self,
        nom_collection: str,
        dimension_embedding: Optional[int] = None,
    ) -> chromadb.Collection:
        """Obtient une collection existante ou en crée une nouvelle.

        Args:
            nom_collection: Nom de la collection
            dimension_embedding: Dimension des embeddings (optionnel, pour validation)

        Returns:
            Collection ChromaDB
        """
        try:
            collection = self.client.get_collection(name=nom_collection)
        except Exception:
            # Collection n'existe pas, on la crée
            # ChromaDB exige des métadonnées non vides
            metadata = {"dimension": dimension_embedding} if dimension_embedding else {"created_by": "opsemia"}
            collection = self.client.create_collection(
                name=nom_collection,
                metadata=metadata,
            )
        return collection

    def ajouter_messages(
        self,
        nom_collection: str,
        ids: List[str],
        embeddings: List[List[float]],
        metadonnees: List[Dict[str, Any]],
        documents: Optional[List[str]] = None,
    ) -> None:
        """Ajoute des messages à la collection.

        Args:
            nom_collection: Nom de la collection
            ids: Liste d'identifiants uniques
            embeddings: Liste de vecteurs d'embedding
            metadonnees: Liste de métadonnées (doit être JSON-serializable)
            documents: Liste de textes originaux (optionnel)
        """
        collection = self.obtenir_ou_creer_collection(nom_collection)
        
        # ChromaDB nécessite que les métadonnées soient JSON-serializable
        metadonnees_nettoyees = [self._nettoyer_metadonnees(m) for m in metadonnees]

        collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadonnees_nettoyees,
            documents=documents,
        )

    def _nettoyer_metadonnees(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Nettoie les métadonnées pour ChromaDB (str, int, float, bool seulement).

        Args:
            meta: Métadonnées brutes

        Returns:
            Métadonnées nettoyées et JSON-serializable
        """
        nettoyees = {}
        for cle, valeur in meta.items():
            if valeur is None:
                nettoyees[cle] = ""
            elif isinstance(valeur, (str, int, float, bool)):
                nettoyees[cle] = valeur
            elif isinstance(valeur, list):
                # Convertir les listes en chaînes séparées par des virgules
                nettoyees[cle] = ",".join(str(v) for v in valeur)
            else:
                # Convertir tout le reste en string
                nettoyees[cle] = str(valeur)
        return nettoyees

    def supprimer_collection(self, nom_collection: str) -> None:
        """Supprime complètement une collection.

        Args:
            nom_collection: Nom de la collection à supprimer
        """
        try:
            self.client.delete_collection(name=nom_collection)
        except Exception:
            pass  # Collection n'existe pas, rien à faire

    def compter_documents(self, nom_collection: str) -> int:
        """Compte le nombre de documents dans une collection.

        Args:
            nom_collection: Nom de la collection

        Returns:
            Nombre de documents
        """
        try:
            collection = self.client.get_collection(name=nom_collection)
            return collection.count()
        except Exception:
            return 0

    def rechercher(
        self,
        nom_collection: str,
        embedding_requete: List[float],
        nombre_resultats: int,
        filtres: Optional[Dict[str, Any]] = None,
        methode: str = "KNN",
    ) -> List[Dict[str, Any]]:
        """Recherche les documents les plus similaires à la requête.

        Args:
            nom_collection: Nom de la collection à rechercher
            embedding_requete: Vecteur d'embedding de la requête
            nombre_resultats: Nombre de résultats à retourner
            filtres: Filtres ChromaDB optionnels (where clause)
            methode: "ANN" (rapide, ~95-99% précis) ou "KNN" (exact, plus lent)

        Returns:
            Liste de résultats avec métadonnées, documents et distances

        Exemple:
            >>> db = BaseVectorielle("data/chroma_db")
            >>> resultats = db.rechercher("messages_cas1", embedding, nombre_resultats=5)
        """
        try:
            collection = self.client.get_collection(name=nom_collection)
        except Exception as e:
            raise ValueError(f"Collection '{nom_collection}' introuvable: {e}")

        if methode.upper() == "KNN":
            # KNN exact: brute-force avec calcul manuel des distances
            return self._recherche_knn_exact(
                collection, embedding_requete, nombre_resultats, filtres
            )
        else:
            # ANN: utilise l'index HNSW de ChromaDB (rapide)
            return self._recherche_ann_hnsw(
                collection, embedding_requete, nombre_resultats, filtres
            )

    def _recherche_ann_hnsw(
        self,
        collection: chromadb.Collection,
        embedding_requete: List[float],
        nombre_resultats: int,
        filtres: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Recherche ANN avec index HNSW (rapide, approximative).

        Args:
            collection: Collection ChromaDB
            embedding_requete: Vecteur d'embedding de la requête
            nombre_resultats: Nombre de résultats
            filtres: Filtres optionnels

        Returns:
            Liste de résultats formatés
        """
        # Recherche vectorielle dans ChromaDB avec HNSW
        resultats_bruts = collection.query(
            query_embeddings=[embedding_requete],
            n_results=nombre_resultats,
            where=filtres,
            include=["metadatas", "documents", "distances"],
        )

        # Formatter les résultats
        resultats_formates = []
        
        # ChromaDB retourne des listes de listes (pour supporter les requêtes batch)
        # On prend uniquement la première requête (index 0)
        if resultats_bruts["ids"] and len(resultats_bruts["ids"][0]) > 0:
            for i in range(len(resultats_bruts["ids"][0])):
                resultat = {
                    "id": resultats_bruts["ids"][0][i],
                    "distance": resultats_bruts["distances"][0][i],
                    "score": 1 - resultats_bruts["distances"][0][i],  # Convertir distance en similarité
                    "metadata": resultats_bruts["metadatas"][0][i] if resultats_bruts["metadatas"] else {},
                    "document": resultats_bruts["documents"][0][i] if resultats_bruts["documents"] else "",
                }
                resultats_formates.append(resultat)

        return resultats_formates

    def _recherche_knn_exact(
        self,
        collection: chromadb.Collection,
        embedding_requete: List[float],
        nombre_resultats: int,
        filtres: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Recherche KNN exacte (brute-force avec calcul manuel des distances).

        Args:
            collection: Collection ChromaDB
            embedding_requete: Vecteur d'embedding de la requête
            nombre_resultats: Nombre de résultats
            filtres: Filtres optionnels

        Returns:
            Liste de résultats formatés
        """
        # Récupérer TOUS les documents de la collection (avec filtres si fournis)
        # ChromaDB limite à 10000 résultats par défaut, on augmente pour être sûr
        count = collection.count()
        
        resultats_bruts = collection.get(
            where=filtres,
            include=["embeddings", "metadatas", "documents"],
            limit=count if count > 0 else 10000,
        )

        if not resultats_bruts["ids"] or len(resultats_bruts["ids"]) == 0:
            return []

        # Convertir en numpy pour calculs vectoriels rapides
        embeddings_db = np.array(resultats_bruts["embeddings"])
        embedding_req = np.array(embedding_requete)

        # Calculer les distances cosine manuellement
        # Distance cosine = 1 - cosine_similarity
        # cosine_similarity = dot(A, B) / (norm(A) * norm(B))
        normes_db = np.linalg.norm(embeddings_db, axis=1)
        norme_req = np.linalg.norm(embedding_req)
        
        # Éviter division par zéro
        normes_db = np.where(normes_db == 0, 1e-10, normes_db)
        norme_req = norme_req if norme_req != 0 else 1e-10
        
        # Produits scalaires
        dots = np.dot(embeddings_db, embedding_req)
        
        # Similarités cosine
        similarites = dots / (normes_db * norme_req)
        
        # Distances cosine (1 - similarité)
        distances = 1 - similarites

        # Trier par distance croissante et prendre les top K
        indices_tries = np.argsort(distances)[:nombre_resultats]

        # Formatter les résultats
        resultats_formates = []
        for idx in indices_tries:
            resultat = {
                "id": resultats_bruts["ids"][idx],
                "distance": float(distances[idx]),
                "score": float(similarites[idx]),
                "metadata": resultats_bruts["metadatas"][idx] if resultats_bruts["metadatas"] else {},
                "document": resultats_bruts["documents"][idx] if resultats_bruts["documents"] else "",
            }
            resultats_formates.append(resultat)

        return resultats_formates

