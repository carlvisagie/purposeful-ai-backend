def calculate_mortality_risk(age, chronic_conditions, lifestyle_flags):
    risk = 0
    if age > 55:
        risk += 1
    if len(chronic_conditions) > 0:
        risk += 2
    if "smoking" in lifestyle_flags or "poor sleep" in lifestyle_flags:
        risk += 1
    if risk >= 3:
        return "critical"
    elif risk == 2:
        return "elevated"
    return "low"
