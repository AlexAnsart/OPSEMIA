# OPSEMIA

**Outil Policier de SEMantique et d'Investigation Analytique**

Moteur de recherche sémantique pour l'analyse de supports numériques (téléphones, ordinateurs) destiné à la police scientifique. Permet la recherche intelligente dans les messages, emails, images et vidéos extraits d'enquêtes.

## 🎯 Fonctionnalités

- **Recherche sémantique** : Recherche par sens plutôt que par mots-clés exacts
- **Support multi-formats** : Messages (SMS), emails, images, vidéos
- **Indexation vectorielle** : Utilisation de modèles d'embedding de pointe (BGE-M3)
- **Chunking contextuel** : Fenêtre glissante pour préserver le contexte conversationnel
- **Débruitage** : Filtrage automatique des pubs et contenus commerciaux
- **Base vectorielle locale** : ChromaDB avec backend SQLite pour garantir la confidentialité
- **Configuration flexible** : Tous les paramètres modifiables via `config/settings.py`

## 📋 Architecture

```
CSV bruts → Parsing → Débruitage → Chunking → Encodage (BGE-M3) → ChromaDB (SQLite)
```

- **Parsing modulable** : Support de différentes structures CSV
- **Encodage** : BGE-M3 (1024 dimensions) ou Nomic Embed v2 MoE
- **Chunking** : Messages individuels + fenêtres de contexte glissantes
- **Stockage** : Base vectorielle persistante ChromaDB

## 🚀 Installation

### 1. Prérequis

- Python 3.9 ou supérieur
- ~6 GB de RAM minimum
- ~3 GB d'espace disque (pour le modèle BGE-M3)

### 2. Créer un environnement virtuel

```bash
python -m venv venv
```

**Activation :**

- Windows : `venv\Scripts\activate`
- Linux/Mac : `source venv/bin/activate`

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Télécharger le modèle d'embedding

**Option 1 : BGE-M3 (par défaut, recommandé pour débuter)**
```bash
python scripts/telecharger_modele_bge.py
```

**Option 2 : Jina-embeddings-v3 (léger et performant)**
```bash
python scripts/telecharger_modele_jina.py
```

**Option 3 : Qwen3-Embedding-8B (haute performance, nécessite 16+ GB RAM)**
```bash
python scripts/telecharger_modele_qwen3.py
```

Cette étape télécharge le modèle choisi et le met en cache. Le temps de téléchargement varie selon le modèle (570 MB à 8 GB).

### 5. Analyser la base vectorielle (optionnel)

```bash
python scripts/analyser_chromadb.py
```

Ce script analyse le contenu de la base ChromaDB et affiche les statistiques d'indexation.

## 📊 Utilisation

### Indexer un CSV de messages

Le pipeline complet indexe automatiquement le CSV de démo (Cas1) :

```bash
python src/backend/core/pipeline_example.py
```

Ce script effectue :
1. **Parsing** du CSV
2. **Débruitage** (flagging du spam/pubs)
3. **Chunking** (fenêtres de contexte glissantes)
4. **Encodage** vectoriel (BGE-M3)
5. **Stockage** dans ChromaDB

### Résultat

Les données indexées sont stockées dans `data/chroma_db/` sous forme de base vectorielle locale. Deux collections sont créées :

- `messages_cas1` : Messages individuels (275 documents)
- `message_chunks_cas1` : Chunks de contexte (1 document)

### Stockage des vecteurs

**Base SQLite** (`chroma.sqlite3`) :

- `collections` : Liste des collections créées
- `embeddings` : Références et IDs des documents
- `embedding_metadata` : Métadonnées (timestamp, contact, GPS, direction, etc.)
- `segments` : Liens entre collections et embeddings

**Fichiers binaires** (par segment UUID) :

- `data_level0.bin` : **Vecteurs d'embedding** (float32, 1024 dimensions)
- `header.bin` : Métadonnées du fichier
- `length.bin` : Longueurs des vecteurs
- `link_lists.bin` : Structure HNSW pour recherche ANN rapide

**Recherche** : ChromaDB utilise automatiquement HNSW (Hierarchical Navigable Small World) pour la recherche ANN (Approximate Nearest Neighbors) - complexité O(log n) au lieu de O(n) pour KNN.

### Logs détaillés

Le pipeline affiche des indicateurs de progression et de durée pour chaque phase :

```text
🚀 Démarrage de l'indexation...
📄 Phase 1/5: Parsing du CSV...
   ✓ 250 messages parsés (0.15s)
🧹 Phase 2/5: Débruitage...
   ✓ Flags de bruit ajoutés (0.01s)
🪟 Phase 3/5: Création des chunks de contexte...
   ✓ 82 chunks créés (fenêtre=5, overlap=2) (0.02s)
🧠 Phase 4/5: Encodage vectoriel...
   ✓ 250 embeddings générés (12.34s)
   ✓ 82 embeddings de chunks générés (4.56s)
💾 Phase 5/5: Stockage dans ChromaDB...
   ✓ Stockage terminé (0.89s)
```

### Recherche sémantique interactive

**Lancer la recherche :**
```bash
python src/backend/core/pipeline_example.py --search
```

**Exemple de session :**
```text
🔍 OPSEMIA - Recherche Sémantique Interactive
======================================================================
📚 Collection: messages_cas1 (275 documents)
🧠 Modèle: BAAI/bge-m3
⚙️  Méthode: ANN
📊 Résultats par requête: 10
🚫 Exclusion bruit: Oui

💡 Tapez votre requête (ou 'quit' pour quitter)
======================================================================

🔎 Requête: rendez-vous argent

⏳ Recherche en cours...

✅ 10 résultat(s) trouvé(s):
----------------------------------------------------------------------

1. [Score: 0.842]
   📅 2024-03-15 14:23:12 | 👤 Marc Durand | ↔️  incoming
   💬 On se retrouve demain à 15h pour le transfert. Prends l'argent liquide...
```

**Démonstration avec filtres :**
```bash
python scripts/demo_recherche_filtree.py
```

**Comparer ANN vs KNN :**
```bash
python scripts/comparer_ann_vs_knn.py
```
Ce script compare la performance et les résultats des deux méthodes sur les mêmes requêtes.

## ⚙️ Configuration

Tous les paramètres sont configurables dans `config/settings.py` :

### Modèle d'embedding
```python
ID_MODELE_EMBEDDING = "BAAI/bge-m3"  # Options disponibles (voir section Benchmark)
PERIPHERIQUE_EMBEDDING = "auto"      # "auto" | "cpu" | "cuda"
```

**Modèles supportés :**
- `"BAAI/bge-m3"` - BGE-M3 : Équilibré, 1024 dims, ~2.2 GB
- `"jinaai/jina-embeddings-v3"` - Jina-v3 : Léger et rapide, 1024 dims, ~570 MB
- `"Qwen/Qwen3-Embedding-8B"` - Qwen3-8B : Haute performance, 4096 dims, ~8 GB

### Chunking
```python
TAILLE_FENETRE_CHUNK = 5   # Nombre de messages par chunk
OVERLAP_FENETRE_CHUNK = 2  # Chevauchement entre chunks
```

### Base vectorielle
```python
CHEMIN_BASE_CHROMA = "data/chroma_db"
NOM_COLLECTION_MESSAGES = "messages"
NOM_COLLECTION_CHUNKS = "message_chunks"
```

### Recherche
```python
METHODE_RECHERCHE = "ANN"              # "ANN" (rapide) | "KNN" (exact)
NOMBRE_RESULTATS_RECHERCHE = 10        # Nombre de résultats (top K)
EXCLURE_BRUIT_PAR_DEFAUT = True        # Filtrer automatiquement le spam/pub
SEUIL_DISTANCE_MAX = None              # Distance cosine max (None = pas de seuil)
```

**ANN vs KNN** :
- **ANN** (Approximate Nearest Neighbors) : Utilise l'index HNSW pour une recherche ultra-rapide. Complexité O(log n). Précision ~95-99%. **Recommandé pour la production.**
- **KNN** (K-Nearest Neighbors) : Recherche exhaustive exacte avec calcul manuel des distances cosine. Complexité O(n). 100% précis, idéal pour validation ou petites bases.

**Changement de méthode** : Modifier `METHODE_RECHERCHE` dans `config/settings.py` puis relancer la recherche. Aucune réindexation nécessaire.

## 📊 Benchmark des modèles d'embedding

OPSEMIA intègre un système de benchmark complet pour évaluer et comparer différents modèles d'embedding.

### Lancer le benchmark

```bash
python scripts/benchmark_modeles.py
```

Ce script évalue automatiquement plusieurs modèles sur un dataset de test thématique (enquêtes policières) et calcule :
- **NDCG@5** : Qualité du classement (métrique principale)
- **MRR** : Position du premier résultat pertinent
- **Precision@K / Recall@K** : Pertinence des résultats
- **Temps de chargement et recherche**


## 📁 Structure du projet

```
OPSEMIA/
├── config/
│   └── settings.py              # Configuration centralisée
├── src/
│   ├── backend/
│   │   ├── api/                 # API REST Flask
│   │   │   ├── routes_indexation.py   # Routes chargement CSV
│   │   │   ├── routes_recherche.py    # Routes recherche sémantique
│   │   │   ├── routes_conversations.py # Routes conversations
│   │   │   ├── routes_donnees.py      # Routes accès données
│   │   │   └── routes_config.py       # Routes configuration
│   │   ├── app.py               # Serveur Flask principal
│   │   ├── core/
│   │   │   ├── denoising.py     # Débruitage (flags spam/pub)
│   │   │   ├── chunking.py      # Fenêtre glissante
│   │   │   ├── filters.py       # Filtres de recherche (temps, GPS, type)
│   │   │   ├── search_engine.py # Moteur de recherche sémantique
│   │   │   └── pipeline_example.py  # Pipeline + recherche interactive
│   │   ├── models/
│   │   │   ├── model_manager.py # Gestion singleton encodeur
│   │   │   └── text_encoder.py  # Wrapper SentenceTransformer
│   │   ├── parsers/
│   │   │   └── message_extractor.py  # Parser CSV messages
│   │   └── database/
│   │       ├── vector_db.py     # Wrapper ChromaDB + recherche
│   │       └── indexer.py       # Pipeline d'indexation
│   └── frontend/                # Interface web
│       ├── templates/
│       │   ├── index.html       # Page de recherche
│       │   ├── conversations.html # Page de conversations
│       │   └── gestion.html     # Page de gestion
│       └── static/
│           ├── css/
│           │   └── main.css     # Styles principaux
│           └── js/
│               ├── api.js       # Communication avec backend
│               ├── search.js    # Logique de recherche
│               ├── conversations.js # Gestion des conversations
│               ├── context.js   # Vue contextuelle
│               └── gestion.js   # Gestion et configuration
├── scripts/
│   ├── telecharger_modele_bge.py  # Téléchargement BGE-M3
│   ├── telecharger_modele_jina.py # Téléchargement Jina-v3
│   ├── telecharger_modele_qwen3.py # Téléchargement Qwen3-8B
│   ├── telecharger_modele_solon.py # Téléchargement Solon (à confirmer)
│   ├── benchmark_modeles.py       # Benchmark comparatif des modèles
│   ├── donnees_benchmark.py       # Dataset de test pour benchmark
│   ├── analyser_chromadb.py       # Analyse de la base vectorielle
│   ├── demo_recherche_filtree.py  # Démonstration filtres
│   ├── comparer_ann_vs_knn.py     # Comparaison ANN vs KNN
│   └── tester_api.py              # Tests de l'API REST
├── Docs Projet/
│   ├── API_Documentation.md          # Documentation complète de l'API
│   ├── Guide_Modeles_Benchmark.md    # Guide modèles et benchmark
│   └── Guide_Phase8_Frontend.md      # Guide développement frontend (si existant)
├── Cas/                         # CSV de démonstration
│   ├── Cas1/
│   └── Cas2/
├── data/                        # Généré après indexation
│   └── chroma_db/              # Base vectorielle SQLite
├── requirements.txt
└── README.md
```

## 🔒 Confidentialité

**Aucune donnée n'est transmise à des services tiers.** Tout le traitement est local :

- Modèles d'embedding téléchargés et exécutés localement
- Base vectorielle stockée localement (SQLite)
- Pas d'API externe ni de télémétrie

## 🔍 Analyse de la base vectorielle

Le script `scripts/analyser_chromadb.py` permet d'inspecter le contenu de la base :

```bash
python scripts/analyser_chromadb.py
```

**Sortie typique** :

```text
=== ANALYSE CHROMADB ===
Collections trouvées: 2
- messages_cas1: 275 documents
- message_chunks_cas1: 1 document

=== METADONNEES (exemple) ===
ID: msg_0
Timestamp: 2024-01-15 14:30:22
Contact: +33123456789
Direction: incoming
GPS: 48.8566, 2.3522
```

## 🔍 Utilisation avancée

### Recherche programmatique

```python
from config.settings import obtenir_parametres
from src.backend.core.search_engine import MoteurRecherche
from src.backend.core.filters import creer_filtre_temporel
from src.backend.database.vector_db import BaseVectorielle

# Initialisation
parametres = obtenir_parametres()
db = BaseVectorielle(parametres.CHEMIN_BASE_CHROMA)
moteur = MoteurRecherche(db, parametres)

# Recherche simple
resultats = moteur.rechercher(
    requete="rendez-vous suspect",
    nom_collection="messages_cas1",
    nombre_resultats=5
)

# Recherche avec filtres
filtre = creer_filtre_temporel("2024-03-01", "2024-03-31")
resultats = moteur.rechercher(
    requete="transfert argent",
    nom_collection="messages_cas1",
    filtres=filtre,
    exclure_bruit=True
)

# Afficher
for res in resultats:
    print(f"[{res['score']:.3f}] {res['document'][:100]}")
```

### Filtres disponibles

- **Temporel** : `creer_filtre_temporel("2024-01-01", "2024-12-31")`
- **Géographique** : `creer_filtre_geographique(lat, lon, rayon_km)`
- **Exclusion bruit** : `creer_filtre_exclusion_bruit(exclure=True)`
- **Combinaison** : `combiner_filtres(filtre1, filtre2)`

### Scores de pertinence

- **> 0.8** : Très pertinent
- **0.6 - 0.8** : Pertinent  
- **< 0.6** : Peu pertinent

## 🖥️ Interface Web

OPSEMIA dispose d'une interface web moderne pour faciliter l'utilisation par les analystes de la police scientifique.

### Démarrage

```bash
python src/backend/app.py
```

Ouvrez votre navigateur à `http://127.0.0.1:5000`

### Pages disponibles

#### 🔍 Page de Recherche (`/`)
- Barre de recherche sémantique en langage naturel
- Sélection de la collection à interroger
- Filtres avancés (dates, direction, exclusion du bruit)
- Affichage des résultats avec score de pertinence
- **Vue contextuelle** : Cliquez sur un résultat pour voir la conversation complète avec messages avant/après
- **Navigation vers conversations** : Bouton pour voir le message dans son contexte conversationnel complet

#### 💬 Page de Conversations (`/conversations`)
- **Vue complète des conversations** : Interface type messagerie avec liste des conversations et messages
- **Filtrage et recherche** : Recherche par nom, numéro ou contenu dans les conversations
- **Bulles de messages** : Affichage chronologique avec distinction messages reçus/envoyés
- **Métadonnées** : GPS, application, flags spam accessibles via badges discrets
- **Navigation contextuelle** : Intégration avec la recherche sémantique - cliquez sur "Voir dans les conversations" depuis un résultat de recherche pour accéder directement au message dans sa conversation complète
- **Recherche intra-conversation** : Recherche par mots-clés dans une conversation spécifique

#### ⚙️ Page de Gestion (`/gestion`)
- **Charger des CSV** : Indexer un fichier ou un dossier complet
- **Statistiques** : Nombre de documents, collections, modèle utilisé
- **Configuration** : Changer méthode de recherche (ANN/KNN), nombre de résultats, filtres par défaut
- **Guide rapide** : Instructions pour bien utiliser l'outil

### Fonctionnalités clés

**Recherche sémantique** : Utilisez des requêtes en langage naturel (ex: "rendez-vous argent suspect", "transfert drogue")

**Vue contextuelle** : En cliquant sur un résultat, un panneau latéral s'ouvre affichant :
- Le message recherché (surligné)
- 10 messages avant (contexte précédent)
- 10 messages après (contexte suivant)
- Métadonnées complètes (date, contact, direction, GPS)

**Filtres avancés** :
- Plage temporelle (dates de début et fin)
- Direction (reçus/envoyés)
- Exclusion automatique du spam/pub

**Design professionnel** : Interface moderne adaptée au contexte police scientifique, responsive, avec thème bleu foncé.

## 🌐 API REST

OPSEMIA expose une API REST complète pour intégration avec un frontend web ou autres applications.

### Démarrage du serveur

```bash
python src/backend/app.py
```

Le serveur démarre sur `http://127.0.0.1:5000`.

### Endpoints principaux

#### Recherche
- `POST /api/search` - Recherche sémantique avec filtres
- `GET /api/message/<id>` - Obtenir un message spécifique
- `GET /api/context/<id>` - Obtenir le contexte d'un message

#### Conversations
- `GET /api/conversations` - Lister toutes les conversations (groupées par contact)
- `GET /api/conversation/<contact>` - Obtenir tous les messages d'une conversation
- `POST /api/conversation/<contact>/search` - Rechercher dans une conversation spécifique

#### Indexation
- `POST /api/load` - Charger et indexer un fichier CSV
- `POST /api/load_dossier` - Charger tous les CSV d'un dossier

#### Configuration
- `GET /api/config` - Obtenir la configuration actuelle
- `POST /api/config` - Modifier la configuration
- `GET /api/stats` - Statistiques d'indexation
- `GET /api/collections` - Lister les collections
- `GET /api/health` - Vérifier la santé de l'API

### Exemple de requête

```bash
curl -X POST http://127.0.0.1:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "requete": "rendez-vous argent",
    "nom_collection": "messages_cas1",
    "nombre_resultats": 5,
    "exclure_bruit": true,
    "filtres": {
      "timestamp_debut": "2024-01-01",
      "timestamp_fin": "2024-12-31"
    }
  }'
```

### Tests de l'API

```bash
# Terminal 1 : Démarrer le serveur
python src/backend/app.py

# Terminal 2 : Lancer les tests
python scripts/tester_api.py
```

**Documentation complète** : Voir `Docs Projet/API_Documentation.md`


## 📊 Architecture technique

**Pipeline complet :**
```
CSV → Parser → Débruitage → Chunking → BGE-M3 → ChromaDB (HNSW)
```

**Performance (sur 275 messages) :**
- **Indexation** : ~15-20s
- **Recherche ANN (HNSW)** : < 0.1s (95-99% précision)
- **Recherche KNN (exact)** : < 0.5s (100% précision)

**Implémentation KNN** : Récupère tous les embeddings, calcule manuellement les distances cosine avec NumPy, trie et retourne les top K. Garantit une précision exacte contrairement à l'approximation HNSW.

**Fichiers clés :**
- `src/backend/core/search_engine.py` : Moteur de recherche
- `src/backend/core/filters.py` : Filtres temporels/GPS/bruit
- `src/backend/database/vector_db.py` : Interface ChromaDB
- `src/backend/app.py` : Serveur API Flask
- `config/settings.py` : Configuration (ANN/KNN, K, filtres)