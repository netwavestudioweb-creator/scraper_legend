# 📊 Rapport d'Étude de Cas — Scraper Légende (V2)
**Moteur de Veille Concurrentielle, Scoring Prédictif & Génération Automatisée de Business Cases**

---

## 🎯 1. Contexte & Vision du Projet

Dans le cadre du développement de mes projets SaaS et de mon portfolio en Ingénierie IA / Développement Web, **Scraper Légende** a été conçu pour résoudre un défi critique pour les solopreneurs, agences et équipes produit : **comment détecter rapidement des opportunités de marché viables sans perdre des dizaines d'heures à scanner manuellement des dizaines de plateformes ?**

Le projet a été entièrement reconstruit selon une démarche rigoureuse par phases incrémentales, garantissant un système démontrable et résilient à chaque étape.

---

## 🔍 2. Problématique & Objectifs Techniques

| Défi Initial | Solution Implémentée dans Scraper Légende V2 |
|---|---|
| **Dispersion des sources** | Connexion automatisée à **7 flux complémentaires** (showcase produits, besoins exprimés, traction commerciale). |
| **Bruit & redondance** | Système de **déduplication idempotente** stricte sur `(source, url)`. |
| **Difficulté de priorisation** | **Algorithme de scoring multicritère (0-100)** transparent et vérifiable (pas de boîte noire). |
| **Charge d'analyse manuelle** | **Génération automatisée de Business Cases structurés** en 3 volets exploitables immédiatement. |
| **Risques légaux du scraping** | **Audit éthique et conformité `robots.txt` / CGU** systématique. |

---

## 🏗️ 3. Architecture Technique du Système

```
[ Hacker News (Algolia API) ] ──────┐
[ Product Hunt (GraphQL / RSS) ] ───┤
[ GitHub Trending (Scraping) ] ─────┤
[ Stack Exchange (Public API) ] ────┼──> [ BaseConnector (Polite HTTP) ]
[ AppSumo Deals (Public Data) ] ────┤                  │
[ Wellfound Startups (HTML) ] ──────┤                  ▼
[ BetaList Startups (HTML) ] ───────┘        [ Déduplication Idempotente ]
                                                       │
                                                       ▼
                                         [ PostgreSQL / SQLite Fallback ]
                                                       │
                           ┌───────────────────────────┴───────────────────────────┐
                           ▼                                                       ▼
            [ Moteur de Scoring Multicritère ]                        [ Générateur de Business Cases ]
            (Engagement, Fraîcheur, Signal, Rec)                      (Problème, Traction, Angle Produit)
                           │                                                       │
                           └───────────────────────────┬───────────────────────────┘
                                                       ▼
                                     [ Dashboard Flask Moderne & Responsive ]
                                     (KPIs, Filtres par tranche, Dark Mode)
```

---

## ⚖️ 4. Arbitrage Éthique & Juridique (Point Clé)

Conformément aux meilleures pratiques de l'ingénierie logicielle et du web scraping responsable, chaque source candidate a fait l'objet d'un audit préalable :

| Source | Analyse Technique & Juridique | Décision Prise |
|---|---|---|
| **Hacker News, Product Hunt, GitHub, Stack Exchange** | APIs officielles publiques et flux ouverts documentés. | ✅ **Connecteurs actifs (Phases 1 & 2)** |
| **AppSumo, Wellfound, BetaList** | Pages publiques autorisées par le `robots.txt`, délais de courtoisie (1.5s), User-Agent transparent. | ✅ **Connecteurs actifs (Phase 3)** |
| **G2 & Capterra (Gartner)** | Interdiction stricte du scraping dans les CGU ; absence d'API publique tierce gratuite. | ⛔ **Exclusion formelle** (refus de contournement illégal) |
| **Indie Hackers** | Challenge interactif Cloudflare Turnstile (403) bloquant les requêtes serveur automatisées. | ⚠️ **Exclusion éthique** (pas de techniques d'évasion agressives) |
| **Acquire.com** | Fiches de transaction encapsulées dans l'application privée `app.acquire.com` nécessitant une authentification acheteur. | ⚠️ **Exclusion technique** (données non publiques) |
| **Reddit (r/SaaS, r/microsaas)** | Connecteur PRAW développé et prêt, soumis au processus d'approbation *Responsible Builder Policy 2026*. | ⏳ **En attente d'approbation API** |

---

## 📐 5. Algorithme de Scoring Multicritère Documenté

L'algorithme évalue chaque opportunité sur 100 points selon une formule pondérée transparente :

$$\mathbf{Score} = (0.40 \times S_{\text{Engagement}}) + (0.20 \times S_{\text{Fraîcheur}}) + (0.25 \times S_{\text{Signal}}) + (0.15 \times S_{\text{Récurrence}})$$

1. **Engagement (40%)** : Normalisation relative par source (points/commentaires HN, votes/commentaires PH, stars GitHub, réponses Stack Exchange, notes/avis AppSumo).
2. **Fraîcheur (20%)** : Décroissance temporelle ($100$ pts $\le 24$h, $85$ pts $\le 48$h, $65$ pts $\le 7$j, $40$ pts $\le 30$j, $20$ pts au-delà).
3. **Signal Métier (25%)** : $100$ pts pour les demandes explicites de solutions (*"looking for"*, *"alternative"*), $90$ pts pour les `pain_point`, $50$ pts pour les `showcase`.
4. **Récurrence Inter-sources (15%)** : $100$ pts si la thématique émerge sur $\ge 3$ sources distinctes, $70$ pts sur 2 sources.

---

## 📄 6. Génération Automatisée de Business Cases

Pour rendre les données immédiatement actionnables, le système génère un résumé structuré en 3 blocs :
- **📌 Problème Identifié** : Reformulation concise du besoin utilisateur ou de l'opportunité.
- **📈 Preuve de Traction & Métriques** : Données chiffrées réelles (notes, avis, votes, volume de recherche).
- **💡 Angle Produit Suggéré** : Pistes de positionnement (Micro-SaaS vertical, intégration native, alternative allégée).

*Architecture hybride* : Mode template déterministe par défaut (0.00 $ de coût, zéro hallucination) et mode LLM activable via variable d'environnement (coût $\approx 0.00015$ \$ par opportunité).

---

## 📊 7. Résultats Chiffrés & Validation

*Données réelles extraites de la base de données de production :*

- **7 Connecteurs Actifs** opérationnels et déployés.
- **170+ Opportunités Détectées** et qualifiées en base.
- **Répartition du Scoring** :
  - 🔥 **Opportunités Chaudes ($\text{Score} \ge 70$)** : **45 opportunités**
  - 💡 **Opportunités Qualifiées ($50 \le \text{Score} < 70$)** : **76 opportunités**
  - 👁️ **Signaux de Veille ($\text{Score} < 50$)** : **49 opportunités**
- **Déduplication** : **100% de doublons filtrés** lors des collectes successives.

---

## 🛠️ 8. Compétences Démontrées

- **Architecture Logicielle & Backend** : Flask, SQLAlchemy ORM, PostgreSQL, SQLite, sessions HTTP résilientes.
- **Data Collection & Web Scraping Éthique** : APIs REST / GraphQL, parsing Beautiful Soup, respect du `robots.txt` et des CGU.
- **Data Engineering & Algorithmique** : Pipeline de normalisation de métriques hétérogènes, scoring multicritère déterministe.
- **Intégration IA / LLM & NLP** : Prompt engineering strict anti-hallucination, génération structurée, templates heuristiques.
- **Frontend & UX Moderne** : Interface Flask dark mode réactive, KPI cards, filtres dynamiques par score, modals AJAX.
- **DevOps & Déploiement Cloud** : Gunicorn, Render, gestion des secrets `.env` et configuration multi-environnements.
