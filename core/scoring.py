"""
Moteur de Scoring Multicritère — Scraper Légende (V2).

Formule :
Score = 0.40 * Engagement + 0.20 * Fraîcheur + 0.25 * Signal + 0.15 * Récurrence
Échelle normalisée : 0 à 100 points.
"""

import re
import sys
import copy
import logging
from datetime import datetime, timezone
from collections import defaultdict
from sqlalchemy.orm.attributes import flag_modified
from db.database import get_session
from db.models import Opportunity

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

logger = logging.getLogger(__name__)

# Mots-clés thématiques pour la détection de tendances transversales
TRACKED_KEYWORDS = [
    "ai", "agent", "llm", "automation", "pdf", "markdown", "dashboard",
    "scraper", "scraping", "api", "saas", "converter", "video", "image",
    "editor", "crm", "workflow", "testing", "monitoring", "analytics",
    "invoice", "scheduler", "seo", "extension", "proxy", "email"
]

# Mots-clés de douleurs explicites
PAIN_KEYWORDS = [
    "looking for", "alternative", "frustrated", "pain point", "is there a tool",
    "is there an app", "how to automate", "struggling", "tired of", "need a tool",
    "recommend", "problem with"
]


def extract_keywords(text: str) -> set:
    """Extrait les mots-clés thématiques présents dans un texte."""
    if not text:
        return set()
    cleaned = re.sub(r"[^\w\s-]", " ", text.lower())
    words = set(cleaned.split())
    found = set()
    for kw in TRACKED_KEYWORDS:
        if kw in cleaned or kw in words:
            found.add(kw)
    return found


def compute_engagement_score(source: str, raw_data: dict) -> float:
    """
    Normalise l'engagement sur une échelle de 0 à 100 selon la source.
    """
    raw_data = raw_data or {}
    source = (source or "").lower()

    if source == "hackernews":
        points = float(raw_data.get("points") or 0)
        comments = float(raw_data.get("num_comments") or 0)
        raw_val = (points * 1.5) + (comments * 2.5)
        return min(100.0, max(20.0, raw_val))

    elif source == "producthunt":
        votes = float(raw_data.get("votes") or 0)
        comments = float(raw_data.get("comments") or 0)
        if votes > 0 or comments > 0:
            raw_val = (votes * 1.2) + (comments * 2.0)
            return min(100.0, max(25.0, raw_val))
        return 35.0

    elif source == "github":
        stars_today = float(raw_data.get("stars_today") or 0)
        forks = float(raw_data.get("forks") or 0)
        total_stars = float(raw_data.get("stars") or 0)
        raw_val = (stars_today * 0.5) + (forks * 1.5) + (total_stars * 0.02)
        return min(100.0, max(25.0, raw_val))

    elif source == "stackexchange":
        score_votes = float(raw_data.get("score_votes") or 0)
        answers = float(raw_data.get("answer_count") or 0)
        views = float(raw_data.get("view_count") or 0)
        raw_val = (score_votes * 8.0) + (answers * 15.0) + min(views * 0.05, 30.0)
        return min(100.0, max(25.0, raw_val))

    elif source == "appsumo":
        reviews = float(raw_data.get("review_count") or 0)
        rating = float(raw_data.get("average_rating") or 0.0)
        raw_val = (reviews * 0.8) + (rating * 12.0)
        return min(100.0, max(30.0, raw_val))

    elif source in ("betalist", "wellfound"):
        return 35.0

    return 30.0


def compute_freshness_score(pub_date: datetime, det_date: datetime) -> float:
    """
    Score de fraîcheur basé sur l'âge de l'opportunité (0 à 100).
    """
    ref_date = pub_date or det_date
    if not ref_date:
        return 50.0

    now = datetime.now(timezone.utc)
    if ref_date.tzinfo is None:
        ref_date = ref_date.replace(tzinfo=timezone.utc)

    hours_old = max(0.0, (now - ref_date).total_seconds() / 3600.0)

    if hours_old <= 24:
        return 100.0
    elif hours_old <= 48:
        return 85.0
    elif hours_old <= 168:  # 7 jours
        return 65.0
    elif hours_old <= 720:  # 30 jours
        return 40.0
    else:
        return 20.0


def compute_signal_score(signal_type: str, title: str, description: str) -> float:
    """
    Score basé sur la nature du signal (Pain Point vs Showcase).
    """
    signal_type = (signal_type or "").lower()
    full_text = f"{title or ''} {description or ''}".lower()

    is_explicit_pain = any(pk in full_text for pk in PAIN_KEYWORDS)

    if signal_type == "pain_point":
        return 100.0 if is_explicit_pain else 90.0
    elif signal_type == "showcase":
        return 60.0 if is_explicit_pain else 50.0
    else:
        return 70.0 if is_explicit_pain else 45.0


def compute_recurrence_score(keywords: set, keyword_sources_map: dict) -> float:
    """
    Évalue si les thématiques de l'opportunité émergent sur plusieurs sources distinctes.
    """
    if not keywords:
        return 35.0

    max_distinct_sources = 1
    for kw in keywords:
        distinct_sources_count = len(keyword_sources_map.get(kw, set()))
        if distinct_sources_count > max_distinct_sources:
            max_distinct_sources = distinct_sources_count

    if max_distinct_sources >= 3:
        return 100.0
    elif max_distinct_sources == 2:
        return 70.0
    else:
        return 35.0


def recalculate_all_scores() -> int:
    """
    Recalcule et met à jour le score composite pour toutes les opportunités en base.
    Sauvegarde le détail du calcul dans raw_data['scoring_breakdown'].
    """
    db = get_session()
    try:
        opportunities = db.query(Opportunity).all()
        total_items = len(opportunities)
        logger.info(f"🚀 Début du recalcul de scoring pour {total_items} opportunités en base...")

        # Étape 1 : Cartographie globale des mots-clés par source
        keyword_sources_map = defaultdict(set)
        items_keywords = {}

        for opp in opportunities:
            text = f"{opp.title} {opp.description or ''}"
            kws = extract_keywords(text)
            items_keywords[opp.id] = kws
            for kw in kws:
                keyword_sources_map[kw].add(opp.source)

        # Étape 2 : Calcul et mise à jour de chaque opportunité
        for opp in opportunities:
            s_eng = compute_engagement_score(opp.source, opp.raw_data)
            s_fresh = compute_freshness_score(opp.published_date, opp.detected_at)
            s_sig = compute_signal_score(opp.signal_type, opp.title, opp.description)
            s_rec = compute_recurrence_score(items_keywords[opp.id], keyword_sources_map)

            # Formule pondérée
            score_total = (0.40 * s_eng) + (0.20 * s_fresh) + (0.25 * s_sig) + (0.15 * s_rec)
            score_final = round(score_total, 1)

            opp.score = score_final

            # Mise à jour avec copie profonde pour forcer SQLAlchemy à persister le JSON
            raw = copy.deepcopy(opp.raw_data) if opp.raw_data else {}
            raw["scoring_breakdown"] = {
                "engagement_score": round(s_eng, 1),
                "freshness_score": round(s_fresh, 1),
                "signal_score": round(s_sig, 1),
                "recurrence_score": round(s_rec, 1),
                "total_score": score_final,
                "formula": "0.40*Eng + 0.20*Fresh + 0.25*Sig + 0.15*Rec",
                "calculated_at": datetime.now(timezone.utc).isoformat(),
            }
            opp.raw_data = raw
            flag_modified(opp, "raw_data")

        db.commit()
        logger.info(f"✅ Recalcul terminé : {total_items} opportunités mises à jour avec succès.")
        return total_items
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur lors du recalcul des scores : {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    count = recalculate_all_scores()
    print(f"\n[OK] {count} opportunites mises a jour avec l'algorithme multicritere.")
