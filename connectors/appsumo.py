"""
Connecteur AppSumo Marketplace — Détection des nouveaux deals SaaS et traction précoce.

Source : https://appsumo.com/browse/
Signal métier : "Showcase / Traction précoce"
Extrait les logiciels récemment mis en vente, leurs offres tarifaires et avis clients.
"""

import sys
import json
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

APPSUMO_BROWSE_URL = "https://appsumo.com/browse/"


class AppSumoConnector(BaseConnector):
    source_name = "appsumo"
    category = "saas_tech"
    default_signal_type = "showcase"

    def __init__(self, max_items: int = 25):
        super().__init__()
        self.max_items = max_items

    def scrape(self) -> list[dict]:
        """Extrait les deals logiciels depuis le catalogue public AppSumo."""
        items = []
        try:
            logger.info(f"[{self.source_name}] Récupération des deals SaaS sur AppSumo Marketplace...")
            response = self.fetch(APPSUMO_BROWSE_URL)
            soup = BeautifulSoup(response.text, "html.parser")

            script = soup.find("script", id="__NEXT_DATA__")
            if not script or not script.string:
                logger.warning(f"[{self.source_name}] Balise __NEXT_DATA__ introuvable.")
                return []

            data = json.loads(script.string)
            fbd = data.get("props", {}).get("pageProps", {}).get("fallbackData", [])
            
            deals = []
            if isinstance(fbd, list) and len(fbd) > 0 and isinstance(fbd[0], dict):
                deals = fbd[0].get("deals", [])

            for d in deals[:self.max_items]:
                public_name = d.get("public_name") or d.get("name")
                slug = d.get("slug")
                if not slug:
                    continue

                public_name = public_name or slug.replace("-", " ").title()
                card_desc = d.get("card_description") or d.get("pitch") or ""
                url = f"https://appsumo.com/products/{slug}/"

                price = d.get("price")
                orig_price = d.get("original_price")
                reviews_info = d.get("deal_review") or {}
                review_count = reviews_info.get("review_count", 0) or 0
                avg_rating = reviews_info.get("average_rating", 0.0) or 0.0

                title = f"{public_name} : {card_desc[:75]}" if card_desc else f"AppSumo Deal : {public_name}"
                desc = card_desc if card_desc else f"Logiciel SaaS disponible sur AppSumo (${price} à vie)."
                if price:
                    desc += f" [Offre: ${price} au lieu de ${orig_price}]"

                # Score basé sur la preuve de traction (nombre d'avis et note)
                score = round(float(min(review_count * 0.8, 35.0) + (avg_rating * 3.0 if avg_rating else 12.0) + 15.0), 1)

                items.append({
                    "title": title.strip(),
                    "url": url,
                    "description": desc.strip(),
                    "published_date": datetime.utcnow(),
                    "signal_type": "showcase",
                    "category": self.category,
                    "score": score,
                    "raw_data": {
                        "deal_name": public_name,
                        "slug": slug,
                        "price": price,
                        "original_price": orig_price,
                        "review_count": review_count,
                        "average_rating": avg_rating,
                        "product_tags": d.get("product_tags", []),
                        "source_type": "marketplace_deal",
                    }
                })

            return items
        except Exception as e:
            logger.error(f"[{self.source_name}] Erreur lors de la collecte AppSumo: {e}")
            return []


if __name__ == "__main__":
    connector = AppSumoConnector(max_items=5)
    resultats = connector.scrape()
    print(f"\n[OK] {len(resultats)} deals SaaS extraits depuis AppSumo :\n")
    for r in resultats:
        print(f"* Titre : {r['title']}")
        print(f"  URL   : {r['url']}")
        print(f"  Score : {r['score']} | Signal : {r['signal_type']}")
        print("---")
