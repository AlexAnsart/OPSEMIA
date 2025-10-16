# Benchmark OPSEMIA - Résultats Complets

**Date:** 16/10/2025 22:45:23  
**Dataset:** Cas4 Breaking Bad (560 messages + 10 images)  
**Requêtes de test:** 100 (90 messages + 10 images)  
**Critère de réussite:** Au moins 1 résultat pertinent dans le top 10

---

## 📊 Résumé Exécutif

Ce benchmark évalue les performances de 4 modèles d'embedding texte et du modèle BLIP pour la description d'images, à travers :
1. **Calcul de durées d'encodage** : temps nécessaire pour encoder des messages et images
2. **Benchmark de qualité** : précision de la recherche sémantique sur 100 requêtes réelles

### Critère de Réussite

Une recherche est considérée comme **réussie** si au moins 1 document pertinent apparaît dans les **10 premiers résultats**.
Le **taux de réussite** (score sur 100) représente le pourcentage de requêtes réussies.

### Modèles Testés

| Modèle | Paramètres | Dimensions | Type |
|--------|-----------|------------|------|
| **Jina-v3** | 137M | 1024 | Local |
| **Solon-large** | 335M | 1024 | Local |
| **BGE-M3** | 568M | 1024 | Local |
| **Qwen3-8B** | 8000M | 8192 | API (DeepInfra) |
| **BLIP** | - | - | Vision (description) |

---

## ⏱️ Partie 1 : Durées d'Encodage

### 1.1 Modèles Texte

| Modèle | Chargement | Msg Court | 100 Tokens | 1000 Msgs | Débit | Est. 1M Msgs |
|--------|-----------|-----------|------------|-----------|-------|-------------|
| **Jina-v3** | 13.4s | N/A | N/A | N/A | 1.0/s | 269.3h |
| **Solon-large** | 3.1s | N/A | N/A | N/A | 0.2/s | 1162.2h |
| **BGE-M3** | 8.1s | N/A | N/A | N/A | 0.3/s | 814.4h |
| **Qwen3-8B** | N/A (API) | N/A | N/A | N/A | ~0.7 | ~391.2 |

> 📝 **Note Qwen3-8B:** Estimation basée sur ratio de paramètres (facteur 14.1x vs BGE-M3)


### 1.2 Images (BLIP + Encodage Description)


| Métrique | Valeur |
|----------|--------|
| **Chargement BLIP** | 6.5s |
| **Description moyenne** | 22.83s |
| **Encodage description** | 506.0ms |
| **Total moyen/image** | 23.33s |
| **Plus rapide** | 18.07s |
| **Plus lent** | 28.59s |
| **Estimation 1000 images** | 6.5h |


### 1.3 Estimations Globales

#### Pour 1 Million de Messages

- **Jina-v3:** 269.3 heures
- **Solon-large:** 1162.2 heures
- **BGE-M3:** 814.4 heures
- **Qwen3-8B:** ~391.2

#### Pour 1000 Images

- **BLIP + Encodage:** 6.5 heures

---

## 🎯 Partie 2 : Benchmark de Qualité (Précision)

### 2.1 Résultats Globaux (100 requêtes)

| Modèle | **Score (/100)** | P@1 | P@3 | P@10 | R@10 | MRR |
|--------|------------------|-----|-----|-----|-----|-----|
| **Solon-large** | **3.0%** | 0.010 | 0.007 | 0.003 | 0.011 | 0.016 |
| **Qwen3-8B** | **2.0%** | 0.010 | 0.003 | 0.002 | 0.005 | 0.012 |
| **BGE-M3** | **1.0%** | 0.000 | 0.000 | 0.001 | 0.003 | 0.003 |
| **Jina-v3** | **0.0%** | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

### 2.2 Résultats par Type de Contenu

#### Messages (90 requêtes)

| Modèle | Taux Réussite | P@10 | R@10 | MRR |
|--------|---------------|-----|-----|-----|
| **Solon-large** | 3.3% | 0.003 | 0.012 | 0.018 |
| **Qwen3-8B** | 2.2% | 0.002 | 0.006 | 0.013 |
| **BGE-M3** | 1.1% | 0.001 | 0.003 | 0.003 |
| **Jina-v3** | 0.0% | 0.000 | 0.000 | 0.000 |

#### Images (10 requêtes)

| Modèle | Taux Réussite | P@10 | R@10 | MRR |
|--------|---------------|-----|-----|-----|
| **Solon-large** | 0.0% | 0.000 | 0.000 | 0.000 |
| **Qwen3-8B** | 0.0% | 0.000 | 0.000 | 0.000 |
| **BGE-M3** | 0.0% | 0.000 | 0.000 | 0.000 |
| **Jina-v3** | 0.0% | 0.000 | 0.000 | 0.000 |

---

## 🏆 Conclusions

### Meilleur Modèle Global: **Solon-large**

- **Score:** 3.0/100 (3.0% de requêtes réussies)
- **MRR:** 0.016
- **Precision@10:** 0.003
- **Recall@10:** 0.011

### Compromis Vitesse/Qualité

- **Solon-large:** Score 3.0/100, Vitesse 1162.2h pour 1M msgs
- **Qwen3-8B:** Score 2.0/100, Vitesse ~391.2 pour 1M msgs
- **BGE-M3:** Score 1.0/100, Vitesse 814.4h pour 1M msgs
- **Jina-v3:** Score 0.0/100, Vitesse 269.3h pour 1M msgs

### Recommandations

1. **Pour la qualité maximale:** Privilégier le modèle avec le meilleur score (taux de réussite sur 10 résultats)
2. **Pour la vitesse:** Choisir un modèle avec moins de paramètres (Jina-v3 ou Solon-large)
3. **Pour les images:** BLIP fournit des descriptions de qualité mais reste lent (~2s/image)
4. **Pour le déploiement:** Considérer le compromis entre score de qualité et temps d'encodage

**Note:** Le critère de réussite (top 10) est configurable dans `config/settings.py` via `TOP_K_BENCHMARK`.

---

*Rapport généré automatiquement par `benchmark_complet_opsemia.py` le 16/10/2025 à 22:45:23*
