from __future__ import annotations

from typing import Any, Dict, Iterable, List


def ajouter_flag_bruit(messages: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Débruitage placeholder: étiquette chaque message avec is_noise=False et retourne une copie.

    Cela maintient la forme du pipeline de traitement sans effectuer de filtrage pour le moment.
    """
    etiquettes: List[Dict[str, Any]] = []
    for msg in messages:
        copie = dict(msg)
        copie["is_noise"] = False
        etiquettes.append(copie)
    return etiquettes


