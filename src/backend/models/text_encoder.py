from __future__ import annotations

from typing import Iterable, List

import numpy as np
import torch
from sentence_transformers import SentenceTransformer


class EncodeurTexte:
    """Enveloppe fine autour d'un SentenceTransformer pour l'embedding de texte.

    L'encodeur charge le modèle sur le périphérique demandé et expose une seule
    méthode encoder retournant des embeddings L2-normalisés comme arrays numpy.
    """

    def __init__(self, id_modele: str, preference_peripherique: str = "auto") -> None:
        self.id_modele: str = id_modele
        self.peripherique: str = self._resoudre_peripherique(preference_peripherique)
        # Certains modèles (Jina, etc.) nécessitent trust_remote_code=True
        try:
            self.modele: SentenceTransformer = SentenceTransformer(
                self.id_modele, 
                device=self.peripherique,
                trust_remote_code=True
            )
        except Exception:
            # Fallback sans trust_remote_code pour les modèles standards
            self.modele: SentenceTransformer = SentenceTransformer(
                self.id_modele, 
                device=self.peripherique
            )

    def _resoudre_peripherique(self, preference_peripherique: str) -> str:
        if preference_peripherique == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        if preference_peripherique in {"cpu", "cuda"}:
            return preference_peripherique
        return "cpu"

    def encoder(self, textes: Iterable[str], taille_lot: int = 32) -> np.ndarray:
        """Embed une séquence de textes en vecteurs L2-normalisés.

        Retourne un array numpy de forme (N, D).
        """
        # normalize_embeddings assure que la similarité cosinus est le produit scalaire
        embeddings: np.ndarray = self.modele.encode(
            list(textes),
            batch_size=taille_lot,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings

    @property
    def dimension_embedding(self) -> int:
        return int(self.modele.get_sentence_embedding_dimension())


def charger_encodeur_texte_depuis_parametres(parametres: object) -> EncodeurTexte:
    """Factory qui instancie l'encodeur de texte depuis un objet paramètres minimal.

    L'objet paramètres est censé exposer ID_MODELE_EMBEDDING et PERIPHERIQUE_EMBEDDING.
    """
    id_modele: str = getattr(parametres, "ID_MODELE_EMBEDDING")
    pref_peripherique: str = getattr(parametres, "PERIPHERIQUE_EMBEDDING", "auto")
    return EncodeurTexte(id_modele=id_modele, preference_peripherique=pref_peripherique)


