<!-- 0bcf6f74-c049-47e9-8f4d-51e0cd7d24da bef7fe24-a6ef-4a5c-b8cc-fc96927ed137 -->
# Plan de Développement OPSEMIA

## Phase 1: Architecture de Base et Configuration

### Structure du Projet

Créer l'arborescence complète :

```
src/
├── backend/
│   ├── api/           # Routes Flask
│   ├── core/          # Logique métier
│   ├── models/        # Gestion des modèles ML
│   ├── database/      # ChromaDB wrapper
│   ├── parsers/       # Parsers CSV modulables
│   └── utils/         # Utilitaires
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── assets/
│   └── templates/
├── data/              # Dossier pour CSV et données
└── config/
    └── settings.py    # Configuration centralisée
```

### Fichier de Configuration

Créer `config/settings.py` avec tous les paramètres configurables :

- Modèle d'embedding (BGE-M3 par défaut, Nomic Embed v2 MoE alternatif)
- Dimensions des vecteurs (1024 pour BGE-M3, 768 pour Nomic)
- Paramètres de chunking (taille, overlap)
- Méthode de recherche (ANN/KNN)
- Type d'index ANN (HNSW, IVF)
- Seuils de filtrage
- Chemins des données

## Phase 2: Parser CSV Modulable

### Parser Générique

Créer `src/backend/parsers/csv_parser.py` :

- Fonction de détection automatique des colonnes pertinentes
- Mapping configurable entre colonnes CSV et champs internes
- Support des différents types : sms, email, media, call, etc.
- Validation et nettoyage des données

### Extracteurs Spécialisés

- `src/backend/parsers/message_extractor.py` : Extraire SMS/messages
- `src/backend/parsers/email_extractor.py` : Extraire emails
- `src/backend/parsers/media_extractor.py` : Extraire images/vidéos
- Chaque extracteur retourne une structure normalisée

## Phase 3: Service de Débruitage

### Détection de Spam/Pub

Créer `src/backend/core/denoising.py` :

- Règles heuristiques (mots-clés commerciaux, patterns)
- Détection contacts administratifs/commerciaux
- Ajout d'un flag `is_noise` booléen
- Système de règles facilement extensible

## Phase 4: Encodage et Vectorisation

### Gestion des Modèles

- `src/backend/models/model_manager.py` : Chargement dynamique selon config
- `src/backend/models/text_encoder.py` : Encodage texte via BGE-M3
- `src/backend/models/image_encoder.py` : BLIP pour description → BGE-M3
- Gestion mémoire et cache

### Chunking

`src/backend/core/chunking.py` :

- Messages individuels
- Fenêtre glissante configurable (N messages pour contexte)
- Préservation des métadonnées

## Phase 5: Base de Données Vectorielle

### ChromaDB Setup

`src/backend/database/vector_db.py` :

- Initialisation ChromaDB avec backend SQLite
- Collections séparées : messages, message_chunks, images, emails
- Fonctions CRUD avec gestion métadonnées
- Support des filtres (timestamp, GPS, type, is_noise)

### Indexation

`src/backend/database/indexer.py` :

- Pipeline complet : CSV → Parser → Débruitage → Encodage → ChromaDB
- Progression et logs
- Gestion des erreurs

## Phase 6: Moteur de Recherche

### Service de Recherche

`src/backend/core/search_engine.py` :

- Encodage de la requête utilisateur
- Application des filtres pré-recherche (réduction du corpus)
- Recherche ANN (HNSW) ou KNN selon config
- Post-ranking avec boost mots-clés
- Retour des top K résultats avec scores

### Filtres

`src/backend/core/filters.py` :

- Filtre temporel (début/fin via timestamp)
- Filtre géographique (rayon autour d'un point)
- Filtre par type (messages/emails/images)
- Exclusion du bruit

## Phase 7: API Backend Flask

### Routes Principales

`src/backend/api/routes.py` :

- `POST /api/load` : Charger un dossier de CSV
- `POST /api/search` : Recherche sémantique avec filtres
- `GET /api/context/<id>` : Obtenir contexte d'un résultat
- `GET /api/timeline` : Timeline complète
- `GET /api/stats` : Statistiques indexation
- `POST /api/config` : Mettre à jour configuration

### Application Flask

`src/backend/app.py` :

- Initialisation Flask avec CORS
- Configuration des routes
- Gestion des erreurs
- Logging

## Phase 8: Interface Frontend

### Page Principale

`src/frontend/templates/index.html` :

- Barre de recherche sémantique
- Filtres avancés (temps, GPS, type, exclusion bruit)
- Section résultats avec scores
- Visualisations multiples (liste, timeline, carte)

### Visualisation des Résultats

`src/frontend/static/js/search.js` :

- Affichage liste des résultats avec pertinence
- Click pour voir contexte
- Navigation dans conversations/timeline

### Vue Contextuelle

`src/frontend/static/js/context.js` :

- Affichage du message/email dans son contexte
- Messages adjacents
- Timeline interactive
- Carte géospatiale avec Leaflet.js

### Interface Admin

`src/frontend/templates/admin.html` :

- Upload/chargement de dossiers CSV
- Sélection du modèle d'embedding
- Configuration des paramètres
- Lancement indexation avec progression

### Styles

`src/frontend/static/css/main.css` :

- Design moderne et professionnel
- Responsive
- Thème adapté au contexte police scientifique

## Phase 9: Tests et Validation

### Test avec CSV de Démo

- Charger `Cas/Cas1/DEMO CSV NIVEAU SIMPLE (DROGUE).csv`
- Vérifier parsing correct (messages, emails, média)
- Indexer dans ChromaDB
- Tester recherches pertinentes ("rendez-vous", "transfert", etc.)
- Valider filtres temporels et géographiques

### Scénarios de Démonstration

Préparer requêtes de démo convaincantes montrant :

- Recherche sémantique vs. mots-clés
- Filtrage efficace
- Visualisation contextuelle

## Phase 10: Documentation et Finalisation

### README.md

Mettre à jour avec :

- Description détaillée du projet
- Architecture et composants
- Installation et dépendances
- Configuration (settings.py expliqué)
- Guide d'utilisation
- Section Fine-tuning (procédure théorique)
- Extensibilité et évolutions futures

### Fichiers de Dépendances

`requirements.txt` :

- Flask, Flask-CORS
- chromadb
- sentence-transformers
- torch
- Pillow (images)
- transformers (BLIP)
- numpy, pandas
- leaflet (via CDN pour cartes)

### Nettoyage

- Vérifier tous fichiers < 100 lignes
- S'assurer d'une fonction principale par fichier
- Commenter le code de manière claire
- Supprimer tout code temporaire

### To-dos

- [ ] Créer structure complète du projet et fichier settings.py avec tous les paramètres configurables
- [ ] Implémenter parser CSV modulable avec extracteurs pour messages, emails et média
- [ ] Créer service de débruitage avec détection spam/pub et flag is_noise
- [ ] Implémenter model_manager, encodeurs texte (BGE-M3) et images (BLIP), et système de chunking
- [ ] Setup ChromaDB avec collections et pipeline d'indexation complet
- [ ] Créer moteur de recherche avec filtres et ranking
- [ ] Implémenter API Flask avec toutes les routes nécessaires
- [ ] Développer interface web complète avec recherche, visualisations et contexte
- [ ] Créer interface admin pour chargement CSV et configuration
- [ ] Tester avec CSV de démo et valider tous les scénarios
- [ ] Finaliser README.md avec documentation complète et requirements.txt