"""
Connecteur GitHub Trending & Repositories Émergents.

Détecte les nouveaux projets open-source, outils d'automatisation, micro-SaaS
et agents IA gagnant rapidement en popularité.

Méthodes :
1. Scraping léger de la page officielle GitHub Trending (tendances quotidiennes)
2. API GitHub REST Search (dépôts récents sur les thématiques saas, automation, ai-agent)
"""

import os
import re
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

GITHUB_TRENDING_URL = "https://github.com/trending"
GITHUB_SEARCH_API_URL = "https://api.github.com/search/repositories"


class GitHubTrendingConnector(BaseConnector):
    source_name = "github"
    category = "saas_tech"
    default_signal_type = "showcase"

    def __init__(self, max_items: int = 25):
        super().__init__()
        self.max_items = max_items
        self.github_token = os.getenv("GITHUB_TOKEN", "").strip()

    def _scrape_trending_page(self) -> list[dict]:
        """Extrait les dépôts en tendance du jour depuis la page GitHub Trending."""
        items = []
        try:
            logger.info(f"[{self.source_name}] Extraction depuis la page GitHub Trending...")
            response = self.fetch(GITHUB_TRENDING_URL)
            soup = BeautifulSoup(response.text, "html.parser")
            rows = soup.select("article.Box-row")

            for row in rows[:self.max_items]:
                title_elem = row.select_one("h2 a")
                if not title_elem:
                    continue

                repo_path = title_elem.get_text().strip().replace("\n", "").replace(" ", "")
                repo_url = f"https://github.com/{repo_path}"
                
                # Description
                desc_elem = row.select_one("p")
                description = desc_elem.get_text().strip() if desc_elem else "Dépôt GitHub en tendance"

                # Langage
                lang_elem = row.select_one("[itemprop='programmingLanguage']")
                language = lang_elem.get_text().strip() if lang_elem else "Inconnu"

                # Étoiles aujourd'hui & total
                stars_today_elem = row.select_one("span.d-inline-block.float-sm-right")
                stars_today_text = stars_today_elem.get_text().strip() if stars_today_elem else ""
                
                # Extraction du nombre d'étoiles aujourd'hui
                stars_today = 0
                digits = re.findall(r"[\d,]+", stars_today_text)
                if digits:
                    try:
                        stars_today = int(digits[0].replace(",", ""))
                    except ValueError:
                        stars_today = 0

                # Score basé sur la vélocité d'étoiles (ex: 50 étoiles aujourd'hui -> score élevé)
                score = round(max(15.0, float(stars_today * 0.8)), 1)

                items.append({
                    "title": f"{repo_path} : {description[:80]}",
                    "url": repo_url,
                    "description": f"[{language}] {description}",
                    "published_date": datetime.utcnow(),
                    "signal_type": self.default_signal_type,
                    "category": self.category,
                    "score": score,
                    "raw_data": {
                        "repo_name": repo_path,
                        "language": language,
                        "stars_today": stars_today,
                        "stars_today_raw": stars_today_text,
                        "api_mode": "trending_html",
                    }
                })

            return items
        except Exception as e:
            logger.warning(f"[{self.source_name}] Échec scraping Trending ({e}), bascule sur l'API Search...")
            return []

    def _scrape_search_api(self) -> list[dict]:
        """Extrait les dépôts récents axés SaaS & automatisation via l'API Search GitHub."""
        items = []
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        params = {
            "q": "topic:saas OR topic:automation OR topic:micro-saas stars:>10",
            "sort": "updated",
            "order": "desc",
            "per_page": min(self.max_items, 30),
        }

        try:
            logger.info(f"[{self.source_name}] Recherche de dépôts SaaS/Automation via l'API Search...")
            response = self.fetch(GITHUB_SEARCH_API_URL, headers=headers, params=params)
            data = response.json()
            repos = data.get("items", [])

            for repo in repos:
                full_name = repo.get("full_name", "")
                html_url = repo.get("html_url", "")
                description = repo.get("description") or "Dépôt SaaS/Automation"
                stars = repo.get("stargazers_count", 0)
                forks = repo.get("forks_count", 0)
                language = repo.get("language") or "Code"
                created_at = repo.get("created_at")

                pub_date = None
                if created_at:
                    try:
                        pub_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    except Exception:
                        pub_date = None

                score = round(float(stars * 0.5 + forks * 1.5 + 10.0), 1)

                items.append({
                    "title": f"{full_name} : {description[:80]}",
                    "url": html_url,
                    "description": f"[{language}] {description} (⭐ {stars} | 🍴 {forks})",
                    "published_date": pub_date,
                    "signal_type": self.default_signal_type,
                    "category": self.category,
                    "score": score,
                    "raw_data": {
                        "repo_name": full_name,
                        "language": language,
                        "stars": stars,
                        "forks": forks,
                        "topics": repo.get("topics", []),
                        "api_mode": "github_search_api",
                    }
                })

            return items
        except Exception as e:
            logger.error(f"[{self.source_name}] Erreur API Search GitHub: {e}")
            return []

    def scrape(self) -> list[dict]:
        """Combine les dépôts Trending et les résultats Search SaaS."""
        items = self._scrape_trending_page()
        if len(items) < self.max_items:
            search_items = self._scrape_search_api()
            # Fusion sans doublons d'URL
            urls_connues = {it["url"] for it in items}
            for it in search_items:
                if it["url"] not in urls_connues and len(items) < self.max_items:
                    items.append(it)
                    urls_connues.add(it["url"])
        return items


if __name__ == "__main__":
    connector = GitHubTrendingConnector(max_items=5)
    resultats = connector.scrape()
    print(f"\n[OK] {len(resultats)} opportunites extraites depuis GitHub :\n")
    for r in resultats:
        print(f"* Titre : {r['title']}")
        print(f"  URL   : {r['url']}")
        print(f"  Score : {r['score']} | Signal : {r['signal_type']}")
        print("---")
