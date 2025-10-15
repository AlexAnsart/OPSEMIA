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

```bash
python scripts/telecharger_modele_bge.py
```

Cette étape télécharge le modèle BGE-M3 (~2.2 GB) et le met en cache. Elle peut prendre plusieurs minutes selon votre connexion.

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

Les données indexées sont stockées dans `data/chroma_db/` sous forme de base SQLite locale. Deux collections sont créées :
- `messages_cas1` : Messages individuels
- `message_chunks_cas1` : Chunks de contexte

### Logs détaillés

Le pipeline affiche des indicateurs de progression et de durée pour chaque phase :

```
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

## ⚙️ Configuration

Tous les paramètres sont configurables dans `config/settings.py` :

### Modèle d'embedding
```python
ID_MODELE_EMBEDDING = "BAAI/bge-m3"  # ou "nomic-ai/nomic-embed-text-v2-moe"
PERIPHERIQUE_EMBEDDING = "auto"      # "auto" | "cpu" | "cuda"
```

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

## 📁 Structure du projet

```
OPSEMIA/
├── config/
│   └── settings.py              # Configuration centralisée
├── src/
│   └── backend/
│       ├── core/
│       │   ├── denoising.py     # Débruitage (flags spam/pub)
│       │   ├── chunking.py      # Fenêtre glissante
│       │   └── pipeline_example.py  # Test du pipeline
│       ├── models/
│       │   ├── model_manager.py # Gestion singleton encodeur
│       │   └── text_encoder.py  # Wrapper SentenceTransformer
│       ├── parsers/
│       │   └── message_extractor.py  # Parser CSV messages
│       └── database/
│           ├── vector_db.py     # Wrapper ChromaDB
│           └── indexer.py       # Pipeline d'indexation
├── scripts/
│   └── telecharger_modele_bge.py  # Téléchargement modèle
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

## 🛠️ Développement en cours

Ce projet est un prototype de hackathon. Phases à venir :
- Moteur de recherche avec filtres (temporel, géospatial, type)
- Support images (BLIP + BGE-M3)
- Interface web Flask
- Visualisations (timeline, carte, graphe de relations)
- Fine-tuning pour jargon criminel français

