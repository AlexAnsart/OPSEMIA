# 🚀 Démarrage Rapide - Indexation avec Progression SSE

## ✅ Corrections apportées

### 🐛 Problème identifié
**Erreur 404** sur la route SSE `/load/progress/<task_id>`

**Cause**: L'URL SSE côté client était incorrecte
- ❌ Ancien: `http://127.0.0.1:5000/load/progress/...` 
- ✅ Nouveau: `http://127.0.0.1:5000/api/load/progress/...`

Le blueprint Flask a le préfixe `/api`, mais le code client utilisait `api.baseURL` (qui est `http://127.0.0.1:5000`) sans ajouter `/api` pour la route SSE.

### 🔧 Modifications
1. **`src/frontend/static/js/gestion.js`**: Ajout de `/api` dans l'URL SSE
2. **`src/backend/api/routes_indexation.py`**: Ajout de logs détaillés pour déboguer
3. **`src/backend/app.py`**: Mise à jour de la documentation API

---

## 🏃 Comment tester

### 1️⃣ **Redémarrer le serveur Flask** ⚠️ IMPORTANT

Les nouvelles routes ne seront disponibles qu'après redémarrage :

```bash
# Si le serveur tourne, arrêtez-le (Ctrl+C)
# Puis redémarrez :
python src/backend/app.py
```

Vous devriez voir :
```
======================================================================
OPSEMIA - Demarrage du serveur
======================================================================
Interface web: http://127.0.0.1:5000
Gestion: http://127.0.0.1:5000/gestion
API JSON: http://127.0.0.1:5000/api
Mode debug: Active
======================================================================
```

### 2️⃣ **Vérifier que les routes sont enregistrées**

Ouvrez dans votre navigateur : http://127.0.0.1:5000/api

Vous devriez voir dans la section `"indexation"`:
```json
{
  "indexation": [
    "POST /api/load - Charger un fichier CSV (retourne task_id)",
    "GET /api/load/progress/<task_id> - Stream SSE pour la progression",
    "GET /api/load/status/<task_id> - Statut d'une tâche (polling)",
    "POST /api/load_dossier - Charger tous les CSV d'un dossier"
  ]
}
```

### 3️⃣ **Tester l'indexation avec progression**

1. Ouvrez : http://127.0.0.1:5000/gestion

2. Dans "Fichier CSV", entrez : `Cas/Cas1/sms.csv` (petit fichier pour commencer)

3. Cliquez sur **📤 Charger et indexer**

4. **Observez** :
   - Une barre de progression devrait apparaître immédiatement
   - Elle devrait progresser de 0% à 100% en plusieurs étapes
   - Les étapes : `parsing` → `debruitage` → `chunking` → `encodage` → `stockage`

### 4️⃣ **Vérifier les logs**

#### 🖥️ **Logs serveur (terminal Python)**

Vous devriez voir :
```
INFO:routes_indexation:📥 POST /api/load - Requête d'indexation reçue
   Données reçues: {'chemin_csv': 'Cas/Cas1/sms.csv', ...}
INFO:routes_indexation:🚀 Début indexation tâche a1b2c3d4: Cas/Cas1/sms.csv
INFO:routes_indexation:📡 GET /api/load/progress/a1b2c3d4 - Client SSE connecté
   Tâches actives: ['a1b2c3d4-...']
📡 Client connecté pour SSE task a1b2c3d4

🚀 Démarrage de l'indexation de Cas/Cas1/sms.csv
   Collections: messages_None / chunks_None

📄 Phase 1/5: Parsing du CSV...
📋 Format CSV détecté: cas1
   ✓ 277 messages parsés (0.12s)

🧹 Phase 2/5: Débruitage...
   ✓ Flags de bruit ajoutés (0.05s)

🪟 Phase 3/5: Création des chunks de contexte...
   ✓ 277 chunks créés (fenêtre=1, overlap=1) (0.01s)

🧠 Phase 4/5: Encodage vectoriel...
   Modèle: BAAI/bge-m3 (dim=1024)
   → Encodage des messages individuels...
     ✓ 277 embeddings générés (2.34s)
   → Encodage des chunks de contexte...
     ✓ 277 embeddings de chunks générés (2.35s)

💾 Phase 5/5: Stockage dans ChromaDB...
   → Stockage des messages...
   → Stockage des chunks...
   ✓ Stockage terminé (0.18s)

============================================================
✅ INDEXATION TERMINÉE
============================================================
📊 Messages indexés : 277
📊 Chunks indexés   : 277
⏱️  Durée totale    : 4.95s
============================================================
INFO:routes_indexation:✅ Indexation terminée tâche a1b2c3d4
✅ SSE terminé pour task a1b2c3d4
```

#### 🌐 **Logs navigateur (Console F12)**

Vous devriez voir :
```javascript
📡 Tâche d'indexation démarrée: a1b2c3d4-...
📡 Tentative connexion SSE: http://127.0.0.1:5000/api/load/progress/a1b2c3d4-...
📡 Connexion SSE établie pour task a1b2c3d4-...

📊 Progression: {progression: 5, etape: "parsing", message: "Lecture du fichier CSV..."}
📊 Progression: {progression: 20, etape: "parsing", message: "277 messages parsés"}
📊 Progression: {progression: 30, etape: "debruitage", message: "Débruitage terminé"}
📊 Progression: {progression: 40, etape: "chunking", message: "277 chunks créés"}
📊 Progression: {progression: 45, etape: "encodage", message: "Encodage de 277 messages..."}
📊 Progression: {progression: 65, etape: "encodage", message: "Messages encodés (2.3s)"}
📊 Progression: {progression: 67, etape: "encodage", message: "Encodage de 277 chunks..."}
📊 Progression: {progression: 80, etape: "encodage", message: "Chunks encodés (2.4s)"}
📊 Progression: {progression: 86, etape: "stockage", message: "Stockage de 277 messages..."}
📊 Progression: {progression: 92, etape: "stockage", message: "Messages stockés"}
📊 Progression: {progression: 94, etape: "stockage", message: "Stockage de 277 chunks..."}
📊 Progression: {progression: 100, etape: "stockage", message: "Indexation terminée avec succès!"}

✅ Indexation terminée: {etat: "termine", statistiques: {...}}
```

---

## 🧪 Tests avec des fichiers plus gros

Une fois que `Cas1/sms.csv` fonctionne, testez avec le gros fichier :

```
Fichier: Cas/Cas3/sms.csv
```

Ce fichier a **2945 messages** et prendra beaucoup plus de temps (30-60s sur CPU, 10-20s sur GPU).

**Avantage de SSE** : Vous verrez la progression en temps réel au lieu d'avoir un timeout !

---

## ❌ Dépannage

### Erreur 404 persiste
```
Failed to load resource: the server responded with a status of 404 (NOT FOUND)
```

**Solutions** :
1. ✅ **Vérifiez que vous avez bien redémarré le serveur Flask**
2. ✅ Ouvrez http://127.0.0.1:5000/api et vérifiez que les routes SSE sont listées
3. ✅ Dans la console navigateur, cherchez : `📡 Tentative connexion SSE: ...` et vérifiez que l'URL est correcte
4. ✅ Si l'URL affichée ne contient pas `/api`, rafraîchissez la page (Ctrl+F5)

### Erreur "Erreur de connexion SSE"
```
❌ Erreur connexion SSE: Event {...}
```

**Solutions** :
1. Vérifiez que le serveur Flask tourne
2. Vérifiez les logs serveur pour voir si la route `/api/load` a été appelée
3. Testez manuellement avec curl :
```bash
# 1. Démarrer indexation
curl -X POST http://127.0.0.1:5000/api/load \
  -H "Content-Type: application/json" \
  -d '{"chemin_csv": "Cas/Cas1/sms.csv"}'

# 2. Copier le task_id retourné, puis :
curl -N http://127.0.0.1:5000/api/load/progress/<task_id>
```

### La barre de progression ne bouge pas
```
Barre reste bloquée à 0%
```

**Solutions** :
1. Vérifiez les logs serveur : l'indexation a-t-elle démarré ?
2. Vérifiez les logs navigateur : recevez-vous des événements SSE ?
3. Vérifiez que le callback de progression est bien appelé :
   - Logs serveur : cherchez les appels à `_emit_progress`
   - Si aucun log, le callback n'est pas passé correctement

### Timeout au bout de 30 secondes
```
La connexion se coupe après ~30s
```

**Solutions** :
1. C'est probablement un timeout de proxy/reverse proxy
2. Si vous utilisez nginx/Apache, augmentez les timeouts SSE
3. Pour Flask en dev, pas de problème normalement

---

## 🎯 Points de validation

Checklist pour confirmer que tout fonctionne :

- [ ] Serveur Flask redémarré avec succès
- [ ] Routes SSE visibles dans http://127.0.0.1:5000/api
- [ ] Console navigateur affiche `📡 Tentative connexion SSE: http://127.0.0.1:5000/api/load/progress/...`
- [ ] Barre de progression s'affiche
- [ ] Barre de progression avance de 0% à 100%
- [ ] Les 5 étapes sont visibles (parsing, debruitage, chunking, encodage, stockage)
- [ ] Message de succès final s'affiche
- [ ] Statistiques affichées (messages indexés, durée)
- [ ] Logs serveur confirment la fin de l'indexation

---

## 📊 Performance attendue

### Cas1/sms.csv (277 messages)
- **CPU** : ~5 secondes
- **GPU** : ~2-3 secondes
- **Étape la plus longue** : Encodage (~80% du temps)

### Cas3/sms.csv (2945 messages)
- **CPU** : ~40-60 secondes
- **GPU** : ~10-20 secondes
- **Étape la plus longue** : Encodage (~80% du temps)

---

## 🎉 Prochaines étapes

Une fois que l'indexation avec progression fonctionne :

1. **Tester la recherche** : Utilisez l'interface de recherche pour interroger les données indexées
2. **Explorer les conversations** : Visitez la page `/conversations`
3. **Ajuster la config** : Modifiez les paramètres d'encodage/chunking dans `/gestion`
4. **Indexer plus de données** : Essayez `load_dossier` pour charger tous les CSV d'un dossier

---

**Besoin d'aide ?** Consultez les logs détaillés dans le terminal Flask et la console navigateur (F12).

