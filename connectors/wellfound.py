"""
Connecteur Wellfound (AngelList) — Détection des startups et levées de fonds émergentes.

Source : https://wellfound.com/startups
Signal métier : "Showcase / Levée de fonds & Croissance"
Extrait les profils de startups tech en phase active de recrutement et de développement.
"""

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

WELLFOUND_STARTUPS_URL = "https://wellfound.com/startups"


class WellfoundConnector(BaseConnector):
    source_name = "wellfound"
    category = "saas_tech"
    default_signal_type = "showcase"

    def __init__(self, max_items: int = 20):
        super().__init__()
        self.max_items = max_items

    def scrape(self) -> list[dict]:
        """Extrait les startups en croissance depuis le répertoire public Wellfound."""
        items = []
        try:
            logger.info(f"[{self.source_name}] Récupération des startups sur Wellfound...")
            response = self.fetch(WELLFOUND_STARTUPS_URL)
            soup = BeautifulSoup(response.text, "html.parser")

            links = soup.find_all("a", href=True)
            seen_names = set()

            for a in links:
                href = a["href"]
                if not href.startswith("/company/") or "/jobs" in href:
                    continue

                name = a.get_text(strip=True)
                if not name or len(name) < 2 or name.lower().startswith("view all") or name in seen_names:
                    continue

                seen_names.add(name)
                url = f"https://wellfound.com{href}"

                parent = a.find_parent("div")
                context_text = parent.get_text(separator=" ", strip=True) if parent else ""
                
                title = f"{name} (Startup en croissance)"
                desc = f"Startup tech sur Wellfound : {name}. {context_text[:120]}".strip()
                score = 25.0

                items.append({
                    "title": title,
                    "url": url,
                    "description": desc,
                    "published_date": datetime.utcnow(),
                    "signal_type": "showcase",
                    "category": self.category,
                    "score": score,
                    "raw_data": {
                        "company_name": name,
                        "wellfound_url": url,
                        "source_type": "angel_list_startups",
                    }
                })

                if len(items) >= self.max_items:
                    break

            return items
        except Exception as e:
            logger.error(f"[{self.source_name}] Erreur lors de la collecte Wellfound: {e}")
            return []


if __name__ == "__main__":
    connector = WellfoundConnector(max_items=5)
    resultats = connector.scrape()
    print(f"\n[OK] {len(resultats)} startups extraites depuis Wellfound :\n")
    for r in resultats:
        print(f"* Titre : {r['title']}")
        print(f"  URL   : {r['url']}")
        print(f"  Score : {r['score']} | Signal : {r['signal_type']}")
        print("---")
