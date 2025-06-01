from flask import Flask, request, jsonify
from backend.diagnostic_engine import diagnose_client_responses
from mortality_screen import calculate_mortality_risk
from tier_validator import is_tier_mismatch
from missing_info_warning import check_missing_info

app = Flask(__name__)

@app.route("/api/run_diagnostic", methods=["POST"])
def run_diagnostic():
    data = request.json

    # Expect: { "text": "...", "age": 63, "tier": "Shift Session", "chronic": [...], "lifestyle": [...], "client_data": {...} }

    text = data.get("text", "")
    age = data.get("age", 0)
    tier = data.get("tier", "")
    chronic = data.get("chronic", [])
    lifestyle = data.get("lifestyle", [])
    client_data = data.get("client_data", {})

    profile = diagnose_client_responses(text)
    risk = calculate_mortality_risk(age, chronic, lifestyle)
    mismatch = is_tier_mismatch(risk, tier)
    missing = check_missing_info(client_data)

    return jsonify({
        "flags": profile,
        "risk": risk,
        "tier_mismatch": mismatch,
        "missing_info": missing
    })

if __name__ == "__main__":
    app.run(debug=True)


