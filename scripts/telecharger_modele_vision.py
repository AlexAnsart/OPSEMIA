#!/usr/bin/env python3
"""Script pour télécharger et pré-cacher les modèles de vision (BLIP + traduction).

Ce script télécharge:
- BLIP pour la description d'images (Salesforce/blip-image-captioning-base)
- MarianMT pour la traduction EN->FR (Helsinki-NLP/opus-mt-en-fr)

Ces modèles sont utilisés pour générer des descriptions textuelles des images
avant de les encoder avec le modèle d'embedding.
"""

import io
import sys
from pathlib import Path

# Forcer UTF-8 pour la sortie console (nécessaire pour les emojis sur Windows)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ajouter le répertoire racine au path pour les imports
racine_projet = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(racine_projet))

from transformers import (
    BlipForConditionalGeneration,
    BlipProcessor,
    MarianMTModel,
    MarianTokenizer,
)


def telecharger_modeles_vision():
    """Télécharge et met en cache les modèles de vision."""
    print("=" * 70)
    print("=== Téléchargement des modèles de vision ===")
    print("=" * 70)
    
    # ========== BLIP ==========
    print("\n🖼️  Étape 1/2: Téléchargement du modèle BLIP...")
    print("   Modèle: Salesforce/blip-image-captioning-base")
    print("   Taille: ~990MB")
    print("   Usage: Génération de descriptions d'images en anglais")
    
    try:
        print("\n   Téléchargement en cours...")
        processor_blip = BlipProcessor.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )
        modele_blip = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )
        
        print("   ✅ BLIP téléchargé avec succès!")
        print(f"   Cache: {modele_blip.config._name_or_path}")
        
    except Exception as e:
        print(f"   ❌ Erreur lors du téléchargement de BLIP: {e}")
        return False
    
    # ========== MarianMT EN->FR ==========
    print("\n🌍 Étape 2/2: Téléchargement du modèle de traduction EN->FR...")
    print("   Modèle: Helsinki-NLP/opus-mt-en-fr")
    print("   Taille: ~300MB")
    print("   Usage: Traduction anglais->français des descriptions")
    
    try:
        print("\n   Téléchargement en cours...")
        tokenizer_trad = MarianTokenizer.from_pretrained(
            "Helsinki-NLP/opus-mt-en-fr"
        )
        modele_trad = MarianMTModel.from_pretrained(
            "Helsinki-NLP/opus-mt-en-fr"
        )
        
        print("   ✅ Traducteur téléchargé avec succès!")
        print(f"   Cache: {modele_trad.config._name_or_path}")
        
    except Exception as e:
        print(f"   ❌ Erreur lors du téléchargement du traducteur: {e}")
        return False
    
    # ========== Test rapide ==========
    print("\n🧪 Test rapide des modèles...")
    
    try:
        from PIL import Image
        import numpy as np
        
        # Créer une image de test (100x100 pixels, bleu)
        image_test = Image.fromarray(
            np.full((100, 100, 3), [0, 0, 255], dtype=np.uint8)
        )
        
        # Test BLIP
        print("   Test BLIP...")
        inputs = processor_blip(image_test, return_tensors="pt")
        outputs = modele_blip.generate(**inputs, max_length=50)
        caption_en = processor_blip.decode(outputs[0], skip_special_tokens=True)
        print(f"   Description générée: '{caption_en}'")
        
        # Test traduction
        print("   Test traducteur...")
        inputs_trad = tokenizer_trad(caption_en, return_tensors="pt")
        translated = modele_trad.generate(**inputs_trad)
        caption_fr = tokenizer_trad.decode(translated[0], skip_special_tokens=True)
        print(f"   Traduction: '{caption_fr}'")
        
        print("\n   ✅ Tests réussis!")
        
    except Exception as e:
        print(f"   ⚠️  Erreur lors des tests: {e}")
        print("   Les modèles ont été téléchargés mais le test a échoué.")
        print("   Vérifiez les dépendances (PIL, torch, transformers)")
    
    return True


if __name__ == "__main__":
    print("\n📦 Téléchargement des modèles de vision pour OPSEMIA")
    print("⚠️  Ce téléchargement peut prendre plusieurs minutes (~1.3GB total)")
    print("Assurez-vous d'avoir une connexion internet stable.\n")
    
    succes = telecharger_modeles_vision()
    
    if succes:
        print("\n" + "=" * 70)
        print("🎉 Les modèles de vision sont maintenant prêts à être utilisés!")
        print("=" * 70)
        print("\n📝 Prochaines étapes:")
        print("   1. Préparez votre CSV d'images (images.csv)")
        print("   2. Lancez l'application: python src/backend/app.py")
        print("   3. Indexez vos images via l'interface web (Configuration)")
        print()
    else:
        print("\n" + "=" * 70)
        print("💥 Échec du téléchargement")
        print("=" * 70)
        print("\n🔧 Vérifications:")
        print("   • Connexion internet active")
        print("   • Espace disque suffisant (~1.5GB)")
        print("   • Dépendances installées: pip install -r requirements.txt")
        print()
        sys.exit(1)


