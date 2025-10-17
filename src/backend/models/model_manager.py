from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

# Ajouter le répertoire racine au path pour les imports
racine_projet = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(racine_projet))

from config.settings import obtenir_parametres
from .text_encoder import EncodeurTexte, charger_encodeur_texte_depuis_parametres


_encodeur_texte_singleton: Optional[EncodeurTexte] = None


def obtenir_encodeur_texte() -> EncodeurTexte:
    """Retourne une instance EncodeurTexte mise en cache configurée via les paramètres.

    Cela évite de recharger le gros modèle d'embedding plusieurs fois.
    """
    global _encodeur_texte_singleton
    if _encodeur_texte_singleton is None:
        print("🔄 [MODEL_MANAGER] Premier chargement de l'encodeur...")
        parametres = obtenir_parametres()
        print(f"🔄 [MODEL_MANAGER] Modèle: {parametres.ID_MODELE_EMBEDDING}, Device: {parametres.PERIPHERIQUE_EMBEDDING}")
        _encodeur_texte_singleton = charger_encodeur_texte_depuis_parametres(parametres)
        print(f"✅ [MODEL_MANAGER] Encodeur chargé avec succès")
    else:
        print(f"♻️  [MODEL_MANAGER] Utilisation de l'encodeur en cache: {_encodeur_texte_singleton.id_modele}")
    return _encodeur_texte_singleton


def recharger_encodeur_texte() -> EncodeurTexte:
    """Force le rechargement de l'encodeur depuis les paramètres actuels.
    
    Utilisé quand la configuration du modèle change (modèle ou périphérique).
    ATTENTION : Peut prendre plusieurs secondes pour les gros modèles (ex: Qwen3 ~8GB).
    
    Returns:
        Le nouvel encodeur rechargé
    """
    global _encodeur_texte_singleton
    print("🔄 [MODEL_MANAGER] Rechargement forcé de l'encodeur...")
    parametres = obtenir_parametres()
    print(f"🔄 [MODEL_MANAGER] Nouveau modèle: {parametres.ID_MODELE_EMBEDDING}, Device: {parametres.PERIPHERIQUE_EMBEDDING}")
    try:
        _encodeur_texte_singleton = charger_encodeur_texte_depuis_parametres(parametres)
        print(f"✅ [MODEL_MANAGER] Encodeur rechargé avec succès")
    except Exception as e:
        print(f"❌ [MODEL_MANAGER] Erreur lors du rechargement: {e}")
        import traceback
        traceback.print_exc()
        raise
    return _encodeur_texte_singleton


def obtenir_id_modele_actuel() -> str:
    """Retourne l'ID du modèle actuellement chargé dans le singleton.
    
    Returns:
        ID du modèle ou None si aucun encodeur n'est chargé
    """
    global _encodeur_texte_singleton
    if _encodeur_texte_singleton is None:
        return None
    return _encodeur_texte_singleton.id_modele


