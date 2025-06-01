def rate_client_session(rating):
    if rating >= 4.5:
        return "🔥 Excellent session — you're on fire!"
    elif rating >= 3.5:
        return "⚠️ Decent session — room to tighten up."
    else:
        return "🚨 Caution — improvement needed. Suggest a follow-up."

# Test the function with different client ratings
print(rate_client_session(4.7))
print(rate_client_session(3.8))
print(rate_client_session(2.9))
from flag_matrix import FLAG_MATRIX

def diagnose_client_responses(text_input):
    profile = {k: [] for k in FLAG_MATRIX}
    for category, flags in FLAG_MATRIX.items():
        for flag in flags:
            if flag.lower() in text_input.lower():
                profile[category].append(flag)
    return profile
def calculate_mortality_risk(age, chronic_conditions, lifestyle_flags):
    risk = 0
    if age > 55: risk += 1
    if len(chronic_conditions) > 0: risk += 2
    if "smoking" in lifestyle_flags or "poor sleep" in lifestyle_flags:
        risk += 1
    if risk >= 3: return "critical"
    elif risk == 2: return "elevated"
    return "low"
def is_tier_mismatch(risk_level, selected_tier):
    recommended = {
        "low": "Shift Session",
        "elevated": "Clarity+",
        "critical": "Mastery"
    }
    return selected_tier.lower() not in recommended[risk_level].lower()
REQUIRED_FIELDS = ["symptoms", "goals", "medications", "emergency_contact"]

def check_missing_info(client_data):
    return [field for field in REQUIRED_FIELDS if not client_data.get(field)]
FLAG_MATRIX = {
    "mental_health": ["anxiety", "burnout", "overthinking", "depression", "negative self-talk"],
    "emotional": ["grief", "emotional regulation", "low self-esteem", "loneliness"],
    "spiritual": ["lack of purpose", "faith struggles", "existential crisis"],
    "physical": ["chronic pain", "poor sleep", "fatigue", "weight issues"],
    "financial": ["debt", "instability", "financial anxiety", "income issues"]
}
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

