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
        """Extrait les startups récemment soumises sur BetaList avec parsing multi-layout résilient."""
        items = []
        try:
            logger.info(f"[{self.source_name}] Récupération des startups en pré-lancement sur {BETALIST_URL}...")
            response = self.fetch(BETALIST_URL)
            
            status_code = getattr(response, "status_code", 200)
            html_len = len(response.text) if response and response.text else 0
            logger.info(f"[{self.source_name}] Réponse HTTP: {status_code} | Taille HTML: {html_len} octets")

            if not response or not response.text or html_len < 500:
                logger.warning(f"[{self.source_name}] Contenu HTML vide ou trop court ({html_len} octets).")
                return []

            soup = BeautifulSoup(response.text, "html.parser")

            # Recherche de tous les liens pointant vers une startup (/startups/...)
            startup_links = soup.find_all("a", href=True)
            seen_urls = set()

            logger.info(f"[{self.source_name}] Analyse de {len(startup_links)} balises <a> trouvées dans la page...")

            for link in startup_links:
                href = link["href"]
                if not href.startswith("/startups/"):
                    continue

                # Éviter les ancres spéciales ou catégories globales
                clean_href = href.split("?")[0].rstrip("/")
                if clean_href in ("/startups", "/startups/all", "/startups/markets", "/startups/regions"):
                    continue

                url = f"https://betalist.com{clean_href}"
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                name = link.get_text(strip=True)
                pitch = ""

                # Support du DOM moderne Tailwind (overlay absolute inset-0 avec texte dans le conteneur parent)
                parent = link.find_parent("div")
                if parent:
                    parent_text = parent.get_text(separator=" | ", strip=True)
                    parts = [p.strip() for p in parent_text.split("|") if p.strip() and p.strip().upper() not in ("BOOSTED", "FEATURED", "TODAY", "YESTERDAY")]
                    if parts:
                        if not name:
                            name = parts[0]
                        if len(parts) > 1:
                            pitch = " | ".join(parts[1:])

                # Fallback de secours si le nom est manquant : reconstruction via le slug d'URL
                if not name or len(name) < 2:
                    slug = clean_href.replace("/startups/", "").replace("-", " ").strip().title()
                    name = slug or "Startup Inconnue"

                title = f"{name} : {pitch[:90]}" if pitch else name
                description = pitch or f"Startup en phase de pré-lancement sur BetaList : {name}."

                # Métadonnées et scoring
                score = 25.0

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

            logger.info(f"[{self.source_name}] Succès : {len(items)} startups extraites sur {len(seen_urls)} liens uniques.")
            return items

        except Exception as e:
            logger.error(f"[{self.source_name}] Erreur lors de la collecte BetaList: {e}", exc_info=True)
            return []


if __name__ == "__main__":
    connector = BetaListConnector(max_items=10)
    resultats = connector.scrape()
    print(f"\n[OK] {len(resultats)} startups extraites depuis BetaList :\n")
    for r in resultats:
        print(f"* Titre : {r['title']}")
        print(f"  URL   : {r['url']}")
        print(f"  Score : {r['score']} | Signal : {r['signal_type']}")
        print("---")
