#!/usr/bin/env python3
"""Script de benchmark pour comparer les performances des modèles d'embedding.

Ce script évalue plusieurs modèles d'embedding sur un dataset de test thématique
et calcule des métriques de performance:
- Precision@K : Proportion de documents pertinents parmi les K premiers résultats
- Recall@K : Proportion de documents pertinents retrouvés parmi tous les pertinents
- MRR (Mean Reciprocal Rank) : Moyenne des rangs réciproques du premier résultat pertinent
- NDCG@K : Normalized Discounted Cumulative Gain (qualité du classement)
- Temps d'encodage et de recherche
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer

# Ajouter le répertoire racine au path pour les imports
racine_projet = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(racine_projet))

from scripts.donnees_benchmark import obtenir_documents_test, obtenir_requetes_test


# Modèles à tester
MODELES_A_TESTER = [
    ("BAAI/bge-m3", "BGE-M3 (baseline)"),
    ("jinaai/jina-embeddings-v3", "Jina-v3"),
    ("Qwen/Qwen3-Embedding-8B", "Qwen3-8B"),
    # Le modèle Solon sera ajouté si l'ID est confirmé
]


def calculer_similarite_cosine(vecteur1: np.ndarray, vecteur2: np.ndarray) -> float:
    """Calcule la similarité cosine entre deux vecteurs (déjà normalisés)."""
    return float(np.dot(vecteur1, vecteur2))


def precision_at_k(resultats_ids: List[str], pertinents_ids: List[str], k: int) -> float:
    """Calcule la Precision@K.
    
    Args:
        resultats_ids: Liste des IDs retournés (ordonnés par pertinence)
        pertinents_ids: Liste des IDs pertinents attendus (ground truth)
        k: Nombre de premiers résultats à considérer
    
    Returns:
        Score de precision entre 0 et 1
    """
    if k == 0:
        return 0.0
    
    top_k = resultats_ids[:k]
    nb_pertinents_trouves = len([doc_id for doc_id in top_k if doc_id in pertinents_ids])
    return nb_pertinents_trouves / k


def recall_at_k(resultats_ids: List[str], pertinents_ids: List[str], k: int) -> float:
    """Calcule le Recall@K.
    
    Args:
        resultats_ids: Liste des IDs retournés
        pertinents_ids: Liste des IDs pertinents attendus
        k: Nombre de premiers résultats à considérer
    
    Returns:
        Score de recall entre 0 et 1
    """
    if len(pertinents_ids) == 0:
        return 0.0
    
    top_k = resultats_ids[:k]
    nb_pertinents_trouves = len([doc_id for doc_id in top_k if doc_id in pertinents_ids])
    return nb_pertinents_trouves / len(pertinents_ids)


def mean_reciprocal_rank(resultats_ids: List[str], pertinents_ids: List[str]) -> float:
    """Calcule le Mean Reciprocal Rank (MRR).
    
    Le MRR mesure à quelle position apparaît le premier résultat pertinent.
    MRR = 1/rang du premier résultat pertinent
    
    Returns:
        Score MRR entre 0 et 1 (1 = meilleur résultat en position 1)
    """
    for i, doc_id in enumerate(resultats_ids, 1):
        if doc_id in pertinents_ids:
            return 1.0 / i
    return 0.0


def ndcg_at_k(resultats_ids: List[str], pertinents_ids: List[str], k: int) -> float:
    """Calcule le Normalized Discounted Cumulative Gain (NDCG@K).
    
    Le NDCG mesure la qualité du classement en donnant plus de poids aux
    résultats pertinents qui apparaissent tôt dans la liste.
    
    Returns:
        Score NDCG entre 0 et 1 (1 = classement parfait)
    """
    def dcg(relevances: List[int], k: int) -> float:
        """Calcule le DCG."""
        dcg_score = 0.0
        for i, rel in enumerate(relevances[:k], 1):
            dcg_score += rel / np.log2(i + 1)
        return dcg_score
    
    # Relevances pour les résultats obtenus
    relevances = [1 if doc_id in pertinents_ids else 0 for doc_id in resultats_ids]
    
    # DCG idéal (résultats pertinents d'abord)
    ideal_relevances = [1] * min(len(pertinents_ids), k) + [0] * (k - len(pertinents_ids))
    
    dcg_score = dcg(relevances, k)
    idcg_score = dcg(ideal_relevances, k)
    
    if idcg_score == 0:
        return 0.0
    
    return dcg_score / idcg_score


def evaluer_modele(
    id_modele: str,
    nom_modele: str,
    documents: List[Dict],
    requetes: List[Tuple[str, List[str], str]],
    k: int = 5,
) -> Dict:
    """Évalue un modèle sur le dataset de test.
    
    Args:
        id_modele: ID Hugging Face du modèle
        nom_modele: Nom lisible du modèle
        documents: Liste des documents de test
        requetes: Liste des requêtes avec ground truth
        k: Nombre de résultats à considérer pour les métriques @K
    
    Returns:
        Dictionnaire avec les résultats et métriques
    """
    print(f"\n{'='*70}")
    print(f"ÉVALUATION: {nom_modele}")
    print(f"{'='*70}")
    print(f"ID Modèle: {id_modele}")
    
    try:
        # Charger le modèle
        print("⏳ Chargement du modèle...")
        debut_chargement = time.time()
        
        # trust_remote_code=True pour certains modèles comme Jina
        try:
            modele = SentenceTransformer(id_modele, trust_remote_code=True)
        except Exception:
            modele = SentenceTransformer(id_modele)
        
        temps_chargement = time.time() - debut_chargement
        print(f"✅ Modèle chargé ({temps_chargement:.2f}s)")
        print(f"   Dimensions: {modele.get_sentence_embedding_dimension()}")
        
        # Encoder les documents
        print("\n⏳ Encodage des documents...")
        debut_encodage = time.time()
        textes_docs = [doc["texte"] for doc in documents]
        embeddings_docs = modele.encode(
            textes_docs,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        temps_encodage_docs = time.time() - debut_encodage
        print(f"✅ {len(documents)} documents encodés ({temps_encodage_docs:.2f}s)")
        
        # Évaluer sur chaque requête
        print(f"\n⏳ Évaluation sur {len(requetes)} requêtes...")
        
        metriques_globales = {
            "precision@3": [],
            "recall@3": [],
            "precision@5": [],
            "recall@5": [],
            "mrr": [],
            "ndcg@5": [],
            "temps_recherche": [],
        }
        
        # Métriques par difficulté
        metriques_par_difficulte = {
            "facile": {"precision@5": [], "recall@5": [], "mrr": []},
            "moyen": {"precision@5": [], "recall@5": [], "mrr": []},
            "difficile": {"precision@5": [], "recall@5": [], "mrr": []},
        }
        
        for i, (requete, docs_pertinents, difficulte) in enumerate(requetes, 1):
            # Encoder la requête
            debut_recherche = time.time()
            embedding_requete = modele.encode(
                [requete],
                normalize_embeddings=True,
                show_progress_bar=False,
            )[0]
            
            # Calculer les similarités
            similarites = [
                (doc["id"], calculer_similarite_cosine(embedding_requete, emb_doc))
                for doc, emb_doc in zip(documents, embeddings_docs)
            ]
            
            # Trier par similarité décroissante
            similarites.sort(key=lambda x: x[1], reverse=True)
            resultats_ids = [doc_id for doc_id, _ in similarites]
            
            temps_recherche = time.time() - debut_recherche
            
            # Calculer les métriques
            p3 = precision_at_k(resultats_ids, docs_pertinents, 3)
            r3 = recall_at_k(resultats_ids, docs_pertinents, 3)
            p5 = precision_at_k(resultats_ids, docs_pertinents, 5)
            r5 = recall_at_k(resultats_ids, docs_pertinents, 5)
            mrr_score = mean_reciprocal_rank(resultats_ids, docs_pertinents)
            ndcg = ndcg_at_k(resultats_ids, docs_pertinents, 5)
            
            # Stocker les métriques
            metriques_globales["precision@3"].append(p3)
            metriques_globales["recall@3"].append(r3)
            metriques_globales["precision@5"].append(p5)
            metriques_globales["recall@5"].append(r5)
            metriques_globales["mrr"].append(mrr_score)
            metriques_globales["ndcg@5"].append(ndcg)
            metriques_globales["temps_recherche"].append(temps_recherche)
            
            # Stocker par difficulté
            metriques_par_difficulte[difficulte]["precision@5"].append(p5)
            metriques_par_difficulte[difficulte]["recall@5"].append(r5)
            metriques_par_difficulte[difficulte]["mrr"].append(mrr_score)
            
            # Afficher progression
            if i % 5 == 0 or i == len(requetes):
                print(f"   Requête {i}/{len(requetes)} traitée...")
        
        # Calculer les moyennes
        resultats = {
            "id_modele": id_modele,
            "nom_modele": nom_modele,
            "dimensions": modele.get_sentence_embedding_dimension(),
            "temps_chargement_sec": temps_chargement,
            "temps_encodage_docs_sec": temps_encodage_docs,
            "temps_moyen_recherche_ms": np.mean(metriques_globales["temps_recherche"]) * 1000,
            "precision@3": np.mean(metriques_globales["precision@3"]),
            "recall@3": np.mean(metriques_globales["recall@3"]),
            "precision@5": np.mean(metriques_globales["precision@5"]),
            "recall@5": np.mean(metriques_globales["recall@5"]),
            "mrr": np.mean(metriques_globales["mrr"]),
            "ndcg@5": np.mean(metriques_globales["ndcg@5"]),
            "metriques_par_difficulte": {
                diff: {
                    "precision@5": np.mean(metriques["precision@5"]) if metriques["precision@5"] else 0,
                    "recall@5": np.mean(metriques["recall@5"]) if metriques["recall@5"] else 0,
                    "mrr": np.mean(metriques["mrr"]) if metriques["mrr"] else 0,
                }
                for diff, metriques in metriques_par_difficulte.items()
            },
            "succes": True,
        }
        
        print(f"\n✅ Évaluation terminée!")
        afficher_resultats_modele(resultats)
        
        return resultats
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'évaluation: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "id_modele": id_modele,
            "nom_modele": nom_modele,
            "succes": False,
            "erreur": str(e),
        }


def afficher_resultats_modele(resultats: Dict):
    """Affiche les résultats d'évaluation d'un modèle."""
    if not resultats.get("succes", False):
        print(f"❌ Échec: {resultats.get('erreur', 'Erreur inconnue')}")
        return
    
    print(f"\n📊 RÉSULTATS:")
    print(f"   Dimensions: {resultats['dimensions']}")
    print(f"\n⏱️  PERFORMANCE:")
    print(f"   Chargement: {resultats['temps_chargement_sec']:.2f}s")
    print(f"   Encodage docs: {resultats['temps_encodage_docs_sec']:.2f}s")
    print(f"   Recherche moyenne: {resultats['temps_moyen_recherche_ms']:.2f}ms")
    print(f"\n🎯 QUALITÉ (moyenne sur toutes les requêtes):")
    print(f"   Precision@3: {resultats['precision@3']:.3f}")
    print(f"   Recall@3: {resultats['recall@3']:.3f}")
    print(f"   Precision@5: {resultats['precision@5']:.3f}")
    print(f"   Recall@5: {resultats['recall@5']:.3f}")
    print(f"   MRR: {resultats['mrr']:.3f}")
    print(f"   NDCG@5: {resultats['ndcg@5']:.3f}")
    
    print(f"\n📈 QUALITÉ PAR DIFFICULTÉ:")
    for difficulte, metriques in resultats["metriques_par_difficulte"].items():
        print(f"   {difficulte.capitalize()}:")
        print(f"      P@5: {metriques['precision@5']:.3f} | R@5: {metriques['recall@5']:.3f} | MRR: {metriques['mrr']:.3f}")


def comparer_modeles(resultats_liste: List[Dict]):
    """Affiche un tableau comparatif des modèles."""
    print(f"\n{'='*100}")
    print("COMPARAISON DES MODÈLES")
    print(f"{'='*100}")
    
    # Filtrer les modèles qui ont réussi
    resultats_valides = [r for r in resultats_liste if r.get("succes", False)]
    
    if not resultats_valides:
        print("❌ Aucun modèle n'a pu être évalué.")
        return
    
    # En-tête du tableau
    print(f"\n{'Modèle':<25} | {'Dim':<6} | {'P@5':<6} | {'R@5':<6} | {'MRR':<6} | {'NDCG@5':<7} | {'Temps(ms)':<10}")
    print("-" * 100)
    
    # Trier par NDCG@5 (métrique globale de qualité)
    resultats_valides.sort(key=lambda x: x["ndcg@5"], reverse=True)
    
    for res in resultats_valides:
        nom = res["nom_modele"][:24]
        dims = res["dimensions"]
        p5 = res["precision@5"]
        r5 = res["recall@5"]
        mrr = res["mrr"]
        ndcg = res["ndcg@5"]
        temps = res["temps_moyen_recherche_ms"]
        
        print(f"{nom:<25} | {dims:<6} | {p5:.3f}  | {r5:.3f}  | {mrr:.3f}  | {ndcg:.3f}   | {temps:>8.2f}")
    
    print("-" * 100)
    
    # Afficher le gagnant
    meilleur = resultats_valides[0]
    print(f"\n🏆 MEILLEUR MODÈLE: {meilleur['nom_modele']}")
    print(f"   NDCG@5: {meilleur['ndcg@5']:.3f} | MRR: {meilleur['mrr']:.3f} | Precision@5: {meilleur['precision@5']:.3f}")


def main():
    """Fonction principale du benchmark."""
    print("=" * 100)
    print("BENCHMARK DES MODÈLES D'EMBEDDING POUR OPSEMIA")
    print("=" * 100)
    
    # Charger les données de test
    documents = obtenir_documents_test()
    requetes = obtenir_requetes_test()
    
    print(f"\n📊 Dataset de test:")
    print(f"   - {len(documents)} documents")
    print(f"   - {len(requetes)} requêtes")
    
    # Évaluer chaque modèle
    resultats_liste = []
    
    for id_modele, nom_modele in MODELES_A_TESTER:
        try:
            resultats = evaluer_modele(id_modele, nom_modele, documents, requetes, k=5)
            resultats_liste.append(resultats)
        except KeyboardInterrupt:
            print("\n\n⚠️  Interruption utilisateur. Arrêt du benchmark.")
            break
        except Exception as e:
            print(f"\n❌ Erreur inattendue pour {nom_modele}: {e}")
            resultats_liste.append({
                "id_modele": id_modele,
                "nom_modele": nom_modele,
                "succes": False,
                "erreur": str(e),
            })
    
    # Comparer les résultats
    if resultats_liste:
        comparer_modeles(resultats_liste)
    
    print(f"\n{'='*100}")
    print("✅ BENCHMARK TERMINÉ")
    print(f"{'='*100}")


if __name__ == "__main__":
    main()

