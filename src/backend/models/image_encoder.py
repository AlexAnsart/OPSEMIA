"""Encodeur d'images utilisant BLIP pour la description et BGE pour l'embedding.

Ce module génère des descriptions textuelles d'images en français, puis les encode
en vecteurs pour la recherche sémantique.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Union

import numpy as np
import torch
from PIL import Image
from transformers import (
    BlipForConditionalGeneration,
    BlipProcessor,
    MarianMTModel,
    MarianTokenizer,
)

# Forcer UTF-8 pour la sortie console
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class EncodeurImage:
    """Encodeur d'images en deux étapes:
    1. Génération de description textuelle en français (BLIP + traduction)
    2. Encodage de la description en vecteur (même modèle que pour les messages)
    
    Attributs:
        peripherique: Device PyTorch (cpu/cuda)
        processor_blip: Processeur BLIP pour les images
        modele_blip: Modèle BLIP pour le captioning
        tokenizer_trad: Tokenizer pour la traduction EN->FR
        modele_trad: Modèle de traduction EN->FR
        encodeur_texte: Encodeur de texte (partagé avec les messages)
    """
    
    def __init__(
        self,
        encodeur_texte,
        preference_peripherique: str = "auto",
        longueur_min_description: int = 30,
        longueur_max_description: int = 150,
        num_beams: int = 15,
        temperature: float = 0.3,
    ) -> None:
        """Initialise l'encodeur d'images.
        
        Args:
            encodeur_texte: Instance de EncodeurTexte pour encoder les descriptions
            preference_peripherique: "auto", "cpu" ou "cuda"
            longueur_min_description: Longueur minimale de la description en tokens
            longueur_max_description: Longueur maximale de la description en tokens
            num_beams: Nombre de beams pour la génération (qualité)
            temperature: Température de sampling (créativité)
        """
        self.peripherique: str = self._resoudre_peripherique(preference_peripherique)
        self.encodeur_texte = encodeur_texte
        
        # Paramètres de génération
        self.longueur_min = longueur_min_description
        self.longueur_max = longueur_max_description
        self.num_beams = num_beams
        self.temperature = temperature
        
        # Charger les modèles
        print(f"🖼️  Chargement du modèle BLIP pour description d'images...")
        self.processor_blip = BlipProcessor.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )
        self.modele_blip = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        ).to(self.peripherique)
        
        print(f"🌍 Chargement du modèle de traduction EN->FR...")
        self.tokenizer_trad = MarianTokenizer.from_pretrained(
            "Helsinki-NLP/opus-mt-en-fr"
        )
        self.modele_trad = MarianMTModel.from_pretrained(
            "Helsinki-NLP/opus-mt-en-fr"
        ).to(self.peripherique)
        
        print(f"✅ Encodeur d'images prêt (périphérique: {self.peripherique})")
    
    def _resoudre_peripherique(self, preference: str) -> str:
        """Résout le périphérique à utiliser."""
        if preference == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        if preference in {"cpu", "cuda"}:
            return preference
        return "cpu"
    
    def decrire_image(self, image: Image.Image) -> str:
        """Génère une description en français d'une image.
        
        Args:
            image: Image PIL à décrire
            
        Returns:
            Description en français
        """
        # Génération de la légende en anglais avec BLIP
        inputs = self.processor_blip(image, return_tensors="pt").to(self.peripherique)
        
        with torch.no_grad():
            outputs = self.modele_blip.generate(
                **inputs,
                max_length=self.longueur_max,
                min_length=self.longueur_min,
                num_beams=self.num_beams,
                length_penalty=1.0,
                repetition_penalty=1.5,
                temperature=self.temperature,
                do_sample=True,
                top_k=50,
                top_p=0.95,
            )
        
        caption_en = self.processor_blip.decode(outputs[0], skip_special_tokens=True)
        
        # Traduction en français
        inputs_trad = self.tokenizer_trad(caption_en, return_tensors="pt").to(
            self.peripherique
        )
        
        with torch.no_grad():
            translated = self.modele_trad.generate(**inputs_trad)
        
        caption_fr = self.tokenizer_trad.decode(translated[0], skip_special_tokens=True)
        
        return caption_fr
    
    def encoder_image(self, image: Union[Image.Image, str, Path]) -> tuple[np.ndarray, str]:
        """Encode une image en vecteur via sa description textuelle.
        
        Args:
            image: Image PIL, chemin vers fichier image, ou Path
            
        Returns:
            Tuple (embedding normalisé, description en français)
        """
        # Charger l'image si c'est un chemin
        if isinstance(image, (str, Path)):
            image = Image.open(image).convert("RGB")
        
        # Générer la description
        description = self.decrire_image(image)
        
        # Encoder la description avec le même encodeur que les messages
        embedding = self.encodeur_texte.encoder([description])[0]
        
        return embedding, description
    
    def encoder_images_batch(
        self, 
        images: List[Union[Image.Image, str, Path]],
        show_progress: bool = True,
    ) -> List[tuple[np.ndarray, str]]:
        """Encode un lot d'images.
        
        Args:
            images: Liste d'images (PIL ou chemins)
            show_progress: Afficher la progression
            
        Returns:
            Liste de tuples (embedding, description)
        """
        resultats = []
        
        for i, image in enumerate(images):
            if show_progress:
                print(f"   Traitement image {i+1}/{len(images)}...", end="\r")
            
            try:
                embedding, description = self.encoder_image(image)
                resultats.append((embedding, description))
            except Exception as e:
                print(f"\n⚠️  Erreur lors du traitement de l'image {i+1}: {e}")
                # Retourner un embedding nul et une description vide
                embedding_nul = np.zeros(self.encodeur_texte.dimension_embedding)
                resultats.append((embedding_nul, ""))
        
        if show_progress:
            print()  # Nouvelle ligne après la progression
        
        return resultats
    
    @property
    def dimension_embedding(self) -> int:
        """Dimension des embeddings (même dimension que l'encodeur de texte)."""
        return self.encodeur_texte.dimension_embedding


def creer_encodeur_image(encodeur_texte, parametres: object) -> EncodeurImage:
    """Factory pour créer un encodeur d'images depuis les paramètres.
    
    Args:
        encodeur_texte: Instance d'EncodeurTexte (partagé avec les messages)
        parametres: Objet de paramètres exposant les attributs de configuration
        
    Returns:
        EncodeurImage configuré
    """
    return EncodeurImage(
        encodeur_texte=encodeur_texte,
        preference_peripherique=getattr(parametres, "PERIPHERIQUE_EMBEDDING", "auto"),
        longueur_min_description=getattr(parametres, "LONGUEUR_MIN_DESCRIPTION_IMAGE", 30),
        longueur_max_description=getattr(parametres, "LONGUEUR_MAX_DESCRIPTION_IMAGE", 150),
        num_beams=getattr(parametres, "NUM_BEAMS_DESCRIPTION_IMAGE", 15),
        temperature=getattr(parametres, "TEMPERATURE_DESCRIPTION_IMAGE", 0.3),
    )


