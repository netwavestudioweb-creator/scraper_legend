"""
Connecteur Stack Exchange (Software Recommendations).

Détecte les expressions directes de besoins et demandes de logiciels / outils
formulées publiquement par des utilisateurs cherchant une solution à un problème précis.

API utilisée :
- Endpoint officiel : https://api.stackexchange.com/2.3/questions
- Site cible : softwarerecs (Software Recommendations)
- Filtre : withbody (inclus le corps de la demande)
"""

import os
import sys
import html
import time
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

STACKEXCHANGE_API_URL = "https://api.stackexchange.com/2.3/questions"


class StackExchangeConnector(BaseConnector):
    source_name = "stackexchange"
    category = "saas_tech"
    default_signal_type = "pain_point"

    def __init__(self, site: str = "softwarerecs", max_items: int = 25):
        super().__init__()
        self.site = site
        self.max_items = max_items
        self.api_key = os.getenv("STACKEXCHANGE_KEY", "").strip()

    def scrape(self) -> list[dict]:
        """Extrait les questions récentes de recherche de logiciels avec leur corps de texte."""
        items = []
        params = {
            "site": self.site,
            "order": "desc",
            "sort": "activity",
            "pagesize": min(self.max_items, 50),
            "filter": "withbody",
        }

        if self.api_key:
            params["key"] = self.api_key

        try:
            logger.info(f"[{self.source_name}] Récupération des demandes d'outils sur {self.site}...")
            response = self.fetch(STACKEXCHANGE_API_URL, params=params)
            data = response.json()

            # Gestion du backoff imposé par Stack Exchange si présent
            if "backoff" in data:
                backoff_time = int(data["backoff"])
                logger.warning(f"[{self.source_name}] Stack Exchange demande une pause (backoff: {backoff_time}s)")
                time.sleep(backoff_time)

            questions = data.get("items", [])

            for q in questions:
                raw_title = q.get("title", "")
                if not raw_title:
                    continue

                clean_title = html.unescape(raw_title).strip()
                url = q.get("link", "")
                if not url:
                    continue

                # Extraction propre du corps de la demande (besoin exprimé)
                raw_body = q.get("body", "")
                clean_body = ""
                if raw_body:
                    soup = BeautifulSoup(raw_body, "html.parser")
                    clean_body = soup.get_text(separator=" ", strip=True)

                q_score = q.get("score", 0)
                answer_count = q.get("answer_count", 0)
                view_count = q.get("view_count", 0)
                tags = q.get("tags", [])
                creation_date_unix = q.get("creation_date")

                pub_date = datetime.utcfromtimestamp(creation_date_unix) if creation_date_unix else None

                # Calcul du score d'opportunité :
                # Les demandes sans solution acceptée (is_answered = False) ou à fort trafic/vues représentent une opportunité plus forte
                is_answered = q.get("is_answered", False)
                base_opportunity_score = 25.0  # Prime de base car il s'agit d'un besoin explicite
                base_opportunity_score += float(q_score * 1.5 + answer_count * 2.0 + min(view_count * 0.02, 30.0))
                if not is_answered:
                    base_opportunity_score += 10.0  # Problème toujours non résolu de façon satisfaisante

                owner = q.get("owner", {})
                author = owner.get("display_name", "anonyme")

                items.append({
                    "title": clean_title,
                    "url": url,
                    "description": clean_body[:400] if clean_body else f"Recherche de logiciel sur {self.site} (tags: {', '.join(tags)}).",
                    "published_date": pub_date,
                    "signal_type": self.default_signal_type,
                    "category": self.category,
                    "score": round(base_opportunity_score, 1),
                    "raw_data": {
                        "site": self.site,
                        "question_id": q.get("question_id"),
                        "tags": tags,
                        "score_votes": q_score,
                        "answer_count": answer_count,
                        "view_count": view_count,
                        "is_answered": is_answered,
                        "author": author,
                        "api_mode": "stackexchange_public_api",
                    }
                })

                if len(items) >= self.max_items:
                    break

            return items
        except Exception as e:
            logger.error(f"[{self.source_name}] Erreur lors de la récupération Stack Exchange: {e}")
            return []


if __name__ == "__main__":
    connector = StackExchangeConnector(max_items=5)
    resultats = connector.scrape()
    print(f"\n[OK] {len(resultats)} demandes d'outils extraites depuis Stack Exchange :\n")
    for r in resultats:
        print(f"* Titre : {r['title']}")
        print(f"  URL   : {r['url']}")
        print(f"  Score : {r['score']} | Signal : {r['signal_type']}")
        print(f"  Tags  : {r['raw_data']['tags']}")
        print("---")
