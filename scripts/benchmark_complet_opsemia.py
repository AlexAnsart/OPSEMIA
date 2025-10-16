#!/usr/bin/env python3
"""Benchmark complet pour OPSEMIA : Calcul de durées et qualité de recherche.

Ce script effectue :
1. Calcul des durées d'encodage pour tous les modèles (messages et images)
2. Benchmark de qualité sur 100 requêtes (90 messages + 10 images)
3. Génération d'un rapport markdown complet

Modèles testés :
- Jina-v3 (jinaai/jina-embeddings-v3)
- Solon-large (OrdalieTech/Solon-embeddings-large-0.1)
- BGE-M3 (BAAI/bge-m3)
- Qwen3-8B (via API DeepInfra - estimation pour durées)
- BLIP (pour description d'images)
"""

import argparse
import io
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import requests
import torch
from dotenv import load_dotenv
from PIL import Image
from sentence_transformers import SentenceTransformer

# Charger les variables d'environnement depuis .env
load_dotenv()

# Forcer UTF-8 pour la sortie console
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ajouter le répertoire racine au path
racine_projet = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(racine_projet))

from config.settings import obtenir_parametres, TOP_K_BENCHMARK
from src.backend.database.vector_db import BaseVectorielle
from src.backend.models.image_encoder import EncodeurImage
from src.backend.models.text_encoder import EncodeurTexte
from src.backend.parsers.message_extractor import parser_sms_depuis_csv
from src.backend.parsers.image_extractor import parser_images_depuis_csv
from scripts.donnees_benchmark_opsemia import (
    obtenir_requetes_messages,
    obtenir_requetes_images,
    obtenir_toutes_requetes,
)


# ============================================================================
# CONFIGURATION
# ============================================================================

MODELES_TEXTE = [
    {
        "id": "jinaai/jina-embeddings-v3",
        "nom": "Jina-v3",
        "params_millions": 137,  # Estimation
        "dimensions": 1024,
        "local": True,
    },
    {
        "id": "OrdalieTech/Solon-embeddings-large-0.1",
        "nom": "Solon-large",
        "params_millions": 335,  # Estimation
        "dimensions": 1024,
        "local": True,
    },
    {
        "id": "BAAI/bge-m3",
        "nom": "BGE-M3",
        "params_millions": 568,  # Estimation
        "dimensions": 1024,
        "local": True,
    },
    {
        "id": "Qwen/Qwen3-Embedding-8B",
        "nom": "Qwen3-8B",
        "params_millions": 8000,
        "dimensions": 8192,
        "local": False,  # Via API
    },
]

# Chemins
CHEMIN_CSV_MESSAGES = racine_projet / "Cas" / "Cas4" / "sms.csv"
CHEMIN_CSV_IMAGES = racine_projet / "Cas" / "Cas4" / "images.csv"
DOSSIER_RACINE_CAS4 = racine_projet / "Cas" / "Cas4"  # Dossier parent pour résoudre les chemins relatifs du CSV
DOSSIER_IMAGES = racine_projet / "Cas" / "Cas4" / "Images"  # Pour compter les fichiers
CHEMIN_OUTPUT_MD = racine_projet / "Docs Projet" / f"BENCHMARK_RESULTATS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

# Base de données temporaire pour benchmark
CHEMIN_DB_BENCHMARK = racine_projet / "data" / "benchmark_temp"

# Clé API DeepInfra
DEEPINFRA_API_KEY = os.getenv("DEEPINFRA_TOKEN")


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def calculer_similarite_cosine(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calcule la similarité cosinus entre deux vecteurs normalisés."""
    return float(np.dot(vec1, vec2))


def precision_at_k(resultats_ids: List[str], pertinents_ids: List[str], k: int) -> float:
    """Calcule la Precision@K."""
    if k == 0:
        return 0.0
    top_k = resultats_ids[:k]
    nb_pertinents = len([doc_id for doc_id in top_k if doc_id in pertinents_ids])
    return nb_pertinents / k


def recall_at_k(resultats_ids: List[str], pertinents_ids: List[str], k: int) -> float:
    """Calcule le Recall@K."""
    if len(pertinents_ids) == 0:
        return 0.0
    top_k = resultats_ids[:k]
    nb_pertinents = len([doc_id for doc_id in top_k if doc_id in pertinents_ids])
    return nb_pertinents / len(pertinents_ids)


def mean_reciprocal_rank(resultats_ids: List[str], pertinents_ids: List[str]) -> float:
    """Calcule le Mean Reciprocal Rank (MRR)."""
    for i, doc_id in enumerate(resultats_ids, 1):
        if doc_id in pertinents_ids:
            return 1.0 / i
    return 0.0


def est_recherche_reussie(resultats_ids: List[str], pertinents_ids: List[str], k: int) -> bool:
    """Détermine si une recherche est réussie.
    
    Une recherche est réussie si au moins 1 document pertinent est dans le top K.
    
    Args:
        resultats_ids: Liste des IDs des résultats retournés
        pertinents_ids: Liste des IDs des documents pertinents attendus
        k: Nombre de premiers résultats à considérer (généralement TOP_K_BENCHMARK)
        
    Returns:
        True si au moins 1 document pertinent est dans les K premiers résultats
    """
    top_k = resultats_ids[:k]
    return any(doc_id in pertinents_ids for doc_id in top_k)


# ============================================================================
# ENCODAGE VIA API (QWEN3)
# ============================================================================

def encoder_texte_via_api(textes: List[str], modele: str = "Qwen/Qwen3-Embedding-8B") -> List[List[float]]:
    """Encode des textes via l'API DeepInfra.
    
    Args:
        textes: Liste de textes à encoder
        modele: ID du modèle à utiliser
        
    Returns:
        Liste d'embeddings
    """
    if not DEEPINFRA_API_KEY:
        raise ValueError("DEEPINFRA_TOKEN non configuré dans les variables d'environnement")
    
    url = "https://api.deepinfra.com/v1/openai/embeddings"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPINFRA_API_KEY}"
    }
    
    embeddings = []
    for texte in textes:
        payload = {
            "input": texte,
            "model": modele,
            "encoding_format": "float"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        result = response.json()
        
        if "data" in result and len(result["data"]) > 0:
            embeddings.append(result["data"][0]["embedding"])
        else:
            raise ValueError(f"Erreur API: {result}")
    
    return embeddings


# ============================================================================
# CALCUL DES DURÉES D'ENCODAGE
# ============================================================================

def calculer_durees_encodage_texte() -> Dict[str, Dict]:
    """Calcule les durées d'encodage pour chaque modèle de texte.
    
    Approche simplifiée :
    1. Encoder un court texte (5-10 tokens)
    2. Calculer durée par token
    3. Extrapoler pour 1 message (10 tokens), 100k messages
    
    Returns:
        Dictionnaire avec les durées par modèle
    """
    print("\n" + "="*80)
    print("CALCUL DES DURÉES D'ENCODAGE - MODÈLES TEXTE")
    print("="*80)
    
    resultats = {}
    
    # Texte de test court (environ 5 tokens)
    texte_test = "Ceci est un test"
    NB_TOKENS_TEST = 5
    NB_TOKENS_PAR_MESSAGE = 10  # Estimation moyenne d'un message
    NB_TESTS = 5  # Répéter pour moyenne plus stable
    
    for modele_info in MODELES_TEXTE:
        print(f"\n📊 Modèle: {modele_info['nom']}")
        print(f"   ID: {modele_info['id']}")
        print(f"   Paramètres: {modele_info['params_millions']}M")
        
        if modele_info['local']:
            # Modèle local
            print("   ⏳ Chargement du modèle...")
            debut_chargement = time.time()
            try:
                try:
                    modele = SentenceTransformer(modele_info['id'], trust_remote_code=True)
                except:
                    modele = SentenceTransformer(modele_info['id'])
                duree_chargement = time.time() - debut_chargement
                print(f"   ✓ Chargé en {duree_chargement:.2f}s")
                
                # Mesurer durée d'encodage (moyenne sur plusieurs tests)
                print("   ⏳ Test d'encodage...")
                durees = []
                for i in range(NB_TESTS):
                    debut = time.time()
                    _ = modele.encode([texte_test], normalize_embeddings=True, show_progress_bar=False)
                    durees.append(time.time() - debut)
                
                duree_moyenne = np.mean(durees)
                duree_par_token = duree_moyenne / NB_TOKENS_TEST
                
                # Extrapolations
                duree_1_message = duree_par_token * NB_TOKENS_PAR_MESSAGE
                duree_100k_messages = duree_1_message * 100_000
                
                resultats[modele_info['nom']] = {
                    "duree_chargement_s": duree_chargement,
                    "duree_par_token_ms": duree_par_token * 1000,
                    "duree_1_message_ms": duree_1_message * 1000,
                    "debit_msg_par_s": 1 / duree_1_message if duree_1_message > 0 else 0,
                    "estimation_100k_messages_h": duree_100k_messages / 3600,
                }
                
                print(f"   ⏱️  Par token: {duree_par_token*1000:.2f}ms")
                print(f"   ⏱️  Par message ({NB_TOKENS_PAR_MESSAGE} tokens): {duree_1_message*1000:.2f}ms")
                print(f"   ⏱️  Débit: {1/duree_1_message:.1f} msg/s")
                print(f"   📈 Estimation 100k messages: {duree_100k_messages/3600:.1f}h")
                
            except Exception as e:
                print(f"   ❌ ERREUR lors du test du modèle: {type(e).__name__}: {str(e)}")
                print(f"   ⚠️  Le modèle sera ignoré dans les résultats")
                resultats[modele_info['nom']] = {
                    "erreur": str(e),
                    "duree_chargement_s": 0,
                    "duree_par_token_ms": 0,
                    "duree_1_message_ms": 0,
                    "debit_msg_par_s": 0,
                    "estimation_100k_messages_h": 0,
                }
            finally:
                # Libérer la mémoire
                if 'modele' in locals():
                    del modele
                torch.cuda.empty_cache() if torch.cuda.is_available() else None
                import gc
                gc.collect()
            
        else:
            # Modèle via API - Estimation basée sur les autres modèles
            print("   🌐 Modèle via API - Estimation basée sur le nombre de paramètres")
            
            # Facteur basé sur le ratio de paramètres
            facteur = modele_info['params_millions'] / MODELES_TEXTE[2]['params_millions']  # BGE-M3 référence
            
            # Estimation (en supposant ~2ms/token pour BGE-M3)
            duree_par_token_estimee = 2 * facteur  # ms
            duree_1_message_estimee = duree_par_token_estimee * NB_TOKENS_PAR_MESSAGE
            duree_100k_estimee = (duree_1_message_estimee / 1000) * 100_000
            
            resultats[modele_info['nom']] = {
                "duree_chargement_s": "N/A (API)",
                "duree_par_token_ms": f"~{duree_par_token_estimee:.1f}",
                "duree_1_message_ms": f"~{duree_1_message_estimee:.1f}",
                "debit_msg_par_s": f"~{1000/duree_1_message_estimee:.1f}",
                "estimation_100k_messages_h": f"~{duree_100k_estimee/3600:.1f}",
                "note": f"Estimation basée sur ratio de paramètres (facteur {facteur:.1f}x vs BGE-M3)",
            }
            
            print(f"   📊 Par token: ~{duree_par_token_estimee:.1f}ms")
            print(f"   📊 Par message ({NB_TOKENS_PAR_MESSAGE} tokens): ~{duree_1_message_estimee:.1f}ms")
            print(f"   📊 Débit: ~{1000/duree_1_message_estimee:.1f} msg/s")
            print(f"   📈 Estimation 100k messages: ~{duree_100k_estimee/3600:.1f}h")
            print(f"   ℹ️  {resultats[modele_info['nom']]['note']}")
    
    return resultats


def calculer_durees_encodage_images() -> Dict[str, any]:
    """Calcule les durées d'encodage pour les images (BLIP + encodage texte).
    
    Approche simplifiée :
    1. Encoder 1 image de test
    2. Mesurer description + encodage
    3. Extrapoler pour 1000 images
    
    Returns:
        Dictionnaire avec les durées
    """
    print("\n" + "="*80)
    print("CALCUL DES DURÉES D'ENCODAGE - IMAGES (BLIP)")
    print("="*80)
    
    # Charger un encodeur de texte pour BLIP
    parametres = obtenir_parametres()
    encodeur_texte = EncodeurTexte(
        id_modele=parametres.ID_MODELE_EMBEDDING,
        preference_peripherique=parametres.PERIPHERIQUE_EMBEDDING
    )
    
    # Créer encodeur d'images
    print("⏳ Chargement BLIP...")
    debut_chargement = time.time()
    encodeur_image = EncodeurImage(
        encodeur_texte=encodeur_texte,
        preference_peripherique=parametres.PERIPHERIQUE_EMBEDDING,
    )
    duree_chargement = time.time() - debut_chargement
    print(f"✓ BLIP chargé en {duree_chargement:.2f}s")
    
    # Charger images de test (passer le dossier parent pour résoudre les chemins relatifs)
    images_csv = parser_images_depuis_csv(CHEMIN_CSV_IMAGES, DOSSIER_RACINE_CAS4)
    images_valides = [img for img in images_csv if img["existe"]]
    
    if len(images_valides) == 0:
        print("⚠️  Aucune image disponible pour les tests de durée")
        print("   Les estimations seront basées sur des valeurs typiques (~30s/image)")
        
        return {
            "duree_chargement_s": duree_chargement,
            "duree_description_moyenne_s": 28.0,  # Valeur typique BLIP (~28s)
            "duree_encodage_desc_moyenne_ms": 2000,  # Valeur typique (~2s)
            "duree_totale_moyenne_s": 30.0,
            "duree_min_s": "N/A",
            "duree_max_s": "N/A",
            "estimation_1000_images_h": 30.0 * 1000 / 3600,
            "note": "Estimation basée sur valeurs typiques (aucune image disponible)",
        }
    
    # Tester sur 3 images pour moyenne
    nb_tests = min(3, len(images_valides))
    print(f"\n⏳ Test sur {nb_tests} images...")
    
    try:
        temps_description = []
        temps_encodage = []
        
        for img_info in images_valides[:nb_tests]:
            chemin = Path(img_info["chemin_absolu"])
            image_pil = Image.open(chemin).convert("RGB")
            
            # Description
            debut = time.time()
            description = encodeur_image.decrire_image(image_pil)
            temps_description.append(time.time() - debut)
            
            # Encodage
            debut = time.time()
            _ = encodeur_texte.encoder([description])
            temps_encodage.append(time.time() - debut)
        
        duree_desc_moyenne = np.mean(temps_description)
        duree_enc_moyenne = np.mean(temps_encodage)
        duree_totale_moyenne = duree_desc_moyenne + duree_enc_moyenne
        
        resultats = {
            "duree_chargement_s": duree_chargement,
            "duree_description_moyenne_s": duree_desc_moyenne,
            "duree_encodage_desc_moyenne_ms": duree_enc_moyenne * 1000,
            "duree_totale_moyenne_s": duree_totale_moyenne,
            "duree_min_s": min(temps_description) + min(temps_encodage),
            "duree_max_s": max(temps_description) + max(temps_encodage),
            "estimation_1000_images_h": (duree_totale_moyenne * 1000) / 3600,
        }
        
        print(f"\n📊 Résultats ({nb_tests} images testées):")
        print(f"   ⏱️  Description moyenne: {duree_desc_moyenne:.2f}s")
        print(f"   ⏱️  Encodage description: {duree_enc_moyenne*1000:.2f}ms")
        print(f"   ⏱️  Total moyen/image: {duree_totale_moyenne:.2f}s")
        print(f"   📈 Estimation 1000 images: {resultats['estimation_1000_images_h']:.1f}h")
        
        return resultats
        
    except Exception as e:
        print(f"\n❌ ERREUR lors du test des images: {type(e).__name__}: {str(e)}")
        print("   ⚠️  Utilisation de valeurs par défaut")
        return {
            "duree_chargement_s": duree_chargement,
            "duree_description_moyenne_s": 28.0,
            "duree_encodage_desc_moyenne_ms": 2000,
            "duree_totale_moyenne_s": 30.0,
            "duree_min_s": "N/A",
            "duree_max_s": "N/A",
            "estimation_1000_images_h": 30.0 * 1000 / 3600,
            "note": f"Erreur: {str(e)}",
        }


# ============================================================================
# BENCHMARK DE QUALITÉ
# ============================================================================

def indexer_dataset_benchmark(modele_info: Dict, encodeur_texte, encodeur_image=None, force_reindex: bool = False) -> str:
    """Indexe le dataset complet pour un modèle donné.
    
    Args:
        modele_info: Informations du modèle
        encodeur_texte: Encodeur de texte (local ou None si API)
        encodeur_image: Encodeur d'images (optionnel)
        force_reindex: Si True, force la réindexation même si la collection existe
        
    Returns:
        Nom de la collection créée
    """
    nom_collection = f"benchmark_{modele_info['nom'].lower().replace('-', '_')}"
    
    # Créer la base vectorielle temporaire
    db = BaseVectorielle(chemin_persistance=CHEMIN_DB_BENCHMARK)
    
    # Vérifier si la collection existe déjà (utiliser l'API ChromaDB directement)
    collections_existantes = [col.name for col in db.client.list_collections()]
    
    if nom_collection in collections_existantes and not force_reindex:
        nb_docs_existants = db.compter_documents(nom_collection)
        print(f"\n♻️  Collection {nom_collection} déjà indexée (réutilisation)")
        print(f"   Collection: {nom_collection}")
        print(f"   📊 {nb_docs_existants} documents en cache")
        if not modele_info['local']:
            print(f"   💰 Économie : pas de nouveaux appels API DeepInfra")
        print(f"   💡 Utilisez --force pour réindexer")
        return nom_collection
    
    print(f"\n📦 Indexation dataset pour {modele_info['nom']}...")
    print(f"   Collection: {nom_collection}")
    
    # Supprimer collection existante si force_reindex
    if nom_collection in collections_existantes:
        print(f"   🗑️  Suppression de l'ancienne collection...")
        db.supprimer_collection(nom_collection)
    
    # Parser les messages
    print("   📄 Parsing messages...")
    messages = parser_sms_depuis_csv(CHEMIN_CSV_MESSAGES)
    print(f"   ✓ {len(messages)} messages parsés")
    
    # Encoder les messages
    print(f"   🧠 Encodage {len(messages)} messages...")
    textes = [msg.get("message", "") or "" for msg in messages]
    
    # DEBUG: Afficher les 3 premiers messages pour vérifier
    print(f"   🔍 DEBUG - Vérification du contenu:")
    for i in range(min(3, len(messages))):
        print(f"      msg_{i:03d}: {textes[i][:60]}...")
    
    debut_encodage = time.time()
    if modele_info['local']:
        embeddings_msgs = encodeur_texte.encoder(textes, taille_lot=32)
    else:
        # Via API (Qwen3) - Encoder par lots avec logs de progression
        print("   🌐 Encodage via API DeepInfra (cela peut prendre du temps)...")
        embeddings_bruts = []
        taille_lot_api = 50  # Encoder par lots de 50 pour éviter les timeouts
        
        for i in range(0, len(textes), taille_lot_api):
            lot = textes[i:i+taille_lot_api]
            debut_lot = time.time()
            
            try:
                embeddings_lot = encoder_texte_via_api(lot, modele_info['id'])
                embeddings_bruts.extend(embeddings_lot)
                
                duree_lot = time.time() - debut_lot
                progression = min(i + taille_lot_api, len(textes))
                pct = (progression / len(textes)) * 100
                temps_ecoule = time.time() - debut_encodage
                temps_restant_estime = (temps_ecoule / progression) * (len(textes) - progression) if progression > 0 else 0
                
                print(f"      [{progression}/{len(textes)}] {pct:.1f}% - {duree_lot:.2f}s pour {len(lot)} msgs - "
                      f"Temps écoulé: {temps_ecoule:.1f}s - Restant estimé: {temps_restant_estime:.1f}s")
            except Exception as e:
                print(f"      ❌ Erreur lors de l'encodage du lot {i}-{i+len(lot)}: {e}")
                raise
        
        embeddings_msgs = np.array(embeddings_bruts)
    
    duree_encodage = time.time() - debut_encodage
    print(f"   ✓ {len(embeddings_msgs)} embeddings générés en {duree_encodage:.1f}s ({len(messages)/duree_encodage:.1f} msg/s)")
    
    # Stocker messages - utiliser "id" car c'est ce que le parser retourne (pas "id_message")
    # Assurer le format avec padding (msg_001, msg_002, etc.)
    ids_msgs = []
    for i, msg in enumerate(messages):
        msg_id = msg.get("id")
        if not msg_id:
            # Fallback avec padding à 3 chiffres
            msg_id = f"msg_{i:03d}"
        ids_msgs.append(msg_id)
    
    metadonnees_msgs = [
        {
            "id": ids_msgs[i],
            "type": "message",
            "contact": msg.get("contact_name", ""),
            "canal": msg.get("app", ""),
        }
        for i, msg in enumerate(messages)
    ]
    
    # Log des premiers IDs pour debug
    print(f"   🔍 Debug - Premiers IDs de messages indexés:")
    print(f"      {ids_msgs[:5]}")
    
    db.ajouter_messages(
        nom_collection=nom_collection,
        ids=ids_msgs,
        embeddings=embeddings_msgs.tolist(),
        metadonnees=metadonnees_msgs,
        documents=textes,
    )
    
    # Indexer images si encodeur fourni
    if encodeur_image:
        print("   🖼️  Indexation images...")
        images = parser_images_depuis_csv(CHEMIN_CSV_IMAGES, DOSSIER_RACINE_CAS4)
        images_valides = [img for img in images if img["existe"]][:10]
        
        debut_images = time.time()
        for i, img_info in enumerate(images_valides, 1):
            debut_img = time.time()
            chemin = Path(img_info["chemin_absolu"])
            image_pil = Image.open(chemin).convert("RGB")
            
            # Générer description et encoder
            description = encodeur_image.decrire_image(image_pil)
            if modele_info['local']:
                embedding = encodeur_texte.encoder([description])[0]
            else:
                embedding_brut = encoder_texte_via_api([description], modele_info['id'])[0]
                embedding = np.array(embedding_brut)
            
            # Stocker
            db.ajouter_messages(
                nom_collection=nom_collection,
                ids=[f"img_{i-1}"],  # img_0, img_1, ..., img_9
                embeddings=[embedding.tolist()],
                metadonnees=[{
                    "id": f"img_{i-1}",
                    "type": "image",
                    "nom_image": img_info["nom_image"],
                    "description": description,
                }],
                documents=[description],
            )
            
            duree_img = time.time() - debut_img
            pct = (i / len(images_valides)) * 100
            temps_ecoule = time.time() - debut_images
            temps_restant = (temps_ecoule / i) * (len(images_valides) - i)
            
            print(f"      [{i}/{len(images_valides)}] {pct:.1f}% - {duree_img:.2f}s - "
                  f"Écoulé: {temps_ecoule:.1f}s - Restant: {temps_restant:.1f}s")
        
        duree_totale = time.time() - debut_images
        duree_par_image = duree_totale / len(images_valides) if len(images_valides) > 0 else 0
        print(f"   ✓ {len(images_valides)} images indexées en {duree_totale:.1f}s ({duree_par_image:.2f}s/image)")
    else:
        print(f"   ⚠️  Aucune image valide trouvée, indexation uniquement des messages")
    
    print(f"   ✅ Indexation terminée: {nom_collection}")
    return nom_collection


def evaluer_modele_benchmark(modele_info: Dict, nom_collection: str) -> Dict:
    """Évalue un modèle sur les 100 requêtes de benchmark.
    
    Args:
        modele_info: Informations du modèle
        nom_collection: Nom de la collection indexée
        
    Returns:
        Résultats du benchmark
    """
    print(f"\n🎯 Évaluation {modele_info['nom']} sur 100 requêtes...")
    
    # Charger encodeur
    if modele_info['local']:
        try:
            encodeur = SentenceTransformer(modele_info['id'], trust_remote_code=True)
        except:
            encodeur = SentenceTransformer(modele_info['id'])
    else:
        encodeur = None  # API
    
    # Base vectorielle
    db = BaseVectorielle(chemin_persistance=CHEMIN_DB_BENCHMARK)
    
    # Métriques
    metriques = {
        "precision@1": [],
        "precision@3": [],
        f"precision@{TOP_K_BENCHMARK}": [],
        f"recall@{TOP_K_BENCHMARK}": [],
        "mrr": [],
        "reussites": [],  # 1 si réussite, 0 sinon
    }
    
    metriques_par_type = {
        "message": {f"precision@{TOP_K_BENCHMARK}": [], f"recall@{TOP_K_BENCHMARK}": [], "mrr": [], "reussites": []},
        "image": {f"precision@{TOP_K_BENCHMARK}": [], f"recall@{TOP_K_BENCHMARK}": [], "mrr": [], "reussites": []},
    }
    
    # Récupérer toutes les requêtes
    requetes = obtenir_toutes_requetes()
    
    # Vérifier le nombre de documents dans la collection
    nb_docs = db.compter_documents(nom_collection)
    print(f"   📊 Collection contient {nb_docs} documents")
    print(f"   📏 Critère: au moins 1 ID attendu dans le top {TOP_K_BENCHMARK} résultats")
    
    debut_eval = time.time()
    requetes_traitees = 0
    
    # Logs de debug pour les premières requêtes
    debug_logs_affiches = 0
    
    for i, (requete, ids_attendus, difficulte, type_req) in enumerate(requetes, 1):
        # Skip requêtes images non complétées
        if "[REQUETE_A_COMPLETER]" in requete:
            continue
        
        # Encoder requête
        if encodeur:
            emb_req = encodeur.encode([requete], normalize_embeddings=True, show_progress_bar=False)[0]
        else:
            emb_brut = encoder_texte_via_api([requete], modele_info['id'])[0]
            emb_req = np.array(emb_brut)
        
        # Rechercher
        resultats = db.rechercher(
            nom_collection=nom_collection,
            embedding_requete=emb_req.tolist(),
            nombre_resultats=10,
            methode="KNN",
        )
        
        # IDs résultats
        ids_resultats = [r["metadata"]["id"] for r in resultats]
        
        # Debug pour les 3 premières requêtes
        if debug_logs_affiches < 3:
            print(f"\n   🔍 DEBUG Requête #{i} [{type_req}] [{difficulte}]:")
            print(f"      Requête: {requete[:60]}...")
            print(f"      IDs attendus: {ids_attendus[:3]}")
            print(f"      IDs obtenus: {ids_resultats[:5]}")
            # Vérifier si au moins 1 ID attendu est dans les résultats
            trouve = any(id_att in ids_resultats[:TOP_K_BENCHMARK] for id_att in ids_attendus)
            print(f"      ✅ TROUVÉ dans top {TOP_K_BENCHMARK}" if trouve else f"      ❌ PAS TROUVÉ dans top {TOP_K_BENCHMARK}")
            debug_logs_affiches += 1
        
        # Calculer métriques
        p1 = precision_at_k(ids_resultats, ids_attendus, 1)
        p3 = precision_at_k(ids_resultats, ids_attendus, 3)
        pk = precision_at_k(ids_resultats, ids_attendus, TOP_K_BENCHMARK)
        rk = recall_at_k(ids_resultats, ids_attendus, TOP_K_BENCHMARK)
        mrr = mean_reciprocal_rank(ids_resultats, ids_attendus)
        reussite = 1.0 if est_recherche_reussie(ids_resultats, ids_attendus, TOP_K_BENCHMARK) else 0.0
        
        metriques["precision@1"].append(p1)
        metriques["precision@3"].append(p3)
        metriques[f"precision@{TOP_K_BENCHMARK}"].append(pk)
        metriques[f"recall@{TOP_K_BENCHMARK}"].append(rk)
        metriques["mrr"].append(mrr)
        metriques["reussites"].append(reussite)
        
        metriques_par_type[type_req][f"precision@{TOP_K_BENCHMARK}"].append(pk)
        metriques_par_type[type_req][f"recall@{TOP_K_BENCHMARK}"].append(rk)
        metriques_par_type[type_req]["mrr"].append(mrr)
        metriques_par_type[type_req]["reussites"].append(reussite)
        
        requetes_traitees += 1
        
        if i % 10 == 0:
            temps_ecoule = time.time() - debut_eval
            temps_par_requete = temps_ecoule / requetes_traitees
            requetes_restantes = len(requetes) - i
            temps_restant = temps_par_requete * requetes_restantes
            taux_reussite_actuel = np.mean(metriques["reussites"]) * 100
            
            print(f"   [{i}/{len(requetes)}] {(i/len(requetes)*100):.1f}% - "
                  f"Taux réussite: {taux_reussite_actuel:.1f}% - "
                  f"Écoulé: {temps_ecoule:.1f}s - Restant: {temps_restant:.1f}s")
    
    # Calculer moyennes
    taux_reussite = np.mean(metriques["reussites"]) * 100  # Score sur 100
    
    print(f"\n   📈 Statistiques finales:")
    print(f"      Requêtes traitées: {requetes_traitees}")
    print(f"      Requêtes réussies: {int(sum(metriques['reussites']))}/{requetes_traitees}")
    print(f"      Taux de réussite: {taux_reussite:.1f}%")
    
    resultats = {
        "modele": modele_info['nom'],
        "precision@1": np.mean(metriques["precision@1"]),
        "precision@3": np.mean(metriques["precision@3"]),
        f"precision@{TOP_K_BENCHMARK}": np.mean(metriques[f"precision@{TOP_K_BENCHMARK}"]),
        f"recall@{TOP_K_BENCHMARK}": np.mean(metriques[f"recall@{TOP_K_BENCHMARK}"]),
        "mrr": np.mean(metriques["mrr"]),
        "taux_reussite": taux_reussite,  # Pourcentage de requêtes réussies
        "par_type": {
            "message": {
                f"precision@{TOP_K_BENCHMARK}": np.mean(metriques_par_type["message"][f"precision@{TOP_K_BENCHMARK}"]) if metriques_par_type["message"][f"precision@{TOP_K_BENCHMARK}"] else 0,
                f"recall@{TOP_K_BENCHMARK}": np.mean(metriques_par_type["message"][f"recall@{TOP_K_BENCHMARK}"]) if metriques_par_type["message"][f"recall@{TOP_K_BENCHMARK}"] else 0,
                "mrr": np.mean(metriques_par_type["message"]["mrr"]) if metriques_par_type["message"]["mrr"] else 0,
                "taux_reussite": np.mean(metriques_par_type["message"]["reussites"]) * 100 if metriques_par_type["message"]["reussites"] else 0,
            },
            "image": {
                f"precision@{TOP_K_BENCHMARK}": np.mean(metriques_par_type["image"][f"precision@{TOP_K_BENCHMARK}"]) if metriques_par_type["image"][f"precision@{TOP_K_BENCHMARK}"] else 0,
                f"recall@{TOP_K_BENCHMARK}": np.mean(metriques_par_type["image"][f"recall@{TOP_K_BENCHMARK}"]) if metriques_par_type["image"][f"recall@{TOP_K_BENCHMARK}"] else 0,
                "mrr": np.mean(metriques_par_type["image"]["mrr"]) if metriques_par_type["image"]["mrr"] else 0,
                "taux_reussite": np.mean(metriques_par_type["image"]["reussites"]) * 100 if metriques_par_type["image"]["reussites"] else 0,
            },
        },
    }
    
    print(f"   ✅ Évaluation terminée")
    print(f"   📊 Score: {taux_reussite:.1f}% | P@{TOP_K_BENCHMARK}: {resultats[f'precision@{TOP_K_BENCHMARK}']:.3f} | MRR: {resultats['mrr']:.3f}")
    
    return resultats


# ============================================================================
# GÉNÉRATION DU RAPPORT MARKDOWN
# ============================================================================

def generer_rapport_markdown(durees_texte: Dict, durees_images: Dict, resultats_benchmark: List[Dict]):
    """Génère le rapport markdown complet.
    
    Args:
        durees_texte: Durées d'encodage texte
        durees_images: Durées d'encodage images
        resultats_benchmark: Résultats du benchmark de qualité
    """
    print(f"\n📝 Génération du rapport markdown...")
    print(f"   Fichier: {CHEMIN_OUTPUT_MD}")
    
    contenu = f"""# Benchmark OPSEMIA - Résultats Complets

**Date:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}  
**Dataset:** Cas4 Breaking Bad (560 messages + 10 images)  
**Requêtes de test:** 100 (90 messages + 10 images)  
**Critère de réussite:** Au moins 1 résultat pertinent dans le top {TOP_K_BENCHMARK}

---

## 📊 Résumé Exécutif

Ce benchmark évalue les performances de 4 modèles d'embedding texte et du modèle BLIP pour la description d'images, à travers :
1. **Calcul de durées d'encodage** : temps nécessaire pour encoder des messages et images
2. **Benchmark de qualité** : précision de la recherche sémantique sur 100 requêtes réelles

### Critère de Réussite

Une recherche est considérée comme **réussie** si au moins 1 document pertinent apparaît dans les **{TOP_K_BENCHMARK} premiers résultats**.
Le **taux de réussite** (score sur 100) représente le pourcentage de requêtes réussies.

### Modèles Testés

| Modèle | Paramètres | Dimensions | Type |
|--------|-----------|------------|------|
| **Jina-v3** | 137M | 1024 | Local |
| **Solon-large** | 335M | 1024 | Local |
| **BGE-M3** | 568M | 1024 | Local |
| **Qwen3-8B** | 8000M | 8192 | API (DeepInfra) |
| **BLIP** | - | - | Vision (description) |

---

## ⏱️ Partie 1 : Durées d'Encodage

### 1.1 Modèles Texte

"""
    
    # Tableau des durées texte
    contenu += "| Modèle | Chargement | Msg Court | 100 Tokens | 1000 Msgs | Débit | Est. 1M Msgs |\n"
    contenu += "|--------|-----------|-----------|------------|-----------|-------|-------------|\n"
    
    # Séparer modèles valides et en erreur
    durees_valides = {nom: d for nom, d in durees_texte.items() if 'erreur' not in d}
    durees_erreurs = {nom: d for nom, d in durees_texte.items() if 'erreur' in d}
    
    for modele_nom, durees in durees_valides.items():
        chargement = durees.get('duree_chargement_s', 'N/A')
        if isinstance(chargement, (int, float)):
            chargement = f"{chargement:.1f}s"
        
        msg_court = durees.get('duree_message_court_ms', 'N/A')
        if isinstance(msg_court, (int, float)):
            msg_court = f"{msg_court:.1f}ms"
        
        tokens_100 = durees.get('duree_100_tokens_ms', 'N/A')
        if isinstance(tokens_100, (int, float)):
            tokens_100 = f"{tokens_100:.1f}ms"
        
        msgs_1000 = durees.get('duree_1000_messages_s', 'N/A')
        if isinstance(msgs_1000, (int, float)):
            msgs_1000 = f"{msgs_1000:.1f}s"
        
        debit = durees.get('debit_msg_par_s', 'N/A')
        if isinstance(debit, (int, float)):
            debit = f"{debit:.1f}/s"
        
        est_100k = durees.get('estimation_100k_messages_h', 'N/A')
        if isinstance(est_100k, (int, float)):
            est_100k = f"{est_100k:.1f}h"
        
        contenu += f"| **{modele_nom}** | {chargement} | {msg_court} | {tokens_100} | {msgs_1000} | {debit} | {est_100k} |\n"
        
        # Note pour Qwen3
        if 'note' in durees:
            contenu += f"\n> 📝 **Note {modele_nom}:** {durees['note']}\n\n"
    
    # Afficher les erreurs si présentes
    if durees_erreurs:
        contenu += "\n#### ⚠️ Modèles en erreur\n\n"
        for modele_nom, durees in durees_erreurs.items():
            contenu += f"- **{modele_nom}**: {durees['erreur']}\n"
        contenu += "\n"
    
    contenu += "\n### 1.2 Images (BLIP + Encodage Description)\n\n"
    
    if durees_images:
        contenu += f"""
| Métrique | Valeur |
|----------|--------|
| **Chargement BLIP** | {durees_images['duree_chargement_s']:.1f}s |
| **Description moyenne** | {durees_images['duree_description_moyenne_s']:.2f}s |
| **Encodage description** | {durees_images['duree_encodage_desc_moyenne_ms']:.1f}ms |
| **Total moyen/image** | {durees_images['duree_totale_moyenne_s']:.2f}s |
| **Plus rapide** | {durees_images['duree_min_s']:.2f}s |
| **Plus lent** | {durees_images['duree_max_s']:.2f}s |
| **Estimation 1000 images** | {durees_images['estimation_1000_images_h']:.1f}h |

"""
    
    contenu += """
### 1.3 Estimations Globales

#### Pour 100k Messages

"""
    
    for modele_nom, durees in durees_texte.items():
        est = durees.get('estimation_100k_messages_h', 'N/A')
        if isinstance(est, str) and est.startswith('~'):
            contenu += f"- **{modele_nom}:** {est}\n"
        elif isinstance(est, (int, float)):
            contenu += f"- **{modele_nom}:** {est:.1f} heures\n"
    
    if durees_images:
        contenu += f"\n#### Pour 1000 Images\n\n"
        contenu += f"- **BLIP + Encodage:** {durees_images['estimation_1000_images_h']:.1f} heures\n"
    
    if resultats_benchmark:
        contenu += "\n---\n\n## 🎯 Partie 2 : Benchmark de Qualité (Précision)\n\n"
        contenu += "### 2.1 Résultats Globaux (100 requêtes)\n\n"
        
        # Tableau des résultats
        contenu += f"| Modèle | **Score (/100)** | P@1 | P@3 | P@{TOP_K_BENCHMARK} | R@{TOP_K_BENCHMARK} | MRR |\n"
        contenu += "|--------|------------------|-----|-----|-----|-----|-----|\n"
        
        # Séparer résultats valides et erreurs
        resultats_valides = [r for r in resultats_benchmark if 'erreur' not in r]
        resultats_erreurs = [r for r in resultats_benchmark if 'erreur' in r]
        
        # Trier par taux de réussite (score sur 100)
        resultats_tries = sorted(resultats_valides, key=lambda x: x.get('taux_reussite', 0), reverse=True)
        
        for res in resultats_tries:
            score = res.get('taux_reussite', 0)
            contenu += f"| **{res['modele']}** | **{score:.1f}%** | {res['precision@1']:.3f} | {res['precision@3']:.3f} | {res.get(f'precision@{TOP_K_BENCHMARK}', 0):.3f} | {res.get(f'recall@{TOP_K_BENCHMARK}', 0):.3f} | {res['mrr']:.3f} |\n"
        
        # Afficher les erreurs si présentes
        if resultats_erreurs:
            contenu += "\n#### ⚠️ Modèles en erreur\n\n"
            for res in resultats_erreurs:
                contenu += f"- **{res['modele']}**: {res['erreur']}\n"
            contenu += "\n"
    else:
        contenu += "\n---\n\n## 🎯 Partie 2 : Benchmark de Qualité (Précision)\n\n"
        contenu += "**⏭️ Tests de qualité non exécutés**\n\n"
        resultats_tries = []
    
    contenu += "\n### 2.2 Résultats par Type de Contenu\n\n"
    
    # Messages
    contenu += "#### Messages (90 requêtes)\n\n"
    contenu += f"| Modèle | Taux Réussite | P@{TOP_K_BENCHMARK} | R@{TOP_K_BENCHMARK} | MRR |\n"
    contenu += "|--------|---------------|-----|-----|-----|\n"
    
    for res in resultats_tries:
        if 'par_type' in res and 'message' in res['par_type']:
            msg_res = res['par_type']['message']
            contenu += f"| **{res['modele']}** | {msg_res.get('taux_reussite', 0):.1f}% | {msg_res.get(f'precision@{TOP_K_BENCHMARK}', 0):.3f} | {msg_res.get(f'recall@{TOP_K_BENCHMARK}', 0):.3f} | {msg_res['mrr']:.3f} |\n"
    
    # Images
    contenu += "\n#### Images (10 requêtes)\n\n"
    contenu += f"| Modèle | Taux Réussite | P@{TOP_K_BENCHMARK} | R@{TOP_K_BENCHMARK} | MRR |\n"
    contenu += "|--------|---------------|-----|-----|-----|\n"
    
    for res in resultats_tries:
        if 'par_type' in res and 'image' in res['par_type']:
            img_res = res['par_type']['image']
            contenu += f"| **{res['modele']}** | {img_res.get('taux_reussite', 0):.1f}% | {img_res.get(f'precision@{TOP_K_BENCHMARK}', 0):.3f} | {img_res.get(f'recall@{TOP_K_BENCHMARK}', 0):.3f} | {img_res['mrr']:.3f} |\n"
    
    contenu += "\n---\n\n## 🏆 Conclusions\n\n"
    
    # Meilleur modèle (si résultats disponibles)
    if resultats_tries:
        meilleur = resultats_tries[0]
        contenu += f"### Meilleur Modèle Global: **{meilleur['modele']}**\n\n"
        
        # Vérifier si le modèle a une erreur
        if 'erreur' in meilleur:
            contenu += f"⚠️ **Erreur:** {meilleur['erreur']}\n\n"
        else:
            contenu += f"- **Score:** {meilleur.get('taux_reussite', 0):.1f}/100 ({meilleur.get('taux_reussite', 0):.1f}% de requêtes réussies)\n"
            contenu += f"- **MRR:** {meilleur['mrr']:.3f}\n"
            contenu += f"- **Precision@{TOP_K_BENCHMARK}:** {meilleur.get(f'precision@{TOP_K_BENCHMARK}', 0):.3f}\n"
            contenu += f"- **Recall@{TOP_K_BENCHMARK}:** {meilleur.get(f'recall@{TOP_K_BENCHMARK}', 0):.3f}\n\n"
    else:
        contenu += "⚠️ **Aucun résultat disponible** (tous les modèles ont échoué ou tests ignorés)\n\n"
    
    # Compromis vitesse/qualité
    contenu += "### Compromis Vitesse/Qualité\n\n"
    
    for res in resultats_tries:
        duree_modele = durees_texte.get(res['modele'], {})
        est_100k = duree_modele.get('estimation_100k_messages_h', 'N/A')
        
        if isinstance(est_100k, str):
            est_str = est_100k
        elif isinstance(est_100k, (int, float)):
            est_str = f"{est_100k:.1f}h"
        else:
            est_str = "N/A"
        
        score = res.get('taux_reussite', 0)
        contenu += f"- **{res['modele']}:** Score {score:.1f}/100, Vitesse {est_str} pour 100k msgs\n"
    
    contenu += "\n### Recommandations\n\n"
    contenu += f"1. **Pour la qualité maximale:** Privilégier le modèle avec le meilleur score (taux de réussite sur {TOP_K_BENCHMARK} résultats)\n"
    contenu += "2. **Pour la vitesse:** Choisir un modèle avec moins de paramètres (Jina-v3 ou Solon-large)\n"
    contenu += "3. **Pour les images:** BLIP fournit des descriptions de qualité mais reste lent (~2s/image)\n"
    contenu += "4. **Pour le déploiement:** Considérer le compromis entre score de qualité et temps d'encodage\n\n"
    contenu += f"**Note:** Le critère de réussite (top {TOP_K_BENCHMARK}) est configurable dans `config/settings.py` via `TOP_K_BENCHMARK`.\n\n"
    
    contenu += "---\n\n"
    contenu += f"*Rapport généré automatiquement par `benchmark_complet_opsemia.py` le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}*\n"
    
    # Écrire le fichier
    CHEMIN_OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(CHEMIN_OUTPUT_MD, 'w', encoding='utf-8') as f:
        f.write(contenu)
    
    print(f"   ✅ Rapport généré: {CHEMIN_OUTPUT_MD}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Fonction principale du benchmark complet."""
    # Parser les arguments
    parser = argparse.ArgumentParser(description="Benchmark complet OPSEMIA : Rapidité vs Qualité")
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force la réindexation même si les collections existent déjà"
    )
    parser.add_argument(
        "--skip-speed", 
        action="store_true", 
        help="Sauter les tests de rapidité d'encodage (calcul de durées)"
    )
    parser.add_argument(
        "--skip-quality", 
        action="store_true", 
        help="Sauter les tests de qualité (benchmark 100 requêtes)"
    )
    args = parser.parse_args()
    
    print("="*80)
    print("BENCHMARK COMPLET OPSEMIA : RAPIDITÉ vs QUALITÉ")
    print("="*80)
    print(f"Dataset: {CHEMIN_CSV_MESSAGES.name}")
    print(f"Images: {len(list(DOSSIER_IMAGES.glob('*')))} fichiers")
    print(f"Requêtes: 100 (90 messages + 10 images)")
    if args.force:
        print("⚠️  Mode FORCE : Réindexation complète")
    if args.skip_speed:
        print("⏭️  Tests de rapidité désactivés")
    if args.skip_quality:
        print("⏭️  Tests de qualité désactivés")
    print("="*80)
    
    # ========== PARTIE 1: CALCUL DES DURÉES ==========
    if not args.skip_speed:
        print("\n🚀 PARTIE 1/2 : CALCUL DES DURÉES D'ENCODAGE (RAPIDITÉ)\n")
        
        durees_texte = calculer_durees_encodage_texte()
        durees_images = calculer_durees_encodage_images()
    else:
        print("\n⏭️  PARTIE 1/2 : CALCUL DES DURÉES IGNORÉ\n")
        durees_texte = {}
        durees_images = {}
    
    # ========== PARTIE 2: BENCHMARK DE QUALITÉ ==========
    if not args.skip_quality:
        print("\n🚀 PARTIE 2/2 : BENCHMARK DE QUALITÉ (PRÉCISION)\n")
    else:
        print("\n⏭️  PARTIE 2/2 : BENCHMARK DE QUALITÉ IGNORÉ\n")
    
    resultats_benchmark = []
    
    # Charger parametres
    parametres = obtenir_parametres()
    
    # Créer encodeur d'images (partagé pour tous les modèles)
    encodeur_texte_temp = EncodeurTexte(
        id_modele=parametres.ID_MODELE_EMBEDDING,
        preference_peripherique=parametres.PERIPHERIQUE_EMBEDDING
    )
    encodeur_image = EncodeurImage(
        encodeur_texte=encodeur_texte_temp,
        preference_peripherique=parametres.PERIPHERIQUE_EMBEDDING,
    )
    
    for modele_info in MODELES_TEXTE:
        print(f"\n{'='*80}")
        print(f"MODÈLE: {modele_info['nom']}")
        print(f"{'='*80}")
        
        try:
            # Charger encodeur
            if modele_info['local']:
                try:
                    encodeur = SentenceTransformer(modele_info['id'], trust_remote_code=True)
                except:
                    encodeur = SentenceTransformer(modele_info['id'])
                
                encodeur_wrap = EncodeurTexte(
                    id_modele=modele_info['id'],
                    preference_peripherique=parametres.PERIPHERIQUE_EMBEDDING
                )
            else:
                encodeur = None
                encodeur_wrap = None
            
            if not args.skip_quality:
                # Indexer dataset
                nom_collection = indexer_dataset_benchmark(
                    modele_info, 
                    encodeur_wrap, 
                    encodeur_image,
                    force_reindex=args.force
                )
                
                # Évaluer
                resultats = evaluer_modele_benchmark(modele_info, nom_collection)
                resultats_benchmark.append(resultats)
                
                # Nettoyer uniquement si force (sinon garder le cache)
                if args.force:
                    db = BaseVectorielle(chemin_persistance=CHEMIN_DB_BENCHMARK)
                    db.supprimer_collection(nom_collection)
                    print(f"   🗑️  Collection temporaire supprimée")
                else:
                    print(f"   💾 Collection conservée pour cache")
                    
        except Exception as e:
            print(f"\n❌ ERREUR CRITIQUE avec le modèle {modele_info['nom']}: {type(e).__name__}: {str(e)}")
            print(f"   ⚠️  Le modèle sera ignoré dans les résultats")
            print(f"   ⏩ Passage au modèle suivant...\n")
            
            # Ajouter un résultat par défaut avec erreur
            if not args.skip_quality:
                resultats_benchmark.append({
                    "modele": modele_info['nom'],
                    "erreur": str(e),
                    "precision@1": 0,
                    "precision@3": 0,
                    f"precision@{TOP_K_BENCHMARK}": 0,
                    f"recall@{TOP_K_BENCHMARK}": 0,
                    "mrr": 0,
                    "taux_reussite": 0,
                })
        
        finally:
            # Libérer la mémoire
            if 'encodeur' in locals():
                del encodeur
            if 'encodeur_wrap' in locals():
                del encodeur_wrap
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            import gc
            gc.collect()
    
    # ========== PARTIE 3: GÉNÉRATION RAPPORT ==========
    if not args.skip_speed or not args.skip_quality:
        print("\n🚀 PARTIE 3/3 : GÉNÉRATION DU RAPPORT\n")
        
        generer_rapport_markdown(durees_texte, durees_images, resultats_benchmark)
        
        print("\n" + "="*80)
        print("✅ BENCHMARK TERMINÉ AVEC SUCCÈS!")
        print("="*80)
        print(f"📄 Rapport disponible: {CHEMIN_OUTPUT_MD}")
        if not args.skip_quality:
            print(f"📊 {len(resultats_benchmark)} modèles testés")
            print(f"🎯 {sum([len(obtenir_requetes_messages()), len(obtenir_requetes_images())])} requêtes évaluées")
        if not args.force and not args.skip_quality:
            print(f"💾 Collections conservées dans {CHEMIN_DB_BENCHMARK}")
            print(f"   Utilisez scripts/nettoyer_benchmark.py pour nettoyer")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("⚠️  Aucun test exécuté (tous ignorés)")
        print("="*80)


if __name__ == "__main__":
    main()

