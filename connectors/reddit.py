"""
Connecteur Reddit — Détection des besoins, questions et douleurs non résolues.

STATUT : EN ATTENTE D'APPROBATION API (Responsible Builder Policy 2026)
---------------------------------------------------------------------
Ce connecteur reste conservé en l'état dans le projet. L'accès à l'API Reddit
nécessite une approbation préalable formelle par Reddit. En attendant la validation,
le signal équivalent (demandes explicites d'outils / pain-points) est collecté
par le connecteur Stack Exchange (Software Recommendations).

Subreddits ciblés à terme :
- r/SaaS : Retours d'expérience, besoins d'outils et problématiques d'éditeurs SaaS.
- r/microsaas : Opportunités de micro-produits et demandes de solutions ciblées.
- r/Entrepreneur : Problèmes de productivité, questions de workflow et gestion d'entreprise.
"""

import os
import sys
import time
import logging
from datetime import datetime
from connectors.base_connector import BaseConnector

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

logger = logging.getLogger(__name__)

# Mots-clés indiquant une friction, un besoin d'outil ou une opportunité de produit
PAIN_POINT_KEYWORDS = [
    "looking for",
    "any tool",
    "recommend a tool",
    "frustrated with",
    "pain point",
    "is there an app",
    "is there a tool",
    "how do you handle",
    "alternative to",
    "wish there was",
    "tired of",
    "need a tool",
    "need software",
    "anyone know",
    "struggling with",
    "how to solve",
    "how to automate",
    "manual work",
    "time consuming",
]


class RedditConnector(BaseConnector):
    source_name = "reddit"
    category = "saas_tech"
    default_signal_type = "pain_point"

    def __init__(self, subreddits: list[str] = None, max_per_sub: int = 15):
        super().__init__()
        self.subreddits = subreddits or ["SaaS", "microsaas", "Entrepreneur"]
        self.max_per_sub = max_per_sub
        self.client_id = os.getenv("REDDIT_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET", "").strip()
        self.user_agent = os.getenv("REDDIT_USER_AGENT", "ScraperLegende/2.0 (by /u/scraper_legende)").strip()

    def _is_pain_point(self, title: str, body: str) -> tuple[bool, str]:
        """Vérifie si le post contient un signal de douleur ou une demande d'outil."""
        texte = f"{title} {body}".lower()
        for kw in PAIN_POINT_KEYWORDS:
            if kw in texte:
                return True, kw
        return False, ""

    def _scrape_via_praw(self) -> list[dict]:
        """Utilise le SDK officiel PRAW pour extraire les posts dès l'approbation obtenue."""
        items = []
        try:
            import praw
            reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent,
            )
            
            for sub_name in self.subreddits:
                logger.info(f"[{self.source_name}] Récupération PRAW sur r/{sub_name}...")
                subreddit = reddit.subreddit(sub_name)
                
                # Parcours des nouveaux posts
                for post in subreddit.new(limit=self.max_per_sub):
                    if getattr(post, 'stickied', False):
                        continue

                    title = post.title or ""
                    selftext = post.selftext or ""
                    url = f"https://www.reddit.com{post.permalink}"
                    ups = getattr(post, 'score', 0) or 0
                    num_comments = getattr(post, 'num_comments', 0) or 0
                    created_utc = getattr(post, 'created_utc', None)

                    is_pain, matched_kw = self._is_pain_point(title, selftext)
                    
                    base_score = float(ups * 1.2 + num_comments * 2.0 + (25.0 if is_pain else 10.0))
                    pub_date = datetime.utcfromtimestamp(created_utc) if created_utc else None
                    signal_type = "pain_point" if is_pain else "discussion"

                    items.append({
                        "title": f"[{sub_name}] {title}",
                        "url": url,
                        "description": selftext[:400] if selftext else f"Discussion sur r/{sub_name} avec {num_comments} commentaires.",
                        "published_date": pub_date,
                        "signal_type": signal_type,
                        "category": self.category,
                        "score": round(base_score, 1),
                        "raw_data": {
                            "subreddit": sub_name,
                            "author": str(post.author),
                            "ups": ups,
                            "num_comments": num_comments,
                            "matched_keyword": matched_kw,
                            "api_mode": "praw_official",
                        }
                    })

                time.sleep(2.0)

            return items
        except Exception as e:
            logger.warning(f"[{self.source_name}] Échec PRAW ({e})")
            return []

    def scrape(self) -> list[dict]:
        """Statut temporaire : en attente d'approbation de clé API Reddit."""
        if not self.client_id or not self.client_secret:
            logger.info(
                f"[{self.source_name}] [STATUT: En attente d'approbation API Reddit (Policy 2026)]. "
                "Connecteur conservé. Actif dès réception des clés."
            )
            return []

        return self._scrape_via_praw()


if __name__ == "__main__":
    connector = RedditConnector(subreddits=["SaaS", "microsaas"], max_per_sub=5)
    resultats = connector.scrape()
    print("\n[INFO] Connecteur Reddit : En attente d'approbation API (Responsible Builder Policy 2026). Code prêt et conservé.")
