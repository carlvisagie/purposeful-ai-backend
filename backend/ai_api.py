from flask import Flask, request, jsonify
from diagnostic_engine import diagnose_client_responses
from mortality_screen import calculate_mortality_risk
from tier_validator import is_tier_mismatch
from missing_info_warning import check_missing_info

app = Flask(__name__)

@app.route("/api/run_diagnostic", methods=["POST"])
def run_diagnostic():
    data = request.json or {}
    text = data.get("text", "")
    age = data.get("age", 0)
    chronic = data.get("chronic", [])
    habits = data.get("habits", [])
    tier = data.get("tier", "")
    client_data = data.get("client_data", {})

    profile = diagnose_client_responses(text)
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
    app.run(debug=True, host="0.0.0.0", port=10000)


