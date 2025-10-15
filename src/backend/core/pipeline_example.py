from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

# Ajouter le répertoire racine au path pour les imports
racine_projet = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(racine_projet))

from config.settings import obtenir_parametres
from src.backend.core.search_engine import MoteurRecherche
from src.backend.database.indexer import indexer_csv_messages
from src.backend.database.vector_db import BaseVectorielle


def executer_pipeline_complet() -> None:
    """Pipeline complet: indexation de TOUT le CSV Cas1 dans ChromaDB.

    Ce script lance l'indexation complète :
    - Parse les 275 messages du CSV
    - Crée des chunks de contexte
    - Encode tout avec BGE-M3
    - Stocke dans ChromaDB (chroma.sqlite3)
    """
    parametres = obtenir_parametres()

    print("=" * 70)
    print("OPSEMIA - Indexation complète du CSV Cas1")
    print("=" * 70)

    # Indexation complète du CSV Cas1
    stats = indexer_csv_messages(
        chemin_csv=parametres.CHEMIN_CSV_DONNEES,
        parametres=parametres,
        nom_cas="cas1",
        reinitialiser=True,  # Réinitialiser pour un test propre
    )

    print(f"\n🎉 Indexation terminée avec succès!")
    print(f"📁 Fichier indexé: {stats['fichier_csv']}")
    print(f"📊 Total: {stats['messages_indexe']} messages + {stats['chunks_indexes']} chunks")
    
    print(f"\n💾 Base de données: {parametres.CHEMIN_BASE_CHROMA}")
    print("📚 Collections créées:")
    print(f"   - messages_cas1 ({stats['messages_indexe']} documents)")
    print(f"   - message_chunks_cas1 ({stats['chunks_indexes']} documents)")
    
    print(f"\n🔍 Pour examiner la base:")
    print(f"   - Fichier: data/chroma_db/chroma.sqlite3")
    print(f"   - Tables importantes: collections, embeddings, embedding_metadata")
    print(f"   - Collections: messages_cas1, message_chunks_cas1")


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
    
    # Si argument "--search" passé, lancer la recherche interactive
    if len(sys.argv) > 1 and sys.argv[1] == "--search":
        recherche_interactive()
    else:
        # Sinon, exécuter le pipeline d'indexation complet
        executer_pipeline_complet()
        
        # Proposer de lancer la recherche
        print("\n" + "=" * 70)
        reponse = input("🔍 Voulez-vous tester la recherche interactive? (o/n): ").strip().lower()
        if reponse in ["o", "oui", "y", "yes"]:
            print()
            recherche_interactive()


