# Documentation API OPSEMIA

## Vue d'ensemble

L'API REST OPSEMIA expose toutes les fonctionnalités du moteur de recherche sémantique via HTTP. Elle est construite avec Flask et supporte CORS pour une intégration facile avec un frontend web.

## Démarrage du serveur

```bash
python src/backend/app.py
```

Le serveur démarre sur `http://127.0.0.1:5000` par défaut.

## Architecture

L'API est organisée en 4 modules de routes (blueprints) :

1. **Indexation** (`routes_indexation.py`) - Chargement et indexation de CSV
2. **Recherche** (`routes_recherche.py`) - Recherche sémantique avec filtres
3. **Données** (`routes_donnees.py`) - Accès aux messages et contexte
4. **Configuration** (`routes_config.py`) - Configuration et statistiques

## Routes disponibles

### 🏠 Route racine

#### `GET /`
Retourne la documentation de l'API et liste tous les endpoints disponibles.

**Réponse:**
```json
{
  "nom": "OPSEMIA API",
  "description": "API REST pour le moteur de recherche sémantique",
  "version": "1.0.0",
  "endpoints": { ... }
}
```

---

### 📥 Routes d'indexation

#### `POST /api/load`
Charge et indexe un fichier CSV de messages dans ChromaDB.

**Body JSON:**
```json
{
  "chemin_csv": "/chemin/vers/fichier.csv",  // Requis
  "nom_cas": "cas1",                          // Optionnel
  "reinitialiser": false                      // Optionnel (défaut: false)
}
```

**Réponse succès:**
```json
{
  "succes": true,
  "statistiques": {
    "fichier_csv": "/chemin/vers/fichier.csv",
    "messages_indexe": 275,
    "chunks_indexes": 55,
    "duree_totale_sec": 18.5
  },
  "message": "Indexation terminée: 275 messages, 55 chunks"
}
```

#### `POST /api/load_dossier`
Charge et indexe tous les CSV d'un dossier (sms.csv, email.csv, etc.).

**Body JSON:**
```json
{
  "chemin_dossier": "/chemin/vers/dossier/",  // Requis
  "nom_cas": "cas1",                           // Optionnel
  "reinitialiser": false                       // Optionnel
}
```

**Réponse succès:**
```json
{
  "succes": true,
  "resultats": {
    "sms": {
      "succes": true,
      "statistiques": { ... }
    },
    "email": {
      "succes": true,
      "statistiques": { ... }
    }
  },
  "message": "2 fichiers traités"
}
```

---

### 🔍 Routes de recherche

#### `POST /api/search`
Recherche sémantique dans une collection avec filtres optionnels.

**Body JSON:**
```json
{
  "requete": "rendez-vous argent",        // Requis
  "nom_collection": "messages_cas1",      // Requis
  "nombre_resultats": 10,                 // Optionnel
  "exclure_bruit": true,                  // Optionnel
  "filtres": {                            // Optionnel
    "timestamp_debut": "2024-01-01",
    "timestamp_fin": "2024-12-31",
    "direction": "incoming",              // "incoming" | "outgoing"
    "gps_lat": 48.8566,
    "gps_lon": 2.3522,
    "rayon_km": 10
  }
}
```

**Réponse succès:**
```json
{
  "succes": true,
  "nombre_resultats": 10,
  "resultats": [
    {
      "id": "msg_123",
      "score": 0.842,
      "distance": 0.158,
      "document": "On se retrouve demain à 15h pour le transfert...",
      "metadata": {
        "timestamp": "2024-03-15T14:23:12",
        "direction": "incoming",
        "contact_name": "Marc Durand",
        "from": "+33123456789",
        "gps_lat": 48.8566,
        "gps_lon": 2.3522,
        "is_noise": false,
        "app": "WhatsApp"
      }
    }
  ]
}
```

---

### 📊 Routes d'accès aux données

#### `GET /api/message/<message_id>`
Obtient un message spécifique par son ID.

**Query params:**
- `collection` (optionnel) - Nom de la collection (défaut: "messages")

**Exemple:**
```
GET /api/message/SM0447?collection=messages_cas1
```

**Réponse succès:**
```json
{
  "succes": true,
  "message": {
    "id": "SM0447",
    "document": "Donne moi l'heure du rendez vous pour récuperer la drogue",
    "metadata": { ... }
  }
}
```

#### `GET /api/context/<message_id>`
Obtient un message avec son contexte (messages adjacents chronologiquement).

**Query params:**
- `collection` (optionnel) - Nom de la collection
- `fenetre_avant` (optionnel) - Nombre de messages avant (défaut: 5)
- `fenetre_apres` (optionnel) - Nombre de messages après (défaut: 5)

**Exemple:**
```
GET /api/context/SM0447?collection=messages_cas1&fenetre_avant=3&fenetre_apres=3
```

**Réponse succès:**
```json
{
  "succes": true,
  "contexte": {
    "message_central": {
      "id": "SM0447",
      "document": "...",
      "metadata": { ... },
      "est_cible": true
    },
    "messages_avant": [ ... ],
    "messages_apres": [ ... ],
    "total_contexte": 7
  }
}
```

---

### ⚙️ Routes de configuration

#### `GET /api/config`
Obtient la configuration actuelle du système.

**Réponse succès:**
```json
{
  "succes": true,
  "configuration": {
    "encodage": {
      "modele": "BAAI/bge-m3",
      "peripherique": "auto"
    },
    "chunking": {
      "taille_fenetre": 1,
      "overlap": 1
    },
    "base_vectorielle": {
      "chemin": "data/chroma_db",
      "collection_messages": "messages",
      "collection_chunks": "message_chunks"
    },
    "recherche": {
      "methode": "KNN",
      "nombre_resultats": 10,
      "exclure_bruit_par_defaut": false,
      "seuil_distance_max": null
    }
  }
}
```

#### `POST /api/config`
Modifie la configuration du système (modifications runtime uniquement).

**Body JSON:**
```json
{
  "methode_recherche": "ANN",           // "ANN" | "KNN"
  "nombre_resultats": 15,
  "exclure_bruit_par_defaut": true
}
```

**Réponse succès:**
```json
{
  "succes": true,
  "message": "3 paramètre(s) modifié(s): methode_recherche, nombre_resultats, exclure_bruit_par_defaut",
  "note": "⚠️ Modifications runtime uniquement. Pour persistance, modifier config/settings.py"
}
```

#### `GET /api/stats`
Obtient les statistiques d'indexation de toutes les collections.

**Réponse succès:**
```json
{
  "succes": true,
  "statistiques": {
    "nombre_collections": 2,
    "total_documents": 330,
    "collections": [
      {
        "nom": "messages_cas1",
        "nombre_documents": 275,
        "metadata": { ... }
      },
      {
        "nom": "message_chunks_cas1",
        "nombre_documents": 55,
        "metadata": { ... }
      }
    ],
    "modele_embedding": "BAAI/bge-m3",
    "methode_recherche": "KNN"
  }
}
```

#### `GET /api/collections`
Liste toutes les collections disponibles dans ChromaDB.

**Réponse succès:**
```json
{
  "succes": true,
  "nombre_collections": 2,
  "collections": [
    {
      "nom": "messages_cas1",
      "nombre_documents": 275,
      "metadata": { ... }
    }
  ]
}
```

#### `GET /api/health`
Vérifie que l'API fonctionne correctement.

**Réponse succès:**
```json
{
  "succes": true,
  "statut": "OK",
  "base_vectorielle": "connectée",
  "nombre_collections": 2
}
```

---

## Gestion des erreurs

Toutes les routes retournent un format d'erreur cohérent :

```json
{
  "succes": false,
  "erreur": "Message d'erreur détaillé"
}
```

### Codes HTTP

- `200` - Succès
- `400` - Requête invalide (paramètres manquants, format incorrect)
- `404` - Ressource non trouvée (collection, message, fichier)
- `500` - Erreur serveur interne

---

## Utilisation avec le frontend (Phase 8)

### Structure recommandée pour le frontend

```javascript
// Classe service pour l'API
class OpsemiaAPI {
  constructor(baseURL = 'http://127.0.0.1:5000') {
    this.baseURL = baseURL;
  }

  async rechercher(requete, collection, filtres = {}) {
    const response = await fetch(`${this.baseURL}/api/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        requete,
        nom_collection: collection,
        ...filtres
      })
    });
    return await response.json();
  }

  async obtenirContexte(messageId, collection) {
    const response = await fetch(
      `${this.baseURL}/api/context/${messageId}?collection=${collection}`
    );
    return await response.json();
  }

  // ... autres méthodes
}

// Exemple d'utilisation
const api = new OpsemiaAPI();
const resultats = await api.rechercher("rendez-vous", "messages_cas1");
const contexte = await api.obtenirContexte("SM0447", "messages_cas1");
```

### Modifications futures de l'API

Si vous modifiez les fonctionnalités backend, voici comment adapter l'API :

1. **Nouveau type de données (ex: emails)** :
   - Créer un nouveau parser dans `src/backend/parsers/email_extractor.py`
   - Étendre `indexer_csv_messages` pour supporter les emails
   - Pas de changement API nécessaire (même endpoint `/api/load`)

2. **Nouveau filtre (ex: par contact)** :
   - Ajouter fonction dans `src/backend/core/filters.py`
   - Étendre `_construire_filtres()` dans `routes_recherche.py`
   - Le frontend peut immédiatement utiliser ce filtre via `/api/search`

3. **Nouveau modèle d'embedding** :
   - Modifier `config/settings.py`
   - Aucune modification API nécessaire (transparent)

4. **Nouvelles métadonnées** :
   - Étendre `_extraire_metadonnees_message()` dans `indexer.py`
   - Les métadonnées apparaissent automatiquement dans les résultats

---

## Tests

Pour tester l'API complète :

```bash
# Terminal 1 : Démarrer le serveur
python src/backend/app.py

# Terminal 2 : Lancer les tests
python scripts/tester_api.py
```

Le script de test vérifie tous les endpoints et affiche les résultats.

---

## Sécurité et production

⚠️ **Cette API est conçue pour un usage local (prototype/démo).**

Pour une utilisation en production, ajoutez :
- Authentification (JWT, OAuth)
- Rate limiting
- Validation renforcée des entrées
- HTTPS
- Configuration de CORS restrictive
- Logging structuré
- Monitoring

