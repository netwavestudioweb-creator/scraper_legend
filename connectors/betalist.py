"""
Connecteur BetaList — Détection des startups et SaaS en phase de pré-lancement.

Source : https://betalist.com/
Signal métier : "Showcase / Pré-lancement"
Extrait le nom de la startup, son pitch de valeur, son URL et calcule un score d'opportunité.
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

BETALIST_URL = "https://betalist.com/"


class BetaListConnector(BaseConnector):
    source_name = "betalist"
    category = "saas_tech"
    default_signal_type = "showcase"

    def __init__(self, max_items: int = 25):
        super().__init__()
        self.max_items = max_items

    def scrape(self) -> list[dict]:
        """Extrait les startups récemment soumises sur BetaList."""
        items = []
        try:
            logger.info(f"[{self.source_name}] Récupération des startups en pré-lancement sur BetaList...")
            response = self.fetch(BETALIST_URL)
            soup = BeautifulSoup(response.text, "html.parser")

            # Sélection des liens vers les startups
            startup_links = soup.find_all("a", href=True)
            seen_urls = set()

            for link in startup_links:
                href = link["href"]
                if not href.startswith("/startups/"):
                    continue

                name = link.get_text(strip=True)
                if not name or len(name) < 2:
                    continue

                url = f"https://betalist.com{href}"
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                # Récupération du pitch depuis le conteneur parent
                parent = link.find_parent("div")
                pitch = ""
                if parent:
                    parent_text = parent.get_text(separator=" ", strip=True)
                    # Enlever le nom pour garder le pitch
                    pitch = parent_text.replace(name, "", 1).strip()
                    if pitch.startswith("|") or pitch.startswith("-") or pitch.startswith(":"):
                        pitch = pitch[1:].strip()

                title = f"{name} : {pitch[:80]}" if pitch else name
                description = pitch or f"Startup en phase de pré-lancement sur BetaList : {name}."

                # Score initial pour un produit pré-lancement (signal précoce intéressant)
                score = 22.0

                items.append({
                    "title": title,
                    "url": url,
                    "description": description,
                    "published_date": datetime.utcnow(),
                    "signal_type": "showcase",
                    "category": self.category,
                    "score": score,
                    "raw_data": {
                        "startup_name": name,
                        "pitch": pitch,
                        "betalist_url": url,
                        "stage": "pre_launch",
                    }
                })

                if len(items) >= self.max_items:
                    break

            return items
        except Exception as e:
            logger.error(f"[{self.source_name}] Erreur lors de la collecte BetaList: {e}")
            return []


if __name__ == "__main__":
    connector = BetaListConnector(max_items=5)
    resultats = connector.scrape()
    print(f"\n[OK] {len(resultats)} startups extraites depuis BetaList :\n")
    for r in resultats:
        print(f"* Titre : {r['title']}")
        print(f"  URL   : {r['url']}")
        print(f"  Score : {r['score']} | Signal : {r['signal_type']}")
        print("---")
