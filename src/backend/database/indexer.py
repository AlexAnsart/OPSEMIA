"""Pipeline d'indexation complet : CSV → Parsing → Débruitage → Encodage → ChromaDB."""

from __future__ import annotations

import io
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

# Forcer UTF-8 pour la sortie console (nécessaire pour les emojis sur Windows)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ajouter le répertoire racine au path pour les imports
racine_projet = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(racine_projet))

from config.settings import Parametres
from src.backend.core.chunking import creer_chunks_fenetre_glissante
from src.backend.core.denoising import ajouter_flag_bruit
from src.backend.database.vector_db import BaseVectorielle
from src.backend.models.model_manager import obtenir_encodeur_texte
from src.backend.parsers.message_extractor import parser_sms_depuis_csv


def indexer_csv_messages(
    chemin_csv: str | Path,
    parametres: Parametres,
    nom_cas: Optional[str] = None,
    reinitialiser: bool = False,
    progress_callback: Optional[callable] = None,
    log_verbose: bool = False,
) -> Dict[str, Any]:
    """Pipeline complet d'indexation d'un CSV de messages dans ChromaDB.

    Args:
        chemin_csv: Chemin vers le fichier CSV à indexer
        parametres: Paramètres de configuration
        nom_cas: Nom du cas pour les collections (ex: "cas1"). Si None, utilise les noms par défaut
        reinitialiser: Si True, supprime les collections existantes avant d'indexer
        progress_callback: Fonction de callback pour la progression (etape, %, message)
        log_verbose: Si True, affiche chaque message/chunk embeddé (verbeux pour gros fichiers)

    Returns:
        Statistiques d'indexation (nombre de messages, chunks, durée, etc.)
    """
    debut_total = time.time()
    stats = {
        "fichier_csv": str(chemin_csv),
        "nom_cas": nom_cas,
        "messages_indexe": 0,
        "chunks_indexes": 0,
        "duree_parsing_sec": 0,
        "duree_debruitage_sec": 0,
        "duree_encodage_messages_sec": 0,
        "duree_encodage_chunks_sec": 0,
        "duree_stockage_sec": 0,
        "duree_totale_sec": 0,
    }

    # Noms des collections (avec suffixe de cas si spécifié)
    suffixe = f"_{nom_cas}" if nom_cas else ""
    nom_collection_messages = parametres.NOM_COLLECTION_MESSAGES + suffixe
    nom_collection_chunks = parametres.NOM_COLLECTION_CHUNKS + suffixe

    print(f"🚀 Démarrage de l'indexation de {chemin_csv}")
    print(f"   Collections: {nom_collection_messages} / {nom_collection_chunks}")
    
    # Helper pour envoyer la progression
    def _emit_progress(etape: str, pct: float, msg: str):
        if progress_callback:
            progress_callback(etape, pct, msg)

    _emit_progress("initialisation", 0, "Démarrage de l'indexation...")

    # ========== 1. PARSING ==========
    print("\n📄 Phase 1/5: Parsing du CSV...")
    _emit_progress("parsing", 5, "Lecture du fichier CSV...")
    debut_phase = time.time()
    messages = parser_sms_depuis_csv(Path(chemin_csv))
    stats["duree_parsing_sec"] = time.time() - debut_phase
    print(f"   ✓ {len(messages)} messages parsés ({stats['duree_parsing_sec']:.2f}s)")
    _emit_progress("parsing", 20, f"{len(messages)} messages parsés")

    # ========== 2. DÉBRUITAGE ==========
    print("\n🧹 Phase 2/5: Débruitage...")
    _emit_progress("debruitage", 22, "Détection du spam et publicités...")
    debut_phase = time.time()
    messages = ajouter_flag_bruit(messages)
    stats["duree_debruitage_sec"] = time.time() - debut_phase
    print(f"   ✓ Flags de bruit ajoutés ({stats['duree_debruitage_sec']:.2f}s)")
    _emit_progress("debruitage", 30, "Débruitage terminé")

    # ========== 3. CHUNKING ==========
    print("\n🪟 Phase 3/5: Création des chunks de contexte...")
    _emit_progress("chunking", 32, "Création des fenêtres de contexte...")
    debut_phase = time.time()
    chunks = creer_chunks_fenetre_glissante(
        messages,
        taille_fenetre=parametres.TAILLE_FENETRE_CHUNK,
        overlap=parametres.OVERLAP_FENETRE_CHUNK,
    )
    duree_chunking = time.time() - debut_phase
    print(f"   ✓ {len(chunks)} chunks créés (fenêtre={parametres.TAILLE_FENETRE_CHUNK}, "
          f"overlap={parametres.OVERLAP_FENETRE_CHUNK}) ({duree_chunking:.2f}s)")
    _emit_progress("chunking", 40, f"{len(chunks)} chunks créés")

    # ========== 4. ENCODAGE ==========
    print("\n🧠 Phase 4/5: Encodage vectoriel...")
    _emit_progress("encodage", 42, f"Chargement du modèle {parametres.ID_MODELE_EMBEDDING}...")
    encodeur = obtenir_encodeur_texte()
    dimension_embedding = encodeur.dimension_embedding
    print(f"   Modèle: {parametres.ID_MODELE_EMBEDDING} (dim={dimension_embedding})")

    # Encodage des messages individuels
    print("   → Encodage des messages individuels...")
    _emit_progress("encodage", 45, f"Encodage de {len(messages)} messages...")
    debut_phase = time.time()
    
    # Coercition pour éviter les None (sentence-transformers n'accepte que des str)
    textes_messages = [(m.get("message") or "") for m in messages]
    
    # Encodage par batch avec progression
    taille_lot = 32
    total_messages = len(textes_messages)
    print(f"     📦 {total_messages} messages à encoder par lots de {taille_lot}...")
    
    liste_embeddings = []
    temps_batches_messages = []  # Pour statistiques
    
    for i in range(0, total_messages, taille_lot):
        batch = textes_messages[i:i+taille_lot]
        batch_debut = time.time()
        
        # Encoder le batch
        batch_embeddings = encodeur.encoder(batch, taille_lot=taille_lot)
        liste_embeddings.append(batch_embeddings)
        
        batch_duree = time.time() - batch_debut
        temps_batches_messages.append(batch_duree)
        
        messages_traites = min(i + taille_lot, total_messages)
        pct = 45 + (messages_traites / total_messages) * 20  # 45-65%
        
        # Log du batch (toujours affiché)
        print(f"     ├─ Batch {i//taille_lot + 1}/{(total_messages + taille_lot - 1)//taille_lot}: "
              f"{messages_traites}/{total_messages} messages ({batch_duree:.2f}s)")
        
        # Log détaillé de chaque message (seulement si verbose activé)
        if log_verbose:
            for j, texte in enumerate(batch):
                msg_idx = i + j
                texte_apercu = (texte[:60] + "...") if len(texte) > 60 else texte
                print(f"        └─ [{msg_idx+1}/{total_messages}] {texte_apercu}")
        
        # Émettre la progression
        _emit_progress("encodage", pct, 
                      f"Messages: {messages_traites}/{total_messages} ({pct-45:.0f}% encodage)")
    
    # Concaténer tous les embeddings
    embeddings_messages = np.vstack(liste_embeddings)
    
    stats["duree_encodage_messages_sec"] = time.time() - debut_phase
    
    # Statistiques d'encodage des messages
    if temps_batches_messages:
        temps_moyen_msg = np.mean(temps_batches_messages)
        temps_min_msg = np.min(temps_batches_messages)
        temps_max_msg = np.max(temps_batches_messages)
        nb_batches_msg = len(temps_batches_messages)
        
        # Stocker les stats pour le résumé final
        stats["nb_batches_messages"] = nb_batches_msg
        stats["temps_moyen_batch_messages"] = temps_moyen_msg
        stats["temps_min_batch_messages"] = temps_min_msg
        stats["temps_max_batch_messages"] = temps_max_msg
        stats["debit_messages_par_sec"] = total_messages/stats['duree_encodage_messages_sec']
        
        print(f"     ✓ {len(embeddings_messages)} embeddings générés ({stats['duree_encodage_messages_sec']:.2f}s)")
        print(f"       📊 Stats encodage messages:")
        print(f"          • {nb_batches_msg} batches de ~{taille_lot} messages")
        print(f"          • Temps moyen/batch: {temps_moyen_msg:.2f}s")
        print(f"          • Batch le plus rapide: {temps_min_msg:.2f}s")
        print(f"          • Batch le plus lent: {temps_max_msg:.2f}s")
        print(f"          • Débit: {stats['debit_messages_par_sec']:.1f} msg/s")
    
    _emit_progress("encodage", 65, f"Messages encodés ({stats['duree_encodage_messages_sec']:.1f}s)")

    # Encodage des chunks
    print("   → Encodage des chunks de contexte...")
    _emit_progress("encodage", 67, f"Encodage de {len(chunks)} chunks...")
    debut_phase = time.time()
    
    # Même précaution pour les chunks
    textes_chunks = [(c.get("texte_concatene") or "") for c in chunks]
    
    # Encodage par batch avec progression
    total_chunks = len(textes_chunks)
    print(f"     📦 {total_chunks} chunks à encoder par lots de {taille_lot}...")
    
    liste_embeddings_chunks = []
    temps_batches_chunks = []  # Pour statistiques
    
    for i in range(0, total_chunks, taille_lot):
        batch = textes_chunks[i:i+taille_lot]
        batch_debut = time.time()
        
        # Encoder le batch
        batch_embeddings = encodeur.encoder(batch, taille_lot=taille_lot)
        liste_embeddings_chunks.append(batch_embeddings)
        
        batch_duree = time.time() - batch_debut
        temps_batches_chunks.append(batch_duree)
        
        chunks_traites = min(i + taille_lot, total_chunks)
        pct = 67 + (chunks_traites / total_chunks) * 13  # 67-80%
        
        # Log du batch (toujours affiché)
        print(f"     ├─ Batch {i//taille_lot + 1}/{(total_chunks + taille_lot - 1)//taille_lot}: "
              f"{chunks_traites}/{total_chunks} chunks ({batch_duree:.2f}s)")
        
        # Log détaillé de chaque chunk (seulement si verbose activé)
        if log_verbose:
            for j, texte in enumerate(batch):
                chunk_idx = i + j
                texte_apercu = (texte[:60] + "...") if len(texte) > 60 else texte
                print(f"        └─ [Chunk {chunk_idx+1}/{total_chunks}] {texte_apercu}")
        
        # Émettre la progression
        _emit_progress("encodage", pct,
                      f"Chunks: {chunks_traites}/{total_chunks} ({pct-67:.0f}% encodage)")
    
    # Concaténer tous les embeddings
    embeddings_chunks = np.vstack(liste_embeddings_chunks)
    
    stats["duree_encodage_chunks_sec"] = time.time() - debut_phase
    
    # Statistiques d'encodage des chunks
    if temps_batches_chunks:
        temps_moyen_chunk = np.mean(temps_batches_chunks)
        temps_min_chunk = np.min(temps_batches_chunks)
        temps_max_chunk = np.max(temps_batches_chunks)
        nb_batches_chunk = len(temps_batches_chunks)
        
        # Stocker les stats pour le résumé final
        stats["nb_batches_chunks"] = nb_batches_chunk
        stats["temps_moyen_batch_chunks"] = temps_moyen_chunk
        stats["temps_min_batch_chunks"] = temps_min_chunk
        stats["temps_max_batch_chunks"] = temps_max_chunk
        stats["debit_chunks_par_sec"] = total_chunks/stats['duree_encodage_chunks_sec']
        
        print(f"     ✓ {len(embeddings_chunks)} embeddings de chunks générés ({stats['duree_encodage_chunks_sec']:.2f}s)")
        print(f"       📊 Stats encodage chunks:")
        print(f"          • {nb_batches_chunk} batches de ~{taille_lot} chunks")
        print(f"          • Temps moyen/batch: {temps_moyen_chunk:.2f}s")
        print(f"          • Batch le plus rapide: {temps_min_chunk:.2f}s")
        print(f"          • Batch le plus lent: {temps_max_chunk:.2f}s")
        print(f"          • Débit: {stats['debit_chunks_par_sec']:.1f} chunks/s")
    
    _emit_progress("encodage", 80, f"Chunks encodés ({stats['duree_encodage_chunks_sec']:.1f}s)")

    # ========== 5. STOCKAGE CHROMADB ==========
    print("\n💾 Phase 5/5: Stockage dans ChromaDB...")
    _emit_progress("stockage", 82, "Connexion à ChromaDB...")
    debut_phase = time.time()
    
    db = BaseVectorielle(chemin_persistance=parametres.CHEMIN_BASE_CHROMA)
    
    # Réinitialiser si demandé
    if reinitialiser:
        print("   ⚠️  Réinitialisation des collections existantes...")
        _emit_progress("stockage", 84, "Suppression des anciennes données...")
        db.supprimer_collection(nom_collection_messages)
        db.supprimer_collection(nom_collection_chunks)

    # Stocker les messages individuels
    print("   → Stockage des messages...")
    _emit_progress("stockage", 86, f"Stockage de {len(messages)} messages...")
    # S'assurer que tous les IDs sont des strings non vides
    ids_messages = [m.get("id") or f"msg_{i}" for i, m in enumerate(messages)]
    metadonnees_messages = [_extraire_metadonnees_message(m) for m in messages]
    
    db.ajouter_messages(
        nom_collection=nom_collection_messages,
        ids=ids_messages,
        embeddings=embeddings_messages.tolist(),
        metadonnees=metadonnees_messages,
        documents=textes_messages,
    )
    stats["messages_indexe"] = len(ids_messages)
    _emit_progress("stockage", 92, "Messages stockés")

    # Stocker les chunks
    print("   → Stockage des chunks...")
    _emit_progress("stockage", 94, f"Stockage de {len(chunks)} chunks...")
    # S'assurer que tous les IDs de chunks sont des strings non vides
    ids_chunks = [c.get("chunk_id") or f"chunk_{i}" for i, c in enumerate(chunks)]
    metadonnees_chunks = [c["metadata"] for c in chunks]
    
    db.ajouter_messages(
        nom_collection=nom_collection_chunks,
        ids=ids_chunks,
        embeddings=embeddings_chunks.tolist(),
        metadonnees=metadonnees_chunks,
        documents=textes_chunks,
    )
    stats["chunks_indexes"] = len(ids_chunks)

    stats["duree_stockage_sec"] = time.time() - debut_phase
    print(f"   ✓ Stockage terminé ({stats['duree_stockage_sec']:.2f}s)")
    _emit_progress("stockage", 100, "Indexation terminée avec succès!")

    # ========== RÉSUMÉ ==========
    stats["duree_totale_sec"] = time.time() - debut_total
    
    print("\n" + "="*70)
    print("✅ INDEXATION TERMINÉE")
    print("="*70)
    print(f"📊 Résultats:")
    print(f"   • Messages indexés : {stats['messages_indexe']}")
    print(f"   • Chunks indexés   : {stats['chunks_indexes']}")
    print(f"\n⏱️  Durées par phase:")
    print(f"   • Parsing          : {stats['duree_parsing_sec']:.2f}s ({stats['duree_parsing_sec']/stats['duree_totale_sec']*100:.1f}%)")
    print(f"   • Débruitage       : {stats['duree_debruitage_sec']:.2f}s ({stats['duree_debruitage_sec']/stats['duree_totale_sec']*100:.1f}%)")
    print(f"   • Encodage messages: {stats['duree_encodage_messages_sec']:.2f}s ({stats['duree_encodage_messages_sec']/stats['duree_totale_sec']*100:.1f}%)")
    print(f"   • Encodage chunks  : {stats['duree_encodage_chunks_sec']:.2f}s ({stats['duree_encodage_chunks_sec']/stats['duree_totale_sec']*100:.1f}%)")
    print(f"   • Stockage         : {stats['duree_stockage_sec']:.2f}s ({stats['duree_stockage_sec']/stats['duree_totale_sec']*100:.1f}%)")
    print(f"   • TOTAL            : {stats['duree_totale_sec']:.2f}s")
    
    # Stats détaillées d'encodage si disponibles
    if "debit_messages_par_sec" in stats:
        print(f"\n📈 Performance encodage messages:")
        print(f"   • {stats['nb_batches_messages']} batches traités")
        print(f"   • Temps moyen/batch: {stats['temps_moyen_batch_messages']:.2f}s")
        print(f"   • Plus rapide: {stats['temps_min_batch_messages']:.2f}s | Plus lent: {stats['temps_max_batch_messages']:.2f}s")
        print(f"   • Débit: {stats['debit_messages_par_sec']:.1f} messages/s")
    
    if "debit_chunks_par_sec" in stats:
        print(f"\n📈 Performance encodage chunks:")
        print(f"   • {stats['nb_batches_chunks']} batches traités")
        print(f"   • Temps moyen/batch: {stats['temps_moyen_batch_chunks']:.2f}s")
        print(f"   • Plus rapide: {stats['temps_min_batch_chunks']:.2f}s | Plus lent: {stats['temps_max_batch_chunks']:.2f}s")
        print(f"   • Débit: {stats['debit_chunks_par_sec']:.1f} chunks/s")
    
    print(f"\n💾 Collections créées:")
    print(f"   • {nom_collection_messages}")
    print(f"   • {nom_collection_chunks}")
    print(f"📁 Base ChromaDB: {parametres.CHEMIN_BASE_CHROMA}")
    print("="*70)

    return stats


def _extraire_metadonnees_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """Extrait les métadonnées pertinentes d'un message pour ChromaDB.

    Args:
        message: Message normalisé

    Returns:
        Métadonnées JSON-serializable
    """
    return {
        "timestamp": message.get("timestamp", ""),
        "direction": message.get("direction", ""),
        "from": message.get("from", ""),
        "to": message.get("to", ""),
        "contact_name": message.get("contact_name", ""),
        "gps_lat": message.get("gps_lat") or 0.0,
        "gps_lon": message.get("gps_lon") or 0.0,
        "is_noise": message.get("is_noise", False),
        "app": message.get("app", ""),
    }

