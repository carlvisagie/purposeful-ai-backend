def is_tier_mismatch(risk_level, selected_tier):
    recommended = {
        "low": "Shift Session",
        "elevated": "Clarity+",
        "critical": "Mastery"
    }
    return selected_tier.lower() not in recommended[risk_level].lower()
