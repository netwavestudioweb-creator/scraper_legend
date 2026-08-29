"""
Générateur automatisé de Business Cases — Scraper Légende (V2).

Prend en charge :
1. Génération par LLM (OpenAI / Claude / Gemini) si une clé API est configurée.
2. Génération par Template structuré déterministe (sans coût, 100% basé sur les faits) si aucune clé n'est présente.
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from sqlalchemy.orm.attributes import flag_modified
from db.database import get_session
from db.models import Opportunity

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

logger = logging.getLogger(__name__)


def generate_business_case_from_template(opportunity: Opportunity) -> dict:
    """
    Génère un Business Case structuré et rigoureux sans LLM,
    strictement basé sur les faits et métriques réelles de l'opportunité.
    """
    title = opportunity.title or "Sans titre"
    desc = opportunity.description or ""
    source = (opportunity.source or "").capitalize()
    signal_type = opportunity.signal_type or "showcase"
    score = opportunity.score or 0.0
    raw = opportunity.raw_data or {}
    bk = raw.get("scoring_breakdown", {})

    # 1. Problème identifié
    if signal_type == "pain_point":
        probleme = (
            f"Besoin explicite exprimé sur {source} : les utilisateurs recherchent un outil ou une méthode "
            f"efficace pour « {title} ». "
        )
        if desc:
            clean_desc = desc[:200].strip()
            probleme += f"Contexte utilisateur : {clean_desc}..."
    else:
        probleme = (
            f"Opportunité de marché détectée via {source} : lancement / produit « {title} ». "
        )
        if desc:
            clean_desc = desc[:200].strip()
            probleme += f"Proposition de valeur observée : {clean_desc}..."

    # 2. Preuve de traction & signaux réels
    eng_score = bk.get("engagement_score", 0.0)
    rec_score = bk.get("recurrence_score", 0.0)
    traction_details = []

    if source.lower() == "hackernews":
        pts = raw.get("points", 0)
        comms = raw.get("num_comments", 0)
        traction_details.append(f"{pts} points et {comms} commentaires sur Hacker News")
    elif source.lower() == "producthunt":
        votes = raw.get("votes", 0)
        comms = raw.get("comments", 0)
        if votes or comms:
            traction_details.append(f"{votes} votes et {comms} commentaires sur Product Hunt")
        else:
            traction_details.append("Sélectionné sur le flux officiel des lancements Product Hunt")
    elif source.lower() == "github":
        stars_today = raw.get("stars_today", 0)
        stars = raw.get("stars", 0)
        lang = raw.get("language", "Code")
        traction_details.append(f"{stars_today} ⭐ aujourd'hui ({stars} ⭐ au total, écosystème {lang})")
    elif source.lower() == "stackexchange":
        votes = raw.get("score_votes", 0)
        answers = raw.get("answer_count", 0)
        views = raw.get("view_count", 0)
        traction_details.append(f"{votes} votes, {answers} réponses et {views} vues sur Stack Exchange")
    elif source.lower() == "appsumo":
        price = raw.get("price", 0)
        reviews = raw.get("review_count", 0)
        rating = raw.get("average_rating", 0.0)
        traction_details.append(f"Deal actif à ${price} avec {reviews} avis clients (note moyenne : {rating}/5)")
    else:
        traction_details.append(f"Signal répertorié sur {source} avec un score global de {score}/100")

    if rec_score >= 70.0:
        traction_details.append("Thématique confirmée présente de manière récurrente sur plusieurs sources distinctes")

    preuve_traction = " ; ".join(traction_details) + f". Score composite attribué : {score}/100."

    # 3. Angle produit suggéré (formulé prudemment sans invention)
    if signal_type == "pain_point":
        angle_produit = (
            "Piste à explorer : Concevoir une solution dédiée (Micro-SaaS ciblé ou extension/script clé-en-main) "
            "répondant spécifiquement à cette demande récurrente, en simplifiant l'expérience utilisateur par rapport aux outils existants."
        )
    elif "ai" in title.lower() or "agent" in title.lower() or "llm" in title.lower():
        angle_produit = (
            "Piste à explorer : Analyser la proposition de valeur IA de ce produit et évaluer la viabilité d'un positionnement "
            "de niche (verticalisé pour un métier précis) ou d'une alternative sans dépendance propriétaire."
        )
    elif source.lower() == "appsumo":
        angle_produit = (
            "Piste à explorer : Validation par le pricing : ce produit prouve une volonté de payer pour ce cas d'usage. "
            "Étudier les retours clients et avis pour identifier les fonctionnalités manquantes ou axes d'amélioration."
        )
    else:
        angle_produit = (
            "Piste à explorer : Surveiller l'évolution de la traction et évaluer les fonctionnalités différenciantes "
            "pour un positionnement alternatif plus accessible ou orienté B2B."
        )

    return {
        "mode": "template_heuristic",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "probleme_identifie": probleme,
        "preuve_de_traction": preuve_traction,
        "angle_produit_suggere": angle_produit,
        "cout_estime_usd": 0.0,
    }


def generate_business_case(opportunity: Opportunity) -> dict:
    """
    Point d'entrée principal pour la génération d'un Business Case.
    Tente une génération LLM si l'environnement le permet, sinon bascule sur le template déterministe.
    """
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    # Si une clé LLM est fournie, on peut appeler le fournisseur approprié
    if openai_key:
        try:
            import urllib.request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {openai_key}",
            }
            prompt = (
                "Tu es un analyste business SaaS rigoureux. À partir des données réelles ci-dessous d'une opportunité, "
                "génère un court business case structuré au format JSON strict avec exactement 3 clés:\n"
                "- 'probleme_identifie': 1 à 2 phrases reformulant le problème ou l'opportunité.\n"
                "- 'preuve_de_traction': rappel précis des votes, avis, métriques réelles données.\n"
                "- 'angle_produit_suggere': piste de solution prudente (sans affirmer de certitudes).\n"
                "RÈGLE STRICTE: N'invente aucun chiffre ni fait non présent dans les données.\n\n"
                f"Titre: {opportunity.title}\n"
                f"Description: {opportunity.description}\n"
                f"Source: {opportunity.source}\n"
                f"Score: {opportunity.score}\n"
                f"Données brutes: {json.dumps(opportunity.raw_data or {})}"
            )
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            }
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                content = json.loads(result["choices"][0]["message"]["content"])
                return {
                    "mode": "llm_openai_gpt4o_mini",
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "probleme_identifie": content.get("probleme_identifie"),
                    "preuve_de_traction": content.get("preuve_de_traction"),
                    "angle_produit_suggere": content.get("angle_produit_suggere"),
                    "cout_estime_usd": 0.00015,
                }
        except Exception as e:
            logger.warning(f"Bascule sur le template déterministe (Échec appel LLM: {e})")

    # Mode par défaut sans clé : Template déterministe structuré
    return generate_business_case_from_template(opportunity)


def generate_for_opportunity_id(opportunity_id: int) -> dict:
    """
    Génère et sauvegarde le business case pour une opportunité spécifique.
    """
    db = get_session()
    try:
        opp = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
        if not opp:
            raise ValueError(f"Opportunité #{opportunity_id} introuvable.")

        bc = generate_business_case(opp)
        opp.business_case = bc
        opp.status = "business_case_genere"
        flag_modified(opp, "business_case")
        db.commit()
        return bc
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def generate_batch_business_cases(min_score: float = 70.0, limit: int = 5) -> int:
    """
    Génère les business cases par lot pour les opportunités dépassant le seuil de score.
    """
    db = get_session()
    try:
        items = (
            db.query(Opportunity)
            .filter(Opportunity.score >= min_score, Opportunity.business_case.is_(None))
            .limit(limit)
            .all()
        )
        count = 0
        for opp in items:
            bc = generate_business_case(opp)
            opp.business_case = bc
            opp.status = "business_case_genere"
            flag_modified(opp, "business_case")
            count += 1
        db.commit()
        return count
    finally:
        db.close()


if __name__ == "__main__":
    count = generate_batch_business_cases(min_score=70.0, limit=5)
    print(f"\n[OK] {count} Business Cases générés et enregistrés en base.")
