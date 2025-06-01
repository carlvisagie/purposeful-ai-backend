from flask import Flask, request, jsonify
from flask_cors import CORS

from diagnostic_engine import diagnose_client_responses
from mortality_screen import calculate_mortality_risk
from tier_validator import is_tier_mismatch
from missing_info_warning import check_missing_info

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return "✅ Purposeful Live API is running."

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
    app.run(debug=True)



