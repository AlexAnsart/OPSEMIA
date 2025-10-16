# Benchmark OPSEMIA - Résultats Complets

**Date:** 17/10/2025 00:05:37  
**Dataset:** Cas4 Breaking Bad (560 messages + 10 images)  
**Requêtes de test:** 100 (90 messages + 10 images)  
**Critère de réussite:** Au moins 1 résultat pertinent dans le top 3

---

## 📊 Résumé Exécutif

Ce benchmark évalue les performances de 4 modèles d'embedding texte et du modèle BLIP pour la description d'images, à travers :
1. **Calcul de durées d'encodage** : temps nécessaire pour encoder des messages et images
2. **Benchmark de qualité** : précision de la recherche sémantique sur 100 requêtes réelles

### Critère de Réussite

Une recherche est considérée comme **réussie** si au moins 1 document pertinent apparaît dans les **3 premiers résultats**.
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
| **Jina-v3** | 10.2s | N/A | N/A | N/A | 2.5/s | 11.2h |
| **Solon-large** | 3.5s | N/A | N/A | N/A | 1.3/s | 20.6h |
| **BGE-M3** | 6.2s | N/A | N/A | N/A | 2.7/s | 10.4h |
| **Qwen3-8B** | N/A (API) | N/A | N/A | N/A | ~3.5 | ~7.8 |

> 📝 **Note Qwen3-8B:** Estimation basée sur ratio de paramètres (facteur 14.1x vs BGE-M3)


### 1.2 Images (BLIP + Encodage Description)


| Métrique | Valeur |
|----------|--------|
| **Chargement BLIP** | 5.9s |
| **Description moyenne** | 16.57s |
| **Encodage description** | 647.6ms |
| **Total moyen/image** | 17.22s |
| **Plus rapide** | 11.78s |
| **Plus lent** | 20.85s |
| **Estimation 1000 images** | 4.8h |


### 1.3 Estimations Globales

#### Pour 100k Messages

- **Jina-v3:** 11.2 heures
- **Solon-large:** 20.6 heures
- **BGE-M3:** 10.4 heures
- **Qwen3-8B:** ~7.8

#### Pour 1000 Images

- **BLIP + Encodage:** 4.8 heures

---

## 🎯 Partie 2 : Benchmark de Qualité (Précision)

### 2.1 Résultats Globaux (100 requêtes)

| Modèle | **Score (/100)** | P@1 | P@3 | P@3 | R@3 | MRR |
|--------|------------------|-----|-----|-----|-----|-----|
| **Solon-large** | **83.0%** | 0.690 | 0.377 | 0.377 | 0.466 | 0.762 |
| **BGE-M3** | **82.0%** | 0.640 | 0.377 | 0.377 | 0.466 | 0.739 |
| **Jina-v3** | **80.0%** | 0.630 | 0.353 | 0.353 | 0.456 | 0.722 |
| **Qwen3-8B** | **56.0%** | 0.430 | 0.230 | 0.230 | 0.307 | 0.536 |

### 2.2 Résultats par Type de Contenu

#### Messages (90 requêtes)

| Modèle | Taux Réussite | P@3 | R@3 | MRR |
|--------|---------------|-----|-----|-----|
| **Solon-large** | 82.2% | 0.385 | 0.440 | 0.753 |
| **BGE-M3** | 81.1% | 0.385 | 0.440 | 0.727 |
| **Jina-v3** | 78.9% | 0.359 | 0.429 | 0.708 |
| **Qwen3-8B** | 56.7% | 0.237 | 0.286 | 0.545 |

#### Images (10 requêtes)

| Modèle | Taux Réussite | P@3 | R@3 | MRR |
|--------|---------------|-----|-----|-----|
| **Solon-large** | 90.0% | 0.300 | 0.700 | 0.850 |
| **BGE-M3** | 90.0% | 0.300 | 0.700 | 0.850 |
| **Jina-v3** | 90.0% | 0.300 | 0.700 | 0.850 |
| **Qwen3-8B** | 50.0% | 0.167 | 0.500 | 0.450 |

---

## 🏆 Conclusions

### Meilleur Modèle Global: **Solon-large**

- **Score:** 83.0/100 (83.0% de requêtes réussies)
- **MRR:** 0.762
- **Precision@3:** 0.377
- **Recall@3:** 0.466

### Compromis Vitesse/Qualité

- **Solon-large:** Score 83.0/100, Vitesse 20.6h pour 100k msgs
- **BGE-M3:** Score 82.0/100, Vitesse 10.4h pour 100k msgs
- **Jina-v3:** Score 80.0/100, Vitesse 11.2h pour 100k msgs
- **Qwen3-8B:** Score 56.0/100, Vitesse ~7.8 pour 100k msgs

### Recommandations

1. **Pour la qualité maximale:** Privilégier le modèle avec le meilleur score (taux de réussite sur 3 résultats)
2. **Pour la vitesse:** Choisir un modèle avec moins de paramètres (Jina-v3 ou Solon-large)
3. **Pour les images:** BLIP fournit des descriptions de qualité mais reste lent (~2s/image)
4. **Pour le déploiement:** Considérer le compromis entre score de qualité et temps d'encodage

**Note:** Le critère de réussite (top 3) est configurable dans `config/settings.py` via `TOP_K_BENCHMARK`.

---

*Rapport généré automatiquement par `benchmark_complet_opsemia.py` le 17/10/2025 à 00:05:37*
