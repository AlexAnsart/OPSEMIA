from __future__ import annotations

import csv
import io
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Forcer UTF-8 pour la sortie console (nécessaire pour les emojis sur Windows)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ajouter le répertoire racine au path pour les imports
racine_projet = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(racine_projet))


def _parser_flottant(valeur: str) -> Optional[float]:
    """Parse une valeur en float, retourne None si invalide."""
    if valeur is None or valeur == "":
        return None
    try:
        return float(valeur)
    except ValueError:
        return None


def _parser_timestamp(ts: str) -> str:
    """Parse le timestamp du CSV en chaîne ISO-8601 (UTC-naive).
    
    Supporte les formats:
    - 2025-07-10 09:21:00 (Cas1/Cas2)
    - 2010-01-01 11:03:53 (Cas3)
    """
    if not ts:
        return ""
    try:
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        return dt.isoformat()
    except Exception:
        return ts  # fallback vers chaîne brute


def _detecter_format_csv(chemin_csv: Path) -> str:
    """Détecte automatiquement le format du CSV en lisant le header.
    
    Args:
        chemin_csv: Chemin vers le fichier CSV
        
    Returns:
        "cas1" pour l'ancienne structure (record_type, id, timestamp, ...)
        "cas3" pour la nouvelle structure (id_message, id_fil, horodatage, ...)
    """
    with chemin_csv.open("r", encoding="utf-8-sig") as f:
        premiere_ligne = f.readline().strip()
        
        # Nettoyer les guillemets de début/fin si présents
        if premiere_ligne.startswith('"') and premiere_ligne.endswith('"'):
            premiere_ligne = premiere_ligne[1:-1]
        
        # Détecter selon les colonnes présentes
        if "id_message" in premiere_ligne and "horodatage" in premiere_ligne:
            return "cas3"
        elif "record_type" in premiere_ligne and "timestamp" in premiere_ligne:
            return "cas1"
        else:
            # Par défaut, considérer comme cas1
            return "cas1"


def _parser_cas1(chemin_csv: Path) -> List[Dict[str, Any]]:
    """Parse le CSV au format Cas1/Cas2 (ancienne structure).
    
    Format: record_type, id, timestamp, direction, from, to, phone_hash, 
            contact_name, message, media_filename, gps_lat, gps_lon, app, 
            app_event, device_id, imei, notes
    """
    resultats: List[Dict[str, Any]] = []
    
    # Lire tout le contenu et nettoyer les guillemets de début/fin de chaque ligne
    with chemin_csv.open("r", encoding="utf-8-sig") as f:
        lignes = f.readlines()
    
    # Nettoyer chaque ligne: retirer les guillemets de début/fin
    lignes_nettoyees = []
    for ligne in lignes:
        ligne_stripped = ligne.strip()
        if ligne_stripped.startswith('"') and ligne_stripped.endswith('"'):
            ligne_stripped = ligne_stripped[1:-1]
        lignes_nettoyees.append(ligne_stripped)
    
    # Créer un lecteur CSV avec le contenu corrigé
    contenu_corrige = '\n'.join(lignes_nettoyees)
    f_corrige = io.StringIO(contenu_corrige)
    lecteur = csv.DictReader(f_corrige)
    
    for ligne in lecteur:
        # Filtrer uniquement les SMS (ignorer les app_event, etc.)
        record_type = ligne.get("record_type", "")
        if record_type != "sms":
            continue
            
        # Normaliser au format standard
        normalise: Dict[str, Any] = {
            "id": ligne.get("id"),
            "timestamp": _parser_timestamp(ligne.get("timestamp", "")),
            "direction": ligne.get("direction"),
            "from": ligne.get("from"),
            "to": ligne.get("to"),
            "phone_hash": ligne.get("phone_hash"),
            "contact_name": ligne.get("contact_name"),
            "message": ligne.get("message"),
            "media_filename": ligne.get("media_filename"),
            "gps_lat": _parser_flottant(ligne.get("gps_lat", "")),
            "gps_lon": _parser_flottant(ligne.get("gps_lon", "")),
            "app": ligne.get("app"),
            "app_event": ligne.get("app_event"),
            "device_id": ligne.get("device_id"),
            "imei": ligne.get("imei"),
            "notes": ligne.get("notes"),
        }
        resultats.append(normalise)
    
    return resultats


def _parser_cas3(chemin_csv: Path) -> List[Dict[str, Any]]:
    """Parse le CSV au format Cas3 (nouvelle structure).
    
    Format: id_message, id_fil, appareil, horodatage, sens, canal, nom_contact, 
            alias_contact, role_contact, identifiant_contact, objet_email, 
            apercu_message, indice_lieu, pieces_jointes, types_pj, score_risque, 
            mots_cles
            
    Note: Les colonnes score_risque, mots_cles, indice_lieu, objet_email, canal
          sont ignorées (colonnes obsolètes).
    """
    resultats: List[Dict[str, Any]] = []
    
    with chemin_csv.open("r", encoding="utf-8-sig") as f:
        lecteur = csv.DictReader(f)
        
        for ligne in lecteur:
            # Vérifier que le canal est SMS (ignorer les autres types)
            canal = ligne.get("canal", "").upper()
            if canal != "SMS":
                continue
            
            # Mapper le sens (reçu/envoyé/brouillon) vers direction (incoming/outgoing)
            sens = ligne.get("sens", "").lower()
            direction = "incoming" if sens == "reçu" else "outgoing" if sens in ["envoyé", "brouillon"] else ""
            
            # Obtenir l'identifiant du contact
            identifiant_contact = ligne.get("identifiant_contact", "")
            
            # Construire from/to selon la direction
            # Note: On n'a pas l'info du numéro de l'appareil dans Cas3, on utilise "user"
            if direction == "incoming":
                from_field = identifiant_contact
                to_field = "user"
            else:
                from_field = "user"
                to_field = identifiant_contact
            
            # Normaliser au format standard
            normalise: Dict[str, Any] = {
                "id": ligne.get("id_message"),
                "timestamp": _parser_timestamp(ligne.get("horodatage", "")),
                "direction": direction,
                "from": from_field,
                "to": to_field,
                "phone_hash": None,  # Non disponible dans Cas3
                "contact_name": ligne.get("nom_contact"),
                "message": ligne.get("apercu_message"),
                "media_filename": ligne.get("pieces_jointes"),  # Approximatif
                "gps_lat": None,  # Non disponible dans Cas3
                "gps_lon": None,  # Non disponible dans Cas3
                "app": "sms",  # Par défaut SMS puisqu'on filtre par canal
                "app_event": None,
                "device_id": ligne.get("appareil"),
                "imei": None,  # Non disponible dans Cas3
                "notes": None,
                # Métadonnées supplémentaires spécifiques à Cas3 (optionnel)
                "id_fil": ligne.get("id_fil"),
                "alias_contact": ligne.get("alias_contact"),
                "role_contact": ligne.get("role_contact"),
                "types_pj": ligne.get("types_pj"),
            }
            resultats.append(normalise)
    
    return resultats


def parser_sms_depuis_csv(chemin_csv: Path | str, format_force: Optional[str] = None) -> List[Dict[str, Any]]:
    """Extrait les SMS d'un CSV et normalise les champs.
    
    Supporte deux formats de CSV :
    - Cas1/Cas2 : ancienne structure avec record_type, id, timestamp, direction, ...
    - Cas3 : nouvelle structure avec id_message, horodatage, sens, canal, ...
    
    La détection du format est automatique selon le header, mais peut être forcée
    avec le paramètre format_force.
    
    Args:
        chemin_csv: Chemin vers le fichier CSV
        format_force: Force le format ("cas1" ou "cas3"), ou None pour détection auto
        
    Returns:
        Liste de messages normalisés au format standard
    """
    chemin = Path(chemin_csv)
    
    # Détecter le format si non forcé
    format_csv = format_force if format_force else _detecter_format_csv(chemin)
    
    print(f"📋 Format CSV détecté: {format_csv}")
    
    # Parser selon le format
    if format_csv == "cas3":
        return _parser_cas3(chemin)
    else:
        return _parser_cas1(chemin)


