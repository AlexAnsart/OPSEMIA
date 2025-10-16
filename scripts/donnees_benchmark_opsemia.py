#!/usr/bin/env python3
"""Dataset de benchmark pour OPSEMIA - 100 requêtes de test.

Ce module contient 90 requêtes pour messages et 10 pour images, basées sur
le dataset Breaking Bad (Cas4/sms.csv et Cas4/images.csv).

Les requêtes couvrent différents aspects :
- Production et qualité de drogue
- Transactions financières et blanchiment
- Rendez-vous et livraisons
- Sécurité et surveillance
- Enquêtes DEA
- Relations entre personnages
- Recherche d'images (descriptions visuelles)
"""

from typing import Dict, List, Tuple


# Requêtes pour MESSAGES (90 requêtes)
# Format: (requête, [IDs des messages pertinents], difficulté)
REQUETES_MESSAGES: List[Tuple[str, List[str], str]] = [
    # Production et qualité (10 requêtes)
    ("production de drogue avec pureté élevée 99%", ["msg_001", "msg_025", "msg_037", "msg_153", "msg_399"], "facile"),
    ("livraison prête qualité exceptionnelle", ["msg_001", "msg_025", "msg_009", "msg_043"], "moyen"),
    ("nouveau record de pureté chimie", ["msg_037", "msg_153", "msg_311"], "moyen"),
    ("rendement production augmente", ["msg_103", "msg_120", "msg_249", "msg_251"], "moyen"),
    ("équipements installés laboratoire", ["msg_013", "msg_065", "msg_263", "msg_435"], "facile"),
    ("test qualité produit fini", ["msg_037", "msg_322", "msg_399"], "moyen"),
    ("objectif 400 livres par mois", ["msg_277", "msg_326", "msg_328"], "difficile"),
    ("batch préparé rendement exceptionnel", ["msg_025", "msg_187", "msg_496"], "facile"),
    ("optimisation processus chimique", ["msg_103", "msg_120", "msg_309", "msg_361"], "moyen"),
    ("capacité production maximale atteinte", ["msg_249", "msg_250", "msg_290", "msg_511"], "difficile"),
    
    # Transactions financières (15 requêtes)
    ("transfert argent liquide cash", ["msg_004", "msg_036", "msg_049", "msg_128"], "facile"),
    ("paiement 20k en espèces", ["msg_004", "msg_024", "msg_071"], "moyen"),
    ("12 millions reçus paiement", ["msg_292", "msg_348", "msg_529"], "facile"),
    ("récupération fonds collecte", ["msg_049", "msg_090", "msg_161", "msg_223"], "moyen"),
    ("blanchiment argent laverie", ["msg_017", "msg_039", "msg_095", "msg_296"], "facile"),
    ("investissement motel centre commercial", ["msg_068", "msg_148", "msg_302", "msg_484"], "moyen"),
    ("offshore Îles Caïmans Vierges", ["msg_079", "msg_341", "msg_377"], "moyen"),
    ("virement compte habituel", ["msg_010", "msg_036", "msg_052"], "facile"),
    ("split offshore investissements", ["msg_091", "msg_162", "msg_224", "msg_295"], "difficile"),
    ("collecte mensuelle record", ["msg_161", "msg_294", "msg_449", "msg_532"], "facile"),
    ("paiement cartel frontière", ["msg_142", "msg_292", "msg_348"], "moyen"),
    ("revenus locatifs blanchiment", ["msg_252", "msg_355", "msg_514"], "moyen"),
    ("société écran Delaware offshore", ["msg_051", "msg_307", "msg_455"], "difficile"),
    ("comptabilité laverie montage fiscal", ["msg_017", "msg_126", "msg_238"], "moyen"),
    ("actifs totaux croissance trimestre", ["msg_230", "msg_540"], "difficile"),
    
    # Rendez-vous et livraisons (12 requêtes)
    ("rendez-vous 15h point habituel", ["msg_002", "msg_006", "msg_008"], "facile"),
    ("livraison prévue ce soir", ["msg_003", "msg_021", "msg_069"], "facile"),
    ("convoi arrivée 20h frontière", ["msg_021", "msg_022", "msg_047"], "moyen"),
    ("transfert demain après-midi", ["msg_002", "msg_008", "msg_014"], "moyen"),
    ("départ 5h du matin sécurité maximale", ["msg_288", "msg_345", "msg_526"], "difficile"),
    ("livraison cartel 500 livres", ["msg_287", "msg_345", "msg_523", "msg_526"], "facile"),
    ("réunion villa Don Eladio", ["msg_409", "msg_410", "msg_411"], "moyen"),
    ("point frontière mexicaine", ["msg_029", "msg_078", "msg_173", "msg_266"], "facile"),
    ("transport vers El Paso Houston", ["msg_021", "msg_175", "msg_227"], "moyen"),
    ("équipe réception prête", ["msg_022", "msg_175"], "difficile"),
    ("livraison effectuée mission accomplie", ["msg_140", "msg_292", "msg_348", "msg_529"], "facile"),
    ("convoi sécurisé route alternative", ["msg_047", "msg_105", "msg_227"], "moyen"),
    
    # Sécurité et surveillance (13 requêtes)
    ("surveillance périmètre sécurisé", ["msg_005", "msg_041", "msg_086"], "facile"),
    ("caméras installées tout périmètre", ["msg_041", "msg_042"], "moyen"),
    ("problème distributeur parle trop", ["msg_019", "msg_035"], "facile"),
    ("occupe-toi discret et rapide", ["msg_020", "msg_035", "msg_076"], "difficile"),
    ("élimination confirmée pas de traces", ["msg_035", "msg_100"], "moyen"),
    ("équipe sécurité 6 hommes armés", ["msg_402", "msg_404"], "moyen"),
    ("nouvelle recrue ex-militaire fiable", ["msg_256", "msg_285", "msg_317"], "moyen"),
    ("protocole rouge alerte DEA", ["msg_193", "msg_209"], "facile"),
    ("suspension opérations temporaire", ["msg_016", "msg_028", "msg_113"], "facile"),
    ("audit sécurité complet clean", ["msg_167", "msg_517", "msg_554"], "moyen"),
    ("indic identifié DEA neutraliser", ["msg_055", "msg_075", "msg_076"], "difficile"),
    ("sécurité maximale voyage Mexique", ["msg_288", "msg_346", "msg_402"], "moyen"),
    ("aucune menace détectée contrôle", ["msg_554", "msg_555"], "facile"),
    
    # Enquêtes et risques (10 requêtes)
    ("enquête DEA laveries zone", ["msg_027", "msg_089", "msg_191"], "facile"),
    ("attention nouvelle enquête alerte", ["msg_027", "msg_192", "msg_193"], "facile"),
    ("arrestation risque Badger", ["msg_053", "msg_073"], "moyen"),
    ("contrôle fiscal IRS laverie", ["msg_124", "msg_125", "msg_177"], "moyen"),
    ("inspection prévue semaine prochaine", ["msg_033", "msg_124", "msg_242"], "facile"),
    ("DEA cible zone industrielle", ["msg_089", "msg_111", "msg_199"], "moyen"),
    ("témoin doit garder silence", ["msg_073", "msg_074", "msg_107"], "difficile"),
    ("surveillance accrue activités suspectes", ["msg_089", "msg_111"], "moyen"),
    ("pression diminue protocole orange", ["msg_207", "msg_209"], "difficile"),
    ("contrôle terminé aucun problème", ["msg_179", "msg_261"], "facile"),
    
    # Négociations et affaires (12 requêtes)
    ("prix 35k la livre pour volume", ["msg_024", "msg_070"], "moyen"),
    ("négociation 200 livres cartel", ["msg_029", "msg_173"], "moyen"),
    ("accord conclu contrat 2 ans", ["msg_328", "msg_411", "msg_415"], "facile"),
    ("expansion Arizona Nevada territoire", ["msg_023", "msg_304", "msg_471"], "moyen"),
    ("nouveau client Flagstaff vérification", ["msg_273", "msg_304"], "difficile"),
    ("besoin 100 livres par semaine", ["msg_336", "msg_440"], "facile"),
    ("surcharge prix urgence 15%", ["msg_070", "msg_071"], "moyen"),
    ("contrat 6 mois prix fixe", ["msg_163", "msg_164"], "moyen"),
    ("cartel satisfait qualité partenariat", ["msg_134", "msg_314", "msg_546"], "facile"),
    ("expansion vers Las Vegas Nevada", ["msg_471", "msg_502", "msg_508"], "moyen"),
    ("proposition achat 800k intéressé", ["msg_057", "msg_058"], "difficile"),
    ("Don Eladio impressionné accord majeur", ["msg_409", "msg_411"], "facile"),
    
    # Relations personnages (10 requêtes)
    ("Walter chimiste production laboratoire", ["msg_001", "msg_011", "msg_045", "msg_187"], "facile"),
    ("Jesse distributeur Albuquerque secteurs", ["msg_003", "msg_015", "msg_031", "msg_083"], "moyen"),
    ("Mike sécurité surveillance équipe", ["msg_005", "msg_019", "msg_055", "msg_167"], "facile"),
    ("Skyler blanchiment laverie investissements", ["msg_017", "msg_039", "msg_068", "msg_126"], "moyen"),
    ("Saul avocat documents montage offshore", ["msg_007", "msg_027", "msg_051", "msg_307"], "moyen"),
    ("Gale assistant chimiste second laboratoire", ["msg_013", "msg_037", "msg_065", "msg_120"], "facile"),
    ("Lydia Madrigal fournisseur méthylamine", ["msg_009", "msg_033", "msg_059", "msg_116"], "moyen"),
    ("Tyrus sécurité transport frontière", ["msg_021", "msg_047", "msg_105", "msg_175"], "facile"),
    ("Hector Salamanca cartel territoire", ["msg_029", "msg_077", "msg_173", "msg_266"], "moyen"),
    ("Declan acheteur Phoenix Arizona", ["msg_023", "msg_043", "msg_069", "msg_163"], "facile"),
    
    # Spam et messages commerciaux (8 requêtes - pour tester le filtrage)
    ("pizza promotion restaurant commercial", ["msg_254"], "facile"),
    ("banque notification relevé mensuel", ["msg_255"], "facile"),
    ("Netflix streaming nouveau contenu", ["msg_260"], "moyen"),
    ("assurance voiture économisez publicité", ["msg_265"], "facile"),
    ("Amazon ventes flash weekend", ["msg_272"], "facile"),
    ("forfait téléphone illimité promotion", ["msg_279", "msg_298"], "moyen"),
    ("fitness gym offre spéciale été", ["msg_282", "msg_384"], "facile"),
    ("services commerciaux promotion soldes", ["msg_254", "msg_255", "msg_260", "msg_265"], "moyen"),
]


# Requêtes pour IMAGES (10 requêtes)
# Format: (requête_utilisateur_à_compléter, [IDs des images attendues], difficulté)
# L'utilisateur doit remplir les requêtes textuelles appropriées
# Note: Les IDs correspondent aux 10 premières images du CSV (img_0 à img_9)
# img_0: 099a5885-a8d9-4ace-a80c-1b91d6dd9873.jpg
# img_1: 0d9375bb-5f53-49e3-a76a-40316932340e.jpg
# img_2: 20180610_FIFA_Friendly_Match_Austria_vs._Brazil_Neymar_850_1705.jpg (Neymar)
# img_3: 2ab0bdb7-5e7f-4786-8f25-d9b89a67ed7b.jpg
# img_4: 4209af9b-753f-423a-9657-3c541f110166.jpg
# img_5: 538b9bdf-5316-417b-9430-97a1b698e7cc.jpg
# img_6: 7c22b5ad-f123-491b-bd4a-f9c03a187587.jpg
# img_7: 8c1c92bb-0048-4c74-96de-78048ae601a9.jpg
# img_8: aae5efdb-58a5-477a-9e16-4b070a49de0e.jpg
# img_9: b03a73b6-4569-4ab5-bf15-c57c1087ae4d.jpg
REQUETES_IMAGES: List[Tuple[str, List[str], str]] = [
    # Requête 1: Image Neymar football
    ("Footballer sur un terrain de foot", ["img_2"], "moyen"),
    
    # Requête 2: Images avec coordonnées GPS Albuquerque (35.08, -106.65)
    ("Billets d'argent", ["img_0", "img_3", "img_5"], "difficile"),
    
    # Requête 3: Image prise en avril 2010
    ("Footballer à genoux sur le terrain", ["img_1"], "moyen"),
    
    # Requête 4: Image prise en juin 2010 (Phoenix)
    ("Voiture garée près du trottoir", ["img_4"], "moyen"),
    
    # Requête 5: Image prise en août 2010 (Juarez, Mexique)
    ("Personne debout sur une voiture de police", ["img_6"], "difficile"),
    
    # Requête 6: Image prise en août 2010 (Monterrey, Mexique)
    ("Personne avec un tshirt rayé et une barbe regardant la caméra", ["img_7"], "difficile"),
    
    # Requête 7: Image prise en septembre 2010 (Albuquerque)
    ("Palmiers", ["img_8"], "moyen"),
    
    # Requête 8: Image prise en septembre 2010 (Phoenix)
    ("Sac à dos avec livre", ["img_9"], "moyen"),
    
    # Requête 9: Images génériques (UUID)
    ("Billets d'argent", ["img_0", "img_1", "img_3"], "facile"),
    
    # Requête 10: Toutes les images de mars-mai 2010
    ("Billets d'argent", ["img_0", "img_1", "img_3"], "facile"),
]


def obtenir_requetes_messages() -> List[Tuple[str, List[str], str]]:
    """Retourne la liste des 90 requêtes pour messages."""
    return REQUETES_MESSAGES


def obtenir_requetes_images() -> List[Tuple[str, List[str], str]]:
    """Retourne la liste des 10 requêtes pour images."""
    return REQUETES_IMAGES


def obtenir_toutes_requetes() -> List[Tuple[str, List[str], str, str]]:
    """Retourne toutes les 100 requêtes (messages + images) avec type.
    
    Returns:
        Liste de tuples (requête, IDs attendus, difficulté, type)
    """
    requetes_completes = []
    
    # Ajouter les requêtes messages
    for requete, ids, diff in REQUETES_MESSAGES:
        requetes_completes.append((requete, ids, diff, "message"))
    
    # Ajouter les requêtes images
    for requete, ids, diff in REQUETES_IMAGES:
        requetes_completes.append((requete, ids, diff, "image"))
    
    return requetes_completes


def afficher_statistiques_dataset():
    """Affiche les statistiques du dataset de benchmark."""
    print("=" * 70)
    print("DATASET DE BENCHMARK OPSEMIA - STATISTIQUES")
    print("=" * 70)
    print(f"Nombre total de requêtes: {len(REQUETES_MESSAGES) + len(REQUETES_IMAGES)}")
    print(f"  - Requêtes messages: {len(REQUETES_MESSAGES)}")
    print(f"  - Requêtes images: {len(REQUETES_IMAGES)}")
    
    # Statistiques par difficulté
    difficultes = {"facile": 0, "moyen": 0, "difficile": 0}
    for _, _, diff in REQUETES_MESSAGES + REQUETES_IMAGES:
        difficultes[diff] += 1
    
    print("\nRépartition par difficulté:")
    for diff, count in difficultes.items():
        pct = count / (len(REQUETES_MESSAGES) + len(REQUETES_IMAGES)) * 100
        print(f"  - {diff.capitalize()}: {count} requêtes ({pct:.1f}%)")
    
    # Statistiques thématiques pour messages
    themes_messages = {
        "Production/Qualité": 10,
        "Transactions financières": 15,
        "Rendez-vous/Livraisons": 12,
        "Sécurité/Surveillance": 13,
        "Enquêtes/Risques": 10,
        "Négociations/Affaires": 12,
        "Relations personnages": 10,
        "Spam/Commercial": 8,
    }
    
    print("\nThèmes couverts (messages):")
    for theme, count in themes_messages.items():
        print(f"  - {theme}: {count} requêtes")
    
    print("=" * 70)


if __name__ == "__main__":
    afficher_statistiques_dataset()
    
    print("\n" + "=" * 70)
    print("EXEMPLES DE REQUÊTES MESSAGES")
    print("=" * 70)
    
    for i, (requete, docs_attendus, diff) in enumerate(REQUETES_MESSAGES[:10], 1):
        print(f"\n{i}. [{diff.upper()}] {requete}")
        print(f"   Documents pertinents: {', '.join(docs_attendus[:3])}...")
    
    print("\n" + "=" * 70)
    print("REQUÊTES IMAGES (À COMPLÉTER)")
    print("=" * 70)
    print("\nLes requêtes images doivent être complétées avec des descriptions")
    print("textuelles appropriées pour tester la recherche d'images via BLIP.")
    print(f"\nNombre d'images à indexer: {len(REQUETES_IMAGES)}")

