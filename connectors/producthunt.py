"""
Connecteur Product Hunt — Détection des nouveaux lancements de produits & SaaS.

Méthodes :
1. API Officielle GraphQL v2 (recommandée si PRODUCTHUNT_DEV_TOKEN est défini)
2. Fallback officiel via flux RSS/Atom de Product Hunt si aucun token n'est configuré.
"""

import os
import sys
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from connectors.base_connector import BaseConnector

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

logger = logging.getLogger(__name__)

PRODUCTHUNT_GRAPHQL_URL = "https://api.producthunt.com/v2/api/graphql"
PRODUCTHUNT_FEED_URL = "https://www.producthunt.com/feed"


class ProductHuntConnector(BaseConnector):
    source_name = "producthunt"
    category = "saas_tech"
    default_signal_type = "showcase"

    def __init__(self, max_items: int = 25):
        super().__init__()
        self.max_items = max_items
        self.dev_token = os.getenv("PRODUCTHUNT_DEV_TOKEN", "").strip()

    def _scrape_via_graphql(self) -> list[dict]:
        """Récupère les produits récents via l'API GraphQL officielle v2 de Product Hunt."""
        if not self.dev_token:
            return []

        logger.info(f"[{self.source_name}] Utilisation de l'API GraphQL avec token...")
        headers = {
            "Authorization": f"Bearer {self.dev_token}",
            "Content-Type": "application/json",
        }

        query = """
        query GetRecentPosts($first: Int!) {
          posts(first: $first, order: VOTES) {
            edges {
              node {
                id
                name
                tagline
                description
                url
                website
                votesCount
                commentsCount
                createdAt
              }
            }
          }
        }
        """
        payload = {
            "query": query,
            "variables": {"first": min(self.max_items, 30)}
        }

        try:
            response = self.session_http.post(
                PRODUCTHUNT_GRAPHQL_URL,
                json=payload,
                headers=headers,
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            edges = data.get("data", {}).get("posts", {}).get("edges", [])
            
            items = []
            for edge in edges:
                node = edge.get("node", {})
                name = node.get("name", "")
                tagline = node.get("tagline", "")
                url = node.get("website") or node.get("url")
                votes = node.get("votesCount", 0)
                comments = node.get("commentsCount", 0)
                created_at = node.get("createdAt")

                pub_date = None
                if created_at:
                    try:
                        pub_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    except Exception:
                        pub_date = None

                title = f"{name} — {tagline}" if tagline else name
                score = round(float(votes * 1.2 + comments * 1.5), 1)

                items.append({
                    "title": title.strip(),
                    "url": url.strip(),
                    "description": node.get("description") or tagline,
                    "published_date": pub_date,
                    "signal_type": self.default_signal_type,
                    "category": self.category,
                    "score": score,
                    "raw_data": {
                        "ph_id": node.get("id"),
                        "ph_url": node.get("url"),
                        "votes": votes,
                        "comments": comments,
                        "api_mode": "graphql_v2",
                    }
                })

            return items
        except Exception as e:
            logger.warning(f"[{self.source_name}] Échec GraphQL ({e}), bascule vers le flux public...")
            return []

    def _scrape_via_feed(self) -> list[dict]:
        """Récupère les lancements récents via le flux public officiel Atom/RSS de Product Hunt."""
        logger.info(f"[{self.source_name}] Récupération via le flux public officiel...")
        try:
            response = self.fetch(PRODUCTHUNT_FEED_URL)
            soup = BeautifulSoup(response.content, "xml") if "xml" in response.headers.get("Content-Type", "") else BeautifulSoup(response.text, "html.parser")
            
            entries = soup.find_all("entry") or soup.find_all("item")
            items = []

            for entry in entries[:self.max_items]:
                title_tag = entry.find("title")
                link_tag = entry.find("link")
                summary_tag = entry.find("summary") or entry.find("description") or entry.find("content")
                published_tag = entry.find("published") or entry.find("pubDate") or entry.find("updated")

                if not title_tag:
                    continue

                title = title_tag.get_text().strip()
                
                # Récupération de l'URL
                url = ""
                if link_tag:
                    if link_tag.get("href"):
                        url = link_tag.get("href")
                    else:
                        url = link_tag.get_text().strip()

                if not url:
                    continue

                description = summary_tag.get_text().strip() if summary_tag else ""
                
                # Nettoyage HTML dans description si nécessaire
                if "<" in description and ">" in description:
                    desc_soup = BeautifulSoup(description, "html.parser")
                    description = desc_soup.get_text().strip()

                pub_date = None
                if published_tag:
                    pub_str = published_tag.get_text().strip()
                    try:
                        pub_date = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
                    except Exception:
                        pub_date = None

                # Score initial pour les items de feed (environ 25.0 points de base pour un produit sélectionné en homepage)
                base_score = 25.0

                items.append({
                    "title": title,
                    "url": url,
                    "description": description[:400] if description else f"Lancement officiel sur Product Hunt : {title}",
                    "published_date": pub_date,
                    "signal_type": self.default_signal_type,
                    "category": self.category,
                    "score": base_score,
                    "raw_data": {
                        "feed_source": "producthunt_rss",
                        "published_raw": published_tag.get_text() if published_tag else None,
                    }
                })

            return items
        except Exception as e:
            logger.error(f"[{self.source_name}] Échec récupération flux Product Hunt: {e}")
            return []

    def scrape(self) -> list[dict]:
        """Tente d'abord l'API GraphQL, sinon bascule sur le flux public."""
        items = self._scrape_via_graphql()
        if not items:
            items = self._scrape_via_feed()
        return items


if __name__ == "__main__":
    connector = ProductHuntConnector(max_items=5)
    resultats = connector.scrape()
    print(f"\n[OK] {len(resultats)} opportunites extraites depuis Product Hunt :\n")
    for r in resultats:
        print(f"* Titre : {r['title']}")
        print(f"  URL   : {r['url']}")
        print(f"  Score : {r['score']} | Signal : {r['signal_type']}")
        print("---")
