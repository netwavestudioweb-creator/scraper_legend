"""
Connecteur "chasseur de signaux" — Avis Google Play sur des apps santé Afrique/Bénin.

Objectif: repérer les avis 1-2 étoiles qui décrivent un problème concret non résolu
par les solutions existantes (= opportunité de faire mieux).

Utilise google-play-scraper (package Python très utilisé, lit les pages publiques
du Play Store — les mêmes infos que n'importe qui peut voir en visitant la fiche
d'une app). Aucune authentification, aucune donnée personnelle identifiable
(les avis Play Store sont déjà anonymisés par pseudonyme côté Google).
"""

from datetime import datetime
from google_play_scraper import reviews, Sort
from connectors.base_connector import BaseConnector
from connectors.translator import traduire_vers_francais

# Apps santé ciblées: mix Bénin/Afrique (marché local, peu de concurrence, entrée facile)
# + standards internationaux (pour comparer et viser un produit vendable plus large).
# Ajoute d'autres app_id ici au fur et à mesure de tes découvertes.
APPS_SANTE_CIBLES = {
    "co.opensi.medical": "goMediCAL (Bénin)",
    "com.app.benincare": "BeninCare (Afrique)",
    "com.esantebdi.e_sante_bdi": "E-Santé Bdi",
    "com.karmamobile": "Qare (France/international — benchmark standard)",
}

# En dessous de ce nombre d'étoiles, on considère l'avis comme un signal de problème
SEUIL_NOTE_PROBLEME = 2


class PlayStoreSanteConnector(BaseConnector):
    source_name = "playstore_sante"
    category = "avis_app"
    region = "afrique"
    secteur = "sante"

    def scrape(self, nb_avis_par_app=100):
        items = []

        for app_id, nom_app in APPS_SANTE_CIBLES.items():
            try:
                resultats, _ = reviews(
                    app_id,
                    lang="fr",
                    country="bj",
                    sort=Sort.NEWEST,
                    count=nb_avis_par_app,
                )
            except Exception as e:
                print(f"⚠️  Impossible de récupérer les avis pour {nom_app} ({app_id}): {e}")
                continue

            for avis in resultats:
                note = avis.get("score", 5)
                contenu = avis.get("content", "")

                if not contenu or note > SEUIL_NOTE_PROBLEME:
                    continue  # on ne garde que les avis négatifs = signaux de problème

                date_avis = avis.get("at")

                items.append({
                    "title": f"[{note}★] {nom_app} — {contenu[:80]}",
                    "url": f"https://play.google.com/store/apps/details?id={app_id}",
                    "description": contenu[:500],
                    "published_date": date_avis if isinstance(date_avis, datetime) else None,
                    "signal_type": "solution_mal_notee",
                    "raw_data": {
                        "app_id": app_id,
                        "app_nom": nom_app,
                        "note": note,
                        "avis_id": avis.get("reviewId"),
                    },
                })

        return items


if __name__ == "__main__":
    connector = PlayStoreSanteConnector()
    resultats = connector.scrape(nb_avis_par_app=50)
    print(f"\n{len(resultats)} avis négatifs (signaux) trouvés:\n")
    for r in resultats[:5]:
        print("Titre  :", r["title"])
        print("Note   :", r["raw_data"]["note"])
        print("---")
