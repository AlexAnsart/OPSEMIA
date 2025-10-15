"""Wrapper ChromaDB pour la gestion de la base vectorielle."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
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
            collection = self.client.create_collection(
                name=nom_collection,
                metadata={"dimension": dimension_embedding} if dimension_embedding else {},
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

