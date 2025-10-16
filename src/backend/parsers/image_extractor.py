"""Extracteur d'informations depuis un CSV d'images.

Parse les métadonnées d'images (nom, chemin, date, heure, GPS) depuis un CSV.
"""

from __future__ import annotations

import csv
import io
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Forcer UTF-8 pour la sortie console
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def _parser_flottant(valeur: str) -> Optional[float]:
    """Parse une valeur en float, retourne None si invalide."""
    if valeur is None or valeur == "":
        return None
    try:
        return float(valeur)
    except ValueError:
        return None


def _parser_timestamp_image(date_str: str, heure_str: str) -> str:
    """Combine date et heure en timestamp ISO-8601.
    
    Args:
        date_str: Date au format YYYY-MM-DD
        heure_str: Heure au format HH:MM:SS
        
    Returns:
        Timestamp ISO-8601 ou chaîne vide si invalide
    """
    if not date_str or not heure_str:
        return ""
    
    try:
        # Combiner date et heure
        datetime_str = f"{date_str} {heure_str}"
        dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        return dt.isoformat()
    except Exception:
        return ""


def parser_images_depuis_csv(
    chemin_csv: Path | str,
    chemin_dossier_images: Optional[Path | str] = None,
) -> List[Dict[str, Any]]:
    """Extrait les informations d'images depuis un CSV.
    
    Format CSV attendu:
        nom_image, chemin, date_prise, heure_prise, latitude, longitude
        
    Args:
        chemin_csv: Chemin vers le fichier CSV d'images
        chemin_dossier_images: Dossier racine contenant les images (optionnel)
            Si fourni, les chemins relatifs seront résolus depuis ce dossier
            
    Returns:
        Liste de dictionnaires normalisés avec métadonnées d'images
        
    Exemple:
        >>> images = parser_images_depuis_csv("Cas/Cas4/images.csv")
        >>> print(images[0])
        {
            'id': 'img_0',
            'nom_image': 'photo.jpg',
            'chemin': 'CLIC/photo.jpg',
            'chemin_absolu': '/path/to/CLIC/photo.jpg',
            'timestamp': '2025-10-05T17:18:08',
            'gps_lat': 48.8566,
            'gps_lon': 2.3522,
            'existe': True
        }
    """
    chemin = Path(chemin_csv)
    
    if not chemin.exists():
        raise FileNotFoundError(f"Fichier CSV introuvable: {chemin}")
    
    # Déterminer le dossier racine des images
    if chemin_dossier_images:
        dossier_images = Path(chemin_dossier_images)
    else:
        # Par défaut, utiliser le dossier contenant le CSV
        dossier_images = chemin.parent
    
    resultats: List[Dict[str, Any]] = []
    
    print(f"📋 Lecture du CSV d'images: {chemin}")
    print(f"📁 Dossier racine des images: {dossier_images}")
    
    with chemin.open("r", encoding="utf-8-sig") as f:
        lecteur = csv.DictReader(f)
        
        for idx, ligne in enumerate(lecteur):
            # Ignorer les lignes vides
            nom_image = ligne.get("nom_image", "").strip()
            if not nom_image:
                continue
            
            # Extraire le chemin relatif
            chemin_relatif = ligne.get("chemin", "").strip()
            
            # Construire le chemin absolu
            if chemin_relatif:
                # Normaliser les séparateurs Windows -> Unix
                chemin_relatif_normalise = chemin_relatif.replace("\\", "/")
                chemin_absolu = dossier_images / chemin_relatif_normalise
            else:
                # Si pas de chemin, essayer avec juste le nom
                chemin_absolu = dossier_images / nom_image
            
            # Vérifier si l'image existe
            existe = chemin_absolu.exists() and chemin_absolu.is_file()
            
            # Parser le timestamp
            date_prise = ligne.get("date_prise", "").strip()
            heure_prise = ligne.get("heure_prise", "").strip()
            timestamp = _parser_timestamp_image(date_prise, heure_prise)
            
            # Parser les coordonnées GPS
            gps_lat = _parser_flottant(ligne.get("latitude", ""))
            gps_lon = _parser_flottant(ligne.get("longitude", ""))
            
            # Normaliser au format standard
            normalise: Dict[str, Any] = {
                "id": f"img_{idx}",
                "nom_image": nom_image,
                "chemin": chemin_relatif or nom_image,
                "chemin_absolu": str(chemin_absolu),
                "timestamp": timestamp,
                "date_prise": date_prise,
                "heure_prise": heure_prise,
                "gps_lat": gps_lat,
                "gps_lon": gps_lon,
                "existe": existe,
            }
            
            resultats.append(normalise)
    
    print(f"✓ {len(resultats)} images parsées depuis le CSV")
    
    # Statistiques sur les images manquantes
    images_manquantes = sum(1 for img in resultats if not img["existe"])
    if images_manquantes > 0:
        print(f"⚠️  {images_manquantes} image(s) manquante(s) (fichier non trouvé)")
    
    return resultats


