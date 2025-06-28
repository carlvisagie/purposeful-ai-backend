from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_login import LoginManager, login_required, current_user
import os
from routes.ai import ai
from routes.coach import coach
from routes.admin import admin
from auth import auth
from diagnostic_engine import diagnose_client_responses
from mortality_screen import calculate_mortality_risk
from tier_validator import is_tier_mismatch
from missing_info_warning import check_missing_info
from crisis_detector import CrisisDetector
from database import init_database
from models import db, User, Session, Diagnostic
TIER_LINKS = {
    "Shift Session": "https://paypal.me/purposefulshift/35",
    "Clarity+": "https://paypal.me/purposefulclarity/75",
    "Mastery": "https://paypal.me/purposefulmastery/195"
}

app = Flask(__name__)
CORS(app)

init_database(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(ai, url_prefix="/api/ai")
app.register_blueprint(auth, url_prefix="/api/auth")
app.register_blueprint(coach, url_prefix="/api/coach")
app.register_blueprint(admin, url_prefix="/api/admin")

crisis_detector = CrisisDetector()
@app.route("/")
def index():
    return "✅ Purposeful Live API is running."
@app.route("/api/get_payment_link", methods=["POST"])
def get_payment_link():
    data = request.get_json()
    selected_tier = data.get("tier", "").strip()
    session_id = data.get("session_id")
    payment_link = TIER_LINKS.get(selected_tier)

    if not payment_link:
        return jsonify({"error": "Invalid tier selected."}), 400

    if session_id:
        session_record = Session.query.get(session_id)
        if session_record:
            session_record.tier = selected_tier
            db.session.commit()

    return jsonify({
        "tier": selected_tier, 
        "payment_link": payment_link,
        "session_id": session_id
    })

@app.route("/api/payment_webhook", methods=["POST"])
def payment_webhook():
    data = request.get_json()
    session_id = data.get("session_id")
    payment_status = data.get("status", "completed")
    
    if session_id:
        session_record = Session.query.get(session_id)
        if session_record:
            session_record.payment_status = payment_status
            db.session.commit()
            return jsonify({"message": "Payment status updated"}), 200
    
    return jsonify({"error": "Session not found"}), 404

@app.route("/api/run_diagnostic", methods=["POST"])
def run_diagnostic():
    data = request.get_json()

    if not data or "text" not in data:
        return jsonify({"error": "Missing or invalid JSON input."}), 400

    text_input = data["text"]
    age = data.get("age", 0)
    chronic = data.get("chronic", [])
    habits = data.get("habits", [])
    tier = data.get("tier", "")
    client_data = data.get("client_data", {})
    user_id = data.get("user_id")

    profile = diagnose_client_responses(text_input)
    risk = calculate_mortality_risk(age, chronic, habits)
    mismatch = is_tier_mismatch(risk, tier)
    missing = check_missing_info(client_data)
    crisis_analysis = crisis_detector.analyze_text(text_input, user_id)

    session_record = Session(
        user_id=user_id,
        session_data={
            "text_input": text_input,
            "age": age,
            "chronic_conditions": chronic,
            "habits": habits,
            "client_data": client_data
        },
        tier=tier,
        payment_status='pending'
    )
    db.session.add(session_record)
    db.session.commit()

    diagnostic_record = Diagnostic(
        session_id=session_record.id,
        profile=profile,
        mortality_risk=risk,
        tier_mismatch=mismatch,
        missing_info=missing
    )
    db.session.add(diagnostic_record)
    db.session.commit()

    return jsonify({
        "session_id": session_record.id,
        "profile": profile,
        "mortality_risk": risk,
        "tier_mismatch": mismatch,
        "missing_info": missing,
        "crisis_analysis": crisis_analysis
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)





