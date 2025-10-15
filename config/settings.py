"""Configuration centralisée pour OPSEMIA.

Tous les paramètres configurables pour l'encodage, le chunking et la base vectorielle.
"""

from pathlib import Path


class Parametres:
    """Paramètres de configuration pour OPSEMIA.

    ENCODAGE:
    - ID_MODELE_EMBEDDING: ID Hugging Face du sentence-transformer (BGE-M3 par défaut)
    - PERIPHERIQUE_EMBEDDING: "auto" sélectionne CUDA si disponible, sinon CPU
    
    CHUNKING:
    - TAILLE_FENETRE_CHUNK: Nombre de messages dans une fenêtre glissante de contexte
    - OVERLAP_FENETRE_CHUNK: Nombre de messages qui se chevauchent entre chunks adjacents
    
    BASE VECTORIELLE:
    - CHEMIN_BASE_CHROMA: Répertoire de stockage pour ChromaDB (SQLite backend)
    - NOM_COLLECTION_MESSAGES: Nom de la collection pour messages individuels
    - NOM_COLLECTION_CHUNKS: Nom de la collection pour chunks de contexte
    
    DONNÉES:
    - CHEMIN_CSV_DONNEES: Chemin vers le CSV de démo par défaut (Cas1)
    """

    # ========== ENCODAGE ==========
    ID_MODELE_EMBEDDING: str = "BAAI/bge-m3"
    PERIPHERIQUE_EMBEDDING: str = "auto"  # "auto" | "cpu" | "cuda"

    # ========== CHUNKING ==========
    TAILLE_FENETRE_CHUNK: int = 1  # Nombre de messages par chunk de contexte
    OVERLAP_FENETRE_CHUNK: int = 1  # Nombre de messages qui se chevauchent

    # ========== BASE VECTORIELLE ==========
    CHEMIN_BASE_CHROMA: str = str(Path(__file__).resolve().parents[1] / "data" / "chroma_db")
    NOM_COLLECTION_MESSAGES: str = "messages"
    NOM_COLLECTION_CHUNKS: str = "message_chunks"

    # ========== DONNÉES ==========
    CHEMIN_CSV_DONNEES: str = str(
        Path(__file__).resolve().parents[1]
        / "Cas"
        / "Cas1"
        / "sms.csv"
    )


def obtenir_parametres() -> Parametres:
    """Retourne les paramètres. Hook conservé pour l'extensibilité future sans changer les imports."""
    return Parametres()


