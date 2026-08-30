import os
import sys
import hmac

# Ajoute la racine du projet au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify, redirect, url_for
from db.database import get_session, init_db
from db.models import Opportunity
from config import PORT, DEBUG
from core.scoring import recalculate_all_scores
from core.business_case import generate_for_opportunity_id
from connectors.hackernews import HackerNewsConnector
from connectors.producthunt import ProductHuntConnector
from connectors.github_trending import GitHubTrendingConnector
from connectors.stackexchange import StackExchangeConnector
from connectors.betalist import BetaListConnector
from connectors.appsumo import AppSumoConnector
from connectors.wellfound import WellfoundConnector

app = Flask(__name__)

# Initialisation automatique des tables au démarrage
try:
    init_db()
except Exception as e:
    print(f"⚠️ Note init_db: {e}")


@app.route("/")
def index():
    db = get_session()
    try:
        # Récupération des filtres
        filtre_source = request.args.get("source", "").strip()
        filtre_status = request.args.get("status", "").strip()
        filtre_signal = request.args.get("signal_type", "").strip()
        filtre_score_tier = request.args.get("score_tier", "").strip()
        recherche = request.args.get("q", "").strip()
        tri = request.args.get("sort_by", "score_desc").strip()

        query = db.query(Opportunity)

        # Application des filtres
        if filtre_source:
            query = query.filter(Opportunity.source == filtre_source)
        if filtre_status:
            query = query.filter(Opportunity.status == filtre_status)
        if filtre_signal:
            query = query.filter(Opportunity.signal_type == filtre_signal)
        
        # Filtre par tranche de score
        if filtre_score_tier == "hot":
            query = query.filter(Opportunity.score >= 70.0)
        elif filtre_score_tier == "qualified":
            query = query.filter(Opportunity.score >= 50.0, Opportunity.score < 70.0)
        elif filtre_score_tier == "cold":
            query = query.filter(Opportunity.score < 50.0)

        if recherche:
            terme = f"%{recherche}%"
            query = query.filter((Opportunity.title.ilike(terme)) | (Opportunity.description.ilike(terme)))

        # Tri
        if tri == "score_desc":
            query = query.order_by(Opportunity.score.desc(), Opportunity.detected_at.desc())
        elif tri == "score_asc":
            query = query.order_by(Opportunity.score.asc(), Opportunity.detected_at.desc())
        elif tri == "date_asc":
            query = query.order_by(Opportunity.detected_at.asc())
        else:  # date_desc par défaut
            query = query.order_by(Opportunity.detected_at.desc())

        items = query.limit(100).all()

        # Statistiques globales pour les KPI cards
        total_opportunites = db.query(Opportunity).count()
        nb_hot_score = db.query(Opportunity).filter(Opportunity.score >= 70.0).count()
        nb_qualified_score = db.query(Opportunity).filter(Opportunity.score >= 50.0, Opportunity.score < 70.0).count()
        nb_cold_score = db.query(Opportunity).filter(Opportunity.score < 50.0).count()
        nb_bc_generes = db.query(Opportunity).filter(Opportunity.business_case.isnot(None)).count()
        
        # Sources et statuts
        toutes_sources = [s[0] for s in db.query(Opportunity.source).distinct().all() if s[0]]
        tous_statuts = ["nouveau", "qualifie", "en_cours", "rejete", "business_case_genere"]
        tous_signaux = [s[0] for s in db.query(Opportunity.signal_type).distinct().all() if s[0]]

        return render_template(
            "index.html",
            items=items,
            total=len(items),
            total_global=total_opportunites,
            nb_hot_score=nb_hot_score,
            nb_qualified_score=nb_qualified_score,
            nb_cold_score=nb_cold_score,
            nb_bc_generes=nb_bc_generes,
            toutes_sources=toutes_sources,
            tous_statuts=tous_statuts,
            tous_signaux=tous_signaux,
            filtre_source=filtre_source,
            filtre_status=filtre_status,
            filtre_signal=filtre_signal,
            filtre_score_tier=filtre_score_tier,
            recherche=recherche,
            tri=tri,
        )
    finally:
        db.close()


@app.route("/opportunity/<int:item_id>", methods=["GET"])
def get_opportunity(item_id):
    """API endpoint pour charger les détails d'une opportunité en modal."""
    db = get_session()
    try:
        item = db.query(Opportunity).filter(Opportunity.id == item_id).first()
        if not item:
            return jsonify({"error": "Opportunité introuvable"}), 404
        return jsonify(item.to_dict())
    finally:
        db.close()


@app.route("/opportunity/<int:item_id>/status", methods=["POST"])
def update_status(item_id):
    """Mise à jour rapide du statut de traitement depuis l'interface."""
    db = get_session()
    try:
        item = db.query(Opportunity).filter(Opportunity.id == item_id).first()
        if not item:
            return jsonify({"success": False, "error": "Opportunité introuvable"}), 404

        nouveau_statut = request.form.get("status") or (request.json and request.json.get("status"))
        if nouveau_statut:
            item.status = nouveau_statut
            db.commit()
            return jsonify({"success": True, "new_status": item.status})
        return jsonify({"success": False, "error": "Statut invalide"}), 400
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@app.route("/opportunity/<int:item_id>/generate-business-case", methods=["POST"])
def generate_single_business_case(item_id):
    """Génère à la demande un Business Case pour une opportunité spécifique."""
    try:
        bc = generate_for_opportunity_id(item_id)
        return jsonify({"success": True, "business_case": bc})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/recalculate-scores", methods=["POST"])
def trigger_recalculate():
    """Déclenche le recalcul des scores multicritères pour toutes les opportunités."""
    try:
        updated_count = recalculate_all_scores()
        return jsonify({"success": True, "updated_count": updated_count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/admin/trigger-collection", methods=["POST", "GET"])
def admin_trigger_collection():
    """
    Route sécurisée pour déclencher la collecte multi-sources et le scoring en production.
    Protégée par la variable d'environnement ADMIN_TRIGGER_KEY.
    """
    expected_key = os.environ.get("ADMIN_TRIGGER_KEY", "").strip()
    if not expected_key:
        return jsonify({
            "success": False,
            "error": "La variable d'environnement ADMIN_TRIGGER_KEY n'est pas configurée sur le serveur."
        }), 403

    # Récupération de la clé depuis l'en-tête, le query param ou le corps JSON
    auth_header = request.headers.get("X-Admin-Key") or request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        provided_key = auth_header.replace("Bearer ", "").strip()
    else:
        provided_key = auth_header.strip()

    if not provided_key:
        provided_key = request.args.get("key", "").strip()
    if not provided_key and request.is_json:
        provided_key = (request.json or {}).get("key", "").strip()

    if not hmac.compare_digest(provided_key, expected_key):
        return jsonify({"success": False, "error": "Accès non autorisé : Clé ADMIN_TRIGGER_KEY invalide ou manquante."}), 401

    # Exécution sécurisée de la collecte
    connecteurs = [
        HackerNewsConnector(tag="show_hn", max_items=25),
        HackerNewsConnector(tag="ask_hn", max_items=15),
        ProductHuntConnector(max_items=20),
        GitHubTrendingConnector(max_items=20),
        StackExchangeConnector(site="softwarerecs", max_items=20),
        BetaListConnector(max_items=20),
        AppSumoConnector(max_items=20),
        WellfoundConnector(max_items=15),
    ]

    total_nouveaux = 0
    total_doublons = 0
    statistiques_sources = {}
    erreurs = []

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
                "statut": "Succès"
            }
        except Exception as e:
            erreurs.append(f"{nom_source}: {str(e)}")
            statistiques_sources[nom_source] = {
                "nouveaux": 0,
                "doublons": 0,
                "statut": f"Erreur ({str(e)})"
            }

    # Recalcul automatique du scoring
    try:
        nb_scores = recalculate_all_scores()
    except Exception as e:
        nb_scores = 0
        erreurs.append(f"Scoring: {str(e)}")

    return jsonify({
        "success": True,
        "message": "Collecte multi-sources et scoring exécutés avec succès en production.",
        "total_nouvelles_opportunites": total_nouveaux,
        "total_doublons_ignores": total_doublons,
        "total_opportunites_scorees": nb_scores,
        "statistiques_par_source": statistiques_sources,
        "erreurs": erreurs
    })


@app.route("/admin/diagnostic/betalist", methods=["GET", "POST"])
def admin_diagnostic_betalist():
    """Route de diagnostic avancée pour inspecter la réponse HTTP et le parsing de BetaList depuis Render."""
    expected_key = os.environ.get("ADMIN_TRIGGER_KEY", "").strip()
    if not expected_key:
        return jsonify({
            "success": False,
            "error": "La variable d'environnement ADMIN_TRIGGER_KEY n'est pas configurée sur le serveur."
        }), 403

    auth_header = request.headers.get("X-Admin-Key") or request.headers.get("Authorization", "")
    provided_key = auth_header.replace("Bearer ", "").strip() if auth_header.startswith("Bearer ") else auth_header.strip()
    if not provided_key:
        provided_key = request.args.get("key", "").strip()
    if not provided_key and request.is_json:
        provided_key = (request.json or {}).get("key", "").strip()

    if not hmac.compare_digest(provided_key, expected_key):
        return jsonify({"success": False, "error": "Accès non autorisé : Clé ADMIN_TRIGGER_KEY invalide."}), 401

    import requests
    from bs4 import BeautifulSoup

    render_commit = os.environ.get("RENDER_GIT_COMMIT") or os.environ.get("GIT_COMMIT") or "Non défini par Render"
    
    outbound_ip = "Inconnue"
    try:
        ip_resp = requests.get("https://api.ipify.org?format=json", timeout=5)
        outbound_ip = ip_resp.json().get("ip", "Inconnue")
    except Exception as e:
        outbound_ip = f"Erreur IP: {e}"

    betalist_diag = {}
    try:
        connector = BetaListConnector(max_items=10)
        raw_response = connector.fetch("https://betalist.com/")
        betalist_diag["status_code"] = raw_response.status_code
        betalist_diag["headers"] = dict(raw_response.headers)
        betalist_diag["html_length"] = len(raw_response.text)
        betalist_diag["first_500_chars"] = raw_response.text[:500]

        soup = BeautifulSoup(raw_response.text, "html.parser")
        all_links = soup.find_all("a", href=True)
        startup_links = [(a["href"], a.get_text(strip=True), a.get("class")) for a in all_links if a["href"].startswith("/startups/")]
        betalist_diag["total_a_tags"] = len(all_links)
        betalist_diag["total_startup_links"] = len(startup_links)
        betalist_diag["sample_startup_links"] = startup_links[:10]

        scraped_items = connector.scrape()
        betalist_diag["scraped_items_count"] = len(scraped_items)
        betalist_diag["scraped_items"] = scraped_items

    except Exception as e:
        betalist_diag["error"] = str(e)
        betalist_diag["error_type"] = type(e).__name__

    return jsonify({
        "success": True,
        "render_commit_sha": render_commit,
        "outbound_ip": outbound_ip,
        "betalist_diagnostic": betalist_diag
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)

