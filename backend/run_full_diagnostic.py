from diagnostic_engine import diagnose_client_responses
from mortality_screen import calculate_mortality_risk
from tier_validator import is_tier_mismatch
from missing_info_warning import check_missing_info

sample_text = """
I'm tired all the time, not sleeping, in pain, and I feel like I’ve lost purpose. 
Also really stressed about debt and can’t keep my finances stable.
"""

client_data = {
    "symptoms": "",
    "goals": "improve energy",
    "medications": None,
    "emergency_contact": ""
}

profile = diagnose_client_responses(sample_text)
risk = calculate_mortality_risk(age=63, chronic_conditions=["hypertension"], lifestyle_flags=["poor sleep"])
tier_issue = is_tier_mismatch(risk, selected_tier="Shift Session")
missing = check_missing_info(client_data)

print("🧠 Diagnostic Flags:", profile)
print("🔬 Mortality Risk:", risk)
print("🧭 Tier Mismatch:", tier_issue)
print("⚠️ Missing Info:", missing)
