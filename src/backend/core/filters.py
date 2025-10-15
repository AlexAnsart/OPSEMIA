"""Gestion des filtres pour la recherche sémantique.

Permet de créer des filtres ChromaDB pour réduire le corpus avant la recherche vectorielle.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional


def creer_filtre_temporel(
    timestamp_debut: Optional[str | datetime] = None,
    timestamp_fin: Optional[str | datetime] = None,
) -> Dict[str, Any]:
    """Crée un filtre pour restreindre la recherche à une période temporelle.

    Args:
        timestamp_debut: Date/heure de début (format ISO ou datetime)
        timestamp_fin: Date/heure de fin (format ISO ou datetime)

    Returns:
        Filtre ChromaDB au format dict

    Exemple:
        >>> filtre = creer_filtre_temporel("2024-01-01", "2024-12-31")
    """
    # Si les deux sont fournis, utiliser $and pour ChromaDB
    if timestamp_debut and timestamp_fin:
        ts_debut = timestamp_debut if isinstance(timestamp_debut, str) else timestamp_debut.isoformat()
        ts_fin = timestamp_fin if isinstance(timestamp_fin, str) else timestamp_fin.isoformat()
        return {
            "$and": [
                {"timestamp": {"$gte": ts_debut}},
                {"timestamp": {"$lte": ts_fin}}
            ]
        }
    
    # Si seulement l'un des deux est fourni
    if timestamp_debut:
        ts_debut = timestamp_debut if isinstance(timestamp_debut, str) else timestamp_debut.isoformat()
        return {"timestamp": {"$gte": ts_debut}}
    
    if timestamp_fin:
        ts_fin = timestamp_fin if isinstance(timestamp_fin, str) else timestamp_fin.isoformat()
        return {"timestamp": {"$lte": ts_fin}}
    
    return {}


def creer_filtre_geographique(
    latitude_centre: float,
    longitude_centre: float,
    rayon_km: float,
) -> Dict[str, Any]:
    """Crée un filtre pour restreindre la recherche à une zone géographique.

    Note: ChromaDB ne supporte pas nativement les filtres géographiques complexes.
    Cette fonction retourne un filtre basé sur un carré englobant (approximation).

    Args:
        latitude_centre: Latitude du point central
        longitude_centre: Longitude du point central
        rayon_km: Rayon en kilomètres

    Returns:
        Filtre ChromaDB approximatif (carré englobant)

    Note:
        Pour une précision GPS optimale, utilisez un post-filtrage avec calcul
        de distance exacte (haversine) après la recherche.
    """
    # Approximation: 1 degré de latitude ≈ 111 km
    # 1 degré de longitude ≈ 111 km * cos(latitude)
    import math
    
    delta_lat = rayon_km / 111.0
    delta_lon = rayon_km / (111.0 * math.cos(math.radians(latitude_centre)))
    
    return {
        "gps_lat": {
            "$gte": latitude_centre - delta_lat,
            "$lte": latitude_centre + delta_lat,
        },
        "gps_lon": {
            "$gte": longitude_centre - delta_lon,
            "$lte": longitude_centre + delta_lon,
        },
    }


def creer_filtre_exclusion_bruit(exclure: bool = True) -> Dict[str, Any]:
    """Crée un filtre pour exclure (ou inclure uniquement) les messages de bruit.

    Args:
        exclure: Si True, exclut les messages flaggés comme bruit

    Returns:
        Filtre ChromaDB
    """
    if exclure:
        return {"is_noise": False}
    return {}


def creer_filtre_direction(direction: str) -> Dict[str, Any]:
    """Crée un filtre pour restreindre par direction (incoming/outgoing).

    Args:
        direction: "incoming", "outgoing", ou "both"

    Returns:
        Filtre ChromaDB
    """
    if direction.lower() in ["incoming", "outgoing"]:
        return {"direction": direction.lower()}
    return {}


def combiner_filtres(*filtres: Dict[str, Any]) -> Dict[str, Any]:
    """Combine plusieurs filtres en un seul filtre ChromaDB.

    Args:
        *filtres: Liste de filtres à combiner

    Returns:
        Filtre combiné (fusion des dictionnaires)

    Note:
        ChromaDB utilise une logique AND implicite pour les clés multiples.
        Pour des conditions OR complexes, utilisez l'opérateur $or.
    """
    filtre_combine = {}
    
    for filtre in filtres:
        for cle, valeur in filtre.items():
            if cle in filtre_combine and isinstance(valeur, dict) and isinstance(filtre_combine[cle], dict):
                # Fusion des sous-dictionnaires (ex: timestamp avec $gte et $lte)
                filtre_combine[cle].update(valeur)
            else:
                filtre_combine[cle] = valeur
    
    return filtre_combine

