import sys
import logging
from config import DATABASE_URL
from db.database import init_db
from connectors.hackernews import HackerNewsConnector
from connectors.producthunt import ProductHuntConnector
from connectors.github_trending import GitHubTrendingConnector
from connectors.stackexchange import StackExchangeConnector
from connectors.betalist import BetaListConnector
from connectors.appsumo import AppSumoConnector
from connectors.wellfound import WellfoundConnector
from connectors.reddit import RedditConnector
from core.scoring import recalculate_all_scores

# Configuration propre de l'encodage console Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("main")


def run_all():
    """
    Orchestrateur principal :
    1. Initialise la base de données (PostgreSQL ou SQLite fallback).
    2. Exécute la collecte séquentielle sur les 7 connecteurs actifs.
    3. Exécute le calcul de scoring multicritère sur l'ensemble de la base.
    4. Affiche le bilan consolidé.
    """
    print("\n" + "=" * 65)
    print(">> SCRAPER LEGENDE (V2) - MOTEUR DE VEILLE & SCORING MULTI-SOURCES")
    print("=" * 65 + "\n")

    # Initialisation de la BDD
    init_db()

    # Liste des 7 sources actives de collecte
    connecteurs = [
        # Sources par API officielle (Phases 1 & 2)
        HackerNewsConnector(tag="show_hn", max_items=25),       # Show HN : Lancement de projets
        HackerNewsConnector(tag="ask_hn", max_items=15),        # Ask HN : Problèmes & pain points
        ProductHuntConnector(max_items=20),                     # Product Hunt : Lancements officiels
        GitHubTrendingConnector(max_items=20),                  # GitHub Trending : Micro-SaaS & IA
        StackExchangeConnector(site="softwarerecs", max_items=20), # Stack Exchange : Recherche d'outils
        
        # Sources par scraping léger & éthique (Phase 3)
        BetaListConnector(max_items=20),                        # BetaList : Startups en pré-lancement
        AppSumoConnector(max_items=20),                         # AppSumo : Deals SaaS & traction
        WellfoundConnector(max_items=15),                       # Wellfound : Startups en croissance
        
        # En attente d'approbation formelle :
        # RedditConnector()  (Responsible Builder Policy 2026)
    ]

    total_nouveaux = 0
    total_doublons = 0
    statistiques_sources = {}

    for connecteur in connecteurs:
        nom_source = connecteur.source_name
        if hasattr(connecteur, "tag"):
            nom_source = f"{nom_source} ({connecteur.tag})"

        try:
            nouveaux, doublons = connecteur.run()
            total_nouveaux += nouveaux
            total_doublons += doublons
            statistiques_sources[nom_source] = {
                "nouveaux": nouveaux,
                "doublons": doublons,
                "statut": "[OK] Succes" if (nouveaux > 0 or doublons > 0) else "[INFO] 0 element"
            }
        except Exception as e:
            logger.error(f"[ERREUR] Echec sur {nom_source}: {e}")
            statistiques_sources[nom_source] = {
                "nouveaux": 0,
                "doublons": 0,
                "statut": f"[ERREUR] ({e})"
            }

    # Calcul et actualisation automatique des scores multicritères
    print("\n" + "-" * 65)
    print("📐 ACTUALISATION DU SCORING MULTICRITÈRE...")
    print("-" * 65)
    nb_scores = recalculate_all_scores()

    print("\n" + "=" * 65)
    print("BILAN DE LA COLLECTE & DU SCORING (7 CONNECTEURS ACTIFS)")
    print("=" * 65)
    for src, stats in statistiques_sources.items():
        print(f" * {src:<32} : {stats['nouveaux']} nouveaux | {stats['doublons']} doublons | {stats['statut']}")
    print("-" * 65)
    print(f"Total opportunités enregistrées : {total_nouveaux} nouvelles | {total_doublons} doublons ignorés")
    print(f"Total opportunités scorées      : {nb_scores} opportunités qualifiées")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_all()
