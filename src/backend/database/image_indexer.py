"""Pipeline d'indexation d'images : CSV → Description → Encodage → ChromaDB.

Ce module gère l'indexation complète des images avec génération de descriptions
textuelles et embeddings vectoriels.
"""

from __future__ import annotations

import io
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from PIL import Image

# Forcer UTF-8 pour la sortie console
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ajouter le répertoire racine au path pour les imports
racine_projet = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(racine_projet))

from config.settings import Parametres
from src.backend.database.vector_db import BaseVectorielle
from src.backend.models.image_encoder import creer_encodeur_image
from src.backend.models.model_manager import obtenir_encodeur_texte
from src.backend.parsers.image_extractor import parser_images_depuis_csv


def indexer_csv_images(
    chemin_csv: str | Path,
    parametres: Parametres,
    nom_cas: Optional[str] = None,
    reinitialiser: bool = False,
    progress_callback: Optional[callable] = None,
    log_verbose: bool = False,
) -> Dict[str, Any]:
    """Pipeline complet d'indexation d'un CSV d'images dans ChromaDB.
    
    Étapes:
    1. Parsing du CSV d'images
    2. Génération des descriptions textuelles (BLIP + traduction)
    3. Encodage vectoriel des descriptions
    4. Stockage dans ChromaDB
    
    Args:
        chemin_csv: Chemin vers le fichier CSV d'images
        parametres: Paramètres de configuration
        nom_cas: Nom du cas pour les collections (ex: "cas4"). Si None, utilise le nom par défaut
        reinitialiser: Si True, supprime la collection existante avant d'indexer
        progress_callback: Fonction de callback pour la progression (etape, %, message)
        log_verbose: Si True, affiche chaque image encodée (verbeux pour gros fichiers)
        
    Returns:
        Statistiques d'indexation (nombre d'images, durée, etc.)
    """
    debut_total = time.time()
    stats = {
        "fichier_csv": str(chemin_csv),
        "nom_cas": nom_cas,
        "images_indexees": 0,
        "images_manquantes": 0,
        "duree_parsing_sec": 0,
        "duree_description_sec": 0,
        "duree_encodage_sec": 0,
        "duree_stockage_sec": 0,
        "duree_totale_sec": 0,
    }
    
    # Nom de la collection (avec suffixe de cas si spécifié)
    suffixe = f"_{nom_cas}" if nom_cas else ""
    nom_collection_images = parametres.NOM_COLLECTION_IMAGES + suffixe
    
    print(f"🖼️  Démarrage de l'indexation d'images: {chemin_csv}")
    print(f"   Collection: {nom_collection_images}")
    
    # Helper pour envoyer la progression
    def _emit_progress(etape: str, pct: float, msg: str):
        if progress_callback:
            progress_callback(etape, pct, msg)
    
    _emit_progress("initialisation", 0, "Démarrage de l'indexation d'images...")
    
    # ========== 1. PARSING ==========
    print("\n📄 Phase 1/4: Parsing du CSV d'images...")
    _emit_progress("parsing", 5, "Lecture du fichier CSV d'images...")
    debut_phase = time.time()
    
    # Déterminer le dossier des images
    chemin_csv_path = Path(chemin_csv)
    dossier_images = chemin_csv_path.parent
    
    images = parser_images_depuis_csv(chemin_csv_path, dossier_images)
    stats["duree_parsing_sec"] = time.time() - debut_phase
    
    # Filtrer les images existantes
    images_valides = [img for img in images if img["existe"]]
    stats["images_manquantes"] = len(images) - len(images_valides)
    
    print(f"   ✓ {len(images)} images parsées, {len(images_valides)} valides ({stats['duree_parsing_sec']:.2f}s)")
    if stats["images_manquantes"] > 0:
        print(f"   ⚠️  {stats['images_manquantes']} image(s) manquante(s) (ignorées)")
    
    _emit_progress("parsing", 10, f"{len(images_valides)} images valides trouvées")
    
    if len(images_valides) == 0:
        print("\n❌ Aucune image valide à indexer!")
        return stats
    
    # ========== 2. CHARGEMENT DES MODÈLES ==========
    print("\n🧠 Phase 2/4: Chargement des modèles...")
    _emit_progress("chargement_modeles", 12, "Chargement des modèles de vision et d'encodage...")
    debut_phase = time.time()
    
    # Charger l'encodeur de texte (partagé avec les messages)
    encodeur_texte = obtenir_encodeur_texte()
    
    # Créer l'encodeur d'images
    encodeur_image = creer_encodeur_image(encodeur_texte, parametres)
    dimension_embedding = encodeur_image.dimension_embedding
    
    duree_chargement = time.time() - debut_phase
    print(f"   ✓ Modèles chargés (dim={dimension_embedding}) ({duree_chargement:.2f}s)")
    _emit_progress("chargement_modeles", 20, "Modèles chargés")
    
    # ========== 3. DESCRIPTION ET ENCODAGE ==========
    print("\n🖼️  Phase 3/4: Description et encodage des images...")
    _emit_progress("encodage", 22, f"Traitement de {len(images_valides)} images...")
    debut_phase = time.time()
    
    embeddings_liste = []
    descriptions_liste = []
    images_traitees = []
    
    total_images = len(images_valides)
    temps_par_image = []
    
    for i, image_info in enumerate(images_valides):
        debut_image = time.time()
        
        try:
            # Charger l'image
            chemin_absolu = Path(image_info["chemin_absolu"])
            image_pil = Image.open(chemin_absolu).convert("RGB")
            
            # Encoder l'image (description + embedding)
            embedding, description = encodeur_image.encoder_image(image_pil)
            
            embeddings_liste.append(embedding)
            descriptions_liste.append(description)
            images_traitees.append(image_info)
            
            duree_image = time.time() - debut_image
            temps_par_image.append(duree_image)
            
            # Progression
            pct = 22 + (i + 1) / total_images * 58  # 22-80%
            
            # Log du traitement avec la description TOUJOURS affichée
            apercu_nom = (image_info["nom_image"][:40] + "...") if len(image_info["nom_image"]) > 40 else image_info["nom_image"]
            print(f"   ├─ [{i+1}/{total_images}] {apercu_nom} ({duree_image:.2f}s)")
            
            # TOUJOURS afficher la description générée (après traduction EN->FR)
            apercu_desc = (description[:100] + "...") if len(description) > 100 else description
            print(f"      └─ 🇫🇷 Description: {apercu_desc}")
            
            # Émettre la progression
            _emit_progress(
                "encodage",
                pct,
                f"Image {i+1}/{total_images}: {apercu_nom}"
            )
            
        except Exception as e:
            print(f"\n   ⚠️  Erreur lors du traitement de l'image {image_info['nom_image']}: {e}")
            continue
    
    stats["duree_description_sec"] = time.time() - debut_phase
    stats["duree_encodage_sec"] = stats["duree_description_sec"]  # Combiné
    
    # Statistiques de traitement
    if temps_par_image:
        temps_moyen = np.mean(temps_par_image)
        temps_min = np.min(temps_par_image)
        temps_max = np.max(temps_par_image)
        
        stats["temps_moyen_par_image"] = temps_moyen
        stats["temps_min_par_image"] = temps_min
        stats["temps_max_par_image"] = temps_max
        stats["debit_images_par_sec"] = len(temps_par_image) / stats["duree_encodage_sec"]
        
        print(f"\n   ✓ {len(embeddings_liste)} images traitées ({stats['duree_encodage_sec']:.2f}s)")
        print(f"   📊 Stats traitement:")
        print(f"      • Temps moyen/image: {temps_moyen:.2f}s")
        print(f"      • Plus rapide: {temps_min:.2f}s | Plus lent: {temps_max:.2f}s")
        print(f"      • Débit: {stats['debit_images_par_sec']:.2f} img/s")
    
    _emit_progress("encodage", 80, f"{len(embeddings_liste)} images encodées")
    
    if len(embeddings_liste) == 0:
        print("\n❌ Aucune image n'a pu être traitée!")
        return stats
    
    # ========== 4. STOCKAGE CHROMADB ==========
    print("\n💾 Phase 4/4: Stockage dans ChromaDB...")
    _emit_progress("stockage", 82, "Connexion à ChromaDB...")
    debut_phase = time.time()
    
    db = BaseVectorielle(chemin_persistance=parametres.CHEMIN_BASE_CHROMA)
    
    # Réinitialiser si demandé
    if reinitialiser:
        print("   ⚠️  Réinitialisation de la collection existante...")
        _emit_progress("stockage", 84, "Suppression des anciennes données...")
        db.supprimer_collection(nom_collection_images)
    
    # Stocker les images
    print("   → Stockage des images...")
    _emit_progress("stockage", 86, f"Stockage de {len(images_traitees)} images...")
    
    # Préparer les IDs et métadonnées
    ids_images = [
        img.get("id") or f"img_{i}" 
        for i, img in enumerate(images_traitees)
    ]
    
    # Nettoyer les descriptions et extraire les métadonnées
    metadonnees_images = []
    descriptions_nettoyees = []
    for img, desc in zip(images_traitees, descriptions_liste):
        meta = _extraire_metadonnees_image(img, desc)
        metadonnees_images.append(meta)
        descriptions_nettoyees.append(meta["description"])  # Description nettoyée
    
    # Convertir les embeddings en liste
    embeddings_array = np.array(embeddings_liste)
    
    db.ajouter_messages(
        nom_collection=nom_collection_images,
        ids=ids_images,
        embeddings=embeddings_array.tolist(),
        metadonnees=metadonnees_images,
        documents=descriptions_nettoyees,  # Utiliser les descriptions nettoyées
    )
    
    stats["images_indexees"] = len(ids_images)
    stats["duree_stockage_sec"] = time.time() - debut_phase
    
    print(f"   ✓ Stockage terminé ({stats['duree_stockage_sec']:.2f}s)")
    _emit_progress("stockage", 100, "Indexation d'images terminée avec succès!")
    
    # ========== RÉSUMÉ ==========
    stats["duree_totale_sec"] = time.time() - debut_total
    
    print("\n" + "="*70)
    print("✅ INDEXATION D'IMAGES TERMINÉE")
    print("="*70)
    print(f"📊 Résultats:")
    print(f"   • Images parsées      : {len(images)}")
    print(f"   • Images indexées     : {stats['images_indexees']}")
    print(f"   • Images manquantes   : {stats['images_manquantes']}")
    print(f"\n⏱️  Durées par phase:")
    print(f"   • Parsing             : {stats['duree_parsing_sec']:.2f}s ({stats['duree_parsing_sec']/stats['duree_totale_sec']*100:.1f}%)")
    print(f"   • Description+Encodage: {stats['duree_encodage_sec']:.2f}s ({stats['duree_encodage_sec']/stats['duree_totale_sec']*100:.1f}%)")
    print(f"   • Stockage            : {stats['duree_stockage_sec']:.2f}s ({stats['duree_stockage_sec']/stats['duree_totale_sec']*100:.1f}%)")
    print(f"   • TOTAL               : {stats['duree_totale_sec']:.2f}s")
    
    if "debit_images_par_sec" in stats:
        print(f"\n📈 Performance:")
        print(f"   • Temps moyen/image: {stats['temps_moyen_par_image']:.2f}s")
        print(f"   • Plus rapide: {stats['temps_min_par_image']:.2f}s | Plus lent: {stats['temps_max_par_image']:.2f}s")
        print(f"   • Débit: {stats['debit_images_par_sec']:.2f} images/s")
    
    print(f"\n💾 Collection créée: {nom_collection_images}")
    print(f"📁 Base ChromaDB: {parametres.CHEMIN_BASE_CHROMA}")
    print("="*70)
    
    return stats


def _extraire_metadonnees_image(
    image_info: Dict[str, Any],
    description: str,
) -> Dict[str, Any]:
    """Extrait les métadonnées pertinentes d'une image pour ChromaDB.
    
    Args:
        image_info: Informations de l'image (depuis le parser)
        description: Description textuelle générée
        
    Returns:
        Métadonnées JSON-serializable
    """
    # Nettoyer la description des répétitions de mots consécutifs
    description_nettoyee = _nettoyer_repetitions(description)
    
    return {
        "nom_image": image_info.get("nom_image", ""),
        "chemin": image_info.get("chemin", ""),
        "timestamp": image_info.get("timestamp", ""),
        "date_prise": image_info.get("date_prise", ""),
        "heure_prise": image_info.get("heure_prise", ""),
        "gps_lat": image_info.get("gps_lat") or 0.0,
        "gps_lon": image_info.get("gps_lon") or 0.0,
        "description": description_nettoyee,
        "type": "image",  # Flag pour distinguer des messages
        "is_noise": False,  # Les images ne sont jamais du bruit (compatibilité filtre)
    }


def _nettoyer_repetitions(texte: str) -> str:
    """Supprime les mots qui se répètent consécutivement dans un texte.
    
    Gère les répétitions avec espaces, virgules, et ponctuation.
    
    Exemple: 
        "un chat chat chat noir" -> "un chat noir"
        "miami, miami, miami" -> "miami"
        "salon, salon salon" -> "salon"
    
    Args:
        texte: Texte à nettoyer
        
    Returns:
        Texte sans répétitions consécutives
    """
    import re
    
    # Pattern amélioré pour gérer les répétitions avec virgules OU espaces
    # Capture: (mot) (séparateur) (mot répété) (séparateur)...
    # Remplace par: (mot) (un seul séparateur approprié)
    
    # D'abord gérer les répétitions avec virgules: "miami, miami, miami" -> "miami"
    texte_nettoye = re.sub(
        r'\b(\w+)(?:\s*,\s*\1)+\b',  # mot, mot, mot...
        r'\1',
        texte,
        flags=re.IGNORECASE
    )
    
    # Ensuite gérer les répétitions avec espaces: "chat chat chat" -> "chat"
    texte_nettoye = re.sub(
        r'\b(\w+)(?:\s+\1)+\b',  # mot mot mot...
        r'\1',
        texte_nettoye,
        flags=re.IGNORECASE
    )
    
    # Nettoyer les virgules orphelines (ex: ", , ," -> ",")
    texte_nettoye = re.sub(r',(\s*,)+', ',', texte_nettoye)
    
    # Nettoyer les espaces multiples
    texte_nettoye = re.sub(r'\s+', ' ', texte_nettoye)
    
    # Nettoyer virgule en fin de phrase
    texte_nettoye = re.sub(r',\s*$', '', texte_nettoye)
    
    return texte_nettoye.strip()


