from __future__ import annotations

import sys
from pathlib import Path

# Ajouter le répertoire racine au path pour les imports
racine_projet = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(racine_projet))

from config.settings import obtenir_parametres
from src.backend.parsers.message_extractor import parser_sms_depuis_csv
from src.backend.models.model_manager import obtenir_encodeur_texte
import time


def executer_pipeline_complet() -> None:
    """Test minimal: lire le CSV et encoder UN seul message pertinent.

    On sélectionne la première ligne dont le message contient un mot-clé
    significatif (par ex. "drogue"). Si aucune correspondance, on prend la
    première ligne non vide.
    """
    parametres = obtenir_parametres()

    print("=" * 70)
    print("OPSEMIA - Test d'encodage d'un seul message")
    print("=" * 70)

    # 1) Lecture du CSV
    debut = time.time()
    messages = parser_sms_depuis_csv(Path(parametres.CHEMIN_CSV_DONNEES))
    print(f"   ✓ {len(messages)} messages chargés ({time.time() - debut:.2f}s)")

    # 2) Sélection d'un message pertinent
    mots_cles = ["drogue", "cocaine", "exta", "argent", "rendez", "vende"]
    message_selectionne = None
    for m in messages:
        contenu = (m.get("message") or "").lower()
        if any(mk in contenu for mk in mots_cles) and contenu:
            message_selectionne = m
            break
    if message_selectionne is None:
        # fallback: première ligne avec message non vide
        for m in messages:
            if (m.get("message") or "").strip():
                message_selectionne = m
                break

    if message_selectionne is None:
        print("⚠️ Aucun message textuel utilisable trouvé dans le CSV.")
        return

    texte = message_selectionne.get("message") or ""
    print(f"\n📝 Message sélectionné (id={message_selectionne.get('id')}):")
    print(f"   → {texte}")

    # 3) Encodage d'un seul message
    encodeur = obtenir_encodeur_texte()
    print(f"\n🧠 Modèle: {parametres.ID_MODELE_EMBEDDING} (dim={encodeur.dimension_embedding})")
    debut = time.time()
    embedding = encodeur.encoder([texte])
    duree = time.time() - debut
    print(f"   ✓ Embedding généré en {duree:.2f}s, forme={embedding.shape}")


if __name__ == "__main__":
    executer_pipeline_complet()


