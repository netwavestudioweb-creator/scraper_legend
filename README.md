# 🚀 Scraper Légende (V2) — Moteur de Veille Concurrentielle & Détection d'Opportunités

Moteur de veille concurrentielle multi-sources conçu pour détecter les signaux faibles, les opportunités SaaS / tech et les besoins non résolus à travers le web, avec scoring prédictif et génération automatisée de business cases.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Ready-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Render](https://img.shields.io/badge/Render-Deployed-46E3B7?logo=render&logoColor=white)](https://render.com)

---

## 📑 Sommaire

1. [Architecture & Fonctionnalités](#-architecture--fonctionnalités)
2. [Sources Actives & Couverture](#-sources-actives--couverture)
3. [Algorithme de Scoring Multicritère](#-algorithme-de-scoring-multicritère)
4. [Génération Automatisée de Business Cases](#-génération-automatisée-de-business-cases)
5. [Déploiement sur Render](#-déploiement-sur-render)
6. [Étude de Cas Complète](#-étude-de-cas-complète)

---

## 🎯 Architecture & Fonctionnalités

- **Modèle de données central (`Opportunity`)** : Stockage PostgreSQL (avec bascule SQLite automatique en local) des opportunités, signaux, scores, statuts de traitement et business cases.
- **Système de déduplication strict** : Contrainte d'unicité et index sur `(source, url)` pour des collectes répétées 100% idempotentes.
- **Connecteurs modulaires (`BaseConnector`)** : Sessions HTTP avec politesse de requêtage, respect de `robots.txt`, User-Agent éthique et délais de courtoisie.
- **Dashboard Flask interactif** : Interface moderne (dark mode, KPI cards, filtres multi-critères, recherche, tri par score, filtres par tranche de score et génération de Business Case à la demande).

---

## 📊 Sources Actives & Couverture (7 Sources Connectées)

| Source | Connecteur | Méthode d'Accès | Type de Signal Métier | Volume Réel |
|---|---|---|---|:---:|
| **Hacker News** | [`connectors/hackernews.py`](file:///c:/Users/HP/Downloads/scraper-legende/connectors/hackernews.py) | Algolia & Firebase API | 🚀 Showcase (Show HN) / 💡 Pain Point (Ask HN) | **44 items** |
| **Product Hunt** | [`connectors/producthunt.py`](file:///c:/Users/HP/Downloads/scraper-legende/connectors/producthunt.py) | GraphQL v2 & RSS officiel | 🚀 Showcase (Lancements SaaS) | **26 items** |
| **AppSumo Marketplace** | [`connectors/appsumo.py`](file:///c:/Users/HP/Downloads/scraper-legende/connectors/appsumo.py) | Extraction catalogue public | 🚀 Showcase (Traction précoce & Deals) | **22 items** |
| **GitHub Trending** | [`connectors/github_trending.py`](file:///c:/Users/HP/Downloads/scraper-legende/connectors/github_trending.py) | Scraping éthique & Search REST | 🚀 Showcase (Micro-SaaS & IA) | **20 items** |
| **Stack Exchange** | [`connectors/stackexchange.py`](file:///c:/Users/HP/Downloads/scraper-legende/connectors/stackexchange.py) | API publique v2.3 | 💡 Pain Point (Demandes de logiciels) | **20 items** |
| **Wellfound** (AngelList) | [`connectors/wellfound.py`](file:///c:/Users/HP/Downloads/scraper-legende/connectors/wellfound.py) | Scraping HTML éthique | 🚀 Showcase (Startups en croissance) | **10 items** |
| **BetaList** | [`connectors/betalist.py`](file:///c:/Users/HP/Downloads/scraper-legende/connectors/betalist.py) | Scraping HTML éthique | 🚀 Showcase (Pré-lancement startups) | **3 items** |
| **Reddit** (r/SaaS, r/microsaas) | [`connectors/reddit.py`](file:///c:/Users/HP/Downloads/scraper-legende/connectors/reddit.py) | PRAW officiel | ⏳ *En attente validation API (Policy 2026)* | Prêt |
| **TOTAL ACTIF** | **7 connecteurs opérationnels** | **Multi-flux** | **7 sources actives** | **170+ opportunités** |

---

## 📐 Algorithme de Scoring Multicritère

Chaque opportunité est évaluée sur une échelle de **0 à 100** via une formule transparente documentée dans [`SCORING.md`](file:///c:/Users/HP/Downloads/scraper-legende/SCORING.md) :

$$\mathbf{Score} = (0.40 \times S_{\text{Engagement}}) + (0.20 \times S_{\text{Fraîcheur}}) + (0.25 \times S_{\text{Signal}}) + (0.15 \times S_{\text{Récurrence}})$$

---

## 📄 Génération Automatisée de Business Cases

Pour chaque opportunité qualifiée, un résumé structuré en 3 volets est généré à la demande depuis le dashboard :
- **📌 Problème Identifié** : Reformulation du besoin ou de la valeur détectée.
- **📈 Preuve de Traction & Métriques** : Métriques concrètes (notes, avis, votes, volume).
- **💡 Angle Produit Suggéré** : Piste d'exploration prudente et qualifiée.

---

## 🚀 Déploiement sur Render

### Variables d'environnement (Render)
- `DATABASE_URL` : URL PostgreSQL (fournie automatiquement par Render PostgreSQL).
- `PORT` : `10000` (défini par Render).
- `OPENAI_API_KEY` *(Optionnel)* : Clé API pour la génération LLM (si omise, le mode template déterministe s'active à 0 coût).

### Commandes de build et de démarrage
- **Build Command** : `pip install -r requirements.txt`
- **Start Command** : `gunicorn dashboard.app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`

---

## 📖 Étude de Cas Complète

Consultez le document d'analyse détaillé : **[`RAPPORT_ETUDE_DE_CAS.md`](file:///c:/Users/HP/Downloads/scraper-legende/RAPPORT_ETUDE_DE_CAS.md)**.
