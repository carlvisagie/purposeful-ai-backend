from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
import os
from config import Config
from models import db
from routes.ai import ai
from routes.auth import auth_bp
from routes.payments import payments_bp
from routes.crisis import crisis_bp
from routes.dashboard import dashboard_bp
from diagnostic_engine import diagnose_client_responses, calculate_crisis_score
from mortality_screen import calculate_mortality_risk
from tier_validator import is_tier_mismatch
from missing_info_warning import check_missing_info

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
CORS(app)

app.register_blueprint(ai, url_prefix="/api/ai")
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(payments_bp, url_prefix="/api/payments")
app.register_blueprint(crisis_bp, url_prefix="/api/crisis")
app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
@app.route("/")
def index():
    return "✅ Purposeful Live API is running."
@app.route("/api/get_payment_link", methods=["POST"])
def get_payment_link():
    data = request.get_json()
    selected_tier = data.get("tier", "").strip()
    
    tier_links = {
        "Shift Session": "/api/payments/create-payment-intent",
        "Clarity+": "/api/payments/create-payment-intent", 
        "Mastery": "/api/payments/create-payment-intent"
    }
    
    payment_endpoint = tier_links.get(selected_tier)

    if not payment_endpoint:
        return jsonify({"error": "Invalid tier selected."}), 400

    return jsonify({
        "tier": selected_tier, 
        "payment_endpoint": payment_endpoint,
        "message": "Use the payment endpoint with authentication to create payment intent"
    })

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

    profile = diagnose_client_responses(text_input)
    crisis_analysis = calculate_crisis_score(text_input, profile)
    risk = calculate_mortality_risk(age, chronic, habits)
    mismatch = is_tier_mismatch(risk, tier)
    missing = check_missing_info(client_data)

    return jsonify({
        "profile": profile,
        "crisis_analysis": {
            "score": crisis_analysis["score"],
            "severity": crisis_analysis["severity"].name,
            "indicators": crisis_analysis["indicators"],
            "requires_escalation": crisis_analysis["requires_escalation"]
        },
        "mortality_risk": risk,
        "tier_mismatch": mismatch,
        "missing_info": missing
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)





