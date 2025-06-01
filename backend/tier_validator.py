def is_tier_mismatch(risk_level, selected_tier):
    risk_map = {
        "low": "Shift Session",
        "elevated": "Clarity+",
        "critical": "Mastery"
    }
    return selected_tier.lower() not in risk_map[risk_level].lower()
