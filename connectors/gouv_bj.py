"""
Connecteur pour gouv.bj — Offres d'emploi officielles du Bénin.

IMPORTANT — à lire avant de lancer:
Je n'ai pu inspecter cette page qu'à travers un rendu texte/markdown (pas le HTML brut),
donc les sélecteurs ci-dessous sont construits sur le pattern d'URL observé
(/opportunite/<id>/<slug>/) qui est fiable, MAIS le parsing de la date de clôture
et de la catégorie (CDD/Avis général) est une estimation à vérifier.

Avant le premier run réel: lance `python -m connectors.gouv_bj` seul, regarde
les 3-4 premiers résultats affichés, et ajuste la fonction `extraire_details_offre`
si la date ou la catégorie ne sortent pas correctement. Dis-moi ce que tu vois
et je corrige le sélecteur avec toi.
"""

import re
from datetime import datetime
from bs4 import BeautifulSoup
from connectors.base_connector import BaseConnector

BASE_URL = "https://www.gouv.bj"
LISTING_URL = "https://www.gouv.bj/opportunites/offres-emploi/"

# Pattern des liens vers une offre individuelle, ex: /opportunite/184/avis-recrutement.../
# ou https://www.gouv.bj/opportunite/184/avis-recrutement.../ (le site utilise des URLs absolues)
PATTERN_LIEN_OFFRE = re.compile(r"^(https://www\.gouv\.bj)?/opportunite/\d+/")

# Le site affiche les dates en abréviations ANGLAISES (Jan, Feb, Mar, Apr, May, Jun,
# Jul, Aug, Sep, Oct, Nov, Dec) même si le contenu textuel est en français.
# Constaté en inspectant les vraies pages : "24 Jul 2026", "20 Apr 2025", "07 Nov 2024".
MOIS_EN = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def parser_date_cloture(texte: str):
    """Cherche un pattern 'Clôture : 17 Jul 2026' dans le texte et le convertit en datetime."""
    match = re.search(r"Clôture\s*:\s*(\d{1,2})\s+(\w+)\s+(\d{4})", texte)
    if not match:
        return None
    jour, mois_txt, annee = match.groups()
    mois_num = MOIS_EN.get(mois_txt.lower()[:3], None)
    if not mois_num:
        return None
    try:
        return datetime(int(annee), mois_num, int(jour))
    except ValueError:
        return None


class GouvBjConnector(BaseConnector):
    source_name = "gouv_bj"
    category = "emploi"
    region = "afrique"

    def scrape(self, max_pages=3):
        return self._scrape_listing(LISTING_URL, max_pages)

    def _scrape_listing(self, listing_url, max_pages):
        items = []
        page = 1
        url = listing_url

        while page <= max_pages:
            response = self.fetch(url)
            soup = BeautifulSoup(response.text, "lxml")

            liens_offres = soup.find_all("a", href=PATTERN_LIEN_OFFRE)
            if not liens_offres:
                break  # plus rien à scraper, on arrête

            urls_deja_vues = set()

            for lien in liens_offres:
                titre = lien.get_text(strip=True)
                href = lien.get("href")
                url_complete = href if href.startswith("http") else BASE_URL + href

                # Chaque offre a 2 liens vers la même URL: le titre ET "En savoir plus".
                # On ne garde que la première occurrence (le titre), on ignore le doublon.
                if url_complete in urls_deja_vues:
                    continue
                urls_deja_vues.add(url_complete)

                # Le lien "En savoir plus" n'a pas de vrai titre, on l'ignore par sécurité
                if titre.lower() in ("en savoir plus", "voir plus", "lire la suite"):
                    continue

                # Le bloc parent contient souvent la description + la date de clôture à côté
                bloc_parent = lien.find_parent(["article", "div", "li"]) or lien.parent
                texte_bloc = bloc_parent.get_text(" ", strip=True) if bloc_parent else ""

                items.append({
                    "title": titre,
                    "url": url_complete,
                    "description": texte_bloc[:500] if texte_bloc else None,
                    "closing_date": parser_date_cloture(texte_bloc),
                    "raw_data": {"page": page},
                })

            # Pagination générique basée sur l'URL de listing passée en paramètre
            page += 1
            url = f"{listing_url}{page}/"

        return items


class GouvBjMarchesPublicsConnector(GouvBjConnector):
    """
    Marchés publics — un appel d'offre révèle un besoin institutionnel réel,
    c'est un signal 'ecart_offre' pour le secteur administratif.
    """
    source_name = "gouv_bj_marches"
    category = "marche_public"
    region = "afrique"
    secteur = "administratif"

    def scrape(self, max_pages=2):
        url_marches = f"{BASE_URL}/opportunites/marches-publics/"
        items = self._scrape_listing(url_marches, max_pages)
        for item in items:
            item["signal_type"] = "ecart_offre"
        return items


if __name__ == "__main__":
    # Test rapide en standalone: affiche les résultats SANS les sauvegarder en DB,
    # pour que tu puisses vérifier que le parsing est correct avant le vrai run.
    connector = GouvBjConnector()
    resultats = connector.scrape(max_pages=1)
    print(f"\n{len(resultats)} offres trouvées sur la page 1:\n")
    for r in resultats[:5]:
        print("Titre    :", r["title"])
        print("URL      :", r["url"])
        print("Clôture  :", r["closing_date"])
        print("---")
