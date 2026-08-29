"""
Connecteur RemoteOK — offres d'emploi remote internationales.

Utilise l'API JSON officielle et publique de RemoteOK (remoteok.com/api),
gratuite, sans clé, sans authentification. Élargit la zone au-delà du Bénin:
c'est un marché mondial, utile pour repérer les compétences/outils demandés
(signal indirect: si 50 boîtes cherchent un "Python + Stripe integration",
il y a peut-être un outil à construire pour simplifier ça).
"""

from datetime import datetime
from connectors.base_connector import BaseConnector

API_URL = "https://remoteok.com/api"


class RemoteOkConnector(BaseConnector):
    source_name = "remoteok"
    category = "emploi"
    region = "autre"  # portée internationale
    secteur = "tech"

    def scrape(self):
        items = []

        response = self.fetch(API_URL)
        data = response.json()

        # Le premier élément de la réponse RemoteOK est toujours des métadonnées, pas une offre
        offres = [d for d in data if isinstance(d, dict) and d.get("id")]

        for offre in offres:
            titre = offre.get("position") or offre.get("title")
            entreprise = offre.get("company")
            url = offre.get("url")

            if not titre or not url:
                continue

            date_pub = offre.get("date")
            date_publication = None
            if date_pub:
                try:
                    date_publication = datetime.fromisoformat(date_pub.replace("Z", "+00:00"))
                except ValueError:
                    pass

            titre_complet = f"{titre} — {entreprise}" if entreprise else titre

            items.append({
                "title": titre_complet,
                "url": url,
                "description": (offre.get("description") or "")[:500],
                "published_date": date_publication,
                "signal_type": "demande",
                "raw_data": {
                    "company": entreprise,
                    "tags": offre.get("tags", []),
                    "salary_min": offre.get("salary_min"),
                    "salary_max": offre.get("salary_max"),
                    "location": offre.get("location"),
                },
            })

        return items


if __name__ == "__main__":
    connector = RemoteOkConnector()
    resultats = connector.scrape()
    print(f"\n{len(resultats)} offres remote trouvées:\n")
    for r in resultats[:5]:
        print("Titre  :", r["title"])
        print("Tags   :", r["raw_data"]["tags"])
        print("---")
