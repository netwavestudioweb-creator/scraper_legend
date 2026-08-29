# 📐 Algorithme de Scoring des Opportunités — Scraper Légende (V2)

Ce document détaille la formule mathématique, les pondérations et la méthode de normalisation utilisées par le moteur de scoring de **Scraper Légende**.

---

## 🎯 1. Philosophie du Scoring

L'objectif de l'algorithme est de **séparer le bruit des opportunités à fort potentiel commercial**.
Une opportunité hautement prioritaire présente généralement :
1. **Un signal explicite de besoin / douleur** (*Pain Point* exprimé directement par un utilisateur cherchant un outil).
2. **Une traction ou un intérêt communautaire mesurable** (*Engagement* : votes, réponses, étoiles, avis).
3. **Une détection récente** (*Fraîcheur* : information chaude et exploitable immédiatement).
4. **Une validation croisée** (*Récurrence* : un thème qui émerge sur plusieurs plateformes distinctes en même temps).

---

## 🔢 2. Formule Globale & Pondération

Chaque opportunité reçoit un score composite normalisé sur une échelle de **0 à 100 points** :

$$\mathbf{Score_{Total}} = (0.40 \times S_{\text{Engagement}}) + (0.20 \times S_{\text{Fraîcheur}}) + (0.25 \times S_{\text{Signal}}) + (0.15 \times S_{\text{Récurrence}})$$

---

## 🧩 3. Détail des 4 Composantes

### 1️⃣ Engagement ($S_{\text{Engagement}}$ — Poids : 40%)
Puisque chaque plateforme utilise des métriques différentes (étoiles GitHub, points Hacker News, votes Product Hunt, avis AppSumo), l'engagement est **normalisé sur 100** selon l'échelle propre à chaque source :

- **Hacker News** :
  $$S_{\text{HN}} = \min(100, \text{points} \times 1.5 + \text{commentaires} \times 2.5)$$
- **Product Hunt** :
  $$S_{\text{PH}} = \min(100, \text{votes} \times 1.2 + \text{commentaires} \times 2.0)$$ *(ou 35.0 par défaut pour les lancements du flux d'accueil)*
- **GitHub Trending** :
  $$S_{\text{GH}} = \min(100, \text{stars\_today} \times 0.5 + \text{forks} \times 1.5 + \text{total\_stars} \times 0.02)$$
- **Stack Exchange (Software Recommendations)** :
  $$S_{\text{SE}} = \min(100, \text{score} \times 8.0 + \text{réponses} \times 15.0 + \min(\text{vues} \times 0.05, 30))$$
- **AppSumo Marketplace** :
  $$S_{\text{AS}} = \min(100, \text{avis} \times 0.8 + \text{note\_moyenne} \times 12.0)$$
- **BetaList & Wellfound** :
  $$S_{\text{Curated}} = 35.0 \text{ (base éditoriale de sélection)}$$

---

### 2️⃣ Fraîcheur ($S_{\text{Fraîcheur}}$ — Poids : 20%)
La valeur d'une opportunité décroît avec le temps écoulé depuis sa publication/détection :

- $\le 24\text{ heures}$ : **100 points** (Signal ultra-frais)
- $24\text{h} \text{ à } 48\text{h}$ : **85 points**
- $48\text{h} \text{ à } 7\text{ jours}$ : **65 points**
- $7\text{ jours} \text{ à } 30\text{ jours}$ : **40 points**
- $> 30\text{ jours}$ : **20 points**

---

### 3️⃣ Signal Métier & Pain Point ($S_{\text{Signal}}$ — Poids : 25%)
Une personne qui cherche activement une solution à un problème non résolu représente une opportunité plus forte qu'un simple produit déjà construit :

- **Type `pain_point` (Stack Exchange, Ask HN, Reddit)** : **90 points**
  - *Bonus de +10 points* si le titre ou le corps contient des expressions explicites de recherche (*"looking for"*, *"alternative to"*, *"how to automate"*, *"frustrated with"*).
- **Type `showcase` (Product Hunt, Show HN, BetaList, AppSumo, GitHub)** : **50 points** (démonstration ou lancement d'une solution).

---

### 4️⃣ Récurrence Inter-sources ($S_{\text{Récurrence}}$ — Poids : 15%)
L'algorithme analyse les mots-clés thématiques (ex: `pdf`, `automation`, `dashboard`, `image`, `ai-agent`, `markdown`, `monitoring`) :

- Sujet détecté sur **$\ge 3$ sources distinctes** : **100 points** (Tendance de marché forte)
- Sujet détecté sur **2 sources distinctes** : **70 points** (Signal émergent)
- Sujet présent sur **1 seule source** : **35 points** (Signal isolé)

---

## 🏷️ 4. Grille de Lecture des Scores

| Tranche de Score | Qualification | Action Recommandée |
|:---:|:---:|---|
| **$\ge 70$** | 🔥 **Opportunité Chaude (Haute priorité)** | Analyse immédiate, génération prioritaire de Business Case. |
| **$50 - 69$** | 💡 **Opportunité Qualifiée (Moyenne priorité)** | Signal valide à approfondir et surveiller. |
| **$< 50$** | 👁️ **Signal Veille (Basse priorité)** | Enregistré en veille passive sans action requise. |
