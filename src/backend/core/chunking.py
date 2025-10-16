"""Service de chunking intelligent pour créer des fenêtres de contexte par conversation."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List


def _identifier_interlocuteur(message: Dict[str, Any], numero_utilisateur: str = "user") -> str:
    """Identifie l'interlocuteur d'un message (la personne avec qui on converse).
    
    Args:
        message: Message normalisé avec 'direction', 'from', 'to'
        numero_utilisateur: Identifiant de l'utilisateur principal (défaut: "user")
        
    Returns:
        Identifiant de l'interlocuteur
    """
    direction = message.get("direction", "")
    
    if direction == "incoming":
        # Message reçu → l'interlocuteur est l'expéditeur
        return message.get("from", "inconnu")
    else:
        # Message envoyé → l'interlocuteur est le destinataire
        return message.get("to", "inconnu")


def _grouper_par_conversation(messages: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Groupe les messages par conversation (même interlocuteur).
    
    Args:
        messages: Liste de tous les messages
        
    Returns:
        Dictionnaire {interlocuteur: [liste de messages]}
    """
    conversations = defaultdict(list)
    
    for msg in messages:
        interlocuteur = _identifier_interlocuteur(msg)
        conversations[interlocuteur].append(msg)
    
    # Trier chaque conversation par timestamp
    for interlocuteur in conversations:
        conversations[interlocuteur].sort(
            key=lambda m: m.get("timestamp", "")
        )
    
    return dict(conversations)


def _formater_message_pour_chunk(message: Dict[str, Any]) -> str:
    """Formate un message pour l'inclure dans un chunk de contexte.
    
    Args:
        message: Message normalisé
        
    Returns:
        Texte formaté avec timestamp et direction
    """
    timestamp = message.get("timestamp", "")
    direction = message.get("direction", "")
    contact_name = message.get("contact_name", "Inconnu")
    contenu = message.get("message", "")
    
    # Format: [timestamp] Direction: message
    direction_label = "Moi" if direction == "outgoing" else contact_name
    
    # Extraire juste la date/heure sans les millisecondes
    ts_simple = timestamp.split("T")[0] + " " + timestamp.split("T")[1][:5] if "T" in timestamp else timestamp
    
    return f"[{ts_simple}] {direction_label}: {contenu}"


def creer_chunks_par_conversation(
    messages: List[Dict[str, Any]],
    taille_fenetre: int = 3,
    overlap: int = 1,
) -> List[Dict[str, Any]]:
    """Crée des chunks de contexte intelligents, groupés par conversation.
    
    Cette fonction groupe d'abord les messages par conversation (même interlocuteur),
    puis crée des chunks au sein de chaque conversation avec fenêtre glissante.
    
    Avantages:
    - Les chunks ne mélangent jamais plusieurs conversations
    - Le contexte conversationnel est préservé
    - La recherche peut retrouver des extraits de conversation pertinents
    
    Args:
        messages: Liste de messages normalisés (triés par timestamp si possible)
        taille_fenetre: Nombre de messages par chunk
        overlap: Nombre de messages qui se chevauchent entre chunks adjacents
        
    Returns:
        Liste de chunks avec métadonnées enrichies:
        - chunk_id: Identifiant unique
        - message_ids: Liste des IDs de messages contenus
        - texte_concatene: Texte formaté des messages
        - metadata: timestamp, contact, premier_message_id, etc.
        
    Exemple:
        >>> messages = [...] # 10 messages avec Alice, 5 avec Bob
        >>> chunks = creer_chunks_par_conversation(messages, taille_fenetre=3, overlap=1)
        >>> # Résultat: chunks séparés pour Alice et Bob, sans mélange
    """
    if taille_fenetre <= 0:
        raise ValueError("taille_fenetre doit être > 0")
    if overlap < 0:
        raise ValueError("overlap doit être >= 0")
    if overlap >= taille_fenetre:
        # Si overlap >= taille_fenetre, pas de progression → 1 seul chunk par conversation
        overlap = taille_fenetre - 1
    
    # Étape 1: Grouper par conversation
    conversations = _grouper_par_conversation(messages)
    
    # Étape 2: Créer des chunks pour chaque conversation
    tous_les_chunks: List[Dict[str, Any]] = []
    compteur_global_chunks = 0
    
    for interlocuteur, messages_conv in conversations.items():
        if not messages_conv:
            continue
        
        # Informations de la conversation
        contact_name = messages_conv[0].get("contact_name", interlocuteur)
        
        # Créer les chunks pour cette conversation
        chunks_conv = _creer_chunks_pour_une_conversation(
            messages_conv,
            taille_fenetre,
            overlap,
            interlocuteur,
            contact_name,
            compteur_global_chunks
        )
        
        tous_les_chunks.extend(chunks_conv)
        compteur_global_chunks += len(chunks_conv)
    
    return tous_les_chunks


def _creer_chunks_pour_une_conversation(
    messages: List[Dict[str, Any]],
    taille_fenetre: int,
    overlap: int,
    interlocuteur: str,
    contact_name: str,
    offset_chunk_id: int,
) -> List[Dict[str, Any]]:
    """Crée des chunks pour une seule conversation avec fenêtre glissante.
    
    IMPORTANT: Les chunks de 1 seul message sont automatiquement filtrés car 
    ils sont redondants (les messages sont déjà indexés individuellement).
    
    Args:
        messages: Messages de la conversation (déjà triés par timestamp)
        taille_fenetre: Taille de la fenêtre
        overlap: Chevauchement
        interlocuteur: Identifiant de l'interlocuteur
        contact_name: Nom du contact
        offset_chunk_id: Offset pour l'ID global du chunk
        
    Returns:
        Liste de chunks pour cette conversation (seulement ceux avec 2+ messages)
    """
    chunks = []
    pas = max(1, taille_fenetre - overlap)  # Décalage entre chunks (min 1)
    
    for i in range(0, len(messages), pas):
        fenetre = messages[i : i + taille_fenetre]
        if not fenetre:
            break
        
        # FILTRAGE: Ignorer les chunks de 1 seul message (redondant avec messages individuels)
        if len(fenetre) < 2:
            continue
        
        # IDs des messages dans ce chunk
        message_ids = [msg.get("id", f"msg_{i+j}") for j, msg in enumerate(fenetre)]
        
        # Texte formaté de chaque message
        textes_formates = [_formater_message_pour_chunk(msg) for msg in fenetre]
        texte_concatene = "\n".join(textes_formates)
        
        # Identifiant unique du chunk
        chunk_id = f"chunk_{offset_chunk_id + len(chunks)}_{interlocuteur}_{i}"
        
        # Métadonnées du chunk
        chunk = {
            "chunk_id": chunk_id,
            "message_ids": message_ids,
            "texte_concatene": texte_concatene,
            "metadata": {
                # Métadonnées temporelles
                "timestamp": fenetre[0].get("timestamp", ""),
                "timestamp_debut": fenetre[0].get("timestamp", ""),
                "timestamp_fin": fenetre[-1].get("timestamp", ""),
                
                # Métadonnées de conversation
                "contact": interlocuteur,
                "contact_name": contact_name,
                "type": "chunk",  # Pour distinguer des messages individuels
                
                # Métadonnées des messages contenus
                "premier_message_id": message_ids[0],
                "dernier_message_id": message_ids[-1],
                "nombre_messages": len(fenetre),
                
                # Position dans la conversation
                "index_debut_conversation": i,
                
                # Hériter de certaines métadonnées du premier message
                "direction": fenetre[0].get("direction", ""),
                "from": fenetre[0].get("from", ""),
                "to": fenetre[0].get("to", ""),
                "app": fenetre[0].get("app", ""),
                "gps_lat": fenetre[0].get("gps_lat", 0.0),
                "gps_lon": fenetre[0].get("gps_lon", 0.0),
                
                # Flags
                "is_noise": False,  # Les chunks ne sont jamais du bruit
            },
        }
        
        chunks.append(chunk)
        
        # Si la fenêtre est incomplète, c'est la dernière
        if len(fenetre) < taille_fenetre:
            break
    
    return chunks


def creer_chunks_fenetre_glissante(
    messages: List[Dict[str, Any]],
    taille_fenetre: int = 5,
    overlap: int = 2,
) -> List[Dict[str, Any]]:
    """Fonction de compatibilité - redirige vers creer_chunks_par_conversation.
    
    Cette fonction est conservée pour la rétrocompatibilité avec le code existant.
    Elle appelle la nouvelle fonction creer_chunks_par_conversation qui est plus intelligente.
    
    Args:
        messages: Liste de messages normalisés
        taille_fenetre: Nombre de messages par chunk
        overlap: Nombre de messages qui se chevauchent
        
    Returns:
        Liste de chunks groupés par conversation
    """
    return creer_chunks_par_conversation(messages, taille_fenetre, overlap)

