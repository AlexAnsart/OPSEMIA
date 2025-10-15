from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ajouter le répertoire racine au path pour les imports
racine_projet = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(racine_projet))


def _parser_flottant(valeur: str) -> Optional[float]:
    if valeur is None or valeur == "":
        return None
    try:
        return float(valeur)
    except ValueError:
        return None


def _parser_timestamp(ts: str) -> str:
    """Parse le timestamp du CSV de démo en chaîne ISO-8601 (UTC-naive)."""
    # Format de démo exemple: 2025-07-10 09:21:00
    try:
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        return dt.isoformat()
    except Exception:
        return ts  # fallback vers chaîne brute


def parser_sms_depuis_csv(chemin_csv: Path | str) -> List[Dict[str, Any]]:
    """Extrait les lignes SMS du CSV fourni et normalise les champs.

    Le CSV contient déjà uniquement des SMS (record_type == "sms").
    """
    chemin = Path(chemin_csv)
    resultats: List[Dict[str, Any]] = []
    
    # Lire tout le contenu et nettoyer les guillemets de début/fin de chaque ligne
    with chemin.open("r", encoding="utf-8-sig") as f:
        lignes = f.readlines()
    
    # Nettoyer chaque ligne: retirer les guillemets de début/fin
    lignes_nettoyees = []
    for ligne in lignes:
        ligne_stripped = ligne.strip()
        if ligne_stripped.startswith('"') and ligne_stripped.endswith('"'):
            ligne_stripped = ligne_stripped[1:-1]
        lignes_nettoyees.append(ligne_stripped)
    
    # Créer un lecteur CSV avec le contenu corrigé
    import io
    contenu_corrige = '\n'.join(lignes_nettoyees)
    f_corrige = io.StringIO(contenu_corrige)
    lecteur = csv.DictReader(f_corrige)
    
    for ligne in lecteur:
            # Le CSV contient déjà uniquement des SMS, pas besoin de filtrer
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


