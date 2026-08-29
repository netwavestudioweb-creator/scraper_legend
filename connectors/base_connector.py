import time
import logging
import requests
from datetime import datetime
from db.database import get_session
from db.models import Opportunity
from config import SCRAPER_USER_AGENT, SCRAPER_DELAY_SECONDS, SCRAPER_TIMEOUT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseConnector:
    """
    Classe de base pour tous les connecteurs de collecte de signaux.
    Fournit :
    - Sessions HTTP configurées avec User-Agent éthique et timeouts
    - Gestion du rate-limiting et pauses de courtoisie
    - Système de déduplication strict lors de la persistance en base
    """

    source_name = "base"
    category = "saas_tech"
    default_signal_type = "showcase"

    def __init__(self):
        self.session_http = requests.Session()
        self.session_http.headers.update({
            "User-Agent": SCRAPER_USER_AGENT,
            "Accept": "application/json, text/html, application/xhtml+xml, */*",
            "Accept-Language": "fr,en-US;q=0.9,en;q=0.8",
        })

    def fetch(self, url: str, **kwargs):
        """Effectue une requête HTTP avec délai de politesse et gestion de timeout."""
        kwargs.setdefault("timeout", SCRAPER_TIMEOUT)
        try:
            response = self.session_http.get(url, **kwargs)
            response.raise_for_status()
            time.sleep(SCRAPER_DELAY_SECONDS)
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"[{self.source_name}] Erreur HTTP lors de l'appel à {url}: {e}")
            raise

    def scrape(self) -> list[dict]:
        """Méthode à implémenter dans chaque connecteur spécifique."""
        raise NotImplementedError("La méthode 'scrape' doit être définie dans la classe enfant.")

    def save_items(self, items: list[dict]) -> tuple[int, int]:
        """
        Sauvegarde une liste d'opportunités en base de données.
        Applique une déduplication stricte basée sur (source, url).
        Retourne (nombre de nouveaux items, nombre de doublons).
        """
        if not items:
            logger.info(f"[{self.source_name}] Aucun élément à enregistrer.")
            return 0, 0

        db = get_session()
        nb_nouveaux = 0
        nb_doublons = 0

        try:
            for item in items:
                url = item.get("url")
                title = item.get("title")

                if not url or not title:
                    continue

                # Vérification de déduplication
                existe_deja = db.query(Opportunity).filter_by(
                    source=self.source_name,
                    url=url
                ).first()

                if existe_deja:
                    nb_doublons += 1
                    # Mise à jour optionnelle des données brutes récentes si nécessaire
                    if item.get("raw_data"):
                        existe_deja.raw_data = item.get("raw_data")
                    continue

                nouvelle_opportunite = Opportunity(
                    source=self.source_name,
                    category=item.get("category", self.category),
                    signal_type=item.get("signal_type", self.default_signal_type),
                    title=title.strip(),
                    description=item.get("description", "").strip() if item.get("description") else None,
                    url=url.strip(),
                    score=float(item.get("score", 0.0)),
                    status="nouveau",
                    published_date=item.get("published_date"),
                    detected_at=datetime.utcnow(),
                    raw_data=item.get("raw_data", {}),
                    business_case=item.get("business_case", None),
                )
                db.add(nouvelle_opportunite)
                nb_nouveaux += 1

            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"[{self.source_name}] Erreur lors de l'enregistrement en DB: {e}")
            raise
        finally:
            db.close()

        logger.info(f"[{self.source_name}] 💾 {nb_nouveaux} nouvelles opportunités | {nb_doublons} doublons ignorés")
        return nb_nouveaux, nb_doublons

    def run(self) -> tuple[int, int]:
        """Exécute la collecte et enregistre les résultats en base."""
        logger.info(f"[{self.source_name}] 🚀 Démarrage de la collecte...")
        items = self.scrape()
        logger.info(f"[{self.source_name}] 📦 {len(items)} éléments bruts extraits.")
        return self.save_items(items)
