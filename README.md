# 🚀 Scraper Légende (V2) — Moteur de Veille Concurrentielle & Détection d'Opportunités

Moteur de veille concurrentielle multi-sources conçu pour détecter les signaux faibles, les opportunités SaaS / tech et les besoins non résolus à travers le web, avec scoring prédictif et génération automatisée de business cases.

[![Demo Live](https://img.shields.io/badge/Demo%20Live-scraper--legend.onrender.com-success?logo=render&logoColor=white)](https://scraper-legend.onrender.com)
[![GitHub Repo](https://img.shields.io/badge/GitHub-netwavestudioweb--creator%2Fscraper__legend-blue?logo=github)](https://github.com/netwavestudioweb-creator/scraper_legend)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Render%20Cloud-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)

---

## 🔗 Démonstration & Liens du Projet

- 🌐 **Application en Ligne (Render)** : **[https://scraper-legend.onrender.com](https://scraper-legend.onrender.com)**
- 🐙 **Dépôt GitHub Public** : **[github.com/netwavestudioweb-creator/scraper_legend](https://github.com/netwavestudioweb-creator/scraper_legend)**
- 📖 **Étude de Cas Complète** : **[`RAPPORT_ETUDE_DE_CAS.md`](./RAPPORT_ETUDE_DE_CAS.md)**
- 📐 **Spécification du Scoring** : **[`SCORING.md`](./SCORING.md)**

---

## 🎯 Architecture & Fonctionnalités

- **Modèle de données central (`Opportunity`)** : Stockage PostgreSQL managé sur Render (avec bascule SQLite automatique en local) des opportunités, signaux, scores, statuts de traitement et business cases.
- **Système de déduplication strict** : Contrainte d'unicité et index sur `(source, url)` pour des collectes répétées 100% idempotentes.
- **Connecteurs modulaires (`BaseConnector`)** : Sessions HTTP avec politesse de requêtage, respect de `robots.txt`, User-Agent éthique et délais de courtoisie.
- **Dashboard Flask Haute Couture** : Interface moderne Obsidian Glassmorphism avec véritables icônes vectorielles SVG, 5 KPI hero cards, filtres multi-critères, recherche, tri par score, filtres par tranche (`hot`, `qualified`, `cold`) et génération de Business Case à la demande.

---

## 📊 Couverture des Sources & État de Déploiement

Le projet intègre **7 connecteurs développés et validés**, dont **6 sources actives en continu en production cloud** (130+ opportunités réelles avec scoring) :

| Source | Connecteur | Méthode d'Accès | Type de Signal | État en Production Cloud (Render) |
|---|---|---|---|:---:|
| **Hacker News** | [`connectors/hackernews.py`](./connectors/hackernews.py) | Algolia & Firebase API | 🚀 Showcase (Show HN) / 💡 Pain Point (Ask HN) | 🟢 **Actif en continu** (40+ items) |
| **Product Hunt** | [`connectors/producthunt.py`](./connectors/producthunt.py) | GraphQL v2 & RSS officiel | 🚀 Showcase (Lancements SaaS) | 🟢 **Actif en continu** (20+ items) |
| **AppSumo Deals** | [`connectors/appsumo.py`](./connectors/appsumo.py) | Extraction catalogue public | 🚀 Showcase (Traction précoce & Deals) | 🟢 **Actif en continu** (20 items) |
| **GitHub Trending** | [`connectors/github_trending.py`](./connectors/github_trending.py) | Scraping éthique & Search REST | 🚀 Showcase (Micro-SaaS & IA) | 🟢 **Actif en continu** (20 items) |
| **Stack Exchange** | [`connectors/stackexchange.py`](./connectors/stackexchange.py) | API publique v2.3 (*softwarerecs*) | 💡 Pain Point (Demandes de solutions) | 🟢 **Actif en continu** (20 items) |
| **Wellfound** (AngelList) | [`connectors/wellfound.py`](./connectors/wellfound.py) | Scraping HTML éthique | 🚀 Showcase (Startups en croissance) | 🟢 **Actif en continu** (10+ items) |
| **BetaList** | [`connectors/betalist.py`](./connectors/betalist.py) | Scraping HTML éthique | 🚀 Showcase (Pré-lancement startups) | 🟡 **Actif en local** *(Filtrage WAF 403 sur IP cloud)* |
| **Reddit** (r/SaaS, r/microsaas) | [`connectors/reddit.py`](./connectors/reddit.py) | PRAW officiel | 💡 Pain Point / Showcase | ⏳ *En attente validation API (Policy 2026)* |

> ℹ️ **Note sur BetaList & Éthique du Scraping** :  
> Le connecteur BetaList fonctionne parfaitement en environnement local (HTTP 200, extraction validée de 10 startups avec structure DOM Tailwind). En environnement cloud (Render), les requêtes sont bloquées par le WAF de BetaList (`HTTP 403 Forbidden` sur l'IP datacenter). Conformément à la charte éthique du projet, aucun contournement agressif (proxies rotatifs) n'est déployé : cette source est documentée en toute transparence.

---

## 📐 Algorithme de Scoring Multicritère

Chaque opportunité est évaluée sur une échelle de **0 à 100** via une formule transparente documentée dans [`SCORING.md`](./SCORING.md) :

$$\mathbf{Score} = (0.40 \times S_{\text{Engagement}}) + (0.20 \times S_{\text{Fraîcheur}}) + (0.25 \times S_{\text{Signal}}) + (0.15 \times S_{\text{Récurrence}})$$

- 🔥 **Chaudes ($\ge 70$ pts)** : Signaux forts combinant fort engagement, forte fraîcheur et besoin explicite.
- 💡 **Qualifiées ($50-69$ pts)** : Signaux réguliers à fort potentiel d'approfondissement.
- 👁️ **En Veille ($< 50$ pts)** : Veille passive et signaux émergents.

---

## 📄 Génération Automatisée de Business Cases

Pour chaque opportunité qualifiée, un résumé structuré en 3 volets est généré à la demande depuis le dashboard :
- **📌 Problème Identifié** : Reformulation du besoin ou de la valeur détectée.
- **📈 Preuve de Traction & Métriques** : Métriques concrètes (notes, avis, votes, volume).
- **💡 Angle Produit Suggéré** : Piste d'exploration prudente et qualifiée.

---

## 🚀 Déploiement & Configuration

### Variables d'environnement
- `DATABASE_URL` : URL PostgreSQL Render.
- `ADMIN_TRIGGER_KEY` : Clé secrète pour déclencher les collectes de production via `/admin/trigger-collection`.
- `PORT` : `10000` (défini par Render).
- `OPENAI_API_KEY` *(Optionnel)* : Clé API pour le mode LLM (si omise, le mode template déterministe s'active à 0.00 $).

### Commandes de production
- **Build Command** : `pip install -r requirements.txt`
- **Start Command** : `gunicorn dashboard.app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`
