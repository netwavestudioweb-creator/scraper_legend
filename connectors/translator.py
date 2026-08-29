"""
Utilitaire de traduction — traduit vers le français par défaut.
Utilise deep-translator (gratuit, sans clé API, s'appuie sur Google Translate).

Si le service de traduction est indisponible (pas de connexion, quota, etc.),
on retombe silencieusement sur le texte original pour ne jamais faire planter
un scraping entier à cause d'un simple souci de traduction.
"""

from deep_translator import GoogleTranslator


def traduire_vers_francais(texte: str, langue_source: str = "auto") -> str:
    """
    Traduit un texte vers le français. Retourne le texte original si:
    - le texte est vide/None
    - la traduction échoue (pas de connexion, texte déjà en français, etc.)
    - le texte dépasse la limite de l'API (5000 caractères), on tronque avant.
    """
    if not texte or not texte.strip():
        return texte

    try:
        texte_a_traduire = texte[:4900]  # marge de sécurité sous la limite de 5000
        traduction = GoogleTranslator(source=langue_source, target="fr").translate(texte_a_traduire)
        return traduction or texte
    except Exception as e:
        print(f"⚠️  Traduction échouée ({e}), texte original conservé")
        return texte
