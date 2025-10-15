#!/usr/bin/env python3
"""Script pour analyser et diagnostiquer la base ChromaDB."""

import sys
import sqlite3
from pathlib import Path

# Ajouter le répertoire racine au path
racine_projet = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(racine_projet))


def analyser_chromadb():
    """Analyse complète de la base ChromaDB."""
    db_path = racine_projet / "data" / "chroma_db" / "chroma.sqlite3"
    
    if not db_path.exists():
        print("ERREUR: Base ChromaDB non trouvee")
        return False
    
    print("=" * 70)
    print("ANALYSE DE LA BASE CHROMADB")
    print("=" * 70)
    print(f"Fichier: {db_path}")
    print(f"Taille: {db_path.stat().st_size / 1024:.2f} KB\n")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # 1. Vérifier les collections
    print("COLLECTIONS:")
    cursor.execute("SELECT id, name FROM collections ORDER BY name;")
    collections = cursor.fetchall()
    
    if not collections:
        print("  Aucune collection trouvee!\n")
        conn.close()
        return False
    
    for coll_id, coll_name in collections:
        print(f"  - {coll_name} (UUID: {coll_id})")
    
    # 2. Vérifier les segments
    print(f"\nSEGMENTS:")
    cursor.execute("SELECT id, collection, type FROM segments;")
    segments = cursor.fetchall()
    for seg_id, coll_id, seg_type in segments:
        cursor.execute("SELECT name FROM collections WHERE id = ?;", (coll_id,))
        coll_name = cursor.fetchone()[0]
        print(f"  - {seg_id}")
        print(f"    Collection: {coll_name}")
        print(f"    Type: {seg_type}")
    
    # 3. Compter dans les tables principales
    print(f"\nSTATISTIQUES:")
    cursor.execute("SELECT COUNT(*) FROM collections;")
    print(f"  Collections: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM segments;")
    print(f"  Segments: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM embeddings;")
    nb_embeddings = cursor.fetchone()[0]
    print(f"  Embeddings: {nb_embeddings}")
    
    cursor.execute("SELECT COUNT(*) FROM embedding_metadata;")
    print(f"  Metadonnees: {cursor.fetchone()[0]}")
    
    # 4. Structure des tables
    print(f"\nSTRUCTURE DES TABLES:")
    
    cursor.execute("PRAGMA table_info(embeddings);")
    emb_cols = cursor.fetchall()
    print(f"  embeddings: {[col[1] for col in emb_cols]}")
    
    cursor.execute("PRAGMA table_info(embedding_metadata);")
    meta_cols = cursor.fetchall()
    print(f"  embedding_metadata: {[col[1] for col in meta_cols]}")
    
    # 5. Examiner les données réelles
    if nb_embeddings > 0:
        print(f"\nECHANTILLON DE DONNEES:")
        cursor.execute("SELECT * FROM embeddings LIMIT 3;")
        for row in cursor.fetchall():
            print(f"  Embedding: {row}")
        
        cursor.execute("SELECT * FROM embedding_metadata LIMIT 10;")
        print(f"\n  Metadonnees:")
        for row in cursor.fetchall():
            print(f"    {row}")
    else:
        print(f"\nATTENTION: Aucun embedding trouve dans la table embeddings!")
        print("  Cela suggere un probleme lors du stockage.")
    
    # 6. Résumé
    print(f"\n" + "=" * 70)
    if nb_embeddings > 0:
        print("STATUT: OK - Base fonctionnelle")
        print(f"  {nb_embeddings} embeddings indexes")
        print(f"\nOu sont les embeddings:")
        print(f"  - Table: 'embeddings' (liens/references)")
        print(f"  - Fichiers binaires separes (Chroma >= 0.5)")
        print(f"  - Metadonnees: table 'embedding_metadata'")
        resultat = True
    else:
        print("PROBLEME: Base vide!")
        print("  L'indexation ne s'est pas effectuee correctement.")
        resultat = False
    
    print("=" * 70)
    
    conn.close()
    return resultat


if __name__ == "__main__":
    succes = analyser_chromadb()
    sys.exit(0 if succes else 1)
