"""
Connecteur Hacker News — Détection des signaux d'opportunités tech & SaaS.

Sources ciblées :
- "Show HN" : Démonstrations de produits / SaaS / projets lancés par des créateurs.
- "Ask HN"  : Demandes de solutions, retours d'expérience et frustrations formulées par la communauté.

Utilise l'API publique Algolia HN Search (sans authentification, rapide et structurée)
avec fallback sur l'API Firebase officielle de Hacker News.
"""

import sys
import logging
from datetime import datetime
from connectors.base_connector import BaseConnector

# Configuration de l'encodage de la console sous Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

logger = logging.getLogger(__name__)

ALGOLIA_API_URL = "https://hn.algolia.com/api/v1/search_by_date"
HN_FIREBASE_BASE_URL = "https://hacker-news.firebaseio.com/v0"


class HackerNewsConnector(BaseConnector):
    source_name = "hackernews"
    category = "saas_tech"

    def __init__(self, tag: str = "show_hn", max_items: int = 40):
        super().__init__()
        self.tag = tag  # "show_hn" ou "ask_hn"
        self.max_items = max_items
        self.default_signal_type = "showcase" if tag == "show_hn" else "pain_point"

    def _scrape_via_algolia(self) -> list[dict]:
        """Récupère les soumissions récentes via l'API Algolia HN."""
        items = []
        hits_per_page = min(self.max_items, 50)
        pages_needed = (self.max_items + hits_per_page - 1) // hits_per_page

        for page in range(pages_needed):
            params = {
                "tags": self.tag,
                "page": page,
                "hitsPerPage": hits_per_page,
            }
            try:
                response = self.fetch(ALGOLIA_API_URL, params=params)
                data = response.json()
            except Exception as e:
                logger.warning(f"[{self.source_name}] Échec Algolia API page {page}: {e}")
                break

            hits = data.get("hits", [])
            if not hits:
                break

            for hit in hits:
                title = hit.get("title")
                object_id = hit.get("objectID")

                if not title or not object_id:
                    continue

                hn_item_url = f"https://news.ycombinator.com/item?id={object_id}"
                external_url = hit.get("url") or hn_item_url
                points = hit.get("points") or 0
                num_comments = hit.get("num_comments") or 0
                author = hit.get("author") or "inconnu"
                story_text = hit.get("story_text") or ""

                # Date de publication
                created_at_str = hit.get("created_at")
                published_date = None
                if created_at_str:
                    try:
                        published_date = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                    except Exception:
                        published_date = None

                # Description synthétique
                if story_text:
                    clean_desc = story_text[:400]
                else:
                    clean_desc = f"Discussion HN par @{author} ({points} pts, {num_comments} comms)."

                # Calcul d'un score initial indicatif (affiné en Phase 4)
                # Pain points (ask_hn) et engagement (points, commentaires)
                base_score = float(points * 1.5 + num_comments * 2.0)
                if self.tag == "ask_hn":
                    base_score += 15.0  # Prime aux questions / expressions de besoins

                items.append({
                    "title": title.strip(),
                    "url": external_url.strip(),
                    "description": clean_desc,
                    "published_date": published_date,
                    "signal_type": self.default_signal_type,
                    "category": self.category,
                    "score": round(base_score, 1),
                    "raw_data": {
                        "hn_id": object_id,
                        "hn_discussion_url": hn_item_url,
                        "points": points,
                        "num_comments": num_comments,
                        "author": author,
                        "tag": self.tag,
                        "api_source": "algolia",
                    },
                })

                if len(items) >= self.max_items:
                    break

            if len(items) >= self.max_items:
                break

        return items

    def _scrape_via_firebase(self) -> list[dict]:
        """Fallback via l'API Firebase officielle de Hacker News."""
        items = []
        endpoint = f"{HN_FIREBASE_BASE_URL}/showstories.json" if self.tag == "show_hn" else f"{HN_FIREBASE_BASE_URL}/askstories.json"
        
        try:
            response = self.fetch(endpoint)
            story_ids = response.json() or []
        except Exception as e:
            logger.error(f"[{self.source_name}] Échec Firebase API: {e}")
            return []

        for story_id in story_ids[:min(self.max_items, 20)]:
            try:
                item_resp = self.fetch(f"{HN_FIREBASE_BASE_URL}/item/{story_id}.json")
                item_data = item_resp.json()
                if not item_data or item_data.get("deleted") or item_data.get("dead"):
                    continue

                title = item_data.get("title", "")
                hn_url = f"https://news.ycombinator.com/item?id={story_id}"
                url = item_data.get("url", hn_url)
                score_pts = item_data.get("score", 0)
                comments_count = len(item_data.get("kids", []))
                time_unix = item_data.get("time")

                pub_date = datetime.utcfromtimestamp(time_unix) if time_unix else None

                items.append({
                    "title": title,
                    "url": url,
                    "description": f"Discussion HN ({score_pts} pts, {comments_count} comms).",
                    "published_date": pub_date,
                    "signal_type": self.default_signal_type,
                    "category": self.category,
                    "score": round(float(score_pts * 1.5 + comments_count * 2.0), 1),
                    "raw_data": {
                        "hn_id": story_id,
                        "hn_discussion_url": hn_url,
                        "points": score_pts,
                        "num_comments": comments_count,
                        "author": item_data.get("by"),
                        "tag": self.tag,
                        "api_source": "firebase",
                    }
                })
            except Exception as item_err:
                logger.warning(f"[{self.source_name}] Erreur item Firebase {story_id}: {item_err}")
                continue

        return items

    def scrape(self) -> list[dict]:
        """Exécute l'extraction avec Algolia et bascule sur Firebase en cas de problème."""
        try:
            items = self._scrape_via_algolia()
            if items:
                return items
        except Exception as e:
            logger.warning(f"[{self.source_name}] Algolia a échoué ({e}), bascule sur Firebase API...")

        return self._scrape_via_firebase()


if __name__ == "__main__":
    connector = HackerNewsConnector(tag="show_hn", max_items=5)
    resultats = connector.scrape()
    print(f"\n[OK] {len(resultats)} opportunites extraites depuis Show HN :\n")
    for r in resultats:
        print(f"* Titre : {r['title']}")
        print(f"  URL   : {r['url']}")
        print(f"  Score : {r['score']} | Signal : {r['signal_type']}")
        print("---")
