from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import Optional

# Forcer UTF-8 pour la sortie console (nécessaire pour les emojis sur Windows)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ajouter le répertoire racine au path pour les imports
racine_projet = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(racine_projet))

from config.settings import obtenir_parametres
from src.backend.core.search_engine import MoteurRecherche
from src.backend.database.indexer import indexer_csv_messages
from src.backend.database.vector_db import BaseVectorielle


def executer_pipeline_complet(nom_cas: str = "cas1", chemin_csv_override: Optional[str] = None) -> None:
    """Pipeline complet: indexation d'un CSV de messages dans ChromaDB.

    Ce script lance l'indexation complète :
    - Parse les messages du CSV (détection automatique du format Cas1/Cas2/Cas3)
    - Crée des chunks de contexte
    - Encode tout avec le modèle configuré (ex: BGE-M3)
    - Stocke dans ChromaDB (chroma.sqlite3)
    
    Args:
        nom_cas: Nom du cas pour les collections (ex: "cas1", "cas3")
        chemin_csv_override: Chemin vers un CSV spécifique (sinon utilise celui de la config)
    
    Exemples d'utilisation:
        # Indexer Cas1 (ancienne structure)
        executer_pipeline_complet("cas1", "Cas/Cas1/sms.csv")
        
        # Indexer Cas3 (nouvelle structure)
        executer_pipeline_complet("cas3", "Cas/Cas3/sms.csv")
    """
    parametres = obtenir_parametres()

    # Utiliser le chemin fourni ou celui de la config
    chemin_csv = chemin_csv_override or parametres.CHEMIN_CSV_DONNEES

    print("=" * 70)
    print(f"OPSEMIA - Indexation complète du CSV {nom_cas.upper()}")
    print("=" * 70)
    print(f"📁 Fichier source: {chemin_csv}")
    print(f"🧠 Modèle: {parametres.ID_MODELE_EMBEDDING}")

    # Indexation complète du CSV
    stats = indexer_csv_messages(
        chemin_csv=chemin_csv,
        parametres=parametres,
        nom_cas=nom_cas,
        reinitialiser=True,  # Réinitialiser pour un test propre
    )

    print(f"\n🎉 Indexation terminée avec succès!")
    print(f"📁 Fichier indexé: {stats['fichier_csv']}")
    print(f"📊 Total: {stats['messages_indexe']} messages + {stats['chunks_indexes']} chunks")
    
    print(f"\n💾 Base de données: {parametres.CHEMIN_BASE_CHROMA}")
    print("📚 Collections créées:")
    print(f"   - messages_{nom_cas} ({stats['messages_indexe']} documents)")
    print(f"   - message_chunks_{nom_cas} ({stats['chunks_indexes']} documents)")
    
    print(f"\n🔍 Pour examiner la base:")
    print(f"   - Fichier: data/chroma_db/chroma.sqlite3")
    print(f"   - Tables importantes: collections, embeddings, embedding_metadata")
    print(f"   - Collections: messages_{nom_cas}, message_chunks_{nom_cas}")


def recherche_interactive(
    nom_cas: str = "cas1",
    nombre_resultats: Optional[int] = None,
) -> None:
    """Interface de recherche interactive dans le terminal.

    Args:
        nom_cas: Nom du cas à rechercher (ex: "cas1")
        nombre_resultats: Nombre de résultats à afficher (utilise config par défaut si None)
    """
    parametres = obtenir_parametres()
    
    # Initialiser la base vectorielle et le moteur de recherche
    db = BaseVectorielle(chemin_persistance=parametres.CHEMIN_BASE_CHROMA)
    moteur = MoteurRecherche(base_vectorielle=db, parametres=parametres)
    
    nom_collection = f"{parametres.NOM_COLLECTION_MESSAGES}_{nom_cas}"
    
    # Vérifier que la collection existe
    try:
        count = db.compter_documents(nom_collection)
        if count == 0:
            print(f"❌ La collection '{nom_collection}' est vide ou n'existe pas.")
            print(f"   Veuillez d'abord indexer les données avec executer_pipeline_complet()")
            return
    except Exception as e:
        print(f"❌ Erreur lors de l'accès à la collection: {e}")
        return

    print("\n" + "=" * 70)
    print("🔍 OPSEMIA - Recherche Sémantique Interactive")
    print("=" * 70)
    print(f"📚 Collection: {nom_collection} ({count} documents)")
    print(f"🧠 Modèle: {parametres.ID_MODELE_EMBEDDING}")
    print(f"⚙️  Méthode: {parametres.METHODE_RECHERCHE}")
    print(f"📊 Résultats par requête: {nombre_resultats or parametres.NOMBRE_RESULTATS_RECHERCHE}")
    print(f"🚫 Exclusion bruit: {'Oui' if parametres.EXCLURE_BRUIT_PAR_DEFAUT else 'Non'}")
    print("\n💡 Tapez votre requête (ou 'quit' pour quitter)")
    print("=" * 70)
    
    while True:
        try:
            # Demander la requête à l'utilisateur
            requete = input("\n🔎 Requête: ").strip()
            
            # Quitter si demandé
            if requete.lower() in ["quit", "exit", "q"]:
                print("\n👋 Au revoir!")
                break
            
            # Ignorer les requêtes vides
            if not requete:
                continue
            
            # Effectuer la recherche
            print(f"\n⏳ Recherche en cours...")
            resultats = moteur.rechercher(
                requete=requete,
                nom_collection=nom_collection,
                nombre_resultats=nombre_resultats,
            )
            
            # Afficher les résultats
            if not resultats:
                print("❌ Aucun résultat trouvé.")
                continue
            
            print(f"\n✅ {len(resultats)} résultat(s) trouvé(s):")
            print("-" * 70)
            
            for i, res in enumerate(resultats, 1):
                score = res["score"]
                texte = res["document"][:150]  # Tronquer à 150 caractères
                metadata = res["metadata"]
                
                # Extraire quelques métadonnées clés
                timestamp = metadata.get("timestamp", "N/A")
                direction = metadata.get("direction", "N/A")
                contact = metadata.get("contact_name") or metadata.get("from", "N/A")
                is_noise = metadata.get("is_noise", False)
                
                # Afficher le résultat
                print(f"\n{i}. [Score: {score:.3f}] {'🔇' if is_noise else ''}")
                print(f"   📅 {timestamp} | 👤 {contact} | ↔️  {direction}")
                print(f"   💬 {texte}{'...' if len(res['document']) > 150 else ''}")
            
            print("-" * 70)
            
        except KeyboardInterrupt:
            print("\n\n👋 Interruption détectée. Au revoir!")
            break
        except Exception as e:
            print(f"\n❌ Erreur lors de la recherche: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    import sys
    
    print("=" * 70)
    print("🚀 OPSEMIA - Pipeline d'indexation et de recherche")
    print("=" * 70)
    print("\nOptions disponibles:")
    print("  1. Indexer Cas1 (ancienne structure)")
    print("  2. Indexer Cas3 (nouvelle structure)")
    print("  3. Recherche interactive dans Cas1")
    print("  4. Recherche interactive dans Cas3")
    print("  5. Quitter")
    print("=" * 70)
    
    # Si argument ligne de commande passé
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["--search", "-s"]:
            cas = sys.argv[2] if len(sys.argv) > 2 else "cas1"
            recherche_interactive(nom_cas=cas)
        elif arg in ["--index", "-i"]:
            cas = sys.argv[2] if len(sys.argv) > 2 else "cas1"
            chemin = sys.argv[3] if len(sys.argv) > 3 else None
            executer_pipeline_complet(nom_cas=cas, chemin_csv_override=chemin)
        else:
            print(f"\n❌ Argument inconnu: {sys.argv[1]}")
            print("\nUtilisation:")
            print("  python pipeline_example.py --index cas1 [chemin_csv]")
            print("  python pipeline_example.py --search cas1")
    else:
        # Menu interactif
        while True:
            choix = input("\n👉 Votre choix (1-5): ").strip()
            
            if choix == "1":
                print("\n📋 Indexation de Cas1...")
                executer_pipeline_complet("cas1", "Cas/Cas1/sms.csv")
                
            elif choix == "2":
                print("\n📋 Indexation de Cas3...")
                executer_pipeline_complet("cas3", "Cas/Cas3/sms.csv")
                
            elif choix == "3":
                print("\n🔍 Recherche interactive dans Cas1...")
                recherche_interactive(nom_cas="cas1")
                
            elif choix == "4":
                print("\n🔍 Recherche interactive dans Cas3...")
                recherche_interactive(nom_cas="cas3")
                
            elif choix == "5":
                print("\n👋 Au revoir!")
                break
                
            else:
                print("❌ Choix invalide. Veuillez choisir entre 1 et 5.")
            
            # Demander si on continue
            continuer = input("\n🔄 Retourner au menu? (o/n): ").strip().lower()
            if continuer not in ["o", "oui", "y", "yes"]:
                print("\n👋 Au revoir!")
                break


