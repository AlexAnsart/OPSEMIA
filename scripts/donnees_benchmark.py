#!/usr/bin/env python3
"""Dataset de test pour le benchmark des modèles d'embedding.

Ce module contient des requêtes de test thématiques pour évaluer les performances
des différents modèles d'embedding dans le contexte d'OPSEMIA (analyse policière).

Les requêtes couvrent différents aspects:
- Transactions financières suspectes
- Rendez-vous et lieux de rencontre
- Trafic de substances
- Menaces et violence
- Relations entre individus
- Dates et horaires précis
"""

from typing import Dict, List, Tuple


# Documents de test thématiques (corpus de référence)
DOCUMENTS_TEST = [
    # Groupe 1: Transactions financières
    {
        "id": "doc_001",
        "texte": "Salut, tu peux me transférer 5000€ sur mon compte avant demain? C'est urgent.",
        "themes": ["finance", "urgence"],
    },
    {
        "id": "doc_002", 
        "texte": "J'ai reçu l'argent liquide. Tout est OK. Je te confirme que les 10k sont bien là.",
        "themes": ["finance", "liquide"],
    },
    {
        "id": "doc_003",
        "texte": "Le paiement doit se faire en espèces. Pas de trace bancaire, tu comprends.",
        "themes": ["finance", "liquide", "suspect"],
    },
    {
        "id": "doc_004",
        "texte": "Merci pour le virement ! J'ai bien reçu les 200€ pour le cadeau d'anniversaire.",
        "themes": ["finance", "normal"],
    },
    
    # Groupe 2: Rendez-vous et lieux
    {
        "id": "doc_005",
        "texte": "On se retrouve au parking du centre commercial à 15h. Viens seul.",
        "themes": ["rendez-vous", "lieu", "suspect"],
    },
    {
        "id": "doc_006",
        "texte": "Rendez-vous confirmé pour demain 14h30 au café de la gare. À demain !",
        "themes": ["rendez-vous", "lieu", "horaire"],
    },
    {
        "id": "doc_007",
        "texte": "Tu connais l'entrepôt près du port? On se voit là-bas ce soir à 22h.",
        "themes": ["rendez-vous", "lieu", "suspect", "horaire"],
    },
    {
        "id": "doc_008",
        "texte": "Je t'attends devant le cinéma à 20h pour la séance. Tu prends le pop-corn?",
        "themes": ["rendez-vous", "lieu", "horaire", "normal"],
    },
    
    # Groupe 3: Trafic
    {
        "id": "doc_009",
        "texte": "La livraison est prête. 500g comme convenu. Même endroit que d'habitude.",
        "themes": ["trafic", "suspect", "quantite"],
    },
    {
        "id": "doc_010",
        "texte": "J'ai ce qu'il te faut. Qualité premium. Appelle-moi en numéro masqué.",
        "themes": ["trafic", "suspect"],
    },
    {
        "id": "doc_011",
        "texte": "Le colis est arrivé ce matin. Tout est conforme à la commande. Merci Amazon!",
        "themes": ["livraison", "normal"],
    },
    
    # Groupe 4: Menaces et violence
    {
        "id": "doc_012",
        "texte": "Tu vas le regretter. Je sais où tu habites. Fais gaffe à toi.",
        "themes": ["menace", "violence"],
    },
    {
        "id": "doc_013",
        "texte": "Si tu parles, tu es mort. Compris? Garde ça pour toi.",
        "themes": ["menace", "violence", "intimidation"],
    },
    {
        "id": "doc_014",
        "texte": "Je suis vraiment désolé pour hier soir. J'étais énervé mais je regrette.",
        "themes": ["excuse", "normal"],
    },
    
    # Groupe 5: Relations et identités
    {
        "id": "doc_015",
        "texte": "Marc a dit que tu étais d'accord pour le plan. Il te contactera demain.",
        "themes": ["relation", "intermediaire"],
    },
    {
        "id": "doc_016",
        "texte": "Le patron veut te voir. Il n'est pas content de ce qui s'est passé.",
        "themes": ["hierarchie", "suspect"],
    },
    {
        "id": "doc_017",
        "texte": "Sophie et Thomas seront là aussi. On se fait une soirée jeux vidéos!",
        "themes": ["relation", "normal"],
    },
    
    # Groupe 6: Dates et événements
    {
        "id": "doc_018",
        "texte": "Le 15 mars à 18h, tout doit être réglé. Pas de retard cette fois.",
        "themes": ["date", "horaire", "urgence"],
    },
    {
        "id": "doc_019",
        "texte": "RDV le 23/03 pour finaliser l'affaire. Tu amènes les documents?",
        "themes": ["date", "rendez-vous", "suspect"],
    },
    {
        "id": "doc_020",
        "texte": "Joyeux anniversaire ! On se fait un resto samedi soir?",
        "themes": ["date", "normal"],
    },
]


# Requêtes de test avec documents pertinents attendus (ground truth)
# Format: (requête, [IDs des documents pertinents], difficulté)
REQUETES_TEST: List[Tuple[str, List[str], str]] = [
    # Requêtes financières
    (
        "transfert d'argent en liquide",
        ["doc_002", "doc_003", "doc_001"],  # doc_003 et doc_002 sont les plus pertinents
        "facile"
    ),
    (
        "transaction financière urgente",
        ["doc_001", "doc_003"],
        "moyen"
    ),
    (
        "paiement en espèces sans trace",
        ["doc_003", "doc_002"],
        "moyen"
    ),
    
    # Requêtes rendez-vous
    (
        "rendez-vous suspect lieu isolé",
        ["doc_005", "doc_007"],
        "facile"
    ),
    (
        "rencontre avec horaire précis",
        ["doc_006", "doc_007", "doc_008", "doc_018"],
        "difficile"  # Beaucoup de résultats possibles
    ),
    (
        "parking centre commercial",
        ["doc_005"],
        "facile"
    ),
    
    # Requêtes trafic
    (
        "livraison marchandise suspecte",
        ["doc_009", "doc_010"],
        "moyen"
    ),
    (
        "produit illégal qualité quantité",
        ["doc_009", "doc_010"],
        "moyen"
    ),
    
    # Requêtes menaces
    (
        "menace violence intimidation",
        ["doc_012", "doc_013"],
        "facile"
    ),
    (
        "menace de mort",
        ["doc_013", "doc_012"],
        "facile"
    ),
    
    # Requêtes relations
    (
        "intermédiaire qui transmet message",
        ["doc_015", "doc_016"],
        "difficile"
    ),
    (
        "hiérarchie patron chef",
        ["doc_016"],
        "moyen"
    ),
    
    # Requêtes temporelles
    (
        "date mars rendez-vous",
        ["doc_018", "doc_019"],
        "moyen"
    ),
    (
        "urgence délai temps limité",
        ["doc_001", "doc_018"],
        "difficile"
    ),
    
    # Requêtes complexes (combinaisons)
    (
        "rendez-vous argent transaction",
        ["doc_005", "doc_001", "doc_003"],
        "difficile"
    ),
    (
        "lieu suspect heure tardive",
        ["doc_007", "doc_005"],
        "moyen"
    ),
]


def obtenir_documents_test() -> List[Dict]:
    """Retourne la liste des documents de test."""
    return DOCUMENTS_TEST


def obtenir_requetes_test() -> List[Tuple[str, List[str], str]]:
    """Retourne la liste des requêtes avec leur ground truth."""
    return REQUETES_TEST


def afficher_statistiques_dataset():
    """Affiche les statistiques du dataset de test."""
    print("=" * 70)
    print("DATASET DE TEST - STATISTIQUES")
    print("=" * 70)
    print(f"Nombre de documents: {len(DOCUMENTS_TEST)}")
    print(f"Nombre de requêtes: {len(REQUETES_TEST)}")
    
    # Statistiques par difficulté
    difficultes = {"facile": 0, "moyen": 0, "difficile": 0}
    for _, _, diff in REQUETES_TEST:
        difficultes[diff] += 1
    
    print("\nRépartition par difficulté:")
    for diff, count in difficultes.items():
        print(f"  - {diff.capitalize()}: {count} requêtes")
    
    # Statistiques par thème
    themes = {}
    for doc in DOCUMENTS_TEST:
        for theme in doc["themes"]:
            themes[theme] = themes.get(theme, 0) + 1
    
    print("\nThèmes couverts:")
    for theme, count in sorted(themes.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {theme}: {count} documents")
    
    print("=" * 70)


if __name__ == "__main__":
    afficher_statistiques_dataset()
    
    print("\n" + "=" * 70)
    print("EXEMPLES DE REQUÊTES")
    print("=" * 70)
    
    for i, (requete, docs_attendus, diff) in enumerate(REQUETES_TEST[:5], 1):
        print(f"\n{i}. [{diff.upper()}] {requete}")
        print(f"   Documents pertinents: {', '.join(docs_attendus)}")

