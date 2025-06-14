from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from routes.ai import ai
from diagnostic_engine import diagnose_client_responses
from mortality_screen import calculate_mortality_risk
from tier_validator import is_tier_mismatch
from missing_info_warning import check_missing_info
TIER_LINKS = {
    "Shift Session": "https://paypal.me/purposefulshift/35",
    "Clarity+": "https://paypal.me/purposefulclarity/75",
    "Mastery": "https://paypal.me/purposefulmastery/195"
}

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return "✅ Purposeful Live API is running."
@app.route("/api/get_payment_link", methods=["POST"])
def get_payment_link():
    data = request.get_json()
    selected_tier = data.get("tier", "").strip()
    payment_link = TIER_LINKS.get(selected_tier)

    if not payment_link:
        return jsonify({"error": "Invalid tier selected."}), 400

    return jsonify({"tier": selected_tier, "payment_link": payment_link})

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
    risk = calculate_mortality_risk(age, chronic, habits)
    mismatch = is_tier_mismatch(risk, tier)
    missing = check_missing_info(client_data)

    return jsonify({
        "profile": profile,
        "mortality_risk": risk,
        "tier_mismatch": mismatch,
        "missing_info": missing
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)





