# 📊 Benchmark OPSEMIA : Rapidité vs Qualité

Ce système de benchmark évalue les modèles d'embedding selon deux axes :
- **Rapidité** : Vitesse d'encodage (tokens/seconde, messages/seconde)
- **Qualité** (Précision) : Qualité des résultats de recherche (score sur 100)

## 🚀 Utilisation Rapide

### Premier lancement (complet)

```bash
python scripts/benchmark_complet_opsemia.py
```

⏱️ Durée estimée : **40-70 minutes**

### Relancement (avec cache)

Les collections encodées sont **conservées** automatiquement. Au 2ème lancement :

```bash
python scripts/benchmark_complet_opsemia.py
```

⏱️ Durée estimée : **~10 minutes** (pas de réencodage !)

### Forcer le réencodage

```bash
python scripts/benchmark_complet_opsemia.py --force
```

Supprime le cache et réencode tout.

## ⚙️ Options Disponibles

| Option | Description | Usage |
|--------|-------------|-------|
| `--force` | Force la réindexation complète | Tests comparatifs |
| `--skip-speed` | Sauter les tests de rapidité | Benchmark qualité uniquement |
| `--skip-quality` | Sauter les tests de qualité | Benchmark rapidité uniquement |

### Exemples

**Tester uniquement la rapidité :**
```bash
python scripts/benchmark_complet_opsemia.py --skip-quality
```
⏱️ ~5-10 minutes

**Tester uniquement la qualité (avec cache) :**
```bash
python scripts/benchmark_complet_opsemia.py --skip-speed
```
⏱️ ~5 minutes si déjà encodé

**Comparer deux modèles après modification :**
```bash
python scripts/benchmark_complet_opsemia.py --force
```

## 📊 Résultats

### Fichier généré

```
Docs Projet/BENCHMARK_RESULTATS_YYYYMMDD_HHMMSS.md
```

### Contenu

1. **Partie 1 : Rapidité**
   - Durée par token (ms)
   - Durée par message (ms)  
   - Débit (messages/s)
   - Estimation 1M messages (h)

2. **Partie 2 : Qualité (Précision)**
   - Score sur 100 (% requêtes réussies)
   - Precision@K, Recall@K, MRR
   - Résultats par type (messages vs images)

3. **Partie 3 : Conclusions**
   - Meilleur modèle global
   - Compromis rapidité/qualité
   - Recommandations

## 🧹 Nettoyage

Les collections de benchmark sont conservées dans `data/benchmark_temp/`.

Pour nettoyer :

```bash
python scripts/nettoyer_benchmark.py
```

Ou automatique avec `--force` :

```bash
python scripts/benchmark_complet_opsemia.py --force
```

## 🎯 Terminologie

### Rapidité (Performance)
- Mesure la **vitesse d'encodage**
- Métriques : ms/token, msg/s, heures pour 1M
- Important pour : déploiement production, gros volumes

### Qualité (Précision)
- Mesure la **qualité des résultats de recherche**
- Métrique principale : **Score /100** (% requêtes réussies)
- Critère : ≥1 résultat pertinent dans top 5
- Important pour : expérience utilisateur, pertinence

### Compromis Rapidité/Qualité

| Scénario | Priorité | Modèle recommandé |
|----------|----------|-------------------|
| Prototype, POC | Rapidité | Jina-v3 (léger) |
| Application web | Équilibre | BGE-M3 ou Solon |
| Recherche critique | Qualité | Meilleur score |
| Gros volumes | Rapidité | Jina-v3 + GPU |

## 🔧 Configuration

### Critère de réussite

Modifiable dans `config/settings.py` :

```python
TOP_K_BENCHMARK = 5  # Résultat dans top 5
```

Valeurs :
- `3` : Strict
- `5` : Standard ⭐ (recommandé)
- `10` : Souple

### API DeepInfra (Qwen3-8B)

Créer `.env` à la racine :

```bash
DEEPINFRA_TOKEN=votre_cle_api
```

Obtenir une clé : https://deepinfra.com/

## 📋 Workflow Recommandé

### 1. Première exécution

```bash
# Vérifier config
python scripts/valider_benchmark.py

# Lancer benchmark complet
python scripts/benchmark_complet_opsemia.py
```

### 2. Tests itératifs

```bash
# Tester rapidité d'un nouveau modèle
python scripts/benchmark_complet_opsemia.py --skip-quality

# Tester qualité avec modif de dataset
python scripts/benchmark_complet_opsemia.py --skip-speed --force
```

### 3. Rapport final

```bash
# Benchmark complet avec cache
python scripts/benchmark_complet_opsemia.py

# Nettoyer
python scripts/nettoyer_benchmark.py
```

## 🐛 Dépannage

### Images manquantes

```
⚠️  28 image(s) manquante(s)
```

**Solution :** Les estimations utilisent des valeurs typiques (~30s/image pour BLIP). Pas de blocage.

### Division par zéro

**Corrigé** : Gestion automatique si aucune image disponible.

### Clé API non trouvée

```
DEEPINFRA_TOKEN non configuré
```

**Solution :** Créer `.env` à la racine (voir Configuration).

### Collections déjà existantes

```
♻️  Collection benchmark_jina_v3 déjà indexée
```

**Normal** : C'est le cache ! Utilisez `--force` pour réindexer.

## 📝 Notes

- Le cache accélère les tests itératifs (10min vs 1h)
- `--force` réindexe mais garde les résultats de rapidité
- Les 3 modèles locaux + 1 API = 4 modèles testés
- Score de qualité : 100% = parfait, 0% = aucun résultat pertinent

---

**Questions ?** Consultez `BENCHMARK_CRITERE_REUSSITE.md` pour les détails.

