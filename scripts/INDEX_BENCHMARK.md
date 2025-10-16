# Index - Système de Benchmark OPSEMIA

Ce fichier référence tous les scripts et documentations du système de benchmark.

## 📚 Documentation

### 🚀 Démarrage Rapide
**[GUIDE_DEMARRAGE_BENCHMARK.md](GUIDE_DEMARRAGE_BENCHMARK.md)**
- Checklist avant de commencer
- Installation et configuration
- Exécution en 3 étapes
- Résolution de problèmes courants
- **👉 Commencez par ici si c'est votre première fois**

### 📖 Documentation Complète
**[README_BENCHMARK.md](README_BENCHMARK.md)**
- Description détaillée de tous les fichiers
- Explications des métriques
- Configuration avancée
- Exemples de résultats
- Références techniques

---

## 🔧 Scripts Principaux

### ⭐ Script Principal
**[benchmark_complet_opsemia.py](benchmark_complet_opsemia.py)**
- Exécute le benchmark complet (durées + qualité)
- Teste 4 modèles sur 100 requêtes
- Génère le rapport markdown final
- **Durée:** 40-70 minutes

**Usage:**
```bash
python benchmark_complet_opsemia.py
```

---

## 📊 Dataset et Configuration

### Dataset de Benchmark
**[donnees_benchmark_opsemia.py](donnees_benchmark_opsemia.py)**
- 90 requêtes pour messages (8 catégories thématiques)
- 10 requêtes pour images
- Résultats attendus (ground truth)
- **⚠️ Compléter les requêtes images avant l'exécution**

### Configuration
Les modèles testés sont définis dans `benchmark_complet_opsemia.py`:
- Jina-v3 (137M params, 1024 dims)
- Solon-large (335M params, 1024 dims)
- BGE-M3 (568M params, 1024 dims)
- Qwen3-8B (8000M params, 8192 dims, via API)

---

## 🛠️ Utilitaires

### Validation Pré-Benchmark
**[valider_benchmark.py](valider_benchmark.py)**
- Vérifie tous les prérequis
- Teste les dépendances
- Valide la configuration
- Affiche les avertissements

**Usage:**
```bash
python valider_benchmark.py
```

**Quand l'utiliser:** Avant chaque exécution du benchmark

---

### Visualisation du Dataset
**[afficher_dataset_benchmark.py](afficher_dataset_benchmark.py)**
- Affiche les statistiques du dataset
- Montre des exemples de requêtes
- Analyse la répartition par difficulté
- Visualise la couverture du corpus

**Usage:**
```bash
python afficher_dataset_benchmark.py
```

**Quand l'utiliser:** Pour comprendre le dataset sans exécuter le benchmark

---

### Test Rapide d'un Modèle
**[test_rapide_modele.py](test_rapide_modele.py)**
- Teste un seul modèle rapidement
- Utile pour le développement
- Vérifie que le modèle se charge
- Teste encodage et recherche

**Usage:**
```bash
python test_rapide_modele.py jina    # Tester Jina-v3
python test_rapide_modele.py bge     # Tester BGE-M3
python test_rapide_modele.py solon   # Tester Solon-large
```

**Quand l'utiliser:** Pour déboguer un modèle spécifique

---

## 📥 Scripts de Téléchargement

Ces scripts téléchargent les modèles en avance pour éviter les téléchargements pendant le benchmark:

- **[telecharger_modele_jina.py](telecharger_modele_jina.py)** - Jina-v3 (~2.5 GB)
- **[telecharger_modele_bge.py](telecharger_modele_bge.py)** - BGE-M3 (~2.2 GB)
- **[telecharger_modele_solon.py](telecharger_modele_solon.py)** - Solon-large (~1.3 GB)
- **[telecharger_modele_vision.py](telecharger_modele_vision.py)** - BLIP + Traduction (~2 GB)

**Usage:**
```bash
python telecharger_modele_jina.py
python telecharger_modele_bge.py
python telecharger_modele_solon.py
python telecharger_modele_vision.py
```

---

## 📄 Fichiers Générés

### Rapport de Benchmark
**`Docs Projet/BENCHMARK_RESULTATS_YYYYMMDD_HHMMSS.md`**

Généré automatiquement après exécution du benchmark complet.

Contient:
- ✅ Tableau comparatif des durées d'encodage
- ✅ Tableau comparatif de la qualité (métriques)
- ✅ Résultats par type (messages vs images)
- ✅ Analyse du compromis vitesse/qualité
- ✅ Recommandations selon les besoins

### Collections Temporaires
**`data/benchmark_temp/`**

Collections ChromaDB créées pendant le benchmark, automatiquement supprimées après.

---

## 🔄 Workflow Recommandé

### Première Utilisation

1. **Lire la documentation**
   ```bash
   cat GUIDE_DEMARRAGE_BENCHMARK.md
   ```

2. **Valider le système**
   ```bash
   python valider_benchmark.py
   ```

3. **Compléter les requêtes images**
   - Éditer `donnees_benchmark_opsemia.py`
   - Remplacer `[REQUETE_A_COMPLETER]` (10 requêtes)

4. **Télécharger les modèles** (optionnel mais recommandé)
   ```bash
   python telecharger_modele_jina.py
   python telecharger_modele_bge.py
   python telecharger_modele_solon.py
   python telecharger_modele_vision.py
   ```

5. **Visualiser le dataset** (optionnel)
   ```bash
   python afficher_dataset_benchmark.py
   ```

6. **Lancer le benchmark**
   ```bash
   python benchmark_complet_opsemia.py
   ```

7. **Consulter les résultats**
   ```bash
   cat ../Docs\ Projet/BENCHMARK_RESULTATS_*.md
   ```

### Développement/Débogage

1. **Tester un modèle rapidement**
   ```bash
   python test_rapide_modele.py jina
   ```

2. **Modifier la configuration**
   - Éditer `benchmark_complet_opsemia.py`
   - Modifier `MODELES_TEXTE` (ajouter/retirer modèles)
   - Modifier chemins de fichiers

3. **Ajouter des requêtes**
   - Éditer `donnees_benchmark_opsemia.py`
   - Ajouter à `REQUETES_MESSAGES` ou `REQUETES_IMAGES`

4. **Relancer la validation**
   ```bash
   python valider_benchmark.py
   ```

---

## 📊 Fichiers de Données

### Dataset Source
- **Cas/Cas4/sms.csv** - 560 messages Breaking Bad
- **Cas/Cas4/images.csv** - Métadonnées de 28 images
- **Cas/Cas4/Images/** - Dossier des images

### Dataset Utilisé
- **Messages:** 560 messages complets
- **Images:** 10 images sélectionnées
- **Requêtes:** 100 (90 messages + 10 images)

---

## 🎯 Résultats Attendus

### Durées d'Encodage Typiques

| Modèle | 1000 Messages | Est. 1M Messages |
|--------|---------------|------------------|
| Jina-v3 | ~12s | ~3.5h |
| Solon-large | ~15s | ~4.2h |
| BGE-M3 | ~18s | ~5h |
| Qwen3-8B (API) | ~250s | ~69h |

| Images | 10 Images | 1000 Images |
|--------|-----------|-------------|
| BLIP | ~20s | ~33h |

### Métriques de Qualité Typiques

| Modèle | P@5 | R@5 | MRR |
|--------|-----|-----|-----|
| Meilleur | 0.85-0.90 | 0.80-0.85 | 0.75-0.80 |
| Moyen | 0.75-0.85 | 0.70-0.80 | 0.65-0.75 |

---

## 🆘 Aide et Support

### En cas de problème

1. **Vérifier les prérequis**
   ```bash
   python valider_benchmark.py
   ```

2. **Consulter la documentation**
   - [GUIDE_DEMARRAGE_BENCHMARK.md](GUIDE_DEMARRAGE_BENCHMARK.md) - Guide rapide
   - [README_BENCHMARK.md](README_BENCHMARK.md) - Documentation complète

3. **Tester un modèle isolément**
   ```bash
   python test_rapide_modele.py [modele]
   ```

4. **Vérifier les logs**
   - Les erreurs s'affichent dans la console
   - Rechercher les lignes commençant par `❌`

### Problèmes Courants

| Problème | Solution |
|----------|----------|
| DEEPINFRA_TOKEN non configuré | `export DEEPINFRA_TOKEN="clé"` |
| Out of memory | Réduire batch size ou utiliser CPU |
| Modèle ne charge pas | Télécharger avec script dédié |
| Requêtes images ignorées | Compléter dans donnees_benchmark_opsemia.py |

---

## 📈 Évolution Future

### Fonctionnalités Prévues
- [ ] Support de modèles supplémentaires
- [ ] Export des résultats en JSON/CSV
- [ ] Graphiques de comparaison
- [ ] Benchmark incrémental (sauvegarder résultats)

### Contributions
Pour ajouter un modèle ou améliorer le système:
1. Modifier `benchmark_complet_opsemia.py`
2. Ajouter aux `MODELES_TEXTE`
3. Créer script de téléchargement si nécessaire
4. Tester avec `test_rapide_modele.py`

---

## 📝 Notes de Version

**Version 1.0** (Octobre 2024)
- ✅ Benchmark complet 4 modèles
- ✅ Dataset 100 requêtes
- ✅ Calcul durées + qualité
- ✅ Génération rapport markdown
- ✅ Support images via BLIP
- ✅ API DeepInfra (Qwen3-8B)

---

*Index créé le 16/10/2024 - Système de Benchmark OPSEMIA*

