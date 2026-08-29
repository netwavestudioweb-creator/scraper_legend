"""
Connecteur "chasseur de signaux" — Reddit, via l'API officielle (PRAW).

IMPORTANT — nécessite un compte développeur Reddit gratuit:
1. Va sur https://www.reddit.com/prefs/apps
2. Clique "create app" / "create another app"
3. Type: "script"
4. Note le client_id (sous le nom de l'app) et le client_secret
5. Ajoute-les dans ton .env: REDDIT_CLIENT_ID et REDDIT_CLIENT_SECRET

On cible des subreddits où les gens expriment soit une frustration ("plainte"),
soit une recherche active de solution ("demande") — les deux sont des signaux
d'opportunité de produit.
"""

import os
import re
import praw
from datetime import datetime
from connectors.base_connector import BaseConnector
from connectors.translator import traduire_vers_francais

SUBREDDITS_CIBLES = ["SomebodyMakeThis", "AppIdeas", "SideProject", "SaaS", "microsaas", "Entrepreneur"]

# Heuristique simple: mots-clés qui trahissent une plainte vs une demande active.
MOTS_PLAINTE = ["wish", "why isn't there", "why is there no", "annoying", "frustrated", "hate that"]
MOTS_DEMANDE = ["looking for", "does anyone know", "need a tool", "need an app", "is there a"]


def classifier_signal(titre: str) -> str:
    titre_lower = titre.lower()
    if any(mot in titre_lower for mot in MOTS_DEMANDE):
        return "demande"
    if any(mot in titre_lower for mot in MOTS_PLAINTE):
        return "plainte"
    return "demande"  # par défaut, ces subreddits sont orientés "je cherche/j'ai besoin"


class RedditSignalsConnector(BaseConnector):
    source_name = "reddit_signals"
    category = "idee_app"
    region = "autre"
    secteur = "tech"

    def __init__(self, limite_par_subreddit=50):
        super().__init__()
        self.limite = limite_par_subreddit
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent="ScraperLegende/1.0 by NetWaveStudio",
        )

    def scrape(self):
        items = []

        for nom_subreddit in SUBREDDITS_CIBLES:
            try:
                subreddit = self.reddit.subreddit(nom_subreddit)
                posts = subreddit.new(limit=self.limite)
            except Exception as e:
                print(f"⚠️  Impossible d'accéder à r/{nom_subreddit}: {e}")
                continue

            for post in posts:
                titre_original = post.title
                description_originale = post.selftext[:500] if post.selftext else ""

                titre_fr = traduire_vers_francais(titre_original, langue_source="en")
                description_fr = traduire_vers_francais(description_originale, langue_source="en") if description_originale else ""

                items.append({
                    "title": titre_fr,
                    "url": f"https://reddit.com{post.permalink}",
                    "description": description_fr,
                    "published_date": datetime.utcfromtimestamp(post.created_utc),
                    "signal_type": classifier_signal(titre_original),
                    "raw_data": {
                        "subreddit": nom_subreddit,
                        "upvotes": post.score,
                        "num_comments": post.num_comments,
                        "title_original_en": titre_original,
                    },
                })

        return items


if __name__ == "__main__":
    connector = RedditSignalsConnector(limite_par_subreddit=20)
    resultats = connector.scrape()
    print(f"\n{len(resultats)} signaux trouvés:\n")
    for r in resultats[:5]:
        print("Titre  :", r["title"])
        print("Signal :", r["signal_type"])
        print("Sub    :", r["raw_data"]["subreddit"])
        print("---")
