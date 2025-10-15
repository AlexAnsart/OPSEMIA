"""Système de suivi de progression pour les opérations longues.

Permet de tracker la progression d'opérations comme l'indexation
et de l'envoyer en temps réel via Server-Sent Events (SSE).
"""

from __future__ import annotations

import io
import sys
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

# Forcer UTF-8 pour la sortie console (nécessaire pour les emojis sur Windows)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


@dataclass
class ProgressEvent:
    """Événement de progression."""
    etape: str  # Nom de l'étape (ex: "parsing", "encodage")
    progression: float  # Pourcentage de progression (0-100)
    message: str  # Message descriptif
    donnees_extra: Optional[Dict[str, Any]] = None  # Données supplémentaires


class ProgressTracker:
    """Gestionnaire de progression pour les opérations longues.
    
    Permet de tracker la progression et de l'envoyer à des listeners
    (utile pour SSE, WebSocket, etc.).
    """
    
    def __init__(self):
        """Initialise le tracker de progression."""
        self._evenements: list[ProgressEvent] = []
        self._listeners: list[callable] = []
        self._lock = threading.Lock()
        self._progression_totale = 0.0
        self._etape_actuelle = ""
        self._termine = False
        
    def ajouter_listener(self, callback: callable) -> None:
        """Ajoute un listener qui sera appelé à chaque événement.
        
        Args:
            callback: Fonction appelée avec un ProgressEvent en paramètre
        """
        with self._lock:
            self._listeners.append(callback)
    
    def retirer_listener(self, callback: callable) -> None:
        """Retire un listener.
        
        Args:
            callback: Fonction à retirer
        """
        with self._lock:
            if callback in self._listeners:
                self._listeners.remove(callback)
    
    def emettre(self, etape: str, progression: float, message: str, 
                donnees_extra: Optional[Dict[str, Any]] = None) -> None:
        """Émet un événement de progression.
        
        Args:
            etape: Nom de l'étape actuelle
            progression: Pourcentage de progression (0-100)
            message: Message descriptif
            donnees_extra: Données supplémentaires optionnelles
        """
        event = ProgressEvent(
            etape=etape,
            progression=min(100.0, max(0.0, progression)),
            message=message,
            donnees_extra=donnees_extra or {}
        )
        
        with self._lock:
            self._evenements.append(event)
            self._progression_totale = event.progression
            self._etape_actuelle = etape
            
            # Notifier tous les listeners
            for listener in self._listeners:
                try:
                    listener(event)
                except Exception as e:
                    print(f"⚠️  Erreur lors de la notification du listener: {e}")
    
    def marquer_termine(self, succes: bool = True, message: str = "Terminé") -> None:
        """Marque l'opération comme terminée.
        
        Args:
            succes: Si l'opération a réussi
            message: Message de fin
        """
        self.emettre(
            etape="termine" if succes else "erreur",
            progression=100.0 if succes else self._progression_totale,
            message=message,
            donnees_extra={"succes": succes}
        )
        with self._lock:
            self._termine = True
    
    def obtenir_progression(self) -> float:
        """Obtient la progression actuelle (0-100)."""
        with self._lock:
            return self._progression_totale
    
    def obtenir_etape(self) -> str:
        """Obtient l'étape actuelle."""
        with self._lock:
            return self._etape_actuelle
    
    def est_termine(self) -> bool:
        """Vérifie si l'opération est terminée."""
        with self._lock:
            return self._termine
    
    def obtenir_evenements(self) -> list[ProgressEvent]:
        """Obtient tous les événements enregistrés."""
        with self._lock:
            return self._evenements.copy()
    
    def reinitialiser(self) -> None:
        """Réinitialise le tracker."""
        with self._lock:
            self._evenements.clear()
            self._listeners.clear()
            self._progression_totale = 0.0
            self._etape_actuelle = ""
            self._termine = False


# Instance globale pour l'indexation (thread-safe)
_trackers: Dict[str, ProgressTracker] = {}
_trackers_lock = threading.Lock()


def obtenir_tracker(id_operation: str) -> ProgressTracker:
    """Obtient ou crée un tracker pour une opération.
    
    Args:
        id_operation: Identifiant unique de l'opération
        
    Returns:
        Tracker de progression
    """
    with _trackers_lock:
        if id_operation not in _trackers:
            _trackers[id_operation] = ProgressTracker()
        return _trackers[id_operation]


def supprimer_tracker(id_operation: str) -> None:
    """Supprime un tracker.
    
    Args:
        id_operation: Identifiant de l'opération
    """
    with _trackers_lock:
        if id_operation in _trackers:
            del _trackers[id_operation]

