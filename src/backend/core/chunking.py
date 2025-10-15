"""Service de chunking pour créer des fenêtres de contexte glissantes."""

from __future__ import annotations

from typing import Any, Dict, List


def creer_chunks_fenetre_glissante(
    messages: List[Dict[str, Any]],
    taille_fenetre: int = 5,
    overlap: int = 2,
) -> List[Dict[str, Any]]:
    """Crée des chunks de contexte avec fenêtre glissante sur les messages.

    Chaque chunk contient N messages consécutifs pour préserver le contexte conversationnel.
    Les chunks se chevauchent pour assurer la continuité.

    Args:
        messages: Liste de messages normalisés (doit contenir au minimum 'id' et 'message')
        taille_fenetre: Nombre de messages par chunk
        overlap: Nombre de messages qui se chevauchent entre chunks adjacents

    Returns:
        Liste de chunks, chaque chunk contenant:
        - chunk_id: Identifiant unique du chunk
        - message_ids: Liste des IDs de messages contenus
        - texte_concatene: Texte combiné de tous les messages du chunk
        - metadata: Métadonnées du premier message (timestamp, etc.)
    """
    if taille_fenetre <= 0:
        raise ValueError("taille_fenetre doit être > 0")
    if overlap < 0 or overlap > taille_fenetre:
        raise ValueError("overlap doit être >= 0 et <= taille_fenetre")

    chunks: List[Dict[str, Any]] = []
    pas = taille_fenetre - overlap  # Décalage entre chunks
    
    # Cas spécial : si overlap = taille_fenetre, on crée un seul chunk avec tous les messages
    if pas <= 0:
        if len(messages) > 0:
            textes = [msg.get("message", "") for msg in messages]
            ids = [msg.get("id", f"msg_{i}") for i, msg in enumerate(messages)]
            
            chunk = {
                "chunk_id": "chunk_all_messages",
                "message_ids": ids,
                "texte_concatene": " ".join(filter(None, textes)),
                "metadata": {
                    "timestamp": messages[0].get("timestamp"),
                    "premier_message_id": ids[0],
                    "dernier_message_id": ids[-1],
                    "nombre_messages": len(messages),
                    "index_debut": 0,
                    "is_noise": False,  # Chunks ne sont jamais du bruit
                },
            }
            chunks.append(chunk)
        return chunks

    for i in range(0, len(messages), pas):
        fenetre = messages[i : i + taille_fenetre]
        if not fenetre:
            break

        # Concaténer les textes des messages de la fenêtre
        textes = [msg.get("message", "") for msg in fenetre]
        ids = [msg.get("id", f"msg_{i+j}") for j, msg in enumerate(fenetre)]

        chunk = {
            "chunk_id": f"chunk_{i}_{i+len(fenetre)-1}",
            "message_ids": ids,
            "texte_concatene": " ".join(filter(None, textes)),
            "metadata": {
                "timestamp": fenetre[0].get("timestamp"),
                "premier_message_id": ids[0],
                "dernier_message_id": ids[-1],
                "nombre_messages": len(fenetre),
                "index_debut": i,
                "is_noise": False,  # Chunks ne sont jamais du bruit
            },
        }
        chunks.append(chunk)

        # Arrêter si la dernière fenêtre est incomplète et qu'on a déjà tout couvert
        if len(fenetre) < taille_fenetre:
            break

    return chunks

